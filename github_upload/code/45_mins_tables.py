# -*- coding: utf-8 -*-
"""生成 MINS 论文的英文结果表（Table 1-4 + 敏感性），两库对称、含 P 值。"""
import json
import os

import numpy as np
import pandas as pd
import warnings

import statsmodels.api as sm
from statsmodels.tools.sm_exceptions import ConvergenceWarning

warnings.simplefilter("ignore", ConvergenceWarning)
from scipy import stats
from sklearn.metrics import roc_auc_score

OUT = "output"
TAB = os.path.join(OUT, "tables")
EN = os.path.join(TAB, "en")
os.makedirs(EN, exist_ok=True)

COV_FULL = ["age", "male", "bmi", "asa_class", "scr_base", "dm", "htn", "chd"]
COV1 = ["age", "male"]


def load(path, has_emergency=True):
    d = pd.read_csv(path)
    m = d[d.monitored == 1].copy()
    med = float(m["bmi"].median())
    m["bmi"] = m["bmi"].fillna(med)
    need = ["mins", "burden_pct", "age", "male", "asa_class", "scr_base", "dm", "htn", "chd"]
    if has_emergency:
        need.append("emergency")
    m = m.dropna(subset=need)
    m["burden10"] = m["burden_pct"] / 10.0
    edges = [-0.001, 0.001, 5, 10, 1e9]
    m["bcat"] = pd.cut(m["burden_pct"], edges, labels=["0", "0-5", "5-10", ">10"])
    m["bcatn"] = pd.Categorical(m["bcat"], categories=["0", "0-5", "5-10", ">10"]).codes + 1
    return m


def fit(d, covs, extra=""):
    cols = "mins ~ burden10" + extra
    if covs:
        cols += " + " + " + ".join(covs)
    mod = sm.Logit.from_formula(cols, data=d).fit(disp=0, maxiter=300)
    return mod


def orci(mod, term="burden10"):
    b = mod.params[term]
    se = mod.bse[term]
    return np.exp(b), np.exp(b - 1.96 * se), np.exp(b + 1.96 * se), mod.pvalues[term]


def fmt(orv, lo, hi, p):
    return f"{orv:.2f} ({lo:.2f}\u2013{hi:.2f})", f"{p:.3f}" if p >= 0.001 else "<0.001"


def med_iqr(x):
    x = pd.Series(x).dropna()
    return f"{x.median():.1f} ({x.quantile(0.25):.1f}\u2013{x.quantile(0.75):.1f})"


def n_pct(x):
    x = pd.Series(x).dropna()
    return f"{int(x.sum())} ({100 * x.mean():.1f})"


def p_cont(a, b):
    a, b = pd.Series(a).dropna(), pd.Series(b).dropna()
    return stats.mannwhitneyu(a, b).pvalue


def p_cat(a, b):
    a, b = pd.Series(a).dropna(), pd.Series(b).dropna()
    tab = pd.crosstab(pd.concat([a, b]), [0] * len(a) + [1] * len(b))
    if tab.shape[0] < 2:
        return np.nan
    if tab.size < 5 or (tab.values < 5).any():
        return stats.fisher_exact(tab.values)[1]
    return stats.chi2_contingency(tab.values, correction=False)[1]


def pfmt(p):
    if not np.isfinite(p):
        return "\u2014"
    return f"{p:.3f}" if p >= 0.001 else "<0.001"


A = load(os.path.join(OUT, "inspire_ortho_analytic.csv"), True)
B = load(os.path.join(OUT, "mover_ortho_analytic.csv"), False)
print("analytic:", len(A), int(A.mins.sum()), "|", len(B), int(B.mins.sum()))

