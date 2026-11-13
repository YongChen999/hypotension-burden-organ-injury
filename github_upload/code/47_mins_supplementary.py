# -*- coding: utf-8 -*-
"""生成 MINS 论文补充材料 Additional_file_MINS.docx。"""
import os

import pandas as pd
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

OUT = "output"
SUB = os.path.join(OUT, "submission")
TAB = os.path.join(OUT, "tables", "en")
FIG = os.path.join(OUT, "figures", "submission")
FONT = "Times New Roman"


def setup(doc):
    st = doc.styles["Normal"]
    st.font.name = FONT
    st.font.size = Pt(11)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), "SimSun")
    st.paragraph_format.line_spacing = 1.3
    for s in doc.sections:
        s.top_margin = Cm(2.2); s.bottom_margin = Cm(2.2)
        s.left_margin = Cm(2.2); s.right_margin = Cm(2.2)


def para(doc, text="", size=11, bold=False, align="justify", before=0, after=4, line=1.4,
         italic=False):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.line_spacing = line
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.alignment = {"justify": WD_ALIGN_PARAGRAPH.JUSTIFY, "left": WD_ALIGN_PARAGRAPH.LEFT,
                    "center": WD_ALIGN_PARAGRAPH.CENTER}[align]
    r = p.add_run(text)
    r.font.name = FONT
    r.font.size = Pt(size)
    r.bold = bold
    r.italic = italic
    return p


def h(doc, text, size=12.5, before=12):
    return para(doc, text, size=size, bold=True, align="left", before=before, after=5, line=1.25)


def table(doc, path, caption, note="", widths=None, fs=7.6):
    df = pd.read_csv(path, encoding="utf-8-sig", dtype=str, keep_default_na=False)
    import re as _re
    df.columns = [_re.sub(r"\.\d+$", "", c) for c in df.columns]  # 重复 P 列被 pandas 加后缀，表头还原
    p = para(doc, caption, size=10.5, bold=True, align="left", before=8, after=4, line=1.2)
    p.paragraph_format.keep_with_next = True
    t = doc.add_table(rows=df.shape[0] + 1, cols=df.shape[1])
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = widths is None
    trPr = t.rows[0]._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader"); el.set(qn("w:val"), "true"); trPr.append(el)
    for row in t.rows:
        for c in row.cells:
            for pp in c.paragraphs:
                pp.paragraph_format.line_spacing = 1.0
                pp.paragraph_format.space_after = Pt(0)
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
    for j, c in enumerate(df.columns):
        cell = t.cell(0, j)
        cell.text = ""
        r = cell.paragraphs[0].add_run(str(c))
        r.bold = True
        r.font.size = Pt(fs)
        r.font.name = FONT
        tcPr = cell._tc.get_or_add_tcPr()
        sh = OxmlElement("w:shd"); sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto")
        sh.set(qn("w:fill"), "EDF1F5"); tcPr.append(sh)
    for i, row in df.iterrows():
        for j, c in enumerate(df.columns):
            cell = t.cell(i + 1, j)
            cell.text = ""
            r = cell.paragraphs[0].add_run(str(row[c]))
            r.font.size = Pt(fs)
            r.font.name = FONT
    if widths:
        for row in t.rows:
            for j, c in enumerate(row.cells):
                c.width = Cm(widths[j])
    if note:
        para(doc, note, size=8, align="left", before=3, after=8, line=1.15)


def figure(doc, name, caption, width=16.0):
    p = para(doc, caption, size=10.5, bold=True, align="left", before=10, after=4, line=1.2)
    p.paragraph_format.keep_with_next = True
    q = doc.add_paragraph()
    q.alignment = WD_ALIGN_PARAGRAPH.CENTER
    q.add_run().add_picture(os.path.join(FIG, name), width=Cm(width))
    para(doc, "", size=6, after=8)


doc = Document()
setup(doc)

# ---------------- cover ----------------
para(doc, "Additional file 1", size=15, bold=True, align="left", line=1.3, after=6)
para(doc, "Intraoperative hypotension and postoperative organ injury after orthopaedic surgery: "
          "a two-database cohort study with external validation", size=12, bold=True, align="left",
     line=1.35, after=12)
