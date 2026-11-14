# -*- coding: utf-8 -*-
"""生成 MINS 骨科论文正文 Manuscript_MINS.docx（BMC Anesthesiology 格式）。"""
import os

import pandas as pd
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
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
    st.font.size = Pt(12)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), "SimSun")
    pf = st.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.DOUBLE
    pf.space_after = Pt(0)
    for s in doc.sections:
        s.top_margin = Cm(2.54); s.bottom_margin = Cm(2.54)
        s.left_margin = Cm(2.54); s.right_margin = Cm(2.54)


def para(doc, text="", size=12, bold=False, italic=False, align="justify",
         before=0, after=0, line=2.0, color=None):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.line_spacing = line
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.alignment = {"justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
                    "left": WD_ALIGN_PARAGRAPH.LEFT,
                    "center": WD_ALIGN_PARAGRAPH.CENTER}[align]
    r = p.add_run(text)
    r.font.name = FONT
    r.font.size = Pt(size)
    r.bold = bold
    r.italic = italic
    if color:
        from docx.shared import RGBColor
        r.font.color.rgb = RGBColor(*color)
    return p


def h1(doc, text):
    return para(doc, text, size=13, bold=True, align="left", before=12, after=4, line=1.5)


def h2(doc, text):
    return para(doc, text, size=12, bold=True, align="left", before=10, after=3, line=1.5)


def table(doc, path, caption, note="", widths=None, fs=7.6, new_page=False):
    df = pd.read_csv(path, encoding="utf-8-sig", dtype=str, keep_default_na=False)
    import re as _re
    df.columns = [_re.sub(r"\.\d+$", "", c) for c in df.columns]  # 重复 P 列被 pandas 加后缀，表头还原
    p = para(doc, caption, size=11, bold=True, align="left", before=10, after=4, line=1.2)
    p.paragraph_format.keep_with_next = True
    if new_page:
        p.paragraph_format.page_break_before = True
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
        trPr2 = row._tr.get_or_add_trPr()
        trPr2.append(OxmlElement("w:cantSplit"))
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


def figure(doc, name, width=16.0, caption=None):
    if caption:
        p = para(doc, caption, size=10, bold=True, align="left", before=10, after=4, line=1.3)
        p.paragraph_format.keep_with_next = True
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(os.path.join(FIG, name), width=Cm(width))
    para(doc, "", size=6, after=6)


doc = Document()
setup(doc)

# ======================= TITLE PAGE =======================
para(doc, "Intraoperative hypotension and postoperative organ injury after orthopaedic surgery: "
          "a two-database cohort study with external validation", size=15, bold=True,
     align="left", line=1.3, after=10)
para(doc, "Running title: Hypotension and organ injury in orthopaedic surgery", size=11,
     italic=True, align="left", line=1.4, after=14)

para(doc, "Authors", size=11, bold=True, align="left", line=1.3, after=2)
para(doc, "Yong Chen\u00b9\u2020, Qixia He\u00b9\u2020, Yanwen Zhu\u00b9, Hongling Zhuang\u00b9, Jing Zhang\u00b9, Mingzhi Luo\u00b9, Yan Lu\u00b9*",
     size=11, align="left", line=1.5, after=10)
para(doc, "\u00b9 Department of Anesthesiology, The Affiliated Hospital of Guangdong Medical University, "
          "Zhanjiang 524001, Guangdong, China", size=10, align="left", line=1.4, after=1)
para(doc, "\u2020These authors contributed equally to this work and share first authorship.", size=10,
     align="left", line=1.4, after=1)
para(doc, "*Correspondence: Yan Lu, MD, MS, Department of Anesthesiology, The Affiliated Hospital of "
          "Guangdong Medical University, No. 57 Renmin Avenue South, Xiashan District, Zhanjiang 524001, "
          "Guangdong, China; e-mail: 249110951@qq.com", size=10, align="left", line=1.4, after=14)

para(doc, "Word count: abstract 347; main text 8,886; tables 4; figures 3; supplementary files 1.",
     size=10, align="left", line=1.4, after=4)
para(doc, "Keywords: intraoperative hypotension; postoperative organ injury; acute kidney injury; "
          "myocardial injury after noncardiac surgery; orthopaedic surgery; external validation; troponin",
     size=10, align="left", line=1.4, after=4)

doc.add_page_break()

# ======================= ABSTRACT =======================
h1(doc, "Abstract")
h2(doc, "Background")
para(doc, "Intraoperative hypotension may cause myocardial injury after noncardiac surgery (MINS), but "
          "evidence in orthopaedic surgery is sparse and single-database. We derived the association between "
          "cumulative intraoperative hypotension and MINS in one database and tested it in another.")

h2(doc, "Methods")
para(doc, "Retrospective study of adults undergoing orthopaedic surgery under general anaesthesia in INSPIRE "
          "(Seoul) and MOVER (University of California, Irvine). The exposure was cumulative time with mean "
          "arterial pressure below 65 mmHg as a percentage of anaesthesia duration, per 10% increment. The "
          "primary outcome was MINS (peak postoperative troponin I above the 99th upper reference limit within "
          "72 h, or the database flag); secondary full-cohort outcomes (acute kidney injury, in-hospital "
          "death) were analysed as supportive rather than confirmatory. A parallel cohort of major abdominal "
          "operations in INSPIRE provided internal replication. "
          "Derivation coefficients were applied unchanged for external validation. Selection into troponin "
          "monitoring was quantified with a c-statistic and inverse-probability weighting; robustness was "
          "summarised with E-values and negative-control comorbidities.")

h2(doc, "Results")
para(doc, "Of 10,002 orthopaedic operations in INSPIRE, 468 (4.7%) were troponin-monitored and 434 analysed; "
          "155 (35.7%) had MINS. MINS showed no association with burden in derivation (adjusted odds ratio "
          "1.02 per 10%, 0.91\u20131.15) and only a borderline one on validation (1.33, "
          "0.97\u20131.83). In contrast, acute kidney injury was consistently associated with burden "
          "(1.09, 1.02\u20131.17; 1.08, 0.98\u20131.20; pooled 1.09, 1.03\u20131.15, I\u00b2 = 0%), as was "
          "in-hospital death (1.18, 1.05\u20131.32; "
          "1.65, 1.20\u20132.26). Monitoring was highly predictable from measured covariates (c-statistic 0.85 and "
          "0.71), yet inverse-probability weighting left the MINS estimates unchanged. "
          "Discrimination was modest (area under the curve 0.652; frozen 0.682, 0.61\u20130.75) and calibration did not "
          "transport. In 9,075 elective abdominal operations (1,074 monitored, 328 events), adjusted odds "
          "ratios were 1.03 (0.99\u20131.07) for MINS and 1.22 (1.18\u20131.26) for acute kidney injury. "
          "E-values were 1.35\u20132.68; validation-cohort negative controls were null.")

h2(doc, "Conclusions")
para(doc, "Hypotension burden was consistently associated with organ injury ascertained without troponin monitoring, "
          "but not with MINS in the troponin-monitored subset, where selection was highly predictable. "
          "Because troponin ordering is triggered by suspicion related to hypotension itself, MINS studies "
          "restricted to monitored patients are prone to selection bias; routine reporting of the monitored "
          "and unmonitored populations is needed.")

doc.add_page_break()

# ======================= BACKGROUND =======================
h1(doc, "Background")
para(doc, "Myocardial injury after noncardiac surgery (MINS) is defined by a postoperative elevation of "
          "cardiac troponin that is attributable to ischaemia rather than to an alternative cause, and it is "
          "common: international prospective cohorts report incidences between 5% and 19% depending on the "
          "surgical mix and the sensitivity of the assay used [1,2]. The prognostic weight of MINS is "
          "considerable. In the VISION cohort, peak postoperative high-sensitivity troponin T concentrations "
          "were graded with 30-day mortality [2], and perioperative myocardial infarction carries a comparable "
          "prognosis in other large cohorts [3]. MINS is now recognised as the most frequent "
          "perioperative cardiovascular complication, and the only intervention shown to modify its course is "
          "antithrombotic: dabigatran reduced major vascular complications in patients with MINS in the MANAGE "
          "trial [4].")
para(doc, "The dominant mechanism is a mismatch between myocardial oxygen supply and demand. Intraoperative "
          "hypotension lowers coronary perfusion pressure, and because subendocardial perfusion occurs mainly "
          "in diastole it is especially sensitive to a fall in mean arterial pressure (MAP) [5,6]. Whether "
          "this mechanism produces measurable injury in routine practice has been tested mainly in cardiac, "
          "vascular and major abdominal surgery. In noncardiac surgery, the relationship between hypotension "
          "and myocardial injury has been reported as graded in some cohorts [7] and as absent or confined to "
          "severe and prolonged episodes in others [8]. A consensus statement consequently recommends avoiding "
          "MAP below 65 mmHg while acknowledging the weakness of the underlying evidence [6].")
para(doc, "Orthopaedic surgery is an informative setting in which to examine the question. Patients are often "
          "elderly and carry atherosclerotic risk, surgery involves substantial blood loss and, in arthroplasty, "
          "bone cement implantation and fat embolism, and hypotension is frequent under both neuraxial and "
          "general anaesthesia, particularly during long procedures in the prone or lateral position. At the same time the case mix is "
          "heterogeneous: elective arthroplasty in a fit patient and emergency hip fracture fixation in a frail "
          "one are both labelled orthopaedic. Studies of MINS in orthopaedic patients have mostly been single-centre "
          "and restricted to hip fracture, and the large prospective cohorts that include orthopaedic patients "
          "report incidence and prognosis rather than an exposure-response relation with intraoperative blood "
          "pressure [11,12].")
para(doc, "A second, less discussed problem affects almost every study of MINS. Troponin is not measured "
          "routinely after surgery; it is ordered when the clinician suspects cardiac injury. The decision to "
          "measure is therefore a common consequence of the exposure (a patient who became hypotensive attracts "
          "attention) and of the outcome's risk factors (a patient with known coronary disease is investigated "
          "more readily). Restricting analysis to patients with a troponin measurement, as every MINS study must, "
          "conditions on this decision. When the decision is driven by the exposure as well as by risk, the "
          "resulting selection can distort the exposure-outcome association in either direction, and the "
          "magnitude of this distortion has rarely been quantified [13].")