# ---------------- Table 1: baseline by MINS status ----------------
rows = []
spec = [
    ("Age, years", "age", "cont"),
    ("Male sex", "male", "cat"),
    ("BMI, kg/m\u00b2", "bmi", "cont"),
    ("ASA physical status \u22653", None, "asa3"),
    ("Baseline serum creatinine, mg/dL", "scr_base", "cont"),
    ("Emergency surgery", "emergency", "cat"),
    ("Anaesthesia duration, h", "ane_h", "cont"),
    ("MAP <65 mmHg, cumulative min", "below65", "cont"),
    ("Hypotension burden, %", "burden_pct", "cont"),
    ("Diabetes", "dm", "cat"),
    ("Hypertension", "htn", "cat"),
    ("Coronary heart disease", "chd", "cat"),
    ("Postoperative AKI", "aki", "cat"),
    ("In-hospital death", "death", "cat"),
]
for label, col, kind in spec:
    if kind == "asa3":
        a0 = (A.loc[A.mins == 0, "asa_class"] >= 3).astype(int)
        a1 = (A.loc[A.mins == 1, "asa_class"] >= 3).astype(int)
        b0 = (B.loc[B.mins == 0, "asa_class"] >= 3).astype(int)
        b1 = (B.loc[B.mins == 1, "asa_class"] >= 3).astype(int)
        rows.append([label, n_pct(a0), n_pct(a1), pfmt(p_cat(a0, a1)),
                     n_pct(b0), n_pct(b1), pfmt(p_cat(b0, b1))])
        continue
    if col not in A.columns or A[col].isna().all():
        continue
    if kind == "cont":
        rows.append([label, med_iqr(A.loc[A.mins == 0, col]), med_iqr(A.loc[A.mins == 1, col]),
                     pfmt(p_cont(A.loc[A.mins == 0, col], A.loc[A.mins == 1, col])),
                     med_iqr(B.loc[B.mins == 0, col]) if col in B.columns else "\u2014",
                     med_iqr(B.loc[B.mins == 1, col]) if col in B.columns else "\u2014",
                     pfmt(p_cont(B.loc[B.mins == 0, col], B.loc[B.mins == 1, col])) if col in B.columns else "\u2014"])
    else:
        rows.append([label, n_pct(A.loc[A.mins == 0, col]), n_pct(A.loc[A.mins == 1, col]),
                     pfmt(p_cat(A.loc[A.mins == 0, col], A.loc[A.mins == 1, col])),
                     n_pct(B.loc[B.mins == 0, col]) if col in B.columns else "\u2014",
                     n_pct(B.loc[B.mins == 1, col]) if col in B.columns else "\u2014",
                     pfmt(p_cat(B.loc[B.mins == 0, col], B.loc[B.mins == 1, col])) if col in B.columns else "\u2014"])

nA0, nA1 = int((A.mins == 0).sum()), int(A.mins.sum())
nB0, nB1 = int((B.mins == 0).sum()), int(B.mins.sum())
tabA = pd.crosstab(A.bcat, A.mins)
tabB = pd.crosstab(B.bcat, B.mins)
pcat_A = stats.chi2_contingency(tabA.values, correction=False)[1]
pcat_B = stats.chi2_contingency(tabB.values, correction=False)[1]
burden_cat_rows = []
for k, lb in enumerate(["0", "0-5", "5-10", ">10"]):
    a0 = int(((A.bcat == lb) & (A.mins == 0)).sum())
    a1 = int(((A.bcat == lb) & (A.mins == 1)).sum())
    b0 = int(((B.bcat == lb) & (B.mins == 0)).sum())
    b1 = int(((B.bcat == lb) & (B.mins == 1)).sum())
    burden_cat_rows.append([f"  {lb}%",
                            f"{a0} ({100 * a0 / nA0:.1f})", f"{a1} ({100 * a1 / nA1:.1f})",
                            pfmt(pcat_A) if k == 0 else "",
                            f"{b0} ({100 * b0 / nB0:.1f})", f"{b1} ({100 * b1 / nB1:.1f})",
                            pfmt(pcat_B) if k == 0 else ""])