para(doc, "This file contains supplementary Tables S1\u2013S7, supplementary Figures S1\u2013S4, and two methodological appendices.", size=10.5,
     align="left", after=10)

para(doc, "Contents", size=11, bold=True, align="left", after=4)
for line in ["Appendix 1. Exposure algorithms in the two platforms",
             "Appendix 2. Definition and ascertainment of MINS in the two databases",
             "Table S1. Additional baseline characteristics of monitored and unmonitored patients (not shown in Table 2)",
             "Table S2. Sensitivity analyses of the association between burden and MINS",
             "Table S3. Sensitivity to within-patient clustering of repeated operations",
             "Table S4. Subgroup analyses of the association between burden and MINS",
             "Table S5. Negative-control analyses using pre-existing comorbidities as outcomes",
             "Table S6. Parallel abdominal cohort: assembly, association estimates and emergency interaction",
             "Table S7. Complete-case and duration-adjusted analyses of the secondary outcomes",
             "Fig. S1. Distribution of hypotension burden in monitored and unmonitored patients",
             "Fig. S2. Forest plot of the sensitivity analyses",
             "Fig. S3. Restricted cubic spline of the burden\u2013MINS association",
             "Fig. S4. Proportion of patients with MINS by burden category"]:
    para(doc, line, size=10.5, align="left", after=2)

# ---------------- appendix 1 ----------------
h(doc, "Appendix 1. Exposure algorithms in the two platforms", 12.5, before=16)
para(doc, "The two databases compute the cumulative time with mean arterial pressure (MAP) below a threshold "
          "by different algorithms. Both were read from the documentation of the analysis platform and then "
          "verified against the exported data; the verification is summarised at the end of this appendix.")
para(doc, "INSPIRE. The platform merges the invasive arterial pressure series and the non-invasive cuff series, "
          "counts the number of records whose MAP falls below the threshold, and multiplies that count by five "
          "minutes, the nominal sampling interval of the intraoperative vital signs table. A patient with no "
          "records in the window, or with records that never cross the threshold, is assigned zero. The "
          "consequence is that the estimate scales with sampling density: a patient monitored every ten minutes "
          "receives half the credit for the same physiological insult as a patient monitored every five minutes, "
          "and a patient with no monitoring is indistinguishable from a patient who was never hypotensive.")
para(doc, "MOVER. The platform orders all MAP readings from the arterial line and the cuff by their true "
          "timestamps, forward-fills the most recent value, and accumulates the interval between consecutive "
          "measurements, capping each interval at five minutes to limit the influence of monitoring gaps. "
          "Readings outside 20\u2013300 mmHg are discarded. A patient with no intraoperative MAP record is left "
          "blank rather than assigned zero, and a patient whose records never cross the threshold is assigned "
          "zero.")
para(doc, "Verification. If the INSPIRE algorithm is a count multiplied by five, every exported value must be "
          "an exact multiple of five minutes. This was the case for all 10,002 operations. In MOVER, where "
          "intervals are integrated from timestamps, only 48.2% of values were multiples of five. In both "
          "databases the exported burden percentage equalled cumulative minutes divided by anaesthesia duration "
          "to four decimal places, confirming a common denominator. The exposure distributions of the two "
          "cohorts are therefore not directly comparable, and no pooled analysis was attempted.")

# ---------------- appendix 2 ----------------
h(doc, "Appendix 2. Definition and ascertainment of MINS in the two databases", 12.5, before=12)
para(doc, "INSPIRE. Only one myocardial marker is available, troponin I, reported without assay attribution. "
          "No database-derived MINS variable exists, so MINS was defined by us as a peak postoperative troponin "
          "I above 0.026 ng/mL within 72 h of surgery, the 99th upper reference limit of the Abbott "
          "high-sensitivity troponin I assay in use at the contributing centre. The same marker was also "
          "analysed with thresholds of 0.04 and 0.10 ng/mL and with a seven-day window.")
