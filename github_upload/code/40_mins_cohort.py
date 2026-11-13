# -*- coding: utf-8 -*-
"""骨科队列 MINS 分析集构建。

人群：成人骨科手术 + 全身麻醉
  INSPIRE  骨科（OS）全部手术 10,002 台
  MOVER    184 个骨科 OP 码 6,940 台
暴露：MAP<65 累计分钟 / 麻醉时长 × 100（平台算法，两库同构）
结局：MINS = 术后 72h 内肌钙蛋白峰值 > 26 ng/L（0.026 ng/mL，Abbott hs-cTnI 99th URL；
      MOVER 用平台 mins 变量，其阈值经数据反推同为 26 ng/L / 常规法 0.04 ng/mL）
分析人群：术后 72h 内测过肌钙蛋白者（监测亚组），选择过程单列表报告。
次要结局：AKI（KDIGO 肌酐口径，同 v3 方案）。
"""
import os
import numpy as np
import pandas as pd

RAW = os.path.join("data", "web")
OUT = "output"
TN_URL = 0.026  # ng/mL


def kdigo_stage(base, p48, p7):
    if pd.isna(base) or base <= 0:
        return np.nan
    ratios, deltas = [], []
    if pd.notna(p48):
        ratios.append(p48 / base); deltas.append(p48 - base)
    if pd.notna(p7):
        ratios.append(p7 / base); deltas.append(p7 - base)
    if not ratios:
        return np.nan
    r, delta = max(ratios), max(deltas)
    peak = max([x for x in (p48, p7) if pd.notna(x)], default=-1)
    if r >= 3.0 or (delta >= 0.3 and peak >= 4.0):
        return 3
    if r >= 2.0:
        return 2
    if r >= 1.5:
        return 1
    if delta >= 0.3:
        return 1
    return 0


def mdrd_scr(age, female, egfr=75.0):
    if pd.isna(age) or age <= 0:
        return np.nan
    k = 175.0 * (age ** -0.203) * (0.742 if female else 1.0) / egfr
    return float(k ** (1 / 1.154))


def comorb(codes):
    s = str(codes or "").upper()
    tok = set(t.strip()[:5] for t in s.replace(",", "\n").split("\n") if t.strip())
    hit = lambda *p: int(any(t.startswith(x) for t in tok for x in p))
    return {"dm": hit("E10", "E11", "E12", "E13", "E14", "250"),
            "htn": hit("I10", "I11", "I12", "I13", "I15", "401", "402", "403", "404"),
            "chd": hit("I20", "I21", "I22", "I24", "I25", "410", "411", "412", "413", "414"),
            "hf": hit("I50", "428"),
            "ckd": hit("N18", "N19", "585", "586")}


def finish(d, label):
    d["monitored"] = d["tn_post72h"].notna().astype(int)
    d["mins"] = np.where(d["monitored"] == 1, (d["tn_post72h"] > TN_URL).astype(float), np.nan)
    d["mins7"] = np.where(d["tn_post7d"].notna(), (d["tn_post7d"] > TN_URL).astype(float), np.nan)
    d["mins_04"] = np.where(d["monitored"] == 1, (d["tn_post72h"] > 0.04).astype(float), np.nan)
    d["mins_10"] = np.where(d["monitored"] == 1, (d["tn_post72h"] > 0.10).astype(float), np.nan)
    d["aki_stage"] = [kdigo_stage(b, a, c) for b, a, c in
                      zip(d["scr_base"], d["scr_p48"], d["scr_p7"])]
    d["aki"] = (d["aki_stage"] >= 1).astype(float)
    d.loc[d["aki_stage"].isna(), "aki"] = np.nan
    d["burden_pct"] = np.where(d["ane_h"] > 0, d["below65"] / (d["ane_h"] * 60) * 100, np.nan)
    d["burden10"] = d["burden_pct"] / 10.0
    cm = d["patient_diagnosis_codes"].apply(comorb).apply(pd.Series) if "patient_diagnosis_codes" in d else \
         d["codes"].apply(comorb).apply(pd.Series)
    d = pd.concat([d, cm], axis=1)
    mon = d[d["monitored"] == 1]
    print(f"[{label}] 队列 {len(d)}  监测 {len(mon)} ({len(mon)/len(d)*100:.1f}%)  "
          f"MINS {int(mon.mins.sum())} ({mon.mins.mean()*100:.1f}%)  "
          f"负荷中位(监测) {mon.burden_pct.median():.1f}%  "
          f"AKI 可评估 {int(d.aki.notna().sum())}", flush=True)
    return d