hdr = ["Characteristic", "INSPIRE MINS\u2212 (n=%d)" % int((A.mins == 0).sum()),
       "INSPIRE MINS+ (n=%d)" % int(A.mins.sum()), "P",
       "MOVER MINS\u2212 (n=%d)" % int((B.mins == 0).sum()),
       "MOVER MINS+ (n=%d)" % int(B.mins.sum()), "P"]
sep = [["MINS by burden category, n (%)"] + [""] * (len(hdr) - 1)]
t1 = pd.DataFrame(rows + sep + burden_cat_rows, columns=hdr)
t1.to_csv(os.path.join(EN, "Table1_baseline.csv"), index=False, encoding="utf-8-sig")

# ---------------- Table 2: models ----------------
def model_block(d, covs_full, label):
    out = []
    m0 = fit(d, [])
    m1 = fit(d, [x for x in COV1 if d[x].nunique() > 1])
    m2 = fit(d, [x for x in covs_full if d[x].nunique() > 1])
    for nm, mod in [("Crude", m0), ("Model 1", m1), ("Model 2", m2)]:
        s, p = fmt(*orci(mod))
        out.append([label, nm, "Per 10% increase in burden", s, p])
    return out, m2


rows2, m2A = model_block(A, COV_FULL + ["emergency"], "INSPIRE (derivation)")
rows2b, m2B = model_block(B, COV_FULL, "MOVER (validation)")
rows2 += rows2b

# categories + trend, adjusted
def cats(d, covs, label):
    out = []
    cov_use = [x for x in covs if d[x].nunique() > 1]
    mod = sm.Logit.from_formula("mins ~ C(bcat, Treatment('0')) + " + " + ".join(cov_use), data=d).fit(disp=0, maxiter=300)
    for term, lab in [("C(bcat, Treatment('0'))[T.0-5]", "0\u20135% vs 0%"),
                      ("C(bcat, Treatment('0'))[T.5-10]", "5\u201310% vs 0%"),
                      ("C(bcat, Treatment('0'))[T.>10]", ">10% vs 0%")]:
        if term in mod.params:
            s, p = fmt(*orci(mod, term))
            out.append([label, "Model 2 (categories)", lab, s, p])
    mt = sm.Logit.from_formula("mins ~ bcatn + " + " + ".join(cov_use), data=d).fit(disp=0, maxiter=300)
    out.append([label, "Model 2", "P for trend across categories", "", f"{mt.pvalues['bcatn']:.3f}"])
    return out


rows2 += cats(A, COV_FULL + ["emergency"], "INSPIRE (derivation)")
rows2 += cats(B, COV_FULL, "MOVER (validation)")
t2 = pd.DataFrame(rows2, columns=["Cohort", "Model", "Contrast", "OR (95% CI)", "P"])
t2.to_csv(os.path.join(EN, "Table2_models.csv"), index=False, encoding="utf-8-sig")

# ---------------- discrimination in derivation ----------------
y = A.mins.values
p_hat = np.asarray(m2A.predict(A))
auc = roc_auc_score(y, p_hat)
# bootstrap CI
rng = np.random.default_rng(20261109)
bs = []
for _ in range(2000):
    idx = rng.integers(0, len(y), len(y))
    if y[idx].min() == y[idx].max():
        continue
    bs.append(roc_auc_score(y[idx], p_hat[idx]))
auc_lo, auc_hi = np.percentile(bs, [2.5, 97.5])
# Hosmer-Lemeshow (10 groups)
q = pd.qcut(p_hat, 10, labels=False, duplicates="drop")
obs = pd.Series(y).groupby(q).sum()
exp = pd.Series(p_hat).groupby(q).sum()
nn = pd.Series(y).groupby(q).size()
hl = (((obs - exp) ** 2) / (exp * (1 - exp / nn))).sum()
p_hl = 1 - stats.chi2.cdf(hl, len(nn) - 2)
lgA = np.log(np.clip(p_hat, 1e-6, 1 - 1e-6) / (1 - np.clip(p_hat, 1e-6, 1 - 1e-6)))
calA = sm.GLM(y, sm.add_constant(lgA), family=sm.families.Binomial()).fit()
slopeA = calA.params[1]

