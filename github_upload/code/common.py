# -*- coding: utf-8 -*-
"""
common.py
---------
双库共用的统一算法（AKI 重算 / MAP 低暴露负荷 / KDIGO 尿量分期 / 模型应用）。
INSPIRE 与 MOVER 必须调用同一份实现，才能保证"暴露同算法、结局同口径"。
"""

import numpy as np
import pandas as pd

GAP_CAP_MIN = 30.0          # 相邻 MAP 记录间隔超过 30 min 视为记录中断，不计入累计时长
FOLLOWUP_MIN = 10080.0      # 术后 7 天
AKI48_MIN = 2880.0          # 48 小时


# ---------------------------------------------------------------- MAP 负荷
def map_burden(series, op_col="op_id", t_col="t_min", v_col="map",
               op_duration_min=None, gap_cap=GAP_CAP_MIN, tag="art"):
    """
    术中 MAP 时序 → 低血压负荷指标。

    采用 LOCF 阶梯积分：相邻两次测量的时间差归属于"前一次测量值"，
    与临床监护仪的面积算法一致。间隔 > gap_cap 的片段丢弃（记录中断）。

    返回 DataFrame(index=op_id)：
      {tag}_n              有效测量次数
      {tag}_cover_min      覆盖时长（分钟）
      {tag}_mean           时间加权平均 MAP
      {tag}_min / _sd      最低值 / 时间加权标准差
      {tag}_below65_min    MAP<65 mmHg 累计分钟数
      {tag}_auc65          MAP<65 的曲线下面积（mmHg·min）
      {tag}_burden_pct     below65_min / 手术时长 × 100
      {tag}_coverage_pct   cover_min / 手术时长 × 100
    """
    recs = []
    for op, g in series.groupby(op_col, sort=False):
        g = g.sort_values(t_col)
        t = pd.to_numeric(g[t_col], errors="coerce").to_numpy(float)
        v = pd.to_numeric(g[v_col], errors="coerce").to_numpy(float)
        ok = ~(np.isnan(t) | np.isnan(v))
        t, v = t[ok], v[ok]
        if len(v) < 2:
            continue
        dt = np.clip(np.diff(t), 0, gap_cap)
        v0 = v[:-1]
        dur = float(dt.sum())
        if dur <= 0:
            continue
        twa = float((v0 * dt).sum() / dur)
        recs.append({
            op_col: op,
            f"{tag}_n": int(len(v)),
            f"{tag}_cover_min": dur,
            f"{tag}_mean": twa,
            f"{tag}_min": float(v.min()),
            f"{tag}_sd": float(np.sqrt((((v0 - twa) ** 2) * dt).sum() / dur)),
            f"{tag}_below65_min": float(dt[v0 < 65].sum()),
            f"{tag}_auc65": float((np.clip(65 - v0, 0, None) * dt).sum()),
        })
    out = pd.DataFrame(recs)
    if out.empty:
        return out
    out = out.set_index(op_col)
    if op_duration_min is not None:
        od = pd.Series(op_duration_min).reindex(out.index).replace(0, np.nan)
        out[f"{tag}_burden_pct"] = out[f"{tag}_below65_min"] / od * 100
        out[f"{tag}_coverage_pct"] = out[f"{tag}_cover_min"] / od * 100
    return out