def build_inspire():
    base = pd.read_excel(os.path.join(RAW, "inspire_ortho_tn_post72h.xlsx"), sheet_name="数据")
    get = lambda f, col: pd.read_excel(os.path.join(RAW, f), sheet_name="数据").set_index("op_id")[col]
    d = base[["op_id", "subject_id", "sex", "age", "asa", "op_duration", "anesthesia_duration",
              "surgery_approach", "icu_admission", "hospital_expire_flag", "los_hospital", "emop",
              "weight", "height", "surgery_seq", "patient_diagnosis_codes",
              "mbp_below_65_min", "troponin_i_max"]].copy()
    d = d.rename(columns={"troponin_i_max": "tn_post72h"})
    idx = d.set_index("op_id").index
    d["tn_post7d"] = pd.to_numeric(get("inspire_ortho_tn_post7d.xlsx", "troponin_i_max"), errors="coerce").reindex(idx).values
    d["tn_pre7d"] = pd.to_numeric(get("inspire_ortho_tn_pre7d.xlsx", "troponin_i_last"), errors="coerce").reindex(idx).values
    b7 = pd.to_numeric(get("inspire_ortho_cr_pre7d.xlsx", "creatinine_min"), errors="coerce").reindex(idx)
    b30 = pd.to_numeric(get("inspire_ortho_cr_pre30d.xlsx", "creatinine_min"), errors="coerce").reindex(idx)
    d["scr_base"] = b7.fillna(b30).values
    d["baseline_src"] = np.where(b7.notna(), "7d", np.where(b30.notna(), "30d", "none"))
    d["scr_p48"] = pd.to_numeric(get("inspire_ortho_cr_post48h.xlsx", "creatinine_max"), errors="coerce").reindex(idx).values
    d["scr_p7"] = pd.to_numeric(get("inspire_ortho_cr_post7d.xlsx", "creatinine_max"), errors="coerce").reindex(idx).values
    d["age"] = pd.to_numeric(d["age"], errors="coerce")
    d["male"] = (d["sex"].astype(str).str.upper().str[0] == "M").astype(int)
    d["asa_class"] = pd.to_numeric(d["asa"], errors="coerce")
    d["ane_h"] = pd.to_numeric(d["anesthesia_duration"], errors="coerce") / 60.0
    d["op_h"] = pd.to_numeric(d["op_duration"], errors="coerce") / 60.0
    d["weight_kg"] = pd.to_numeric(d["weight"], errors="coerce")
    d["height_cm"] = pd.to_numeric(d["height"], errors="coerce")
    d["bmi"] = d["weight_kg"] / (d["height_cm"] / 100) ** 2
    d["emergency"] = (d["emop"].astype(str).str.lower() == "true").astype(int)
    d["open_surgery"] = (d["surgery_approach"].astype(str).str.lower() == "open").astype(int)
    d["below65"] = pd.to_numeric(d["mbp_below_65_min"], errors="coerce")
    d["icu"] = (d["icu_admission"].astype(str).str.lower() == "true").astype(int)
    d["death"] = pd.to_numeric(d["hospital_expire_flag"], errors="coerce").fillna(0).astype(int)
    d["cohort"] = "INSPIRE-Ortho"
    d = finish(d, "INSPIRE-Ortho")
    d.to_csv(os.path.join(OUT, "inspire_ortho_analytic.csv"), index=False, encoding="utf-8-sig")
    return d