para(doc, "MOVER. The platform provides a derived MINS flag together with the peak high-sensitivity troponin I "
          "value in ng/L and the peak conventional troponin I value in ng/mL. The documentation states that the "
          "flag is set when the postoperative peak exceeds the 99th upper reference limit, but does not state the "
          "numerical threshold or the length of the window over which the peak is taken. We therefore recovered "
          "the threshold empirically from the exported data: among patients with a high-sensitivity value, the "
          "highest peak in patients not flagged was 25 ng/L and the lowest peak in flagged patients was 26 ng/L, "
          "with no overlap; among patients with a conventional value the cut-point lay between 0.03 and "
          "0.04 ng/mL. Agreement between the platform flag and our own 0.026 ng/mL rule was 97.8%; since the "
          "rule was recovered from the flagged values, this confirms the cut-point rather than the accuracy of "
          "the flag. Because the "
          "window is not exposed, a seven-day sensitivity analysis could not be performed in MOVER; this is "
          "stated in the limitations.")

# ---------------- Table S1 ----------------
table(doc, os.path.join(TAB, "TableS1_selection.csv"),
      "Table S1. Additional baseline characteristics of monitored and unmonitored patients",
      "This table lists the variables that are not shown in Table 2 (main text); together the two tables present "
      "the full set of baseline characteristics. Values are median (interquartile range) or n (%). Monitoring "
      "denotes at least one postoperative troponin measurement within 72 h of surgery. P values are from the "
      "Mann\u2013Whitney test for continuous variables and the chi-square or Fisher exact test for categorical "
      "variables. Emergency surgery is not recorded in MOVER. Hypotension burden, age, sex, ASA physical status, "
      "anaesthesia duration, coronary heart disease, postoperative acute kidney injury and in-hospital death are "
      "reported in Table 2; the c-statistic for being monitored is reported in Table 2. BMI, body mass index; "
      "MAP, mean arterial pressure.",
      widths=[4.2, 2.7, 2.7, 1.3, 2.7, 2.7, 1.3], fs=7.2)
para(doc, "Monitored patients had 2.6-fold (INSPIRE) and 1.4-fold (MOVER) the hypotension burden of unmonitored "
          "patients, together with markedly more coronary disease, more emergency surgery and longer "
          "anaesthesia. Because the decision to measure troponin is therefore a consequence of the exposure as "
          "well as of cardiac risk, analyses restricted to monitored patients condition on a common effect; the "
          "direction and magnitude of the resulting bias cannot be estimated from these data and are discussed "
          "in the main text.", size=9.5, line=1.35)

# ---------------- Table S2 ----------------
doc.add_page_break()
table(doc, os.path.join(TAB, "TableS_sensitivity.csv"),
      "Table S2. Sensitivity analyses of the association between hypotension burden and MINS",
      "All estimates are adjusted odds ratios per 10% increase in the percentage of anaesthesia duration with "
      "MAP <65 mmHg, with the same covariate set as Model 2 in the main analysis. The asterisk marks an analysis "
      "that could not be performed because the platform MINS flag does not expose the window over which the "
      "postoperative peak is taken. The dagger marks the INSPIRE composite outcome, in which myocardial "
      "infarction was ascertained from patient-level ICD-10 codes I21/I22; these codes cannot be timed "
      "relative to surgery, but acute infarction codes in elective orthopaedic patients are overwhelmingly "
      "perioperative. The two inverse-probability-of-monitoring rows reweight the monitored "
      "analytic cohort to the covariate distribution of the full cohort using stabilised weights derived from a "
      "logistic model for being monitored (overall monitoring probability divided by the predicted probability), "
      "with robust sandwich standard errors; effective sample sizes were 119 of 434 (INSPIRE) and 113 of 226 "
      "(MOVER), and truncating the weights at their 99th percentile changed each odds ratio by less than 0.02 "
      "while raising the effective sample sizes to 130 of 434 and 115 of 226 respectively. "
      "Weighting adjusts only for measured covariates. The final six rows are secondary analyses of the full cohorts rather than of monitored "
      "patients: two for postoperative acute kidney injury and four for in-hospital death, including two that exclude the top 1% of burden. CI, confidence interval; MINS, myocardial injury "
      "after noncardiac surgery; OR, odds ratio.",
      widths=[7.4, 2.0, 2.0, 3.6, 1.4], fs=7.4)

