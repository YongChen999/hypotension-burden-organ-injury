# -*- coding: utf-8 -*-
"""骨科 MINS 主分析：推导（INSPIRE-Ortho）+ 外部验证（MOVER-Ortho）。

模型
  Crude   mins ~ burden10
  Model 1 + age + male + bmi + asa_class
  Model 2 + scr_base + emergency + dm + htn + chd
敏感性
  阈值 0.04 / 0.10 ng/mL；术后 7 天窗口；MINS∪ICD-MI；AKI 次要结局（全队列）
"""
import json
import os

import numpy as np
import patsy
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.model_selection import StratifiedKFold

OUT = "output"
TAB = os.path.join(OUT, "tables")
os.makedirs(TAB, exist_ok=True)
COV1 = "age + male + bmi + asa_class"
COV2 = COV1 + " + scr_base + emergency + dm + htn + chd"
LABELS = ["0%", "0-5%", "5-10%", ">10%"]
EDGES = [-0.001, 0.0, 5.0, 10.0, 100.0]


def log(m):
    print(m, flush=True)


def pf(p):
    return "<0.001" if p < 0.001 else f"{p:.3f}"


def load():
    a = pd.read_csv(os.path.join(OUT, "inspire_ortho_analytic.csv"))
    b = pd.read_csv(os.path.join(OUT, "mover_ortho_analytic.csv"))
    for d in (a, b):
        d["bmi"] = pd.to_numeric(d["bmi"], errors="coerce")
    # BMI 用各自监测亚组中位数填补
    for d, nm in ((a, "INSPIRE"), (b, "MOVER")):
        med = float(d.loc[d.monitored == 1, "bmi"].median())
        d["bmi"] = d["bmi"].fillna(med)
        d["surgery_group"] = np.where(
            d.get("primary_procedure_nm", pd.Series([""] * len(d))).str.contains(
                "ORIF|FRACTURE|PINNING|REDUCTION", case=False, na=False), "Fracture",
            np.where(d.get("primary_procedure_nm", pd.Series([""] * len(d))).str.contains(
                "ARTHROPLASTY|REPLACEMENT|HEMIARTH", case=False, na=False), "Arthroplasty", "Other"))
    return a, b


def cov_usable(d, cov):
    return " + ".join(c for c in cov.split(" + ") if d[c].nunique() > 1)


def models(d, outcome="mins"):
    rows, fitted = [], {}
    cov1, cov2 = cov_usable(d, COV1), cov_usable(d, COV2)
    for name, f in [("Crude", f"{outcome} ~ burden10"),
                    ("Model 1", f"{outcome} ~ burden10 + {cov1}"),
                    ("Model 2", f"{outcome} ~ burden10 + {cov2}")]:
        try:
            m = smf.logit(f, data=d).fit(disp=0, maxiter=200)
        except Exception:
            continue
        b, se, p = m.params["burden10"], m.bse["burden10"], m.pvalues["burden10"]
        rows.append({"模型": name, "暴露": "每 +10% 负荷", "OR": round(float(np.exp(b)), 3),
                     "95%CI": f"{np.exp(b-1.96*se):.3f}-{np.exp(b+1.96*se):.3f}", "P": pf(p)})
        fitted[name] = m
    # 分类
    d = d.copy()
    d["cat"] = pd.cut(d["burden_pct"], EDGES, labels=LABELS)
    d["catn"] = d["cat"].cat.codes + 1
    mc = smf.logit(f"{outcome} ~ C(cat, Treatment('0%')) + {cov2}", data=d).fit(disp=0)
    for lb in LABELS[1:]:
        k = [x for x in mc.params.index if f"'{lb}'" in str(x)]
        if k:
            b, se, p = mc.params[k[0]], mc.bse[k[0]], mc.pvalues[k[0]]
            rows.append({"模型": "Model 2", "暴露": f"{lb} vs 0%", "OR": round(float(np.exp(b)), 3),
                         "95%CI": f"{np.exp(b-1.96*se):.3f}-{np.exp(b+1.96*se):.3f}", "P": pf(p)})
    mt = smf.logit(f"{outcome} ~ catn + {cov2}", data=d).fit(disp=0)
    rows.append({"模型": "Model 2", "暴露": "P for trend", "OR": "", "95%CI": "",
                 "P": pf(mt.pvalues["catn"])})
    return pd.DataFrame(rows), fitted["Model 2"]