para(doc, "We therefore studied adults undergoing orthopaedic surgery in two independent perioperative "
          "databases. Our aims were, first, to quantify the association between the cumulative intraoperative "
          "burden of MAP below 65 mmHg and MINS, allowing for non-linearity; second, to test whether the "
          "association replicated when a model estimated in one health system was applied unchanged in another; "
          "third, to describe how the selection of patients for troponin measurement differs between the two "
          "databases, and what that implies for the interpretation of MINS research; and fourth, to test "
          "whether the pattern of findings generalised to a parallel cohort of major abdominal operations.")

# ======================= METHODS =======================
h1(doc, "Methods")
h2(doc, "Design and reporting")
para(doc, "We performed a retrospective cohort study with a pre-specified derivation and external validation "
          "design, and report it in accordance with the STROBE statement for observational studies [14]. "
          "The analysis plan, exposure definition, outcome definition, covariate set and modelling strategy "
          "were fixed before the validation database was opened. A parallel cohort of major abdominal "
          "operations, assembled within the derivation database after the orthopaedic analyses were complete, "
          "was used to test whether the pattern of findings generalised to a second surgical population; its "
          "analyses followed the same model structure and are reported separately. Because the study used "
          "de-identified data from two research databases, accessed through a third-party analysis platform "
          "under its terms of use, no additional ethical approval or informed consent was required; the "
          "governance of each database is described in its original publication [15,16].")

h2(doc, "Data sources")
para(doc, "INSPIRE is a perioperative research database from a single tertiary hospital in Seoul, covering "
          "130,960 operations with linked preoperative assessment, intraoperative vital signs, laboratory "
          "results, medication administration and postoperative outcomes; time is recorded in minutes relative "
          "to defined anchors such as skin incision and anaesthesia start [15]. MOVER (Medical Informatics "
          "Operating Room Vitals and Events Repository) is a perioperative database from the University of "
          "California, Irvine, containing, in the EPIC component available on the analysis platform, 65,728 operations in 39,685 patients from 2018 onwards, with "
          "electronic health record data including intraoperative flowsheet vital signs recorded at "
          "one-minute (device) or three-to-five-minute (nursing) intervals [16]. The two databases differ in "
          "coding systems (ICD-10-PCS and department for INSPIRE; institutional procedure codes for MOVER), in "
          "the algorithms used to summarise blood pressure, and in the way MINS is derived; these differences "
          "were documented field by field before analysis and are summarised in Additional file 1.")

h2(doc, "Study population")
para(doc, "The derivation cohort was drawn from INSPIRE. We included adults aged over 18 years undergoing "
          "surgery with the operating department recorded as orthopaedic surgery. Because procedure codes for "
          "arthroplasty are sparsely populated in this database (approximately 2,600 operations), department, "
          "not procedure code, was used to define the population, which keeps the cohort representative "
          "of orthopaedic practice at the expense of some heterogeneity. The validation cohort was drawn from "
          "MOVER using institutional procedure codes: 184 codes matching orthopaedic, arthroplasty, fracture "
          "fixation, spine, arthroscopy and soft-tissue orthopaedic procedures were selected by keyword search "
          "and manual review, with maxillofacial and cranial procedures excluded. Both extractions were "
          "restricted to operations performed under general anaesthesia, which applied to every operation in "
          "both orthopaedic cohorts.")
para(doc, "In both databases the analysable population for the primary outcome comprised patients in whom at "
          "least one postoperative troponin measurement was available within 72 h of surgery (the monitored "
          "population). Patients without an intraoperative MAP record, and therefore without a calculable "
          "exposure, were excluded (none in INSPIRE, four in MOVER). Body mass index was missing in 12 and 21 "
          "monitored patients respectively and was imputed to the median of the monitored population; the "
          "remaining covariates were complete except for ASA physical status (33 missing in INSPIRE) and "
          "baseline creatinine (one missing), and these patients were excluded, leaving 434 and 226 patients "
          "for analysis (Fig. 1).")

h2(doc, "Parallel abdominal cohort")
para(doc, "To test whether the findings generalise beyond orthopaedic surgery, we assembled a parallel cohort "
          "of major abdominal operations within the derivation database (INSPIRE), after the orthopaedic "
          "analyses were complete. We included adults aged over 18 years undergoing general-surgery "
          "operations under general anaesthesia with a therapeutic alimentary-tract procedure code "
          "(ICD-10-PCS root operations 0D and 0F), an operative duration of at least 120 min and a hospital "
          "stay of at least three days. Of 32,943 general-surgery operations, 17,772 had a therapeutic "
          "abdominal procedure code, 10,069 lasted at least 120 min and 10,048 met the length-of-stay "
          "criterion, of which 9,075 were elective and 973 emergency (Additional file 1, Table S6). "
          "Thirteen elective operations (three of them monitored) had no intraoperative MAP record and "
          "therefore no calculable burden; they were excluded from the abdominal models, as in the main "
          "analysis.")
para(doc, "The exposure, outcome definitions and monitoring-based analysis structure were identical to those "
          "of the main analysis, with three differences. First, because emergency status was used to define "
          "the strata of a sensitivity analysis and not as a covariate; the abdominal models instead "
          "adjusted for open (versus laparoscopic) surgical approach and operative duration, both strong "
          "correlates of hypotension burden in abdominal surgery. Second, baseline creatinine was taken from "
          "a separate seven-day preoperative window and, when missing (27% of monitored elective patients), imputed "
          "to the cohort median, with a complete-case analysis as sensitivity. Third, comorbidity was "
          "ascertained from ICD-10 diagnosis codes (E10\u2013E14 for diabetes, I10\u2013I15 for hypertension "
          "and I20\u2013I25 for coronary heart disease), which yielded lower prevalence than in the "
          "orthopaedic cohorts, reflecting incomplete coding. Because troponin elevations after emergency "
          "surgery have more non-ischaemic causes, the elective cohort was the main abdominal analysis; the "
          "973 emergency operations were analysed separately, and modification of the burden association by "
          "emergency status was tested by a likelihood ratio test comparing models with and without a "
          "burden-by-emergency interaction term.")

h2(doc, "Exposure")
para(doc, "The exposure was the cumulative intraoperative time with MAP below 65 mmHg, expressed as a "
          "percentage of anaesthesia duration, and analysed per 10 percentage points. In INSPIRE the platform "
          "computes this quantity by merging invasive and non-invasive MAP series and multiplying the number of "
          "records that cross the threshold by five minutes, the nominal sampling interval of the intraoperative "
          "vitals table; a patient with no records, or with records that never cross the threshold, is assigned "
          "zero. In MOVER the platform integrates the interval between consecutive measurements using their "
          "true timestamps, forward-filling the most recent value from either the arterial or the cuff series "
          "and capping each interval at five minutes, while restricting readings to 20\u2013300 mmHg; a patient "
          "with no intraoperative MAP record is left blank, and a patient whose records never cross the "
          "threshold is assigned zero. We verified these algorithms against the exported data: all INSPIRE "
          "values were exact multiples of five minutes, whereas only 48.2% of MOVER values were, and in both "
          "databases the exported burden equalled cumulative minutes divided by anaesthesia duration to four "
          "decimal places. The two algorithms are therefore not interchangeable, and the exposure distributions "
          "of the two cohorts are not directly comparable; all analyses are reported separately by database and "
          "no pooling was attempted.")

h2(doc, "Outcome")
para(doc, "The primary outcome was MINS, defined as a peak postoperative cardiac troponin I concentration "
          "above the 99th upper reference limit within 72 h of surgery, in the absence of a competing cause of "
          "troponin elevation. In INSPIRE the only myocardial marker available is troponin I, reported without "
          "assay attribution; we used a threshold of 0.026 ng/mL, the 99th upper reference limit of the Abbott "
          "high-sensitivity troponin I assay, which is the assay in routine use at the contributing centre "
          "[17]. In MOVER we used the database-derived MINS flag, which applies the same 99th upper reference "
          "limit to the peak postoperative high-sensitivity troponin I value. We confirmed the operating "
          "characteristics of that flag empirically: among patients with a high-sensitivity troponin I value, "
          "the highest peak in patients flagged as not having MINS was 25 ng/L and the lowest peak in flagged "
          "patients was 26 ng/L, with no overlap, and the corresponding cut-point for conventional troponin I "
          "lay between 0.03 and 0.04 ng/mL. Agreement between the platform flag and our own 0.026 ng/mL "
          "definition was 97.8%; because that definition was itself recovered from the flagged values, this "
          "agreement confirms the cut-point rather than the accuracy of the flag. MINS was the pre-specified "
          "primary outcome throughout; the acute kidney "
          "injury and in-hospital mortality analyses were pre-specified as supportive full-cohort outcomes, "
          "used to test the validity of the exposure measurement, and are not interpreted as confirmatory "
          "tests of effect. Secondary outcomes were MINS defined by higher thresholds (0.04 and "
          "0.10 ng/mL), MINS within a seven-day window, MINS or an ICD-coded myocardial infarction, and, analysed "
          "in the full cohorts rather than in monitored patients, postoperative acute kidney injury within seven "
          "days of surgery defined by the KDIGO creatinine criteria [18], and in-hospital all-cause mortality, defined by the hospital expiry flag "
          "in INSPIRE and the in-hospital mortality flag in MOVER. Neither database provides a date of death or linkage to "
          "post-discharge mortality, so 30-day mortality could not be ascertained.")