# ---------------- Table S3 ----------------
table(doc, os.path.join(TAB, "TableS_cluster_sensitivity_pub.csv"),
      "Table S3. Sensitivity of all primary and secondary analyses to within-patient clustering",
      "Operations are shown as operations (patients); 6.0% of operations in the INSPIRE monitored cohort "
      "(434 operations in 408 patients) and 7.5% in the MOVER monitored cohort (226 in 209) were repeat "
      "surgeries in the same patient (17.4% and 16.3% in the full cohorts). All estimates are adjusted odds ratios per 10% increase in the "
      "percentage of anaesthesia duration with MAP <65 mmHg, with the same covariate set as Model 2 in the "
      "main analysis and missing body mass index handled identically (cohort-specific median of monitored "
      "patients). P (model) uses conventional standard errors; P (clustered) uses standard errors clustered "
      "at the patient level (sandwich estimator). The \u201cFirst operation\u201d rows restrict each cohort "
      "to each patient\u2019s first qualifying operation. All estimates retained their direction, and every confidence interval overlapped between the "
      "all-operations and first-operation populations. AKI, acute kidney injury; CI, confidence interval; MINS, myocardial injury after "
      "noncardiac surgery; OR, odds ratio.",
      widths=[3.6, 2.5, 2.2, 1.2, 3.4, 1.5, 1.5], fs=7.2)

# ---------------- Table S4 ----------------
doc.add_page_break()
table(doc, os.path.join(TAB, "TableS_subgroup.csv"),
      "Table S4. Subgroup analyses of the association between hypotension burden and MINS",
      "Odds ratios are per 10% increase in the percentage of anaesthesia duration with MAP <65 mmHg. Each "
      "subgroup model was adjusted for the same covariates as Model 2, with the stratifying variable removed from "
      "the adjustment set. P values in the last column are from a likelihood ratio test comparing models with and "
      "without a burden-by-subgroup interaction term. Strata with fewer than 40 patients, fewer than 10 events or "
      "no variation in the outcome were not estimated. Emergency surgery is not recorded in MOVER, and fewer than "
      "5% of MOVER patients had coded diabetes, so those strata are not shown for that database. Nine interaction "
      "tests were performed (six in INSPIRE and three in MOVER); none survived a Bonferroni correction for nine "
      "tests (all adjusted P \u2265 0.09), and the main text reports the pre-specified age subgroup only. CI, "
      "confidence interval; MINS, myocardial injury after noncardiac surgery; OR, odds ratio.",
      widths=[4.4, 2.3, 1.4, 1.4, 3.4, 1.4, 1.9], fs=7.2)

# ---------------- Table S5 ----------------
doc.add_page_break()
table(doc, os.path.join(TAB, "TableS_negative_control.csv"),
      "Table S5. Negative-control analyses: association between hypotension burden and pre-existing comorbidities",
      "Each odds ratio is per 10% increase in the percentage of anaesthesia duration with MAP <65 mmHg. Heart failure, "
      "chronic kidney disease and coronary heart disease are pre-existing conditions defined before surgery, so the "
      "intraoperative exposure cannot causally influence them; a null association is therefore expected under no "
      "confounding. Models were fitted in the full orthopaedic cohorts (all operations) and adjusted for the same "
      "covariates as Model 2 in the main analysis (age, sex, body mass index, ASA physical status, baseline "
      "creatinine, diabetes, hypertension and coronary heart disease; emergency surgery was added in INSPIRE and "
      "coronary heart disease was omitted from the adjustment set when it was the outcome). Crude and Model 1 "
      "(age, sex) estimates are shown for context. The largely null results, including a fully null independent "
      "validation cohort, support the specificity of the organ-injury associations. ASA, American Society of "
      "Anesthesiologists; CI, confidence interval; OR, odds ratio.",
      widths=[2.7, 2.4, 1.2, 1.1, 2.6, 2.6, 2.6, 1.3], fs=7.2)

