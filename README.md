# Intraoperative Hypotension and Postoperative Organ Injury

**骨科手术中低血压暴露与术后器官损伤（急性肾损伤、心肌损伤 MINS、院内死亡）的双数据库队列分析**

This repository contains the analysis code for the manuscript
*"Intraoperative hypotension and postoperative organ injury after orthopaedic surgery: a two-database cohort study with external validation"*
(derivation cohort: INSPIRE / SNUH; external validation cohort: MOVER / UCI).

> 中文简介：本仓库存放与稿件对应的统计分析与出图代码。原始患者数据来自两个受限临床研究数据库（INSPIRE、MOVER），**不随本仓库发布**；数据获取方式见下方 Data access。

## Data access

- **INSPIRE** (Seoul National University Hospital) and **MOVER** (University of California, Irvine) are restricted, IRB-approved research databases. Per their data-use agreements, **individual-level patient data are not publicly shared**.
- All exposure (intraoperative MAP < 65 mmHg cumulative percentage of anaesthesia duration), outcome, and covariate definitions are implemented in the scripts below and can be re-run by any investigator with approved access to the two databases.
- Aggregate analytic outputs that allow the reported estimates to be reproduced are available to editors and reviewers on request during peer review and will be deposited with a permanent DOI on acceptance.

## Pipeline (run in order)

All scripts live in `code/`. Run them from the repository root, for example
`python code/40_mins_cohort.py` or `Rscript code/42_mins_figures.R`.

| Step | Script | Purpose |
|------|--------|---------|
| 1 | `40_mins_cohort.py` | Build derivation (INSPIRE) and validation (MOVER) orthopaedic cohorts; eligibility, exposure, outcomes and covariates |
| 2 | `41_mins_analysis.py` | Logistic models, spline diagnostics, discrimination and cross-validation |
| 3 | `41b_organ_rcs.py` | Restricted cubic spline curves for AKI and in-hospital death |
| 4 | `45_mins_tables.py` | Main and sensitivity tables |
| 5 | `49_negative_control.py` | Negative-control analyses using coded chronic conditions; diagnosis timing is not available |
| 6 | `54_r_selection_table.R` | Monitoring-selection table and c-statistic |
| 7 | `55_r_ipw.R` | Inverse-probability-of-monitoring weighted analysis |
| 8 | `55b_merge_ipw.py` | Merge IPW rows into Table S2 and the forest-plot source data |
| 9 | `55c_r_ipw_ess.R` | Effective sample sizes after 99th-percentile weight truncation |
| 10 | `56_r_evalue.R` | E-values for the reported associations |
| 11 | `57_abdo_rebuild.py` | Parallel abdominal cohort assembly |
| 12 | `58_r_abdo_interaction.R` | Abdominal cohort emergency-by-burden interaction tests |
| 13 | `58b_r_abdo_models.R` | Abdominal model ladder and Table S6 |
| 14 | `59_r_aki_cc_duration.R` | Complete-case AKI analysis and anaesthesia-duration adjustment |
| 15 | `42_mins_figures.R` | Figs S1–S4 and external-validation Fig. 3 |
| 16 | `42b_organ_fig.R` | Fig. 2 organ-injury dose–response panel |
| 17 | `61_r_fig1_flow.R` | Fig. 1 cohort flow diagram |
| 18 | `48_r_cluster_check.R`, `51_r_consistency_check.R`, `52_r_full_recompute.R`, `53_r_selection_cstat.R` | Independent verification |

> **Important:** `45_mins_tables.py` rebuilds the base sensitivity table and removes previously merged IPW rows. Run `55b_merge_ipw.py` before `42_mins_figures.R`; otherwise Fig. S2 will omit the two IPW analyses.

`43_mins_fig1.py` is an earlier Python implementation of Fig. 1, retained for reference; `61_r_fig1_flow.R` produces the submitted figure. `common.py` is a shared helper imported by the Python scripts.

> **Note on data extraction:** these scripts operate on already-exported cohort CSV files. The retrieval scripts that query the non-public analysis interface used to obtain those extracts are intentionally **not** included in this repository. Investigators with approved access to INSPIRE and MOVER can re-export the required variables and re-run the analysis scripts directly.

## Dependencies

- **Python 3** with `pandas`, `numpy`, `patsy`, `statsmodels`, `scipy` and `scikit-learn`; `matplotlib` is needed only for the superseded `43_mins_fig1.py`.
- **R 4.x** with `ggplot2`, `scales`, `jsonlite`, `patchwork` and `sandwich`; the auxiliary checks also use `readr`, `dplyr`, `tidyr` and `rms`. `ragg` is optional for faster high-resolution figures.
- CSV inputs are read with `fileEncoding = "UTF-8-BOM"` (project convention).

## Reproducing the results

1. Obtain approved access to INSPIRE and MOVER and export the cohort extracts expected by `40_mins_cohort.py`.
2. Run the scripts in the order shown above from the repository root. R scripts resolve paths via `Sys.getenv("STUDY_ROOT")`, falling back to the working directory; export `STUDY_ROOT` if you run them from elsewhere.
3. Tables are written as CSV to `output/tables/en/` and figures as PNG files to `output/figures/submission/`; these are the source of every number and panel in the manuscript and its supplementary material.

## License

Released under the MIT License (see `LICENSE`).