# ---------------- Table 3: frozen-model validation ----------------
mj = json.load(open(os.path.join(OUT, "model_mins.json")))
co = mj["coef"]
lp = (co["age"] * B.age + co["male"] * B.male + co["bmi"] * B.bmi + co["asa_class"] * B.asa_class
      + co["scr_base"] * B.scr_base + co["emergency"] * 0 + co["dm"] * B.dm + co["htn"] * B.htn
      + co["chd"] * B.chd + co["burden10"] * B.burden10 + mj["intercept"])
pb = 1 / (1 + np.exp(-lp))
o = B.mins.sum()
e = pb.sum()
oe = o / e
eps = 1e-6
pcl = np.clip(pb, eps, 1 - eps)
lg = np.log(pcl / (1 - pcl))
cal = sm.GLM(B.mins.values, sm.add_constant(lg), family=sm.families.Binomial()).fit()
auc_frozen = roc_auc_score(B.mins.values, pb)
# bootstrap 95% CI for the frozen-model AUC (2,000 resamples of the validation set)
# 独立随机流，避免扰动下游 refit bootstrap 的既有序列
rng_f = np.random.default_rng(20261113)
pbv0 = np.asarray(pb)
bsf = []
for _ in range(2000):
    idx = rng_f.integers(0, len(B), len(B))
    if B.mins.values[idx].min() == B.mins.values[idx].max():
        continue
    bsf.append(roc_auc_score(B.mins.values[idx], pbv0[idx]))
frozen_lo, frozen_hi = np.percentile(bsf, [2.5, 97.5])
m2B_refit = fit(B, COV_FULL)
pred_refit = np.asarray(m2B_refit.predict(B))
auc_refit = roc_auc_score(B.mins.values, pred_refit)
oe_refit = B.mins.sum() / pred_refit.sum()
bs2 = []
for _ in range(2000):
    idx = rng.integers(0, len(B), len(B))
    if B.mins.values[idx].min() == B.mins.values[idx].max():
        continue
    bs2.append(roc_auc_score(B.mins.values[idx], pred_refit[idx]))
refit_lo, refit_hi = np.percentile(bs2, [2.5, 97.5])

# H-L for the frozen model
pbv = np.asarray(pb)
q3 = pd.qcut(pbv, 10, labels=False, duplicates="drop")
obs3 = pd.Series(B.mins.values).groupby(q3).sum()
exp3 = pd.Series(pbv).groupby(q3).sum()
n3 = pd.Series(B.mins.values).groupby(q3).size()
hl3 = (((obs3 - exp3) ** 2) / (exp3 * (1 - exp3 / n3))).sum()
p_hl3 = 1 - stats.chi2.cdf(hl3, len(n3) - 2)

slope = cal.params.iloc[1]
slope_lo, slope_hi = slope - 1.96 * cal.bse.iloc[1], slope + 1.96 * cal.bse.iloc[1]
cal_int = cal.params.iloc[0]  # calibration intercept on the logit scale (frozen model in MOVER)

