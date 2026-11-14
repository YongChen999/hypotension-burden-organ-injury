# -*- coding: utf-8 -*-
"""生成 AKI 与院内死亡的 RCS 剂量-反应曲线（推导+验证库），供 Fig.2 双联图。
复用 41 的 cr() 样条定义与协变量集，确保方法口径一致。"""
import os

import numpy as np
import pandas as pd
import patsy
import statsmodels.api as sm

OUT = "output"
TAB = os.path.join(OUT, "tables")
os.makedirs(TAB, exist_ok=True)
COV1 = "age + male + bmi + asa_class"
COV2 = COV1 + " + scr_base + emergency + dm + htn + chd"


def cov_usable(d, cov):
    return " + ".join(c for c in cov.split(" + ") if c in d.columns and d[c].nunique() > 1)


def load():
    a = pd.read_csv(os.path.join(OUT, "inspire_ortho_analytic.csv"))
    b = pd.read_csv(os.path.join(OUT, "mover_ortho_analytic.csv"))
    for d in (a, b):
        d["bmi"] = pd.to_numeric(d["bmi"], errors="coerce")
        med = float(d.loc[d.monitored == 1, "bmi"].median())
        d["bmi"] = d["bmi"].fillna(med)
    return a, b


def rcs(d, outcome="aki", df=4):
    covs = [c for c in COV2.split(" + ") if c in d.columns]
    d = d.dropna(subset=["burden_pct", outcome] + covs).copy()
    kn = list(np.linspace(np.quantile(d.burden_pct, 0.02), np.quantile(d.burden_pct, 0.98), df + 1))
    X = patsy.dmatrix(f"cr(burden_pct, df={df}) + {cov_usable(d, COV2)}", d, return_type="dataframe")
    y = d[outcome].values
    m = sm.Logit(y, X.values).fit(disp=0, maxiter=200)
    xs = np.linspace(0, min(45, d.burden_pct.quantile(0.98)), 200)
    grid = pd.DataFrame({"burden_pct": xs})
    for c in COV2.split(" + "):
        if c not in d.columns:
            continue
        v = d[c]
        grid[c] = v.mode()[0] if set(np.unique(v.dropna())) <= {0, 1} else v.mean()
    Xp = np.asarray(patsy.build_design_matrices([X.design_info], grid)[0])
    V = np.asarray(m.cov_params())
    ref = grid.iloc[[0]].copy()
    Xr = np.asarray(patsy.build_design_matrices([X.design_info], ref)[0])
    eta0 = float(np.asarray(Xr @ np.asarray(m.params)).ravel()[0])
    eta = Xp @ np.asarray(m.params) - eta0
    D = Xp - Xr
    se = np.sqrt(np.einsum("ij,jk,ik->i", D, V, D))
    out = pd.DataFrame({"x": xs, "or": np.exp(eta), "lo": np.exp(eta - 1.96 * se),
                        "hi": np.exp(eta + 1.96 * se)})
    names = list(X.columns)
    nl = [i for i, n in enumerate(names) if n.startswith("cr(burden_pct") and i > 0]
    if nl:
        R = np.zeros((len(nl), len(np.asarray(m.params))))
        for i, j in enumerate(nl):
            R[i, j] = 1
        try:
            p_nl = float(m.wald_test(R, scalar=True).pvalue)
        except Exception:
            p_nl = float("nan")
    else:
        p_nl = float("nan")
    return out, p_nl, kn


def main():
    a, b = load()
    rows = []
    for db, d in (("INSPIRE", a), ("MOVER", b)):
        for outcome in ("aki", "death"):
            if outcome not in d.columns:
                print("SKIP (no col)", db, outcome)
                continue
            try:
                out, p_nl, kn = rcs(d, outcome)
            except Exception as e:
                print("SKIP", db, outcome, repr(e))
                continue
            out = out.assign(db=db, outcome=outcome, p_nl=round(p_nl, 3))
            rows.append(out)
            sub = d.dropna(subset=[outcome, "burden_pct"])
            print(f"[RCS] {db} {outcome}: n={len(sub)} events={int(sub[outcome].sum())} "
                  f"P_nonlin={p_nl:.3f}")
    df = pd.concat(rows, ignore_index=True)
    df.to_csv(os.path.join(TAB, "organ_rcs_curve.csv"), index=False)
    print("saved", os.path.join(TAB, "organ_rcs_curve.csv"), df.shape)


if __name__ == "__main__":
    main()