# ---------------- Table S6 ----------------
doc.add_page_break()
table(doc, os.path.join(TAB, "TableS6_abdo_parallel.csv"),
      "Table S6. Parallel abdominal cohort: assembly, association estimates and emergency interaction",
      "The parallel abdominal cohort comprises adults aged over 18 years undergoing general-surgery "
      "operations under general anaesthesia in the derivation database (INSPIRE) with a therapeutic "
      "alimentary-tract procedure code (ICD-10-PCS root operations 0D and 0F), an operative duration of at "
      "least 120 min and a hospital stay of at least three days; it was assembled after the orthopaedic "
      "analyses were complete, as a replication, and is not an external validation. All odds ratios are per "
      "10% increase in the percentage of anaesthesia duration with MAP <65 mmHg, computed with the same "
      "platform algorithm as the orthopaedic derivation cohort. MINS was defined as a peak postoperative "
      "troponin I above 0.026 ng/mL within 72 h and acute kidney injury (AKI) by the KDIGO creatinine "
      "criteria, both identical to the main analysis. The abdominal models adjusted for age, sex, body mass "
      "index, open (versus laparoscopic) surgical approach, operative duration, ASA physical status, baseline "
      "creatinine (median-imputed when missing, 27% of monitored elective patients), diabetes, hypertension and "
      "coronary heart disease; emergency surgery defined the strata of the sensitivity analysis rather than "
      "entering as a covariate. Interaction P values are from likelihood ratio tests comparing models with "
      "and without a burden-by-emergency term. The two pooled rows labelled 'complete covariates' were "
      "fitted in the 1,311 of the 1,408 monitored operations (465 events) with complete covariate data; "
      "the stratum-specific event counts (328 elective and 195 emergency) therefore do not sum to the "
      "pooled count. The pooled estimate including emergency operations is driven "
      "by the composition of the emergency stratum (58.4% MINS among monitored, median burden twice that of "
      "elective operations) rather than by a steeper exposure\u2013outcome slope within strata. ASA, American "
      "Society of Anesthesiologists; CI, confidence interval; MINS, myocardial injury after noncardiac "
      "surgery; OR, odds ratio.",
      widths=[7.6, 1.9, 1.9, 3.1, 1.4], fs=7.2)
para(doc, "The abdominal cohort replicates both halves of the orthopaedic pattern: a crude MINS association "
          "abolished by adjustment for operative duration and case complexity, and a stable adjusted "
          "association with acute kidney injury. Troponin monitoring, although two and a half times more "
          "frequent than in the orthopaedic derivation cohort, still covered only 11.8% of elective "
          "operations, indicating that selection into monitoring is a structural feature of MINS research "
          "across procedure types rather than an artefact of orthopaedic practice.", size=9.5, line=1.35)

# ---------------- Table S7 ----------------
doc.add_page_break()
table(doc, os.path.join(TAB, "TableS7_aki_cc_duration.csv"),
      "Table S7. Complete-case and duration-adjusted analyses of the secondary outcomes",
      "All estimates are adjusted odds ratios per 10% increase in the percentage of anaesthesia duration with "
      "MAP <65 mmHg, with the same covariate set as Model 2 in the main analysis. The dagger marks the "
      "complete-case analyses of postoperative acute kidney injury (AKI), which are restricted to patients with "
      "a measured baseline serum creatinine (within 7 or 30 days before surgery) and at least one postoperative "
      "measurement. In MOVER, baseline creatinine values missing after the 7/30-day look-back were "
      "back-calculated from age and sex with the MDRD study equation and entered both the covariate set and "
      "the KDIGO baseline; this sensitivity removes the 2,269 AKI-evaluable patients whose baseline was "
      "imputed. In INSPIRE no imputed baseline enters the primary model (patients without a measured baseline "
      "were already excluded by the complete-covariate requirement), so the complete-case row reproduces the "
      "primary estimate. The double "
      "dagger marks models that add anaesthesia duration (hours) to the Model 2 covariate set; because the "
      "exposure is duration-normalised (cumulative minutes below 65 mmHg divided by anaesthesia duration), "
      "these models test whether the associations are driven by the hypotensive fraction rather than by "
      "absolute time under anaesthesia. AKI, acute kidney injury; CI, confidence interval; MAP, mean arterial "
      "pressure; MINS, myocardial injury after noncardiac surgery; OR, odds ratio.",
      widths=[7.6, 1.9, 1.9, 3.1, 1.4], fs=7.2)
para(doc, "Neither restriction changed any conclusion. Removing imputed baselines moved the MOVER AKI estimate "
          "from 1.08 to 1.09 with a wider interval, and adjusting for anaesthesia duration moved every estimate "
          "by 0.01 or less, including the primary MINS estimates (1.02 to 1.02 in INSPIRE and 1.33 to 1.34 "
          "in MOVER).", size=9.5, line=1.35)