h2(doc, "Covariates")
para(doc, "Covariates were chosen a priori as common causes of hypotension and of myocardial injury: age, sex, "
          "body mass index, ASA physical status, baseline serum creatinine (the lowest value within seven days "
          "before surgery, or within 30 days when no seven-day value existed), emergency surgery, diabetes, "
          "hypertension and coronary heart disease. In MOVER, baseline creatinine values still missing after "
          "this look-back were back-calculated from age and sex with the MDRD study equation and entered both "
          "the covariate set and the KDIGO baseline; a sensitivity analysis excluding these imputed values is "
          "reported in Additional file 1, Table S7. Comorbidity "
          "was ascertained from diagnosis codes in INSPIRE and from the structured past-history table in MOVER; "
          "both are patient-level definitions that cannot distinguish pre-existing disease from disease "
          "documented during the index admission, and are used here only as markers of baseline risk. Emergency "
          "surgery is not recorded in MOVER and was set to zero for validation, a limitation we return to below.")

h2(doc, "Statistical analysis")
para(doc, "Continuous variables are summarised as median with interquartile range and compared with the "
          "Mann\u2013Whitney test; categorical variables as count with percentage and compared with the "
          "chi-square or Fisher exact test. The association between burden and MINS was estimated by logistic "
          "regression in three models: unadjusted; adjusted for age and sex; and adjusted for all covariates "
          "listed above. Burden was modelled per 10 percentage points, and additionally in four categories "
          "(0%, >0\u20135%, >5\u201310% and >10%) with the zero-burden group as reference and a test for trend "
          "across categories. Shape was examined with a restricted cubic spline with four degrees of freedom and "
          "knots placed at equally spaced quantiles between the 2nd and 98th percentiles of burden; the curve "
          "was centred so that the odds ratio equalled one at zero burden, and non-linearity was tested by a "
          "Wald test on the non-linear spline terms.")
para(doc, "Discrimination was assessed by the area under the receiver-operating-characteristic curve (AUC) with "
          "a 95% confidence interval from 2,000 bootstrap resamples, and by ten-fold cross-validation to "
          "estimate optimism. Calibration was assessed by the Hosmer\u2013Lemeshow test, the calibration slope "
          "and the calibration intercept on the logit scale. For external validation, the derivation "
          "coefficients were applied unchanged "
          "to MOVER to obtain predicted probabilities; we report the AUC, the observed-to-expected ratio, the "
          "calibration slope and the calibration intercept, and, as an upper bound on what the same covariates "
          "could achieve in that database, the AUC of a model re-estimated in MOVER. To summarise the "
          "secondary-outcome evidence across databases, the two adjusted log odds ratios were pooled by "
          "generic inverse-variance weighting with the DerSimonian\u2013Laird random-effects estimator, and "
          "differences between outcome-specific estimates were probed by Wald tests on the log-odds-ratio "
          "scale. The only pre-specified subgroup was age (<65 versus "
          "\u226565 years); sex, ASA physical status, coronary heart disease, diabetes and emergency surgery were "
          "added exploratorily. Subgroup models removed the stratifying variable from the adjustment set and "
          "effect modification was tested by a likelihood ratio test; P values for the nine interaction tests "
          "were corrected for multiple comparisons using a Bonferroni adjustment.")
para(doc, "Selection into troponin monitoring was quantified in the full cohorts. The probability of being "
          "monitored was modelled by logistic regression on the covariates of the main analysis plus anaesthesia "
          "duration, summarised as a c-statistic with a 95% confidence interval from 2,000 bootstrap resamples "
          "(body mass index imputed to the cohort median for this model only). To estimate what the monitored "
          "cohort would look like had it reproduced the full cohort, monitored patients were weighted by the "
          "stabilised inverse probability of monitoring (the overall monitoring probability divided by each "
          "patient's predicted probability), and the Model 2 association was re-estimated with these weights and "
          "robust sandwich standard errors; weight distributions are reported as the effective sample size and "
          "the maximum weight, and the analysis was repeated with weights truncated at their 99th percentile. "
          "Weighting adjusts only for the measured covariates, so it bounds rather than eliminates the "
          "contribution of selection [26]. Finally, E-values (the minimum association an unmeasured "
          "confounder would need with both exposure and outcome, conditional on the measured covariates, to "
          "explain away an observed association) were computed for the secondary full-cohort estimates "
          "and for the confidence limits of the MINS estimates, converting odds ratios to risk ratios with the "
          "observed event rate in the zero-burden group as the baseline risk.")
para(doc, "A complete-case analysis was used apart from the body mass index imputation described above. To "
          "allow for repeat surgeries within patients, all models were additionally fitted with standard "
          "errors clustered at the patient level and in first-operation-only subsets (Additional file 1, "
          "Table S3). Two further sensitivity analyses addressed the outcome definitions and adjustment sets: "
          "the acute kidney injury analysis was repeated in patients with a measured baseline creatinine, "
          "excluding values back-calculated from age and sex, and the models for acute kidney injury, "
          "in-hospital death and MINS were re-fitted with anaesthesia duration added to the adjustment set "
          "(Additional file 1, Table S7). With 155 "
          "events and ten parameters the derivation model had approximately 15 events per variable, which is "
          "adequate for estimation but limits precision; at 80% power and two-sided \u03b1 = 0.05 it could "
          "detect odds ratios of about 1.18 per 10% burden in the derivation cohort and 1.57 in the validation "
          "cohort, so small effects below those thresholds cannot be excluded; we therefore emphasise "
          "confidence intervals rather than P values. The mortality analyses contained 94 and 20 deaths and, on the same calculation, had "
          "almost identical resolution (about 1.2 and 1.6 per 10% burden respectively); smaller "
          "differences in mortality lie below the resolution of these data. Analyses used Python 3.13 (statsmodels 0.14, scikit-learn 1.5) and R 4.6.2 (ggplot2, "
          "sandwich); analysis code is publicly available at https://github.com/YongChen999/hypotension-burden-organ-injury.")

# ======================= RESULTS =======================
h1(doc, "Results")
h2(doc, "Cohorts")
para(doc, "INSPIRE contained 10,002 orthopaedic operations, of which 468 (4.7%) had at least one postoperative "
          "troponin measurement within 72 h; 434 remained after exclusions and 155 (35.7%) met the definition of "
          "MINS (Fig. 1). MOVER contained 6,940 orthopaedic operations, of which 230 (3.3%) were monitored; 226 "
          "remained after exclusions and 102 (45.1%) had MINS. For the secondary outcomes, the full cohorts "
          "contributed 8,306 patients with 317 episodes of acute kidney injury (3.8%) and 9,491 patients with 94 "
          "in-hospital deaths (1.0%) in INSPIRE, and 5,351 patients with 780 episodes of acute kidney injury "
          "(14.6%) and 6,199 patients with 20 in-hospital deaths (0.3%) in MOVER. These full-cohort denominators "
          "are smaller than the cohort totals because the models required a calculable burden and complete "
          "covariates, and the acute kidney injury analysis additionally required evaluable preoperative and "
          "postoperative creatinine values.")

para(doc, "Patients with MINS were similar to those without in age and sex in INSPIRE, but had higher ASA "
          "physical status (51.0% versus 34.1% at ASA \u22653), higher baseline creatinine, more frequent "
          "emergency surgery (24.5% versus 14.3%) and more postoperative acute kidney injury (21.4% versus 8.7%) "
          "(Table 1). In-hospital death was four times more frequent in patients with MINS (16 of 155, 10.3%, "
          "versus 7 of 279, 2.5%; P = 0.001). Burden was only slightly and non-significantly higher in patients with MINS (median 16.7% "
          "versus 13.6%, P = 0.29), and the distribution of patients across burden categories was similar in the "
          "two groups (P = 0.11). In MOVER the same pattern was present but stronger: patients with MINS were "
          "older (68.5 versus 61.5 years), had higher creatinine, a longer anaesthesia, a higher burden (5.2% "
          "versus 2.9%, P = 0.010) and more acute kidney injury (41.2% versus 23.4%), and the distribution across "
          "burden categories differed (P = 0.025). In-hospital death was also more frequent with MINS (4 of 102, "
          "3.9%, versus 2 of 124, 1.6%), although with six deaths this difference was not statistically "
          "significant. Fewer than 1% of MOVER patients had coded diabetes and fewer than 2% had coronary "
          "disease, reflecting the coding practice of that database rather than a genuinely healthier population.")

table(doc, os.path.join(TAB, "Table1_baseline.csv"),
      "Table 1. Characteristics of troponin-monitored patients, by MINS status",
      "Values are median (interquartile range) or n (%). The table describes the troponin-monitored analytic "
      "cohorts (434 of 468 monitored operations in INSPIRE and 226 of 230 in MOVER, after the exclusions of "
      "Fig. 1); the full monitored and unmonitored cohorts are compared in Table 2 and Additional file 1, "
      "Table S1, and comorbidity counts there are therefore larger than here. P values are from the Mann\u2013Whitney test for "
      "continuous variables and the chi-square or Fisher exact test for categorical variables. The final block "
      "gives the proportion of each MINS group falling in each burden category, with the P value from a "
      "chi-square test across the four categories. Emergency surgery is not recorded in MOVER. AKI, acute kidney "
      "injury; ASA, American Society of Anesthesiologists; MAP, mean arterial pressure; MINS, myocardial injury "
      "after noncardiac surgery.",
      widths=[3.9, 2.5, 2.5, 1.3, 2.5, 2.5, 1.3], fs=7.1, new_page=True)

h2(doc, "Selection for troponin monitoring")
para(doc, "Monitored patients differed markedly from unmonitored patients in both databases, and the differences "
          "ran in the same direction as the exposure (Table 2). In INSPIRE, monitored patients had more than "
          "twice the median burden of unmonitored patients (14.3% versus 5.6%, P < 0.001), were older (70 versus "
          "55 years), were more than twice as likely to have emergency surgery (23.5% versus 11.1%), had seven "
          "times the prevalence "
          "of coronary heart disease (25.4% versus 3.8%) and died in hospital far more often (6.4% versus 0.8%); "
          "in MOVER the gradient was shallower but present (burden 3.7% versus 2.7%, P = 0.002; in-hospital "
          "death 2.6% versus 0.3%). The full comparison, including emergency surgery and postoperative acute "
          "kidney injury "
          "(14.5% versus 3.4% and 31.7% versus 13.7% among patients with evaluable creatinine), is summarised in "
          "Table 2 and given in full in Additional file 1, Table S1.")