t3 = pd.DataFrame([
    ["Derivation (INSPIRE), apparent", f"{auc:.3f} ({auc_lo:.3f}\u2013{auc_hi:.3f})", "\u2014",
     f"{slopeA:.2f}", "0.00", pfmt(p_hl)],
    ["Derivation (INSPIRE), 10-fold cross-validated", f"{mj['auc_cv']:.3f}", "\u2014", "\u2014", "\u2014", "\u2014"],
    ["Validation (MOVER), frozen model", f"{auc_frozen:.3f} ({frozen_lo:.3f}\u2013{frozen_hi:.3f})", f"{oe:.2f}",
     f"{slope:.2f} ({slope_lo:.2f}\u2013{slope_hi:.2f})", f"{cal_int:.2f}", pfmt(p_hl3)],
    ["Validation (MOVER), model re-estimated in validation data", f"{auc_refit:.3f} ({refit_lo:.3f}\u2013{refit_hi:.3f})",
     f"{oe_refit:.2f}", "\u2014", "\u2014", "\u2014"],
], columns=["Model", "AUC (95% CI)", "O:E ratio", "Calibration slope (95% CI)",
            "Calibration intercept", "Hosmer-Lemeshow P"])
t3.to_csv(os.path.join(EN, "Table3_validation.csv"), index=False, encoding="utf-8-sig")

# ---------------- Table 4: subgroups ----------------
def subgroup(d, covs, strat_col, label, labels=("No", "Yes")):
    out = []
    for lv, lvlab in enumerate([0, 1]):
        sub = d[d[strat_col] == lv]
        cov_sub = [x for x in covs if x != strat_col and sub[x].nunique() > 1]
        if len(sub) < 40 or sub.mins.sum() < 10 or sub.mins.nunique() < 2:
            continue
        try:
            mod = fit(sub, cov_sub)
        except Exception:
            continue
        s_, p_ = fmt(*orci(mod))
        out.append([label, labels[lv], len(sub), int(sub.mins.sum()), s_, p_])
    # likelihood-ratio test for effect modification
    try:
        d = d.copy()
        d["g"] = d[strat_col].astype(int)
        cov_use = [x for x in covs if x != strat_col and d[x].nunique() > 1]
        base = sm.Logit.from_formula("mins ~ burden10 + " + " + ".join(cov_use), data=d).fit(disp=0, maxiter=300)
        inter = sm.Logit.from_formula("mins ~ burden10 * g + " + " + ".join(cov_use), data=d).fit(disp=0, maxiter=300)
        lr = 2 * (inter.llf - base.llf)
        p_int = 1 - stats.chi2.cdf(lr, 1)
    except Exception:
        p_int = np.nan
    return out, p_int


A["age65"] = (A.age >= 65).astype(int)
B["age65"] = (B.age >= 65).astype(int)
A["asa3g"] = (A.asa_class >= 3).astype(int)
B["asa3g"] = (B.asa_class >= 3).astype(int)

rows4 = []
for d, covs, lab in [(A, COV_FULL + ["emergency"], "INSPIRE"), (B, COV_FULL, "MOVER")]:
    blocks = [("Age \u226565 years", "age65", ("<65", "\u226565")),
              ("Sex", "male", ("Female", "Male")),
              ("ASA \u22653", "asa3g", ("ASA 1\u20132", "ASA \u22653")),
              ("Coronary heart disease", "chd", ("No", "Yes")),
              ("Diabetes", "dm", ("No", "Yes"))]
    if "emergency" in d.columns and d.emergency.nunique() > 1:
        blocks.append(("Emergency surgery", "emergency", ("Elective", "Emergency")))
    for name, col, labs in blocks:
        res, p_int = subgroup(d, covs, col, f"{lab}: {name}", labs)
        if len(res) < 2:
            continue
        for r in res:
            rows4.append(r + [(f"{p_int:.3f}" if np.isfinite(p_int) else "\u2014")])
t4 = pd.DataFrame(rows4, columns=["Cohort: subgroup", "Stratum", "n", "MINS", "OR per 10% (95% CI)", "P", "P interaction"])
t4.to_csv(os.path.join(EN, "TableS_subgroup.csv"), index=False, encoding="utf-8-sig")