# ---------------- Fig S1 ----------------
figure(doc, "MINS_FigS1_selection.png",
       "Fig. S1 Distribution of intraoperative hypotension burden in monitored and unmonitored patients. "
       "Side-by-side histograms are shown separately for each database, with burden truncated at 60% for "
       "display; the height "
       "of each bar is the percentage of patients in that group falling in a five-percentage-point bin, so that "
       "the two groups can be compared despite their very different sizes (INSPIRE 468 monitored versus 9,505 "
       "unmonitored; MOVER 226 versus 5,975). In INSPIRE the extraction assigns zero minutes below the "
       "threshold \u2013 and therefore a burden of 0% \u2013 to patients whose record contains no MAP "
       "measurement, so the zero-burden bar includes such zero-assigned patients; in MOVER such patients have "
       "no calculable burden and are excluded from the plot (735 unmonitored, 4 monitored), as are 29 INSPIRE "
       "patients without a recorded anaesthesia duration. Monitored "
       "patients are shifted towards higher burden in both "
       "databases, which is the empirical basis for the selection argument developed in the Discussion.")

# ---------------- Fig S2 ----------------
doc.add_page_break()
figure(doc, "MINS_FigS2_sensitivity.png",
       "Fig. S2 Forest plot of the sensitivity analyses. Each row is one analysis; the point is the adjusted "
       "odds ratio per 10% increase in burden and the horizontal line the 95% confidence interval, on a "
       "logarithmic scale. Blue rows are analyses of MINS under alternative definitions; red rows are the "
       "secondary analyses of the full cohorts, postoperative acute kidney injury and in-hospital death, in "
       "which the outcome does not require troponin monitoring. The two inverse-probability-weighted rows "
       "rest on effective sample sizes of 119 of 434 (INSPIRE) and 113 of 226 (MOVER) and are imprecise by "
       "construction. The vertical dashed line is "
       "the null. The derivation cohort is stable across definitions of MINS, whereas the validation cohort "
       "attenuates as the troponin threshold rises, indicating that its borderline association is carried by "
       "small troponin elevations.")

# ---------------- Fig S3 ----------------
doc.add_page_break()
figure(doc, "MINS_FigS3_rcs.png",
       "Fig. S3 Shape of the association between hypotension burden and MINS in the derivation cohort (n = 434). "
       "The solid line is the adjusted odds ratio from a restricted cubic spline with four degrees of freedom; "
       "the shaded band is the pointwise 95% confidence interval. Knots were placed at equally spaced quantiles "
       "between the 2nd and 98th percentiles of burden, and the curve was centred at zero burden, so that the "
       "odds ratio is one at the reference. The model was adjusted for age, sex, body mass index, ASA physical "
       "status, baseline creatinine, emergency surgery, diabetes, hypertension and coronary heart disease. There "
       "was no evidence of departure from linearity (P = 0.89); the confidence band widens steeply over the "
       "first 10% of burden and remains wide thereafter; few patients contributed beyond 30% burden. MINS, "
       "myocardial injury after noncardiac surgery.")

# ---------------- Fig S4 ----------------
figure(doc, "MINS_FigS4_dose.png",
       "Fig. S4 Proportion of patients with MINS in each burden category, by database. Bars are the observed "
       "proportions among troponin-monitored patients in the analytic cohorts (INSPIRE n = 434, MOVER n = 226); "
       "error bars are 95% confidence intervals from the Wilson score method, and the fractions above each bar "
       "are the number of patients with MINS over the number in that category. In the derivation cohort the "
       "crude proportions were 41%, 28%, 26% and 39% across the four categories, a non-monotonic pattern with "
       "no consistent gradient; the zero-burden category contained only 41 patients and its confidence "
       "interval (28\u201357%) overlaps the highest category. In the validation cohort the proportions rose "
       "from 27% to 45%, 53% and 55%, levelling off above 5% burden. Crude proportions and "
       "covariate-adjusted odds ratios need not share the same ordering. MINS, myocardial injury after "
       "noncardiac surgery.")

path = os.environ.get("SUPP_OUT", os.path.join(SUB, "Additional_file_MINS.docx"))
doc.save(path)
print("saved", path)