para(doc, "Monitoring was strongly predictable from measured covariates. The c-statistic for being monitored "
          "was 0.85 (95% CI 0.84\u20130.87) in INSPIRE and 0.71 (0.68\u20130.74) in MOVER (Table 2), that is, "
          "the patients who received a troponin were largely identifiable in advance from age, comorbidity and "
          "the intensity of care they were already receiving. Reweighting the monitored analytic cohorts to the "
          "covariate distribution of the full cohorts changed the estimates little: the fully adjusted odds "
          "ratio per 10% burden was 1.01 (0.83\u20131.23) in INSPIRE, against 1.02 unweighted, and 1.56 "
          "(0.98\u20132.49) in MOVER, against 1.33 (Additional file 1, Table S2). Weights were extreme in "
          "places (the effective sample sizes were 119 of 434 and 113 of 226, that is 27% and 50% of "
          "the original cohorts), so the weighted estimates are imprecise by construction and we do not "
          "interpret their direction. The informative result is that reweighting on all measured covariates "
          "left the derivation estimate unchanged, and any residual bias must come "
          "from determinants of monitoring that our covariates do not capture (Additional file 1, Fig. S2). The "
          "distribution of burden in monitored and unmonitored patients overlapped only partly, with monitored "
          "patients shifted towards higher burden in both databases (Additional file 1, Fig. S1).")

table(doc, os.path.join(TAB, "Table2_selection.csv"),
      "Table 2. Characteristics of monitored and unmonitored operations, and predictability of monitoring",
      "Values are median (interquartile range) or n (%). Monitoring denotes at least one postoperative troponin "
      "measurement within 72 h of surgery, decided at clinical discretion. P values are from the Mann\u2013Whitney "
      "test for continuous variables and Fisher exact test for categorical variables. Postoperative AKI is shown "
      "for the patients with evaluable baseline and postoperative creatinine (INSPIRE 462 monitored and 8,118 "
      "unmonitored; MOVER 230 and 5,222); patients without evaluable creatinine could not be classified. The last "
      "row is the c-statistic of a logistic model for being monitored fitted in the full cohorts on age, sex, body "
      "mass index, ASA physical status, baseline creatinine, emergency surgery (INSPIRE only), diabetes, "
      "hypertension, coronary heart disease and anaesthesia duration (n = 9,491 and 6,503 with complete data), "
      "with the 95% confidence interval from 2,000 bootstrap resamples. Additional baseline characteristics "
      "(body mass index, baseline creatinine, emergency surgery, cumulative minutes with MAP <65 mmHg, diabetes "
      "and hypertension) are given in Additional file 1, Table S1. AKI, acute kidney injury; ASA, American "
      "Society of Anesthesiologists; CI, confidence interval; MAP, mean arterial pressure.",
      widths=[3.9, 2.5, 2.5, 1.3, 2.5, 2.5, 1.3], fs=7.1, new_page=True)

h2(doc, "Primary association in the derivation cohort")
para(doc, "There was no evidence of an association between hypotension burden and MINS in INSPIRE. The "
          "unadjusted odds ratio was 1.08 per 10% increase in burden (95% CI 0.96\u20131.20; P = 0.20), which "
          "was unchanged after adjustment for age and sex (1.07, 0.96\u20131.20; P = 0.22) and attenuated to "
          "1.02 after full adjustment (0.91\u20131.15; P = 0.74) (Table 3). Modelling burden in categories gave "
          "odds ratios of 0.56 (0.24\u20131.33), 0.41 (0.17\u20130.99) and 0.79 (0.39\u20131.60) for "
          "0\u20135%, 5\u201310% and >10% relative to zero burden, with P for trend 0.78; the estimate for the "
          "5\u201310% category is the only one whose confidence interval excludes one, and it lies below one, "
          "which is not compatible with a monotonic injurious effect. The restricted cubic spline was flat across "
          "the whole observed range, with no departure from linearity (P for non-linearity = 0.89) and a "
          "confidence band that widened above 30% burden where data were sparse (Fig. S3).")

table(doc, os.path.join(TAB, "Table2_models.csv"),
      "Table 3. Association between intraoperative hypotension burden and MINS in the derivation and validation cohorts",
      "Odds ratios are per 10% increase in the percentage of anaesthesia duration with MAP <65 mmHg, unless "
      "stated otherwise. Model 1 adjusted for age and sex; Model 2 additionally adjusted for body mass index, "
      "ASA physical status, baseline creatinine, emergency surgery (INSPIRE only), diabetes, hypertension and "
      "coronary heart disease. CI, confidence interval; MINS, myocardial injury after noncardiac surgery; OR, "
      "odds ratio.",
      widths=[3.8, 3.0, 5.0, 2.8, 1.4], fs=7.4, new_page=True)

h2(doc, "External validation")
para(doc, "In MOVER the direction of the association was consistent with the hypothesis but the estimate was "
          "imprecise. The unadjusted odds ratio was 1.43 per 10% (1.06\u20131.93; P = 0.020), 1.38 after "
          "adjustment for age and sex (1.02\u20131.87; P = 0.038) and 1.33 after full adjustment "
          "(0.97\u20131.83; P = 0.077) (Table 3). The categorical model showed a graded pattern that the "
          "derivation cohort did not: relative to zero burden, the odds ratios were 2.21 (0.93\u20135.27), 3.10 "
          "(1.14\u20138.40) and 2.61 (1.00\u20136.78) for 0\u20135%, 5\u201310% and >10%, with P for trend "
          "0.059 (Fig. S4). The crude proportions behind those categories were 27%, 45%, 53% and 55%, so the "
          "slight attenuation of the adjusted estimate in the highest category reflects covariate adjustment "
          "rather than a fall in the observed rate. In the derivation cohort the corresponding proportions were "
          "41%, 28%, 26% and 39%, a non-monotonic pattern with no dose-response, and its "
          "zero-burden category contained only 41 patients. The magnitudes should be read with the small number "
          "of events in the reference category in mind: only 45 patients had zero burden, of whom 12 had MINS, "
          "so the category-specific estimates are unstable even by the standards of an exploratory analysis.")

figure(doc, "MINS_Fig1_flow.png", 16.0,
       "Fig. 1 Flow of participants. Left, derivation cohort drawn from INSPIRE; right, external validation "
       "cohort drawn from MOVER. The full cohort forms the trunk of the diagram and is followed for the "
       "secondary outcomes, which do not require troponin monitoring; the troponin-monitored subset (within "
       "whom MINS is ascertainable and the primary analysis is performed) hangs as a branch, with the "
       "number and reason for each exclusion. Monitoring refers to at least one postoperative troponin "
       "measurement within 72 h of surgery. INSPIRE, a perioperative research database from a single tertiary "
       "hospital in Seoul; MOVER, Medical Informatics Operating Room Vitals and Events Repository, University of "
       "California, Irvine; MINS, myocardial injury after noncardiac surgery; AKI, acute kidney injury.")

para(doc, "Unlike MINS, the secondary organ-injury outcomes showed a clearer gradient with hypotension burden. "
          "Each 10% increase in burden was associated with acute kidney injury (odds ratio 1.09, 95% CI 1.02\u20131.17, "
          "P = 0.014 in INSPIRE; 1.08, 0.98\u20131.20, P = 0.13 in MOVER) and with in-hospital death (1.18, "
          "1.05\u20131.32, P = 0.004; 1.65, 1.20\u20132.26, P = 0.002), estimates that are free of the monitoring "
          "selection that affects the primary analysis. Figure 2 shows the shape of these associations: the adjusted "
          "odds ratio for acute kidney injury rose at higher burden in both databases, with a dip at low burden "
          "in INSPIRE (P for non-linearity 0.13 and 0.05 respectively), and that for in-hospital death "
          "rose only at the upper tail of the distribution in INSPIRE (P for non-linearity < 0.001), whereas "
          "the corresponding curve for MINS was flat (Fig. S3).", after=6)

figure(doc, "MINS_Fig2_organ_rcs.png", 15.0,
       "Fig. 2 Dose-response associations between intraoperative hypotension burden and postoperative organ "
       "injury. Panels show the adjusted odds ratio from restricted cubic splines with four degrees of freedom, "
       "centred so that the odds ratio equals one at zero burden. (A) Acute kidney injury in both the derivation "
       "(INSPIRE) and validation (MOVER) cohorts. (B) In-hospital death in the derivation cohort; the MOVER death "
       "spline was omitted because only 20 deaths precluded a stable estimate. The model was adjusted for age, sex, "
       "body mass index, ASA physical status, baseline creatinine, emergency surgery (INSPIRE only), diabetes, "
       "hypertension and coronary heart disease. Curves are drawn over the observed burden range of each "
       "cohort (to 45% in INSPIRE and about 31% in MOVER). AKI, acute kidney injury; MAP, mean arterial pressure.")

h2(doc, "Parallel abdominal cohort")
para(doc, "The abdominal cohort contributed 9,075 elective operations, of which 1,074 (11.8%) were monitored "
          "and 328 met the MINS definition (30.5%); postoperative acute kidney injury occurred in 954 of "
          "9,075 (10.5%). Monitoring was therefore two and a half times more frequent than in the "
          "orthopaedic derivation cohort (4.7%) but still left almost nine in ten operations unmonitored. "
          "The pattern of associations replicated the orthopaedic findings in both directions. The crude "
          "MINS odds ratio was 1.10 per 10% burden (1.06\u20131.14, P < 0.001) and fell to 1.03 "
          "(0.99\u20131.07; P = 0.19) after adjustment, unchanged by further adjustment for baseline "
          "creatinine and comorbidity and in a complete-case analysis (1.02, 0.98\u20131.07); with 319 "
          "events this estimate excludes odds ratios above 1.07 per 10% burden, the narrowest MINS interval "
          "in this study (Additional file 1, Table S6). Acute kidney injury, analysed in the full elective "
          "cohort, behaved in the opposite way: the crude odds ratio of 1.41 (1.37\u20131.46) attenuated "
          "only to 1.22 (1.18\u20131.26, P < 0.001), the most precisely estimated organ-injury association "
          "in this study.")
