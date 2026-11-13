# -*- coding: utf-8 -*-
"""打包 MINS 投稿包 v11（2026-11-13）。
在 v10（腹部队列）基础上新增 Table S7（AKI 完整病例 + 麻醉时长校正敏感性）
与脚本 59_r_aki_cc_duration.R，正文/补充材料已同步。
"""
import os
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
SUB = os.path.join(OUT, "submission")
EN = os.path.join(OUT, "tables", "en")
FIG = os.path.join(OUT, "figures", "submission")
CODE = os.path.join(SUB, "github_upload", "code")

README = """MINS SUBMISSION PACKAGE - v14 (2026-11-13)
==========================================

This build adds two small reviewer-facing fixes: a 95% confidence interval for
the frozen-model AUC throughout (Table 4, Results, Fig. 3A annotation and
legend), and a rewritten Fig. S1 legend that states exactly how patients
without an intraoperative MAP record are handled in each database. It sits on
top of v13 (statistical-consistency audit). The .docx files are the
authoritative, submission-ready documents.

Contents
--------
01_Manuscript/      Manuscript_MINS.docx
02_Supplementary/   Additional_file_MINS.docx  (Tables S1-S7, Figures S1-S4,
                    Appendices 1-2)
03_Figures/         7 figures, 300 dpi PNG
                      Main:  Fig 1 flow; Fig 2 organ dose-response (2-panel
                             AKI + in-hospital death); Fig 3 external validation
                      Suppl: Fig S1 burden by monitoring (side-by-side
                             histograms); Fig S2 forest of sensitivity
                             analyses; Fig S3 RCS for MINS; Fig S4 MINS rate
                             by burden category
04_Tables/          11 tables as CSV (Table 1-4, S1-S7)
05_Code/            29 analysis scripts (see pipeline order below)

Changes in v14 (AUC interval; Fig. S1 legend)
---------------------------------------------
* Frozen-model AUC now carries a bootstrap 95% CI (2,000 resamples of the
  validation set): 0.682 (0.611-0.749). It is reported in Table 4, in the
  Results ("an AUC of 0.682, 95% CI 0.61-0.75"), in the Fig. 3A annotation,
  in the Fig. 3 legend and in the abstract. The re-estimated-model bootstrap
  CI is unchanged (0.711, 0.640-0.777) because the new bootstrap uses its own
  random stream.
* Language-style pass over the main text: parenthetical dashes reduced from
  29 to 0, "rather than" trimmed from 29 to 22 (replaced with "not" or
  rephrased where natural); no numerical or structural content changed.
* Fig. S1 legend rewritten: the 0% bar in INSPIRE includes patients whose
  record contains no MAP measurement, to whom the extraction assigns zero
  minutes below threshold; in MOVER such patients have no calculable burden
  and are excluded from the plot (735 unmonitored, 4 monitored), as are 29
  INSPIRE patients without a recorded anaesthesia duration. The group sizes in
  the legend now match what is plotted (468 vs 9,505; 226 vs 5,975).
* Word counts: abstract 347; main text 8,880.

Changes in v13 (statistical-consistency audit)
----------------------------------------------
* Abstract: AKI reported as consistent across databases with the pooled
  estimate (1.09, 1.03-1.15; I2 = 0%); "negative controls were null" now
  restricted to the validation cohort. Abstract 347 words.
* Methods: calibration intercept added to the validation reporting; pooled
  (DerSimonian-Laird inverse-variance) estimation and Wald comparisons between
  outcome-specific log odds ratios described.
* Results: pooled AKI estimate added (the only estimate replicated formally);
  calibration intercept 0.81 reported; inverse-probability-weighted results no
  longer given a directional reading (effective sample sizes 27% and 50%).
* Discussion: "the main finding" -> "the central pattern", with an explicit
  statement that the MINS-versus-AKI and MINS-versus-death differences were
  themselves non-significant in both databases (all P >= 0.08), so the contrast
  is descriptive; the replicated AKI association is emphasised instead.
* Negative controls: the chronic kidney disease association (1.18) is now
  stated to be comparable to, and slightly larger than, the adjusted AKI
  association in INSPIRE (1.09), with the null pattern in MOVER as the
  specificity evidence.
* Table 4 (validation): new calibration intercept column (frozen model 0.81).
* Table S6: the two pooled rows are labelled "complete covariates" and the
  footnote explains the 1,311 of 1,408 monitored operations (465 events), so
  that the stratum-specific counts no longer appear to disagree with the
  pooled count.
* Table 1 footnote now states the monitored analytic denominators (434/226)
  and points to Table 2 / Table S1 for the full cohorts; Fig. S1 footnote
  discloses that INSPIRE assigns zero burden to patients with no record;
  Fig. S2 footnote gives the IPW effective sample sizes.
* Fig. 3B: decile-grouping bug fixed (a ceiling() artefact had placed the last
  patient alone in an eleventh "decile", producing a spurious isolated point);
  the panel now also prints the calibration intercept.
* Word counts: abstract 347; main text 8,880.

Changes in v12 (figure-text-layout audit)
-----------------------------------------
* Fig. S4 redrawn: the category factor had been mapped to levels that did not
  exist, collapsing four categories to NA. Now 4 categories x 2 databases,
  Wilson 95% CI per bar, fractions on top (INSPIRE 41/28/26/39%, MOVER
  27/45/53/55%).
* Fig. S2 redrawn: the MINS-or-ICD-MI row now carries n = 434, 165 events,
  OR 1.01 (0.90-1.14), P = 0.813 (was NA). Root cause: the R read converted
  UTF-8 to the local code page and lost the dagger; now read from raw bytes.
* Fig. S1 redrawn as side-by-side histograms, y-axis reaches the tallest
  zero-burden bar (previously clipped at 32%, dropping 6 bars).
* Fig. 1 redrawn in R/grid (61_r_fig1_flow.R): "no troponin monitoring
  required" in the outcome boxes, BMI imputation labelled "retained", footnote
  no longer claims ascertainment "in everyone".
* Table 1, Table 2 and Table S1: duplicate P columns no longer render "P.1".
* Text: AKI/death curve descriptions match Fig. 2; calibration "in most
  deciles"; Fig. S3 confidence-band description; Fig. 2 states each cohort's
  plotted range; "ascertained in every patient" replaced at six sites; AKI
  seven-day window added to Methods; E-values and negative controls added to
  the abstract; one duplicate "Finally" removed.
* Word counts: abstract 347; main text 8,880.

Carried over from v11
---------------------
* Table S7: complete-case AKI (measured baseline only) and models additionally
  adjusted for anaesthesia duration. No estimate moved by more than 0.01.

Carried over from v10 (abdominal cohort)
----------------------------------------
* Parallel elective major abdominal cohort (INSPIRE GS, PCS 0D/0F, >=120 min,
  stay >=3 d; 9,075 elective + 973 emergency): MINS crude 1.10 -> adjusted 1.03
  (0.99-1.07, P = 0.19); AKI adjusted 1.22 (1.18-1.26); no burden-by-emergency
  interaction (P = 0.49 MINS, 0.53 AKI). Table S6.

PDF regeneration note
---------------------
Generate PDFs in Word before submitting: open each .docx -> File -> Save As ->
PDF.

BEFORE SUBMISSION (still outstanding)
-------------------------------------
* Push the updated 05_Code scripts (59 and 61 are new; 42/43/46/47/60 changed)
  to the GitHub repository via Upload files.

Pipeline order to reproduce
---------------------------
40 (cohort) -> 41 (analysis) -> 41b (organ RCS) -> 42 (figures S1/S2/S3/S4 +
validation, R) -> 42b (organ Fig. 2, R) -> 61 (Fig 1, R port of 43) ->
45 (tables) -> 49 (negative control) -> 54 (selection table + c-statistic, R) ->
55 (IPW, R) -> 55b (merge IPW) -> 55c (truncated-weight ESS, R) ->
56 (E-values, R) -> 57 (abdominal cohort) -> 58 (abdominal interaction, R) ->
58b (abdominal models + Table S6, R) -> 59 (complete-case AKI + duration
adjustment, R) -> 46 (manuscript) -> 47 (supplementary) -> 48/51/52
(verification, R).
"""