# ---------------- Table S: sensitivity (both cohorts, symmetric) ----------------
def sens(d, covs, ycol, label):
    dd = d.dropna(subset=[ycol, "burden_pct"])
    cov_use = [x for x in covs if dd[x].nunique() > 1]
    mod = sm.Logit.from_formula(f"{ycol} ~ burden10 + " + " + ".join(cov_use), data=dd).fit(disp=0, maxiter=300)
    s, p = fmt(*orci(mod))
    return [label, f"{len(dd)}", f"{int(dd[ycol].sum())}", s, p]


rows5 = []
rows5.append(sens(A, COV_FULL + ["emergency"], "mins", "INSPIRE: primary definition (>0.026 ng/mL, 72 h)"))
rows5.append(sens(A, COV_FULL + ["emergency"], "mins_04", "INSPIRE: threshold >0.04 ng/mL"))
rows5.append(sens(A, COV_FULL + ["emergency"], "mins_10", "INSPIRE: threshold >0.10 ng/mL"))
rows5.append(sens(A, COV_FULL + ["emergency"], "mins7", "INSPIRE: 7-day window"))
rows5.append(sens(B, COV_FULL, "mins", "MOVER: primary (platform MINS flag)"))
rows5.append(sens(B, COV_FULL, "mins_04", "MOVER: threshold >0.04 ng/mL"))
rows5.append(sens(B, COV_FULL, "mins_10", "MOVER: threshold >0.10 ng/mL"))
if B["mins7"].notna().sum() > 50:
    rows5.append(sens(B, COV_FULL, "mins7", "MOVER: 7-day window"))
else:
    rows5.append(["MOVER: 7-day window", "\u2014", "\u2014", "not estimable*", "\u2014"])
# MINS or ICD-coded MI
# INSPIRE: acute MI from patient-level ICD-10 codes I21/I22 (cannot be timed relative
# to surgery, but acute codes in elective orthopaedic patients are overwhelmingly
# perioperative; limitation noted in the table footnote)
for d, covs, lab in [(A, COV_FULL + ["emergency"], "INSPIRE"), (B, COV_FULL, "MOVER")]:
    d = d.copy()
    if "mi_dx" in d.columns:
        d["mins_or_mi"] = ((d.mins == 1) | (d.mi_dx == 1)).astype(int)
        rows5.append(sens(d, covs, "mins_or_mi", f"{lab}: MINS or ICD-coded MI"))
    elif "patient_diagnosis_codes" in d.columns:
        has_mi = d["patient_diagnosis_codes"].fillna("").astype(str).str.contains(r"\bI2[12]", regex=True)
        d["mins_or_mi"] = ((d.mins == 1) | has_mi).astype(int)
        rows5.append(sens(d, covs, "mins_or_mi", f"{lab}: MINS or ICD-coded MI\u2020"))
t5 = pd.DataFrame(rows5, columns=["Analysis", "n", "Events", "OR per 10% (95% CI)", "P"])
t5.to_csv(os.path.join(EN, "TableS_sensitivity.csv"), index=False, encoding="utf-8-sig")

# AKI secondary, full cohorts
rows6 = []
for path, covs, lab in [(os.path.join(OUT, "inspire_ortho_analytic.csv"), COV_FULL + ["emergency"], "INSPIRE"),
                        (os.path.join(OUT, "mover_ortho_analytic.csv"), COV_FULL, "MOVER")]:
    d = pd.read_csv(path)
    med = float(d.loc[d.monitored == 1, "bmi"].median())
    d["bmi"] = d["bmi"].fillna(med)
    d = d.dropna(subset=["aki", "burden_pct"] + [x for x in covs if x in d.columns])
    d["burden10"] = d.burden_pct / 10
    cov_use = [x for x in covs if d[x].nunique() > 1]
    mod = sm.Logit.from_formula("aki ~ burden10 + " + " + ".join(cov_use), data=d).fit(disp=0, maxiter=300)
    s, p = fmt(*orci(mod))
    rows6.append([f"{lab}: postoperative AKI (full cohort)", len(d), int(d.aki.sum()), s, p])