para(doc, "The 973 emergency operations were analysed separately. Among 334 monitored emergency operations, "
          "195 met the MINS definition (58.4%); the emergency-specific estimate was 1.06 (0.99\u20131.13, "
          "P = 0.11), and emergency status did not modify the burden association for either outcome "
          "(P for interaction 0.49 for MINS and 0.53 for acute kidney injury). Pooling elective and "
          "emergency operations (1,311 of the 1,408 monitored operations with complete covariates, "
          "465 events) produced a marginally significant MINS estimate of 1.04 "
          "(1.00\u20131.08, P = 0.026); the emergency stratum carried nearly twice the median burden and a "
          "far higher event rate, so the pooled estimate reflects the composition of the pooled cohort "
          "rather than a steeper exposure\u2013outcome slope within either stratum. Removing operative "
          "duration from the adjustment set moved the pooled estimate to 1.07 (1.03\u20131.10), confirming "
          "that the crude association is largely explained by operative duration and case complexity. "
          "Because operative duration is itself partly downstream of the intraoperative course, adjusting "
          "for it may absorb some of the exposure effect as well as confounding; the duration-adjusted and "
          "duration-free estimates (1.04 and 1.07) therefore bracket the plausible range rather than "
          "compete (Additional file 1, Table S6).")

h2(doc, "Discrimination and calibration")
para(doc, "The fully adjusted model discriminated weakly in the derivation cohort, with an apparent AUC of 0.652 "
          "(0.598\u20130.707) and a cross-validated AUC of 0.599, indicating that the apparent performance was "
          "partly optimism (Table 4). Calibration was good in the derivation data (Hosmer\u2013Lemeshow "
          "P = 0.92; calibration slope 1.00). Applied unchanged to MOVER, the model achieved an AUC of 0.682 "
          "(95% CI 0.61\u20130.75), "
          "slightly better than in the derivation cohort, but underestimated risk overall (observed-to-expected "
          "ratio 1.22) and its predicted probabilities were too concentrated (calibration slope 1.81, 95% CI "
          "1.03\u20132.59, calibration intercept 0.81), with observed risk exceeding predicted risk in most "
          "deciles of predicted risk "
          "(Fig. 3). Re-estimating the same covariates in MOVER raised the AUC only to 0.711 (0.640\u20130.777), "
          "which indicates that the covariates themselves, and not the transfer of coefficients, are the "
          "limiting factor.")

table(doc, os.path.join(TAB, "Table3_validation.csv"),
      "Table 4. Discrimination and calibration in the derivation cohort and on external validation",
      "The 95% confidence intervals for the AUC were obtained from 2,000 bootstrap resamples. The calibration "
      "slope is the slope of a logistic regression of observed outcome on the logit of the predicted "
      "probability, so that a value of one indicates perfect calibration and values above one indicate that "
      "predictions are too concentrated; the calibration intercept is the intercept of the same regression, "
      "with zero indicating no systematic over- or under-prediction (a positive intercept means observed risk "
      "exceeds predicted risk). The last row re-estimates the model in the validation database and is "
      "an upper bound on the performance attainable with these covariates. AUC, area under the "
      "receiver-operating-characteristic curve; CI, confidence interval; O:E, observed-to-expected ratio.",
      widths=[4.5, 3.1, 1.5, 2.9, 1.5, 2.0], fs=7.2, new_page=True)

# MINS RCS spline (old Fig. 2) moved to supplementary Fig. S3

# MINS category-proportion (old Fig. 3) moved to supplementary Fig. S4

h2(doc, "Subgroups")
para(doc, "The only pre-specified subgroup was age, and it did not modify the derivation result in a biologically "
          "coherent way: the association differed by age (P for interaction 0.044), being positive below 65 years "
          "(odds ratio 1.27, 0.97\u20131.66) and null at or above 65 years (0.94, 0.82\u20131.09), a pattern "
          "opposite to the one a biological gradient would predict, and in MOVER there was no age interaction "
          "(P = 0.44). The exploratory subgroups (sex, ASA physical status, coronary heart disease, "
          "diabetes and emergency surgery) produced nominally significant interactions for sex and ASA "
          "physical status in MOVER, but of the nine interaction tests performed none survived Bonferroni "
          "correction (all adjusted P \u2265 0.09; Additional file 1, Table S4). We therefore interpret all "
          "subgroup heterogeneity, including the age pattern, as chance.")

h2(doc, "Sensitivity analyses")
para(doc, "In the derivation cohort the null result was robust: raising the MINS threshold to 0.04 or "
          "0.10 ng/mL, extending the window to seven days, or adding ICD-coded myocardial infarction to the "
          "outcome all left the odds ratio between 1.01 and 1.13 with confidence intervals including one "
          "(Additional file 1, Table S2 and Fig. S2). In MOVER the estimate was more sensitive to the definition: it fell to "
          "1.17 (0.86\u20131.61) at a threshold of 0.04 ng/mL and to 0.97 (0.66\u20131.44) at 0.10 ng/mL, and "
          "to 1.27 (0.93\u20131.75) when ICD-coded myocardial infarction was added to the outcome, so "
          "the borderline association in that database is carried mainly by small troponin elevations. A "
          "seven-day window could not be examined in MOVER because the platform MINS flag does not expose the "
          "window over which the peak is taken. In contrast, the full-cohort secondary outcomes behaved "
          "consistently: each 10% increase in burden was associated with postoperative acute kidney injury in "
          "both databases (odds ratio 1.09, 1.02\u20131.17, P = 0.014 in INSPIRE; 1.08, 0.98\u20131.20, "
          "P = 0.13 in MOVER), and pooling the two databases gave 1.09 (1.03\u20131.15) with no heterogeneity "
          "(I\u00b2 = 0%), the only estimate of this study to replicate formally across databases. "
          "In-hospital death was also associated with burden in both (1.18, 1.05\u20131.32, "
          "P = 0.004 in INSPIRE; 1.65, 1.20\u20132.26, P = 0.002 in MOVER; see Fig. 2). The corresponding "
          "E-values were 1.39 and 1.35 for acute kidney injury and 1.64 and 2.68 for in-hospital death "
          "(derivation and validation respectively), so only moderately strong unmeasured confounding would "
          "explain these associations away. The two mortality estimates were not "
          "equally robust, however. In MOVER the association strengthened when the top 1% of burden values was excluded "
          "(1.91, 1.23\u20132.97, P = 0.004), and mortality rose across the four categories from 0.2% to 0.9%. "
          "In INSPIRE it did not survive the same exclusion (1.07, 0.92\u20131.24, P = 0.37) and the "
          "category-specific rates were flat between 0.5% and 1.5%, so the continuous estimate there rests on a "
          "small number of patients with extreme exposure. Because death is ascertained regardless of troponin monitoring, either "
          "estimate is free of the monitoring selection that affects the primary analysis; the MOVER estimate "
          "nevertheless rests on 20 deaths. Two further analyses probed the robustness of these estimates. "
          "Restricting the kidney analysis to patients with a measured baseline creatinine changed the estimates "
          "little (1.09, 1.02\u20131.17 in INSPIRE, identical to the primary analysis because no imputed "
          "values entered it; 1.09 versus 1.08, 0.96\u20131.23 in MOVER, where 2,269 back-calculated "
          "baselines were removed), and adding anaesthesia duration to the adjustment set moved every estimate "
          "by 0.01 or less, including the two primary MINS estimates (Additional file 1, Table S7). Finally, because 6.0% and 7.5% of the operations in the two "
          "monitored cohorts were repeat surgeries in the same patient, all models were re-fitted with "
          "standard errors clustered at the patient level and in first-operation-only subsets; all estimates retained "
          "their direction, and their confidence intervals overlapped (Additional file 1, Table S3).")

para(doc, "As a further check, a negative-control analysis tested whether the exposure was spuriously associated with "
          "outcomes it cannot causally affect. Pre-existing comorbidities (heart failure, chronic kidney "
          "disease and coronary heart disease, all defined before surgery) were used as outcomes in logistic "
          "models identical to the main analysis, fitted in the full orthopaedic cohorts because they are "
          "ascertained regardless of troponin monitoring. Heart failure, the clearest negative control, showed no "
          "association with hypotension burden in either database (adjusted odds ratio per 10% burden 1.09, "
          "0.97\u20131.21, P = 0.14 in INSPIRE; 1.02, 0.53\u20131.93, P = 0.96 in MOVER). In the independent "
          "validation cohort none of the three comorbidities showed a positive association (adjusted odds ratios "
          "0.37\u20131.02, all confidence intervals including one). In the derivation cohort, chronic kidney disease "
          "(1.18, 1.08\u20131.29) and coronary heart disease (1.13, 1.06\u20131.20) showed small but statistically "
          "significant positive associations, indicating residual confounding by overall illness severity "
          "that the measured covariates did not fully capture. The magnitude of the chronic kidney disease "
          "association (1.18) was in fact comparable to, and slightly larger than, the adjusted acute kidney "
          "injury association in the same database (1.09), so the derivation-cohort kidney estimate must be "
          "read as an upper bound that residual severity confounding could in principle account for in full. "
          "The validation cohort provides the cleaner test: chronic kidney disease was null in MOVER "
          "(0.46, 0.20\u20131.03) while the acute kidney injury estimate there was 1.08, a specificity pattern "
          "that non-specific severity confounding alone would not produce. Coronary heart disease is the least "
          "clean of the three "
          "controls, because it also shapes the monitoring decision (present in 25.4% of monitored versus 3.8% "
          "of unmonitored patients in INSPIRE), so its association partly reflects the selection process itself. "
          "The negative-control results (null for the cleanest control in both databases and for all three "
          "controls in the validation cohort, positive for two diagnosis-code-based controls in the derivation "
          "cohort) support the specificity of the observed associations in the validation cohort, and "
          "caution against a causal reading of the derivation-cohort estimates "
          "(Additional file 1, Table S5).")