def build_mover():
    m = pd.read_csv(os.path.join(RAW, "mover_ortho_main.csv.gz"))
    get = lambda tag: pd.read_csv(os.path.join(RAW, f"mover_ortho_lab_{tag}.csv.gz")).set_index("log_id")
    d = m[["log_id", "age_years", "sex", "asa_rating_c", "primary_procedure_nm", "height_cm", "weight_kg",
           "bmi", "anes_duration_min", "or_duration_min", "icu_admin_flag", "in_hosp_mortality",
           "mi_dx", "mins", "mins_peak_hs_tni_ngl", "mins_peak_tni_ngml", "mbp_below_65min",
           "patient_diagnosis_codes" if "patient_diagnosis_codes" in m else "visit_diagnosis_codes"]].copy()
    d = d.rename(columns={d.columns[-1]: "codes"})
    hs = pd.to_numeric(d.pop("mins_peak_hs_tni_ngl"), errors="coerce") / 1000.0
    cv = pd.to_numeric(d.pop("mins_peak_tni_ngml"), errors="coerce")
    d["tn_post72h"] = hs.fillna(cv)          # ng/mL
    d["tn_post7d"] = np.nan                   # 平台 mins 窗口未公开，敏感性仅 INSPIRE
    d["tn_pre7d"] = np.nan
    mins = pd.to_numeric(d.pop("mins"), errors="coerce")
    d["mins_platform"] = mins
    idx = d.set_index("log_id").index
    d["scr_7d"] = pd.to_numeric(get("pre7d")["labp_creatinine_min"], errors="coerce").reindex(idx).values
    d["scr_30d"] = pd.to_numeric(get("pre30d")["labp_creatinine_min"], errors="coerce").reindex(idx).values
    d["scr_p48"] = pd.to_numeric(get("post48h")["labp_creatinine_max"], errors="coerce").reindex(idx).values
    d["scr_p7"] = pd.to_numeric(get("post7d")["labp_creatinine_max"], errors="coerce").reindex(idx).values
    d["age"] = pd.to_numeric(d["age_years"], errors="coerce")
    d["male"] = (d["sex"].astype(str).str.upper().str[0] == "M").astype(int)
    d["asa_class"] = pd.to_numeric(d["asa_rating_c"], errors="coerce")
    d["ane_h"] = pd.to_numeric(d["anes_duration_min"], errors="coerce") / 60.0
    d["op_h"] = pd.to_numeric(d["or_duration_min"], errors="coerce") / 60.0
    d["weight_kg"] = pd.to_numeric(d["weight_kg"], errors="coerce")
    d["height_cm"] = pd.to_numeric(d["height_cm"], errors="coerce")
    d["bmi"] = pd.to_numeric(d["bmi"], errors="coerce")
    meas = d["scr_7d"].fillna(d["scr_30d"])
    imp = [mdrd_scr(a, 1 - s) for a, s in zip(d["age"], d["male"])]
    d["scr_base"] = meas.fillna(pd.Series(imp, index=d.index))
    d["baseline_src"] = np.where(d["scr_7d"].notna(), "7d",
                                 np.where(d["scr_30d"].notna(), "30d",
                                          np.where(pd.notna(d["scr_base"]), "mdrd", "none")))
    d["emergency"] = 0
    d["open_surgery"] = (~d["primary_procedure_nm"].fillna("").str.contains(
        "ARTHROSCOP", case=False)).astype(int)
    d["below65"] = pd.to_numeric(d["mbp_below_65min"], errors="coerce")
    d["icu"] = pd.to_numeric(d["icu_admin_flag"], errors="coerce").fillna(0).astype(int)
    d["death"] = pd.to_numeric(d["in_hosp_mortality"], errors="coerce").fillna(0).astype(int)
    d["cohort"] = "MOVER-Ortho"
    d = finish(d, "MOVER-Ortho")
    # 主口径用平台 mins（按各测定法 99th URL 判定）；与 26 ng/L 自判的一致性单列报告
    d["mins_26ngl"] = d["mins"]
    d["mins"] = d["mins_platform"]
    both = d[d.mins_platform.notna() & d.mins_26ngl.notna()]
    agree = (both.mins_platform == both.mins_26ngl).mean()
    print(f"[MOVER-Ortho] 平台 mins 与 26 ng/L 自判一致率 {agree*100:.1f}% (n={len(both)})", flush=True)
    d.to_csv(os.path.join(OUT, "mover_ortho_analytic.csv"), index=False, encoding="utf-8-sig")
    return d


if __name__ == "__main__":
    build_inspire()
    build_mover()
