# -*- coding: utf-8 -*-
"""把 55_r_ipw.R 的 IPW 结果合并进 TableS_sensitivity.csv 与 mins_forest.csv（幂等）。"""
import csv, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EN = os.path.join(ROOT, "output", "tables", "en")
EN_DASH = "\u2013"

with open(os.path.join(ROOT, "output", "tables", "ipw_results.csv"), encoding="ascii") as f:
    ipw = list(csv.DictReader(f))

def merge(path, is_forest):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    if any("inverse-probability" in r[0] for r in rows[1:]):
        print("already merged:", path); return
    out = [rows[0]]
    inserted = False
    for r in rows[1:]:
        if not inserted and r[0].startswith("INSPIRE: postoperative AKI"):
            for x in ipw:
                if is_forest:
                    out.append([x["analysis"], x["n"], x["ev"], f'{float(x["or"]):.2f}',
                                f'{float(x["lo"]):.2f}', f'{float(x["hi"]):.2f}', f'{float(x["p"]):.3f}'])
                else:
                    out.append([x["analysis"], x["n"], x["ev"],
                                f'{float(x["or"]):.2f} ({float(x["lo"]):.2f}{EN_DASH}{float(x["hi"]):.2f})',
                                f'{float(x["p"]):.3f}'])
            inserted = True
        out.append(r)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        csv.writer(f).writerows(out)
    print("merged", len(ipw), "rows ->", path)

merge(os.path.join(EN, "TableS_sensitivity.csv"), is_forest=False)
merge(os.path.join(ROOT, "output", "tables", "mins_forest.csv"), is_forest=True)