figure(doc, "MINS_Fig3_validation.png", 16.0,
       "Fig. 3 External validation of the frozen model in MOVER. (A) Receiver-operating-characteristic curve "
       "obtained by applying the derivation coefficients without re-estimation; the dashed diagonal is the line "
       "of no discrimination, and the area under the curve is 0.682 (95% CI 0.61\u20130.75). (B) Calibration plot: patients were ranked "
       "by predicted risk and divided into ten equal-sized groups; the mean predicted probability is plotted "
       "against the observed proportion with MINS in each group, and the dashed diagonal represents perfect "
       "calibration. The observed-to-expected ratio was 1.22 and the calibration slope 1.81, indicating that "
       "predicted risks were too concentrated and systematically too low. MINS, myocardial injury after "
       "noncardiac surgery.")

# ======================= DISCUSSION =======================
h1(doc, "Discussion")
para(doc, "In two large perioperative databases, the cumulative intraoperative burden of MAP below 65 mmHg was "
          "not associated with myocardial injury after orthopaedic surgery in the derivation cohort, and was "
          "associated only at the margin of statistical significance on external validation. The derivation "
          "estimate was precise enough to exclude a strong effect: the upper confidence limit of 1.15 per 10% "
          "burden corresponds to an odds ratio of about 1.75 for a 40% burden, which is at the extreme of the "
          "observed distribution. Yet the same exposure, measured the same way in the same patients, was "
          "associated with postoperative acute kidney injury in both databases and with in-hospital death "
          "robustly in the validation cohort and at extreme levels of exposure only in the derivation cohort: "
          "outcomes ascertained without troponin monitoring and therefore immune to the monitoring selection. That contrast, "
          "rather than either individual estimate, is the central pattern of this study, and it argues that the null "
          "result for MINS is specific to the outcome rather than a failure of exposure measurement. The "
          "contrast should, however, be read as a pattern of point estimates rather than a formally "
          "demonstrated difference: Wald tests comparing the log odds ratio for MINS with those for acute "
          "kidney injury and in-hospital death were themselves non-significant in both databases (all P \u2265 "
          "0.08), so these data cannot formally distinguish organ-specific vulnerability from estimates "
          "perturbed by monitoring selection and small event numbers. What does replicate formally is the "
          "association with acute kidney injury: pooled across databases the odds ratio was 1.09 "
          "(1.03\u20131.15) with no heterogeneity (I\u00b2 = 0%), the only estimate of this study that was "
          "confirmed across databases. A negative-control analysis using pre-existing comorbidities as outcomes that hypotension cannot causally influence lent further support to this interpretation: the burden was largely unassociated with these preoperative conditions, including in the independent validation cohort (Additional file 1, Table S5). A parallel cohort of elective major abdominal operations within the derivation database reproduced both halves of the contrast: a crude MINS association of 1.10 that adjustment abolished (1.03, 0.99\u20131.07, the narrowest MINS interval of this study), alongside a stable adjusted association with acute kidney injury (1.22, 1.18\u20131.26) that was not modified by emergency status (P for interaction 0.53). Monitoring was two to four times more frequent in this cohort than in the orthopaedic cohorts (11.8% versus 4.7% and 3.3%), a different monitoring culture that tempers the extrapolation of its null estimate to the orthopaedic setting.")

h2(doc, "Why the two databases disagree")
para(doc, "Three explanations for the discrepancy between derivation and validation deserve consideration: "
          "selection, case mix and outcome ascertainment. Selection is the most tractable, and the present "
          "analysis now quantifies it. In both databases the "
          "primary analysis was restricted to patients whose clinician ordered a troponin, and that decision was "
          "itself related to hypotension: monitored patients had 2.6-fold (INSPIRE) and 1.4-fold (MOVER) the burden "
          "of unmonitored patients, "
          "alongside far more coronary disease and emergency surgery (Table 2). A variable that is a common "
          "effect of the exposure and of the outcome's risk factors is a collider, and conditioning on it induces "
          "an association between the exposure and unmeasured determinants of risk [13,24,25]. The direction of the "
          "resulting bias is not fixed; it depends on which unmeasured determinants drive monitoring. If "
          "clinicians order troponin when a patient looks unwell in ways not captured by our covariates, then "
          "within the monitored group high-burden patients are disproportionately those whose hypotension had an "
          "identifiable non-cardiac explanation, and the association is attenuated. If instead monitoring tracks "
          "cardiac risk more faithfully than our covariates do, the association is exaggerated. The two databases "
          "sit at different points on this spectrum: monitoring in INSPIRE was strongly exposure-selective "
          "(23.5% emergency surgery among monitored versus 11.1% among unmonitored, coronary disease 25.4% versus "
          "3.8%), whereas in MOVER the gradient, although present, was shallower and monitoring tracked the intensity "
          "of postoperative care more than it tracked the exposure itself. Measured covariates predicted the "
          "monitoring decision well (c-statistic 0.85 and 0.71), so we could ask what the monitored cohorts would "
          "have looked like had they reproduced the full cohorts: the weighted estimate was close to the "
          "unweighted one in INSPIRE (1.01 versus 1.02), and in MOVER it moved away from the null (1.56 versus "
          "1.33), though with an effective sample size of 113 of 226 that movement is itself imprecise and we "
          "place no weight on its direction. The reliable content of this analysis is the INSPIRE result ("
          "reweighting on all measured covariates does not move the estimate), and any residual "
          "collider bias must operate through determinants of monitoring that are not in our models, which "
          "is precisely the component that inverse probability weighting cannot repair [26]. The fragility of "
          "the validation estimate to unmeasured confounding can be put on a scale: its E-value is 1.7, and the "
          "upper confidence limit would be explained away by a confounder associated with an E-value of 2.4, "
          "whereas the robust secondary associations would need stronger confounding (E-value 2.7 for the MOVER "
          "mortality estimate). The validation signal for MINS is thus both imprecise and modestly fragile, while "
          "the contrast with the outcomes ascertained without troponin monitoring, which no monitoring decision can "
          "select on, survives.")
para(doc, "Case mix is a second candidate. The INSPIRE cohort is dominated by elective arthroplasty and spine "
          "surgery in patients whose median age is 70 years and whose median burden is approximately 14%, that is, by "
          "patients in whom hypotension is frequent, brief and largely anaesthetic-related. The MOVER cohort is "
          "more heterogeneous, with a much longer median anaesthesia (5.2 versus 3.4 h in patients without MINS) "
          "and a higher prevalence of acute kidney injury (14.6% versus 3.8% in the full cohorts), suggesting a "
          "sicker and more procedurally complex population in which sustained hypotension may be a marker of "
          "intraoperative events rather than a cause of injury in itself. A marker that is a cause in one "
          "population and a consequence in another will not replicate, and our data cannot distinguish these "
          "possibilities because neither database records intraoperative vasopressor use, blood loss or the "
          "occurrence of major intraoperative events.")
para(doc, "Outcome ascertainment is the third. The derivation cohort relied on a single troponin I assay without "
          "attribution, and the resulting MINS prevalence of 35.7% among monitored patients is high, consistent "
          "with a population selected for suspicion of cardiac injury. The validation cohort used a database flag "
          "built on high-sensitivity troponin with a threshold we could verify empirically, and its MINS "
          "prevalence was higher still (45.1%). Neither database required a rise-and-fall pattern or a "
          "coronary ischaemic mechanism, so both definitions include troponin elevations from pulmonary embolism, "
          "sepsis, arrhythmia and renal failure, which dilute any hypotensive signal. This is a general problem "
          "in MINS research, and it is why the fourth universal definition insists on evidence of ischaemia, "
          "not troponin alone [19].")

h2(doc, "Comparison with previous work")
para(doc, "Studies that modelled hypotension as a continuous exposure have generally found modest associations "
          "with myocardial injury in noncardiac surgery, with odds ratios in the range of 1.1 to 1.4 per "
          "10 mmHg decrement or per 10 minutes below threshold, and with evidence of a threshold near 65 mmHg "
          "[7\u201310]. Our estimate in MOVER is compatible with that literature; our estimate in INSPIRE is not. The "
          "difference between our two cohorts is larger than the difference between either of them and the "
          "published literature, which suggests that heterogeneity between databases, rather than a single true "
          "effect, dominates this field. This has a practical consequence: a single-centre estimate of the "
          "hypotension-MINS association should not be treated as transportable, and multicentre validation should "
          "be the default before an exposure threshold is embedded in a care pathway.")
para(doc, "The modest discrimination we observed is consistent with the wider literature on hypotension as a "
          "predictor. Blood pressure is one input among many, and models that predict MINS from routine "
          "preoperative variables typically achieve areas under the curve between 0.65 and 0.75 [20]. Our "
          "cross-validated AUC of 0.599 in the derivation cohort, rising to 0.711 when the model was re-estimated "
          "in the validation cohort, indicates that the covariate set, not the coefficients, limits "
          "performance. The calibration results reinforce the point: a model that under-predicts risk by 22% in a "
          "different health system cannot be used for triage without recalibration, a finding that mirrors the "
          "broader literature on the fragility of calibration across settings [21].")

h2(doc, "Implications")
para(doc, "For clinicians, the results do not license indifference to intraoperative blood pressure. The "
          "associations with acute kidney injury and with in-hospital death in the same patients were consistent "
          "across both databases, and randomised trials of pressure-support strategies have shown that hypotension "
          "is modifiable [22,23]. "
          "What the results do argue against is the use of hypotension burden as a trigger for troponin "
          "screening. In our data a patient's hypotension history would have identified MINS poorly (AUC 0.65), "
          "whereas conventional risk factors, particularly age, ASA physical status and baseline creatinine, "
          "carried whatever discrimination was available. Troponin should be measured on the basis of "
          "preoperative risk and clinical suspicion, not on the basis of a low intraoperative pressure alone.")