def rcs(d, outcome="mins", df=4):
    kn = list(np.linspace(np.quantile(d.burden_pct, 0.02), np.quantile(d.burden_pct, 0.98), df + 1))
    X = patsy.dmatrix(f"cr(burden_pct, df={df}) + {cov_usable(d, COV2)}", d, return_type="dataframe")
    y = d[outcome].values
    m = sm.Logit(y, X.values).fit(disp=0)
    xs = np.linspace(0, min(45, d.burden_pct.quantile(0.98)), 200)
    grid = pd.DataFrame({"burden_pct": xs})
    for c in COV2.split(" + "):
        v = d[c]
        grid[c] = v.mode()[0] if set(np.unique(v.dropna())) <= {0, 1} else v.mean()
    Xp = patsy.build_design_matrices([X.design_info], grid)[0]
    Xp = np.asarray(Xp)
    V = np.asarray(m.cov_params())
    eta = Xp @ np.asarray(m.params)
    # 以 x = 0（无低血压暴露）为参照，使曲线在参照点 OR = 1
    ref = grid.iloc[[0]].copy()
    Xr = np.asarray(patsy.build_design_matrices([X.design_info], ref)[0])
    eta0 = float(np.asarray(Xr @ np.asarray(m.params)).ravel()[0])
    eta = eta - eta0
    D = Xp - Xr
    se = np.sqrt(np.einsum("ij,jk,ik->i", D, V, D))
    out = pd.DataFrame({"x": xs, "or": np.exp(eta), "lo": np.exp(eta - 1.96 * se), "hi": np.exp(eta + 1.96 * se)})
    # 非线性检验：联合检验样条非线性基
    names = list(X.columns)
    nl = [i for i, n in enumerate(names) if n.startswith("cr(burden_pct") and i > 0]
    R = np.zeros((len(nl), len(np.asarray(m.params))))
    for i, j in enumerate(nl):
        R[i, j] = 1
    wald = m.wald_test(R, scalar=True)
    return out, float(wald.pvalue), kn


def discrimination(d):
    y = d["mins"].values
    X = patsy.dmatrix(f"burden10 + {cov_usable(d, COV2)}", d, return_type="dataframe")
    m = sm.Logit(y, X.values).fit(disp=0)
    p = m.predict(X.values)
    auc = roc_auc_score(y, p)
    skf = StratifiedKFold(10, shuffle=True, random_state=42)
    ps = np.full(len(y), np.nan)
    try:
        for tr, te in skf.split(X, y):
            mf = sm.Logit(y[tr], X.values[tr]).fit(disp=0, maxiter=200)
            ps[te] = mf.predict(X.values[te])
        auc_cv = roc_auc_score(y[~np.isnan(ps)], ps[~np.isnan(ps)])
    except Exception:
        auc_cv = float("nan")
    # 校准
    lp = np.log(p / (1 - p))
    cal = smf.ols("y ~ lp", data=pd.DataFrame({"y": y, "lp": lp})).fit()
    hl = 0
    g = pd.qcut(p, 8, duplicates="drop")
    gr = np.asarray(pd.Categorical(g).codes)
    for k in np.unique(gr):
        m_ = gr == k
        e, o = p[m_].mean(), y[m_].mean()
        hl += (o - e) ** 2 / (e * (1 - e) / m_.sum())
    p_hl = 1 - stats.chi2.cdf(hl, len(np.unique(gr)) - 2)
    rng = np.random.default_rng(42)
    boot = [roc_auc_score(y[idx], p[idx]) for idx in
            (rng.integers(0, len(y), len(y)) for _ in range(1000))]
    return {"auc": auc, "auc_lo": float(np.percentile(boot, 2.5)), "auc_hi": float(np.percentile(boot, 97.5)),
            "auc_cv": auc_cv, "cal_slope": float(cal.params["lp"]), "hl": float(hl), "p_hl": float(p_hl),
            "pred": p, "n": len(y), "events": int(y.sum())}


