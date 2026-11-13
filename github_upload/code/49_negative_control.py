# -*- coding: utf-8 -*-
"""阴性对照分析（C1）：用术前已存在的合并症作阴性对照结局。

设计：术中低血压负荷在时间上不可能"造成"术前即存在的疾病（心衰/慢性肾病/冠心病），
因此暴露与这些结局的理论真实关联应为零。若仍观察到显著关联，则提示存在未被已测
协变量充分控制的混杂（如整体病情严重度、虚弱），而这类混杂同样可能污染主分析
（MINS / AKI / 院内死亡）。这是 Lipsitch 2010 负对照框架的实证应用。

分析人群：两库全部骨科手术（合并症与肌钙蛋白监测无关，且在所有患者中均有定义，
故用全队列以最大化透明度并避免监测选择偏倚）。
模型：与主分析同构 —— Crude、Model 1（age+male）、Model 2（COV_FULL，INSPIRE 含
emergency）；当结局 = 冠心病 (chd) 时，从协变量中剔除 chd 以免循环论证。
暴露：MAP<65 累计分钟 / 麻醉时长 ×100，每 +10% 为一单位。

输出：
  output/tables/en/TableS_negative_control.csv   (供补充材料 Table S5)
  output/negative_control.json                   (摘要，供正文/讨论撰写引用)
"""
import json
import os

import numpy as np
import pandas as pd
import statsmodels.api as sm

OUT = "output"
EN = os.path.join(OUT, "tables", "en")
os.makedirs(EN, exist_ok=True)

COV_FULL = ["age", "male", "bmi", "asa_class", "scr_base", "dm", "htn", "chd"]
OUTCOMES = [("hf", "Heart failure"), ("ckd", "Chronic kidney disease"),
            ("chd", "Coronary heart disease")]


def pf(p):
    return "<0.001" if p < 0.001 else f"{p:.3f}"


def orci(mod, term="burden10"):
    b = mod.params[term]
    se = mod.bse[term]
    return float(np.exp(b)), float(np.exp(b - 1.96 * se)), float(np.exp(b + 1.96 * se)), float(mod.pvalues[term])


def load_full(path, has_emergency):
    d = pd.read_csv(path)
    d["bmi"] = d["bmi"].fillna(d.loc[d.monitored == 1, "bmi"].median())
    d["burden10"] = d["burden_pct"] / 10.0
    return d, has_emergency


def fit(d, outcome, has_emergency):
    covs = list(COV_FULL)
    if not has_emergency:
        covs = [c for c in covs if c != "emergency"]
    # 循环保护：结局本身不应作为协变量
    if outcome in covs:
        covs = [c for c in covs if c != outcome]
    covs_use = [c for c in covs if d[c].nunique() > 1]
    out = {}
    for label, extra in [("Crude", ""), ("Model 1", "age + male"),
                         ("Model 2", " + ".join(covs_use))]:
        f = f"{outcome} ~ burden10" if label == "Crude" else f"{outcome} ~ burden10 + {extra}"
        try:
            m = sm.Logit.from_formula(f, data=d).fit(disp=0, maxiter=300)
            orv, lo, hi, p = orci(m)
            out[label] = (round(orv, 2), f"{lo:.2f}\u2013{hi:.2f}", pf(p))
        except Exception:
            out[label] = (np.nan, "", "")
    return out, covs_use


def main():
    rows = []
    summary = {}
    for path, lab, has_em in [
        (os.path.join(OUT, "inspire_ortho_analytic.csv"), "INSPIRE (derivation)", True),
        (os.path.join(OUT, "mover_ortho_analytic.csv"), "MOVER (validation)", False),
    ]:
        d, _ = load_full(path, has_em)
        n = len(d)
        summary[lab] = {}
        for col, name in OUTCOMES:
            res, _ = fit(d, col, has_em)
            ev = int(d[col].sum())
            rows.append({"Database": lab, "Negative control outcome": name,
                         "Events (n)": ev, "n": n,
                         "Crude OR (95% CI)": "" if np.isnan(res["Crude"][0]) else
                         f"{res['Crude'][0]:.2f} ({res['Crude'][1]})",
                         "Model 1 OR (95% CI)": "" if np.isnan(res["Model 1"][0]) else
                         f"{res['Model 1'][0]:.2f} ({res['Model 1'][1]})",
                         "Model 2 OR (95% CI)": "" if np.isnan(res["Model 2"][0]) else
                         f"{res['Model 2'][0]:.2f} ({res['Model 2'][1]})", "Model 2 P": res["Model 2"][2]})
            summary[lab][name] = {"or": res["Model 2"][0], "ci": res["Model 2"][1], "p": res["Model 2"][2],
                                  "events": ev, "n": n}
            print(f"[{lab}] {name}: events={ev}/{n}  Model2 OR={res['Model 2'][0]} "
                  f"({res['Model 2'][1]}) P={res['Model 2'][2]}", flush=True)

    t = pd.DataFrame(rows)
    out_csv = os.path.join(EN, "TableS_negative_control.csv")
    t.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print("\n" + t.to_string(index=False))
    print(f"\n[saved] {out_csv}")

    json.dump(summary, open(os.path.join(OUT, "negative_control.json"), "w"), indent=2)
    print("[saved] output/negative_control.json")


if __name__ == "__main__":
    main()