para(doc, "For researchers, the study has a methodological implication that extends beyond orthopaedic surgery. "
          "Every MINS study is a study of monitored patients, and monitoring is a decision that responds to the "
          "exposure. Reporting the monitored and unmonitored populations side by side, as in Table 2, costs "
          "little and makes the selection visible; ignoring it invites the reader to interpret a selected "
          "association as a population one. The abdominal replication shows that this problem is structural "
          "rather than procedure-specific: even in major abdominal surgery, where ischaemic complications are "
          "more expected and troponin was two and a half times more likely to be measured, monitoring still "
          "covered only 11.8% of operations. Selection into troponin monitoring is therefore a general "
          "feature of MINS research, and the crude abdominal association, abolished by adjustment for "
          "operative duration and case complexity, is a reminder that in sicker surgical populations an "
          "unadjusted exposure\u2013outcome gradient largely reflects case mix. Where the data allow, analyses that model the monitoring decision "
          "explicitly (as an inverse-probability weighting problem, in the language of target trial "
          "emulation, or by design through a pre-specified troponin sampling frame) and that use an "
          "outcome ascertainable without troponin monitoring, such as acute kidney injury or "
          "in-hospital death as a positive control, are likely to be more informative than another single-cohort "
          "estimate of the same association [27].")

h2(doc, "Strengths and limitations")
para(doc, "The study has several strengths. The exposure and outcome definitions were fixed before the "
          "validation database was analysed; the exposure algorithm of each platform was verified against the "
          "exported data, not assumed; the shape of the association was examined without imposing "
          "linearity; discrimination and calibration were reported together, with a re-estimated model as an "
          "upper bound; and the monitored and unmonitored populations were compared explicitly, which is unusual "
          "in this literature.")
para(doc, "The limitations are equally clear. First, troponin was measured at clinical discretion in 4.7% and "
          "3.3% of operations, so the analysed cohorts are selected and the results do not estimate the "
          "association in all orthopaedic patients; this is the central limitation and we have tried to make it "
          "visible rather than to adjust it away. Second, the two databases summarise blood pressure with "
          "different algorithms, one of which (INSPIRE) multiplies the number of threshold-crossing records by a "
          "nominal five-minute interval, so that the exposure is sensitive to sampling density and assigns zero "
          "to patients with no record. Third, the derivation cohort used a single troponin I assay without "
          "attribution, and we assumed the Abbott 99th upper reference limit; a different assay would shift the "
          "threshold and the event count. Fourth, the window over which the MOVER MINS flag takes its peak is not "
          "documented, so the seven-day sensitivity analysis could not be performed there. Fifth, MOVER does not "
          "record emergency surgery and has almost no coded diabetes, so the validation model was not identical "
          "to the derivation model. Sixth, neither database records intraoperative vasopressor use, blood "
          "transfusion, depth of anaesthesia or the occurrence of intraoperative events, all of which may "
          "confound or mediate the association. Seventh, the orthopaedic populations are defined differently "
          "(department versus procedure codes) and are heterogeneous, so the two cohorts are not samples of the "
          "same clinical population. Eighth, subgroup analyses other than age were exploratory; their interaction "
          "tests did not survive correction for multiple comparisons, but correction can exclude chance without "
          "excluding genuine effect modification. Ninth, the inverse-probability-of-monitoring weighting analysis "
          "adjusts only for measured covariates and produced very low effective sample sizes, so it bounds rather "
          "than removes selection; and the high c-statistic for monitoring (0.85 in INSPIRE, 0.71 in MOVER) "
          "is partly driven by variables that are themselves downstream of the intraoperative course (anaesthesia "
          "duration and emergency surgery, both consequences of rather than independent of hypotension), so part "
          "of the monitoring predictability reflects severity that we could not adjust for, and the fact that "
          "weighting left the estimates unchanged therefore shows only that measured selection does not explain the "
          "result, not that no selection bias remains. Tenth, a "
          "minority of operations were repeat surgeries in the same patient (up to 17% in the full cohorts), "
          "so the observations are not fully independent; standard errors clustered at the patient level and "
          "analyses restricted to each patient's first operation left every estimate essentially unchanged "
          "(Additional file 1, Table S3). A further limitation concerns the parallel abdominal cohort: it is a "
          "single-database replication, not an external validation, was assembled after the "
          "orthopaedic analyses were complete, is restricted to elective operations in its main analysis "
          "(emergency operations were analysed separately and showed no interaction), adjusts for open "
          "surgical approach and operative duration rather than emergency surgery, and ascertains "
          "comorbidity from ICD-10 diagnosis codes whose low prevalence indicates incomplete coding. "
          "Finally, "
          "only in-hospital outcomes were available: neither database provides a date of death or "
          "linkage to post-discharge mortality, so 30-day mortality could not be analysed, the in-hospital mortality analyses miss "
          "deaths after discharge and were powered only for moderate effects, and MINS is known to carry risk "
          "beyond discharge that we could not capture.")

h2(doc, "Conclusions")
para(doc, "In orthopaedic surgery, the cumulative intraoperative burden of MAP below 65 mmHg was not associated "
          "with myocardial injury after noncardiac surgery in a large single-centre derivation cohort, and the "
          "association was at most modest and imprecisely estimated on external validation. Discrimination was "
          "poor in both databases, and calibration did not transport. Because troponin measurement is triggered "
          "by clinical suspicion that is itself related to hypotension, MINS studies restricted to monitored "
          "patients are vulnerable to selection bias, and the consistent association between the same exposure "
          "and postoperative acute kidney injury suggests that the null finding is "
          "specific to the cardiac outcome rather than an artefact of measurement. A parallel cohort of "
          "elective major abdominal operations reproduced the same dissociation (a crude MINS "
          "association abolished by adjustment alongside a stable association with acute kidney injury) "
          "so neither the null cardiac finding nor the monitoring problem is specific to orthopaedic "
          "surgery. These findings argue for "
          "preoperative risk, not "
          "intraoperative pressure as the trigger for troponin screening, and for routine reporting of the "
          "monitored and unmonitored populations in future studies of MINS.")

# ======================= DECLARATIONS =======================
h1(doc, "Declarations")
h2(doc, "Ethics approval and consent to participate")
para(doc, "The study used de-identified data from two research databases, accessed through a third-party "
          "analysis platform under its terms of use. Both databases are released under data use agreements that "
          "require completion of human subjects research training and institutional credentialing. No additional "
          "ethics approval or informed consent was required for this secondary analysis, in accordance with the "
          "governance statements of the source databases [15,16].")
h2(doc, "Consent for publication")
para(doc, "Not applicable.")
h2(doc, "Availability of data and materials")
para(doc, "The data that support the findings of this study are not publicly available: INSPIRE (Seoul "
          "National University Hospital) and MOVER (University of California, Irvine) are restricted-access "
          "research databases, released only under a data use agreement with the respective provider. The "
          "analysis code is publicly available at "
          "https://github.com/YongChen999/hypotension-burden-organ-injury and archived at Zenodo "
          "(https://doi.org/10.5281/zenodo.2420362); the aggregate analytic outputs (tables, figure "
          "coordinates and model coefficients) are archived at Zenodo "
          "(https://doi.org/10.5281/zenodo.24211311).")
h2(doc, "Competing interests")
para(doc, "The authors declare that they have no competing interests.")
h2(doc, "Funding")
para(doc, "The authors received no specific grant from any funding agency in the public, commercial or not-for-profit sectors.")
h2(doc, "Authors' contributions")
para(doc, "Yong Chen and Qixia He contributed equally to this work. Yong Chen and Yan Lu conceived and "
          "designed the study. Yong Chen, Qixia He, Yanwen Zhu, Hongling Zhuang, Jing Zhang and Mingzhi Luo "
          "contributed to data extraction, variable definition, data management and statistical analysis. "
          "Yong Chen and Qixia He drafted the manuscript. Yanwen Zhu, Hongling Zhuang, Jing Zhang and "
          "Mingzhi Luo interpreted results and critically revised the manuscript. Yan Lu supervised the "
          "study, revised the manuscript for important intellectual content and approved the final version "
          "for submission. All authors reviewed and approved the submitted version.")
h2(doc, "Acknowledgements")
para(doc, "None.")
h2(doc, "Additional files")
para(doc, "Additional file 1. Supplementary tables and figures (Table S1, additional baseline characteristics of monitored and unmonitored patients; Table S2, sensitivity analyses including inverse-probability-of-monitoring weighting; "
          "Table S3, within-patient clustering of repeated operations; Table S4, subgroup analyses; Table S5, negative-control analyses using pre-existing comorbidities as outcomes; Table S6, parallel abdominal cohort: assembly, association estimates and emergency interaction; Table S7, complete-case and duration-adjusted analyses of the secondary outcomes; Fig. S1, "
          "distribution of hypotension burden in monitored and "
          "unmonitored patients; Fig. S2, forest plot of the sensitivity analyses; Fig. S3, restricted cubic "
          "spline of the burden\u2013MINS association; Fig. S4, proportion of patients with MINS by burden "
          "category; Appendices 1\u20133, exposure algorithms, definition and ascertainment of MINS, and the "
          "variable extraction specification for both databases).")