FIGS = ["MINS_Fig1_flow.png", "MINS_Fig2_organ_rcs.png", "MINS_Fig3_validation.png",
        "MINS_FigS1_selection.png", "MINS_FigS2_sensitivity.png", "MINS_FigS3_rcs.png",
        "MINS_FigS4_dose.png"]

# zip 内表号与正文一致：Table2_models->Table3_models, Table3_validation->Table4_validation
TABLES = [("Table1_baseline.csv", "Table1_baseline.csv"),
          ("Table2_selection.csv", "Table2_selection.csv"),
          ("Table2_models.csv", "Table3_models.csv"),
          ("Table3_validation.csv", "Table4_validation.csv"),
          ("TableS1_selection.csv", "TableS1_selection.csv"),
          ("TableS_sensitivity.csv", "TableS_sensitivity.csv"),
          ("TableS_cluster_sensitivity_pub.csv", "TableS_cluster_sensitivity_pub.csv"),
          ("TableS_subgroup.csv", "TableS_subgroup.csv"),
          ("TableS_negative_control.csv", "TableS_negative_control.csv"),
          ("TableS6_abdo_parallel.csv", "TableS6_abdo_parallel.csv"),
          ("TableS7_aki_cc_duration.csv", "TableS7_aki_cc_duration.csv")]

path = os.path.join(SUB, "MINS_Submission_Package_20261113.zip")
n = 0
with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("README.txt", README); n += 1
    z.write(os.path.join(SUB, "Manuscript_MINS.docx"), "01_Manuscript/Manuscript_MINS.docx"); n += 1
    z.write(os.path.join(SUB, "Additional_file_MINS.docx"), "02_Supplementary/Additional_file_MINS.docx"); n += 1
    for f in FIGS:
        z.write(os.path.join(FIG, f), f"03_Figures/{f}"); n += 1
    for src, dst in TABLES:
        z.write(os.path.join(EN, src), f"04_Tables/{dst}"); n += 1
    for f in sorted(os.listdir(CODE)):
        z.write(os.path.join(CODE, f), f"05_Code/{f}"); n += 1
print("saved", path, n, "entries,", round(os.path.getsize(path) / 1e6, 2), "MB")
