# Intraoperative Hypotension and Postoperative Organ Injury

**骨科手术中低血压暴露与术后器官损伤（急性肾损伤、心肌损伤 MINS、院内死亡）的双侧队列分析**

This repository contains the analysis code for the manuscript
*"Intraoperative hypotension and postoperative organ injury in orthopaedic surgery: a two-center cohort study using INSPIRE and MOVER"*
(derivation cohort: INSPIRE / SNUH; external validation cohort: MOVER / UCI).

> 中文简介：本仓库存放与稿件对应的统计分析与出图代码。原始患者数据来自两个受限临床研究数据库（INSPIRE、MOVER），**不随本仓库发布**；数据获取方式见下方 Data access。

## Data access

- **INSPIRE** (Seoul National University Hospital) and **MOVER** (University of California, Irvine) are restricted, IRB-approved research databases. Per their data-use agreements, **individual-level patient data are not publicly shared**.
- All exposure (intraoperative MAP < 65 mmHg cumulative % of anaesthesia duration), outcome, and covariate definitions are implemented in the scripts below and can be re-run by any investigator with approved access to the two platforms.
- Aggregate/derived tables that are not patient-identifiable may be shared on request from the corresponding author.

## Pipeline (run in order)

All scripts live in `code/`. Run them from the repository root, for example `python code/40_mins_cohort.py` or `Rscript code/42_mins_figures.R`.

| Step | Script | Purpose |
|------|--------|---------|
| 1 | `40_mins_cohort.py` | Build derivation (INSPIRE) & validation (MOVER) MINS cohorts; eligibility, exposure, outcomes, covariates |
| 2 | `41_mins_analysis.py` | Primary logistic regression (Model 1: age+sex; Model 2: full adjustment); INSPIRE + MOVER |
| 2b | `41b_organ_rcs.py` | Restricted cubic spline (RCS) curves for AKI & in-hospital death → `organ_rcs_curve.csv` |
| 3 | `42_mins_figures.R` | MINS RCS spline & category-proportion figures |
| 3b | `42b_organ_fig.R` | Fig. 2 organ-injury dose–response (AKI + death) two-panel figure |
| 4 | `43_mins_fig1.py` | Cohort flow diagram (Fig. 1) |
| 5 | `45_mins_tables.py` | Main tables (baseline, primary results, sensitivity) |
| 6 | `46_mins_manuscript.py` | Manuscript (`Manuscript_MINS.docx`) |
| 7 | `47_mins_supplementary.py` | Supplementary material (`Additional_file_MINS.docx`) |
| S1 | `48_r_cluster_check.R` | Patient-level clustering robustness (sandwich SE) |
| S2 | `51_r_consistency_check.R` | Cross-database consistency checks |
| S3 | `52_r_full_recompute.R` | Full independent recomputation of effect estimates |
| S4 | `53_r_selection_cstat.R` | Monitoring-selection c-statistic |
| S5 | `54_r_selection_table.R` | Monitoring-selection table (IPW inputs) |
| S6 | `55_r_ipw.R` + `55b_merge_ipw.py` | Inverse-probability-weighting sensitivity analysis |
| S7 | `56_r_evalue.R` | E-value for unmeasured confounding |
| S8 | `49_negative_control.py` | Negative-control outcomes (pre-existing heart failure, CKD, coronary heart disease) to test outcome-specificity of the exposure–MINS association |
| S9 | `57_abdo_rebuild.py` | Parallel abdominal cohort (INSPIRE): assembly from platform exports → `abdo_full_cohort.csv` |
| S10 | `58_r_abdo_interaction.R` | Abdominal cohort: emergency-by-burden interaction tests (MINS, AKI) |
| S11 | `58b_r_abdo_models.R` | Abdominal cohort: elective model ladder + supplementary Table S6 |

`common.py` is a shared helper imported by the Python scripts.
The repository also includes auxiliary R/Python scripts used for intermediate data checks and figures: `30_r_check.R`, `31_r_figures.R` (cross-platform data validation/figures), `41b_organ_rcs.py` (organ-injury RCS curves), and `55b_merge_ipw.py` (IPW table merge).

> **Note on data extraction:** the scripts above operate on already-exported cohort CSV files. The retrieval scripts that query the non-public analysis interface used to obtain those extracts are intentionally **not** included in this repository, because that interface is not publicly endorsed. Investigators with approved access to INSPIRE and MOVER can re-export the required variables and re-run the analysis scripts directly.

## Dependencies

- **Python 3** with: `pandas`, `numpy`, `statsmodels`, `scipy`, `python-docx`.
- **R 4.x** with: `ggplot2`, `patchwork`, `splines`, `survival`, `WeightIt`, `EValue`.
- CSV inputs are read with `fileEncoding = "UTF-8-BOM"` (project convention).

## Reproducing the results

1. Obtain approved access to INSPIRE and MOVER and export the cohort extracts per `40_mins_cohort.py`.
2. Run the scripts in the order shown above, from the repository root. R scripts resolve paths via
   `Sys.getenv("STUDY_ROOT")`, falling back to the working directory; export `STUDY_ROOT` if you run
   them from elsewhere.
3. `46_mins_manuscript.py` / `47_mins_supplementary.py` emit the submitted `.docx` files; convert to PDF with Word (File → Save As → PDF).

## License

Released under the MIT License (see `LICENSE`).