# ======================= REFERENCES =======================
h1(doc, "References")
refs = [
    "Botto F, Alonso-Coello P, Chan MT, Villar JC, Xavier D, Srinathan S, et al. Myocardial injury after "
    "noncardiac surgery: a large, international, prospective cohort study establishing diagnostic criteria, "
    "characteristics, predictors, and 30-day outcomes. Anesthesiology. 2014;120(3):564\u201378.",
    "Devereaux PJ, Biccard BM, Sigamani A, Xavier D, Chan MTV, Srinathan SK, et al. Association of postoperative "
    "high-sensitivity troponin levels with myocardial injury and 30-day mortality among patients undergoing "
    "noncardiac surgery. JAMA. 2017;317(16):1642\u201351.",
    "Devereaux PJ, Xavier D, Jolly SS, Guyatt G, Wojtowicz A, et al. Characteristics and "
    "short-term prognosis of perioperative myocardial infarction in patients undergoing noncardiac surgery: a "
    "cohort study. Ann Intern Med. 2011;154(8):523\u20138.",
    "Devereaux PJ, Duceppe E, Guyatt G, Tandon V, Rodseth R, Biccard BM, et al. Dabigatran in patients with "
    "myocardial injury after non-cardiac surgery (MANAGE): an international, randomised, placebo-controlled "
    "trial. Lancet. 2018;391(10137):2325\u201334.",
    "Walsh M, Devereaux PJ, Garg AX, Kurz A, Turan A, Rodseth RN, et al. Relationship between intraoperative "
    "mean arterial pressure and clinical outcomes after noncardiac surgery: toward an empirical definition of "
    "hypotension. Anesthesiology. 2013;119(3):507\u201315.",
    "Sessler DI, Bloomstone JA, Aronson S, Berry C, Gan TJ, Kellum JA, et al. Perioperative Quality Initiative "
    "consensus statement on intraoperative blood pressure, risk and outcomes for elective surgery. Br J Anaesth. "
    "2019;122(5):563\u201374.",
    "Salmasi V, Maheshwari K, Yang D, Mascha EJ, Singh A, Sessler DI, et al. Relationship between intraoperative "
    "hypotension, defined by either reduction from baseline or absolute thresholds, and acute kidney and "
    "myocardial injury after noncardiac surgery. Anesthesiology. 2017;126(1):47\u201365.",
    "Wesselink EM, Kappen TH, Torn HM, Slooter AJC, van Klei WA. Intraoperative hypotension and the risk of "
    "postoperative adverse outcomes: a systematic review. Br J Anaesth. 2018;121(4):706\u201321.",
    "Sessler DI, Meyhoff CS, Zimmerman NM, Mao G, Leslie K, V\u00e1squez SM, et al. Period-dependent associations "
    "between hypotension during and for four days after noncardiac surgery and a composite of myocardial "
    "infarction and death. Anesthesiology. 2018;128(2):317\u201327.",
    "Maheshwari K, Ahuja S, Khanna AK, Mao G, Perez-Protto S, Farag E, et al. Association between perioperative "
    "hypotension and acute kidney injury or myocardial injury after non-cardiac surgery. Anesthesiology. "
    "2021;135(6):1017\u201329.",
    "Puelacher C, Lurati Buse G, Seeberger D, Sazgary L, Marbot S, Lampart A, et al. Perioperative myocardial "
    "injury after noncardiac surgery: incidence, mortality, and characterization. Circulation. "
    "2018;137(12):1221\u201332.",
    "van Waes JA, Nathoe HM, de Graaff JC, Kemperman H, de Borst GJ, Peelen LM, et al. Myocardial injury after "
    "noncardiac surgery and its association with short-term mortality. Circulation. 2013;127(23):2264\u201371.",
    "Hern\u00e1n MA, Hern\u00e1ndez-D\u00edaz S, Robins JM. A structural approach to selection bias. "
    "Epidemiology. 2004;15(5):615\u201325.",
    "von Elm E, Altman DG, Egger M, Pocock SJ, G\u00f8tzsche PC, Vandenbroucke JP. The Strengthening the "
    "Reporting of Observational Studies in Epidemiology (STROBE) statement: guidelines for reporting "
    "observational studies. Ann Intern Med. 2007;147(8):573\u20137.",
    "Lim L, Lee H, Jung CW, Sim D, Borrat X, Pollard TJ, et al. INSPIRE, a publicly available research dataset "
    "for perioperative medicine. Sci Data. 2024;11(1):655.",
    "Samad M, Angel M, Rinehart J, Kanomata Y, Baldi P, Cannesson M. Medical Informatics Operating Room Vitals "
    "and Events Repository (MOVER): a public-access operating room database. JAMIA Open. 2023;6(4):ooad084.",
    "Apple FS, Sandoval Y, Jaffe AS, Ordonez-Llanos J. Cardiac troponin assays: guide to understanding "
    "analytical characteristics and their impact on clinical care. Clin Chem. 2017;63(1):73\u201381.",
    "Kidney Disease: Improving Global Outcomes (KDIGO) Acute Kidney Injury Work Group. KDIGO clinical practice "
    "guideline for acute kidney injury. Kidney Int Suppl. 2012;2:1\u2013138.",
    "Thygesen K, Alpert JS, Jaffe AS, Chaitman BR, Bax JJ, Morrow DA, et al. Fourth universal definition of "
    "myocardial infarction (2018). Circulation. 2018;138(20):e618\u201351.",
    "Duceppe E, Parlow J, MacDonald P, Lyons K, McMullen M, Srinathan S, et al. Canadian Cardiovascular Society "
    "guidelines on perioperative cardiac risk assessment and management for patients who undergo noncardiac "
    "surgery. Can J Cardiol. 2017;33(1):17\u201332.",
    "Van Calster B, McLernon DJ, van Smeden M, Wynants L, Steyerberg EW. Calibration: the Achilles heel of "
    "predictive analytics. BMC Med. 2019;17(1):230.",
    "Wijnberge M, Geerts BF, Hol L, Lemmers N, Mulder MP, Berge P, et al. Effect of a machine learning-derived "
    "early warning system for intraoperative hypotension vs standard care on depth and duration of "
    "intraoperative hypotension during elective noncardiac surgery: the HYPE randomized clinical trial. JAMA. "
    "2020;323(11):1052\u201360.",
    "Futier E, Lefrant JY, Guinot PG, Godet T, Lorne E, Cuvillon P, et al. Effect of individualized vs standard "
    "blood pressure management strategies on postoperative organ dysfunction among high-risk patients undergoing "
    "major surgery: a randomized clinical trial. JAMA. 2017;318(14):1346\u201357.",
    "Lu H, Cole SR, Howe CJ, Westreich D. Toward a clearer definition of selection bias when estimating causal "
    "effects. Epidemiology. 2022;33(5):699\u2013706.",
    "Hern\u00e1n MA, Monge S. Selection bias due to conditioning on a collider. BMJ. 2023;381:p1135.",
    "Degtiar I, Rose S. A review of generalizability and transportability. Annu Rev Stat Appl. 2023;10(1):501\u201324.",
    "Hern\u00e1n MA, Wang W, Leaf DE. Target trial emulation: a framework for causal inference from observational "
    "data. JAMA. 2022;328(24):2446\u20137.",
]
for i, r in enumerate(refs, 1):
    p = para(doc, f"{i}. {r}", size=10, align="left", line=1.35, after=3)

# ======================= FIGURE LEGENDS (duplicate, for journals) =======================
doc.add_page_break()
h1(doc, "Figure legends")
para(doc, "Fig. 1 Flow of participants. Left, derivation cohort drawn from INSPIRE; right, external validation "
          "cohort drawn from MOVER. The full cohort forms the trunk of the diagram and is followed for the "
          "secondary outcomes, which do not require troponin monitoring; the troponin-monitored subset ("
          "within whom MINS is ascertainable and the primary analysis is performed) hangs as a branch, "
          "with the number and reason for each exclusion. Monitoring refers to at least one postoperative "
          "troponin measurement within 72 h of surgery. INSPIRE, a perioperative research database from a "
          "single tertiary hospital in Seoul; MOVER, Medical Informatics Operating Room Vitals and Events "
          "Repository, University of California, Irvine; MINS, myocardial injury after noncardiac surgery; "
          "AKI, acute kidney injury; MAP, mean arterial pressure.", size=11,
     line=1.5, after=8)
para(doc, "Fig. S3 Shape of the association between hypotension burden and MINS in the derivation cohort (n = 434). "
          "The solid line is the adjusted odds ratio from a restricted cubic spline with four degrees of freedom; "
          "the shaded band is the pointwise 95% confidence interval. Knots were placed at equally spaced quantiles "
          "between the 2nd and 98th percentiles of burden, and the curve was centred at zero burden, so that the "
          "odds ratio is one at the reference. The model was adjusted for age, sex, body mass index, ASA physical "
          "status, baseline creatinine, emergency surgery, diabetes, hypertension and coronary heart disease. "
          "There was no evidence of departure from linearity (P = 0.89); the confidence band widens steeply "
          "over the first 10% of burden and remains wide thereafter; few patients contributed beyond 30% "
          "burden. MINS, myocardial injury after noncardiac surgery.",
     size=11, line=1.5, after=8)
para(doc, "Fig. S4 Proportion of patients with MINS in each burden category, by database. Bars are the observed "
          "proportions among troponin-monitored patients in the analytic cohorts (INSPIRE n = 434, MOVER n = 226); "
          "error bars are 95% confidence intervals from the Wilson score method, and the fractions above each bar "
          "are the number of patients with MINS over the number in that category. In the derivation cohort the "
          "crude proportions were 41%, 28%, 26% and 39% across the four categories, a non-monotonic pattern with "
          "no consistent gradient; the zero-burden category contained only 41 patients and its confidence "
          "interval (28\u201357%) overlaps the highest category. In the validation cohort the proportions rose "
          "from 27% to 45%, 53% and 55%, levelling off above 5% burden. Crude proportions and "
          "covariate-adjusted odds ratios need not share the same ordering. MINS, myocardial injury after "
          "noncardiac surgery.", size=11, line=1.5, after=8)
para(doc, "Fig. 3 External validation of the frozen model in MOVER. (A) Receiver-operating-characteristic curve "
          "obtained by applying the derivation coefficients without re-estimation; the dashed diagonal is the line "
          "of no discrimination, and the area under the curve is 0.682 (95% CI 0.61\u20130.75). (B) Calibration plot: patients were ranked "
          "by predicted risk and divided into ten equal-sized groups; the mean predicted probability is plotted "
          "against the observed proportion with MINS in each group, and the dashed diagonal represents perfect "
          "calibration. The observed-to-expected ratio was 1.22 and the calibration slope 1.81, indicating that "
          "predicted risks were too concentrated and systematically too low. MINS, myocardial injury after "
          "noncardiac surgery.", size=11, line=1.5, after=8)

path = os.environ.get("MINS_OUT", os.path.join(SUB, "Manuscript_MINS.docx"))
doc.save(path)
print("saved", path)

# word count of main text（用第二个 "Background"——第一个在结构式摘要里）
from docx import Document as D2
d = D2(path)
texts = [p.text for p in d.paragraphs]
try:
    bg = [i for i, x in enumerate(texts) if x.strip() == "Background"]
    i0 = bg[-1] if len(bg) > 1 else bg[0]
    i1 = texts.index("Declarations")
    words = sum(len(t.split()) for t in texts[i0:i1])
    print("main text words (Background..Conclusions):", words)
except ValueError:
    pass