t5 = pd.concat([t5, pd.DataFrame(rows6, columns=t5.columns)], ignore_index=True)

# in-hospital mortality secondary, full cohorts (outcome ascertained in everyone,
# so no troponin-monitoring selection)
rows7 = []
for path, covs, lab in [(os.path.join(OUT, "inspire_ortho_analytic.csv"), COV_FULL + ["emergency"], "INSPIRE"),
                        (os.path.join(OUT, "mover_ortho_analytic.csv"), COV_FULL, "MOVER")]:
    d = pd.read_csv(path)
    med = float(d.loc[d.monitored == 1, "bmi"].median())
    d["bmi"] = d["bmi"].fillna(med)
    d = d.dropna(subset=["death", "burden_pct"] + [x for x in covs if x in d.columns])
    d["burden10"] = d.burden_pct / 10
    cov_use = [x for x in covs if d[x].nunique() > 1]
    mod = sm.Logit.from_formula("death ~ burden10 + " + " + ".join(cov_use), data=d).fit(disp=0, maxiter=300)
    s, p = fmt(*orci(mod))
    rows7.append([f"{lab}: in-hospital death (full cohort)", len(d), int(d.death.sum()), s, p])
    # robustness: drop the top 1% of burden
    dd = d[d.burden_pct <= d.burden_pct.quantile(0.99)]
    cov_use2 = [x for x in cov_use if dd[x].nunique() > 1]
    mod2 = sm.Logit.from_formula("death ~ burden10 + " + " + ".join(cov_use2), data=dd).fit(disp=0, maxiter=300)
    s2, p2 = fmt(*orci(mod2))
    rows7.append([f"{lab}: in-hospital death, excluding top 1% of burden", len(dd), int(dd.death.sum()), s2, p2])
t5 = pd.concat([t5, pd.DataFrame(rows7, columns=t5.columns)], ignore_index=True)
t5.to_csv(os.path.join(EN, "TableS_sensitivity.csv"), index=False, encoding="utf-8-sig")

print(t1.to_string(index=False))
print()
print(t2.to_string(index=False))
print()
print(t3.to_string(index=False))
print()
print(t4.to_string(index=False))
print()
print(t5.to_string(index=False))
print()
print("AUC %.3f (%.3f-%.3f) HL P %.3f | frozen AUC %.3f O:E %.3f cal slope %.3f | refit AUC %.3f (%.3f-%.3f)"
      % (auc, auc_lo, auc_hi, p_hl, auc_frozen, oe, cal.params.iloc[1], auc_refit, refit_lo, refit_hi))

# ---------------- metrics for figures ----------------
json.dump({
    "auc_apparent": float(auc), "auc_lo": float(auc_lo), "auc_hi": float(auc_hi),
    "auc_cv": float(mj["auc_cv"]), "hl_p": float(p_hl),
    "cal_slope_apparent": float(slopeA),
    "auc_frozen": float(auc_frozen), "auc_frozen_lo": float(frozen_lo),
    "auc_frozen_hi": float(frozen_hi), "oe_frozen": float(oe),
    "cal_slope_frozen": float(slope), "cal_slope_frozen_lo": float(slope_lo),
    "cal_slope_frozen_hi": float(slope_hi), "hl_p_frozen": float(p_hl3),
    "auc_refit": float(auc_refit), "auc_refit_lo": float(refit_lo),
    "auc_refit_hi": float(refit_hi), "oe_refit": float(oe_refit),
    "n_der": int(len(A)), "ev_der": int(A.mins.sum()),
    "n_val": int(len(B)), "ev_val": int(B.mins.sum()),
}, open(os.path.join(OUT, "validation_metrics.json"), "w"), indent=2)
print("metrics ->", os.path.join(OUT, "validation_metrics.json"))

# ---------------- Fig 3 data (analytic cohorts, consistent with Table 1) ----------------
from statsmodels.stats.proportion import proportion_confint