def selection_table(a, b):
    rows = []
    for nm, d in (("INSPIRE", a), ("MOVER", b)):
        mon, un = d[d.monitored == 1], d[d.monitored == 0]
        def row(var, f, dig=1):
            v1, v2 = f(mon), f(un)
            rows.append({"数据库": nm, "变量": var, "监测": v1, "未监测": v2})
        row("n", lambda x: str(len(x)))
        row("年龄（岁）", lambda x: f"{x.age.mean():.1f}")
        row("男性", lambda x: f"{(x.male == 1).mean()*100:.1f}%")
        row("ASA III+（INSPIRE）/ ASA 分级", lambda x: f"{x.asa_class.mean():.2f}")
        row("急诊手术", lambda x: f"{x.emergency.mean()*100:.1f}%" if nm == "INSPIRE" else "—")
        row("麻醉时长（h）", lambda x: f"{x.ane_h.median():.1f}")
        row("MAP<65 负荷（%）", lambda x: f"{x.burden_pct.median():.1f}")
        row("合并糖尿病", lambda x: f"{x.dm.mean()*100:.1f}%")
        row("合并冠心病", lambda x: f"{x.chd.mean()*100:.1f}%")
        row("术后 AKI", lambda x: f"{x.aki.mean()*100:.1f}%" if x.aki.notna().any() else "—")
        row("院内死亡", lambda x: f"{x.death.mean()*100:.1f}%")
    return pd.DataFrame(rows)


def baseline_table(d):
    d = d.copy()
    d["cat"] = pd.cut(d["burden_pct"], EDGES, labels=LABELS)
    rows = []
    gs = [d[d.cat == lb] for lb in LABELS]
    def add(name, f):
        vals = [f(g) for g in gs]
        try:
            pv = stats.kruskal(*[pd.to_numeric(pd.Series([v.strip('%') for v in vals]), errors='coerce')]).pvalue
        except Exception:
            pv = np.nan
        rows.append({"变量": name, **{lb: v for lb, v in zip(LABELS, vals)}, "P": pf(pv) if pv == pv else ""})
    add("n", lambda g: str(len(g)))
    add("年龄（岁）", lambda g: f"{g.age.median():.0f} ({g.age.quantile(.25):.0f}-{g.age.quantile(.75):.0f})")
    add("男性", lambda g: f"{(g.male==1).sum()} ({(g.male==1).mean()*100:.1f}%)")
    add("BMI（kg/m²）", lambda g: f"{g.bmi.median():.1f}")
    add("ASA 分级", lambda g: f"{g.asa_class.median():.0f}")
    add("基线 SCr（mg/dL）", lambda g: f"{g.scr_base.median():.2f}")
    add("急诊手术", lambda g: f"{(g.emergency==1).sum()} ({(g.emergency==1).mean()*100:.1f}%)")
    add("麻醉时长（h）", lambda g: f"{g.ane_h.median():.1f}")
    add("MAP<65 累计（min）", lambda g: f"{g.below65.median():.0f}")
    add("糖尿病", lambda g: f"{(g.dm==1).mean()*100:.1f}%")
    add("高血压", lambda g: f"{(g.htn==1).mean()*100:.1f}%")
    add("冠心病", lambda g: f"{(g.chd==1).mean()*100:.1f}%")
    add("MINS", lambda g: f"{int(g.mins.sum())} ({g.mins.mean()*100:.1f}%)")
    return pd.DataFrame(rows)