# ---------------------------------------------------------------- KDIGO
def kdigo_creatinine(scr_series, op_col="op_id", t_col="t_min", v_col="scr",
                     baseline=None, rrt=None, followup=FOLLOWUP_MIN):
    """
    KDIGO 肌酐-only 分期（锚点 = 麻醉开始，术后 0 ~ followup 分钟）。

    参数
      scr_series : 术后 SCr 时序（长表）
      baseline   : Series(index=op_id) 基线 SCr（术前 7d 最低）
      rrt        : Series(index=op_id) 术后 CRRT 0/1，可空
    返回 DataFrame(index=op_id): peak_48h, peak_7d, max_delta_48h, aki_stage, aki
    """
    s = scr_series.copy()
    s[v_col] = pd.to_numeric(s[v_col], errors="coerce")
    s = s[(s[t_col] >= 0) & (s[t_col] <= followup)].dropna(subset=[v_col])
    s = s[s[v_col] > 0].sort_values([op_col, t_col])

    rows = []
    for op, g in s.groupby(op_col, sort=False):
        t = g[t_col].to_numpy(float)
        v = g[v_col].to_numpy(float)
        peak7 = v.max()
        m48 = t <= AKI48_MIN
        peak48 = v[m48].max() if m48.any() else np.nan
        dmax = 0.0
        for i in range(len(v)):
            lo = np.searchsorted(t, t[i] - AKI48_MIN, side="left")
            dmax = max(dmax, v[i] - v[lo:i + 1].min())
        rows.append({op_col: op, "peak_7d": peak7, "peak_48h": peak48, "max_delta_48h": dmax})
    out = pd.DataFrame(rows).set_index(op_col)

    out["baseline"] = pd.Series(baseline).reindex(out.index) if baseline is not None else np.nan
    ratio = out["peak_7d"] / out["baseline"]

    stage = pd.Series(0, index=out.index, dtype=int)
    stage[ratio >= 1.5] = 1
    stage[ratio >= 2.0] = 2
    stage[ratio >= 3.0] = 3
    stage[(out["max_delta_48h"] >= 0.3) & (stage < 1)] = 1
    stage[(out["peak_7d"] >= 4.0) & (out["max_delta_48h"] >= 0.3)] = 3
    if rrt is not None:
        r = pd.Series(rrt).reindex(out.index).fillna(0)
        stage[r == 1] = 3
    out["aki_stage"] = stage.astype(int)
    out["aki"] = (out["aki_stage"] >= 1).astype(int)
    return out


def kdigo_urine(uo_series, weight_kg, op_col="op_id", t_col="t_min", v_col="uo_ml",
                window_h=1.0):
    """
    KDIGO 尿量路径分期（MOVER 专用，用于敏感性分析）。
      Stage 1: <0.5 mL/kg/h 连续 ≥6 h
      Stage 2: <0.5 mL/kg/h 连续 ≥12 h
      Stage 3: <0.3 mL/kg/h 连续 ≥24 h，或 ≥12 h 无尿
    以固定小时窗（默认 1 h）重采样后滑动评估。
    """
    s = uo_series.copy()
    s[v_col] = pd.to_numeric(s[v_col], errors="coerce")
    s = s.dropna(subset=[v_col]).sort_values([op_col, t_col])

    rows = []
    for op, g in s.groupby(op_col, sort=False):
        t = g[t_col].to_numpy(float)
        v = g[v_col].to_numpy(float)
        wt = float(pd.Series(weight_kg).get(op, np.nan))
        if not np.isfinite(wt) or wt <= 0:
            rows.append({op_col: op, "uo_stage": np.nan})
            continue
        # 重采样为小时窗
        bins = np.arange(0, FOLLOWUP_MIN + 60, 60)
        idx = np.clip(np.digitize(t, bins) - 1, 0, len(bins) - 2)
        vol = np.zeros(len(bins) - 1)
        np.add.at(vol, idx, v)
        rate = vol / wt  # mL/kg/h
        stage = 0
        for w, need in [(6, 0.5), (12, 0.5)]:
            if len(rate) >= w:
                run = np.convolve(rate, np.ones(w), "valid") / w
                if (run < need).any():
                    stage = max(stage, 1 if w == 6 else 2)
        if len(rate) >= 24:
            run = np.convolve(rate, np.ones(24), "valid") / 24
            if (run < 0.3).any():
                stage = 3
        if 12 <= len(rate) and (vol[:12].sum() == 0):
            stage = 3
        rows.append({op_col: op, "uo_stage": int(stage), "uo_rate_mean": float(np.nanmean(rate))})
    return pd.DataFrame(rows).set_index(op_col)


# ---------------------------------------------------------------- 模型应用
def apply_logit(params, data):
    """params: dict{term: beta}，data 需含全部 term（除 Intercept）。返回预测概率。"""
    lp = np.full(len(data), params["Intercept"], dtype=float)
    for k, b in params.items():
        if k == "Intercept":
            continue
        lp = lp + b * pd.to_numeric(data[k], errors="coerce").fillna(0).to_numpy(float)
    return 1 / (1 + np.exp(-lp))


COVARIATES = ["age", "male", "asa_class", "op_duration_h", "baseline_scr",
              "preop_acei_arb", "open_surgery"]