rows_f3 = []
for d, lab in [(A, "INSPIRE"), (B, "MOVER")]:
    for lb in ["0", "0-5", "5-10", ">10"]:
        g = d[d.bcat == lb]
        if len(g) == 0:
            continue
        ev, n = int(g.mins.sum()), len(g)
        lo, hi = proportion_confint(ev, n, method="wilson")
        rows_f3.append([lab, lb, ev, n, ev / n, lo, hi])
pd.DataFrame(rows_f3, columns=["cohort", "cat", "ev", "n", "rate", "lo", "hi"]).to_csv(
    os.path.join(TAB, "mins_fig3_data.csv"), index=False)
print("fig3 data ->", os.path.join(TAB, "mins_fig3_data.csv"))

# ---------------- machine-readable forest data (Fig S2) ----------------
import re as _re
_forest = []
for _, r in t5.iterrows():
    mm = _re.match(r"([0-9.]+) \(([0-9.]+)\u2013([0-9.]+)\)", str(r["OR per 10% (95% CI)"]))
    if not mm:
        continue
    _forest.append([r["Analysis"], r["n"], r["Events"], float(mm.group(1)),
                    float(mm.group(2)), float(mm.group(3)), r["P"]])
pd.DataFrame(_forest, columns=["analysis", "n", "ev", "or", "lo", "hi", "p"]).to_csv(
    os.path.join(TAB, "mins_forest.csv"), index=False)
print("forest data ->", os.path.join(TAB, "mins_forest.csv"), len(_forest), "rows")

# ---------------- Table S1: monitored vs not monitored ----------------
def full(path, has_emergency=True):
    d = pd.read_csv(path)
    d["bmi"] = d["bmi"].fillna(d.loc[d.monitored == 1, "bmi"].median())
    return d


FA, FB = full(os.path.join(OUT, "inspire_ortho_analytic.csv")), full(os.path.join(OUT, "mover_ortho_analytic.csv"))
sel = []
sel_spec = [("Age, years", "age", "cont"), ("Male sex", "male", "cat"), ("BMI, kg/m\u00b2", "bmi", "cont"),
            ("ASA physical status", "asa_class", "cont"),
            ("Baseline serum creatinine, mg/dL", "scr_base", "cont"),
            ("Emergency surgery", "emergency", "cat"),
            ("Anaesthesia duration, h", "ane_h", "cont"),
            ("MAP <65 mmHg, cumulative min", "below65", "cont"),
            ("Hypotension burden, %", "burden_pct", "cont"),
            ("Diabetes", "dm", "cat"), ("Hypertension", "htn", "cat"),
            ("Coronary heart disease", "chd", "cat"), ("Postoperative AKI", "aki", "cat"),
            ("In-hospital death", "death", "cat")]
for label, col, kind in sel_spec:
    row = [label]
    for d in (FA, FB):
        if col not in d.columns:
            row += ["\u2014", "\u2014", "\u2014"]
            continue
        x1 = d.loc[d.monitored == 1, col]
        x0 = d.loc[d.monitored == 0, col]
        if kind == "cont":
            row += [med_iqr(x1), med_iqr(x0), pfmt(p_cont(x1, x0))]
        else:
            row += [n_pct(x1), n_pct(x0), pfmt(p_cat(x1, x0))]
    sel.append(row)
pd.DataFrame(sel, columns=["Characteristic",
                           "INSPIRE monitored (n=%d)" % int(FA.monitored.sum()),
                           "INSPIRE not monitored (n=%d)" % int((FA.monitored == 0).sum()), "P",
                           "MOVER monitored (n=%d)" % int(FB.monitored.sum()),
                           "MOVER not monitored (n=%d)" % int((FB.monitored == 0).sum()), "P"]).to_csv(
    os.path.join(EN, "TableS1_selection.csv"), index=False, encoding="utf-8-sig")
print("selection table ->", os.path.join(EN, "TableS1_selection.csv"))