def main():
    a, b = load()
    der = a[(a.monitored == 1)].dropna(
        subset=["mins", "burden_pct", "age", "male", "bmi", "asa_class", "scr_base",
                "emergency", "dm", "htn", "chd"]).copy()
    log(f"[推导] 监测分析集 n={len(der)} MINS={int(der.mins.sum())} ({der.mins.mean()*100:.1f}%)")
    val = b[(b.monitored == 1)].dropna(
        subset=["mins", "burden_pct", "age", "male", "bmi", "asa_class", "scr_base",
                "dm", "htn", "chd"]).copy()
    val["emergency"] = 0
    log(f"[验证] 监测分析集 n={len(val)} MINS={int(val.mins.sum())} ({val.mins.mean()*100:.1f}%)")

    t1s = selection_table(a, b)
    t1s.to_csv(os.path.join(TAB, "mins_table1_selection.csv"), index=False, encoding="utf-8-sig")
    log("\n" + t1s.to_string(index=False))

    t1b = baseline_table(der)
    t1b.to_csv(os.path.join(TAB, "mins_table2_baseline.csv"), index=False, encoding="utf-8-sig")

    t2, m2 = models(der)
    t2.to_csv(os.path.join(TAB, "mins_table3_models.csv"), index=False, encoding="utf-8-sig")
    log("\n" + t2.to_string(index=False))

    rcs_curve, p_nl, kn = rcs(der)
    rcs_curve.to_csv(os.path.join(TAB, "mins_rcs_curve.csv"), index=False)
    log(f"\n[RCS] 非线性 P={p_nl:.3f} 节点={np.round(kn,1)}")

    disc = discrimination(der)
    log(f"[表观] AUC {disc['auc']:.3f} ({disc['auc_lo']:.3f}-{disc['auc_hi']:.3f}) "
        f"CV {disc['auc_cv']:.3f} 校准斜率 {disc['cal_slope']:.2f} HL P {disc['p_hl']:.3f}")

    # ---------- 外部验证：冻结模型 ----------
    co = dict(zip(["burden10"] + COV2.split(" + "), np.asarray(m2.params)[1:]))
    def frozen(d):
        lp = sum(co[k] * d[k] for k in co) + np.asarray(m2.params)[0]
        return 1 / (1 + np.exp(-lp))
    pv = frozen(val)
    auc_f = roc_auc_score(val.mins, pv)
    oe = val.mins.sum() / pv.sum()
    lpv = np.log(pv / (1 - pv))
    cal_f = smf.ols("y ~ lp", data=pd.DataFrame({"y": val.mins, "lp": lpv})).fit()
    # 重拟合
    t4, m4 = models(val)
    disc_v = discrimination(val)
    np.savez(os.path.join(TAB, "mins_pred.npz"),
             val_y=val.mins.values, val_p=pv, insp_y=der.mins.values, insp_p=disc["pred"])
    log(f"[验证-冻结] AUC {auc_f:.3f}  O:E {oe:.2f}  校准斜率 {cal_f.params['lp']:.2f}")
    log(f"[验证-重拟合] AUC {disc_v['auc']:.3f} ({disc_v['auc_lo']:.3f}-{disc_v['auc_hi']:.3f})")

    # ---------- 敏感性 ----------
    sens = []
    for label, col in [(">0.04 ng/mL", "mins_04"), (">0.10 ng/mL", "mins_10"),
                       ("7 天窗口", "mins7")]:
        dd = der[der[col].notna()].dropna(subset=["burden_pct", "age", "male", "bmi", "asa_class",
                                                  "scr_base", "emergency", "dm", "htn", "chd"])
        if len(dd) < 30 or dd[col].sum() < 10:
            continue
        f = smf.logit(f"{col} ~ burden10 + {cov_usable(dd, COV2)}", data=dd).fit(disp=0)
        sens.append({"分析": label, "n": len(dd), "事件": int(dd[col].sum()),
                     "OR": round(float(np.exp(f.params.burden10)), 2),
                     "95%CI": f"{np.exp(f.params.burden10-1.96*f.bse.burden10):.2f}-{np.exp(f.params.burden10+1.96*f.bse.burden10):.2f}",
                     "P": pf(f.pvalues.burden10)})
    # MINS ∪ ICD-MI（INSPIRE：patient_diagnosis_codes 的 I21/I22，患者级无法定时，局限已标注；MOVER：mi_dx）
    der["mins_mi"] = ((der.mins == 1) | der["patient_diagnosis_codes"].fillna("").astype(str).str.contains(r"\bI2[12]", regex=True)).astype(float)
    f = smf.logit(f"mins_mi ~ burden10 + {cov_usable(der, COV2)}", data=der).fit(disp=0)
    sens.append({"分析": "INSPIRE MINS∪ICD-MI", "n": len(der), "事件": int(der.mins_mi.sum()),
                 "OR": round(float(np.exp(f.params.burden10)), 2),
                 "95%CI": f"{np.exp(f.params.burden10-1.96*f.bse.burden10):.2f}-{np.exp(f.params.burden10+1.96*f.bse.burden10):.2f}",
                 "P": pf(f.pvalues.burden10)})
    valm = val.copy()
    valm["mins_mi"] = ((valm.mins == 1) | (valm.get("mi_dx", 0) == 1)).astype(float)
    f = smf.logit(f"mins_mi ~ burden10 + {cov_usable(valm, COV2)}", data=valm).fit(disp=0)
    sens.append({"分析": "MOVER MINS∪ICD-MI", "n": len(valm), "事件": int(valm.mins_mi.sum()),
                 "OR": round(float(np.exp(f.params.burden10)), 2),
                 "95%CI": f"{np.exp(f.params.burden10-1.96*f.bse.burden10):.2f}-{np.exp(f.params.burden10+1.96*f.bse.burden10):.2f}",
                 "P": pf(f.pvalues.burden10)})
    # AKI 次要结局（全队列，无选择）
    for nm, dd in (("INSPIRE", a), ("MOVER", b)):
        ak = dd[dd.aki.notna()].dropna(subset=["burden_pct", "age", "male", "bmi", "asa_class",
                                               "scr_base", "emergency", "dm", "htn", "chd"])
        f = smf.logit(f"aki ~ burden10 + {cov_usable(ak, COV2)}", data=ak).fit(disp=0)
        sens.append({"分析": f"{nm} AKI（次要，全队列）", "n": len(ak), "事件": int(ak.aki.sum()),
                     "OR": round(float(np.exp(f.params.burden10)), 2),
                     "95%CI": f"{np.exp(f.params.burden10-1.96*f.bse.burden10):.2f}-{np.exp(f.params.burden10+1.96*f.bse.burden10):.2f}",
                     "P": pf(f.pvalues.burden10)})
    ts = pd.DataFrame(sens)
    ts.to_csv(os.path.join(TAB, "mins_tableS_sensitivity.csv"), index=False, encoding="utf-8-sig")
    log("\n" + ts.to_string(index=False))

    # 亚组（推导）
    sub = []
    for var, lab in [("age", "≥65 岁"), ("male", "男性"), ("emergency", "急诊"), ("asa_class", "ASA≥3"), ("chd", "冠心病")]:
        for k, kl in [(1, "是"), (0, "否")]:
            dd = der[der[var] == k]
            if dd.mins.sum() < 8 or (1 - dd.mins).sum() < 8:
                continue
            cov = cov_usable(dd, COV2.replace(f"{var} + ", "") if var in COV2.split(" + ") else COV2)
            try:
                f = smf.logit(f"mins ~ burden10 + {cov}", data=dd).fit(disp=0)
                sub.append({"亚组": lab, "层": kl, "n": len(dd), "事件": int(dd.mins.sum()),
                            "OR": round(float(np.exp(f.params.burden10)), 2),
                            "95%CI": f"{np.exp(f.params.burden10-1.96*f.bse.burden10):.2f}-{np.exp(f.params.burden10+1.96*f.bse.burden10):.2f}"})
            except Exception:
                pass
        try:
            fi = smf.logit(f"mins ~ burden10*{var} + {cov_usable(der, COV2.replace(var+' + ', ''))}", data=der).fit(disp=0)
            k = [x for x in fi.params.index if ":" in str(x)][0]
            sub.append({"亚组": lab, "层": "P interaction", "n": "", "事件": "",
                        "OR": "", "95%CI": pf(fi.pvalues[k])})
        except Exception:
            pass
    pd.DataFrame(sub).to_csv(os.path.join(TAB, "mins_tableS_subgroup.csv"), index=False, encoding="utf-8-sig")

    json.dump({"coef": co, "intercept": float(np.asarray(m2.params)[0]),
               "n": len(der), "events": int(der.mins.sum()),
               "auc": disc["auc"], "auc_ci": [disc["auc_lo"], disc["auc_hi"]],
               "auc_cv": disc["auc_cv"], "cal_slope": disc["cal_slope"], "p_hl": disc["p_hl"],
               "p_nl": p_nl, "knots": [float(x) for x in kn],
               "val_n": len(val), "val_events": int(val.mins.sum()),
               "val_auc_frozen": float(auc_f), "val_oe": float(oe),
               "val_cal_slope": float(cal_f.params["lp"]),
               "val_auc_refit": disc_v["auc"], "val_auc_refit_ci": [disc_v["auc_lo"], disc_v["auc_hi"]]},
              open(os.path.join(OUT, "model_mins.json"), "w"), indent=2)
    log("\n[saved] output/model_mins.json")


if __name__ == "__main__":
    main()
