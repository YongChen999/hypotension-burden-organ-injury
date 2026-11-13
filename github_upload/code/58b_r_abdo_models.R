# Abdominal parallel cohort: elective model ladder + Table S6 (manuscript supplement).
# Reproducible from output/abdo_full_cohort.csv (built by 57_abdo_rebuild.py).

d <- read.csv("output/abdo_full_cohort.csv", fileEncoding = "UTF-8-BOM")

prep <- function(x) {
  x$asa_f <- factor(x$asa)
  x$scr_base[is.na(x$scr_base)] <- median(x$scr_base, na.rm = TRUE)
  x
}
fmt <- function(m, lab) {
  s <- summary(m)
  b <- s$coefficients["burden10", ]
  ci <- suppressMessages(confint.default(m))["burden10", ]
  cat(sprintf("%-26s n=%5d ev=%4d  OR=%.2f (%.2f-%.2f)  P=%.3g\n", lab,
              nobs(m), sum(m$y), exp(b[1]), exp(ci[1]), exp(ci[2]), b[4]))
}
getest <- function(m) {
  s <- summary(m)
  b <- unname(s$coefficients["burden10", ])
  ci <- unname(suppressMessages(confint.default(m))["burden10", ])
  c(or = exp(b[1]), lo = exp(ci[1]), hi = exp(ci[2]), p = b[4],
    n = nobs(m), ev = sum(m$y))
}
pfmt <- function(p) ifelse(p < 0.001, "<0.001", sprintf("%.3f", p))
cifmt <- function(e) sprintf("%.2f (%.2f%s%.2f)", e["or"], e["lo"],
                             intToUtf8(8211), e["hi"])

el <- prep(subset(d, emergency == 0))
cov1 <- "age + male + bmi + open_surgery + op_h + asa_f"
cov2 <- paste(cov1, "+ scr_base + dm + htn + cad")

cat("=== Elective cohort counts ===\n")
cat("Elective n =", nrow(el), "\n")
cat("Elective monitored =", sum(el$monitored == 1),
    "(", sprintf("%.1f", 100*sum(el$monitored == 1)/nrow(el)), "% )\n")
cat("Elective MINS events =", sum(el$mins, na.rm = TRUE), "\n")
cat("Elective MINS rate =", sprintf("%.1f", 100*sum(el$mins, na.rm=TRUE)/sum(el$monitored==1)), "%\n")
cat("Elective AKI =", sum(el$aki, na.rm = TRUE), "of", sum(!is.na(el$aki)), "\n\n")

m0e <- subset(el, monitored == 1 & !is.na(mins) & !is.na(burden10))
e_m1 <- getest(glm(mins ~ burden10, data = m0e, family = binomial))
e_m2 <- getest(glm(as.formula(paste("mins ~ burden10 +", cov1)), data = m0e, family = binomial))
e_m3 <- getest(glm(as.formula(paste("mins ~ burden10 +", cov2)), data = m0e, family = binomial))
# complete-case (no median imputation of baseline creatinine): build from raw data
el_raw <- subset(d, emergency == 0)
cc <- subset(el_raw, monitored == 1 & !is.na(mins) & !is.na(burden10) &
              !is.na(scr_base) & !is.na(bmi) & !is.na(asa) & !is.na(op_h))
cc$asa_f <- factor(cc$asa)
cc$scr_base[is.na(cc$scr_base)] <- median(cc$scr_base, na.rm = TRUE)  # no-op, kept for symmetry
e_cc <- getest(glm(as.formula(paste("mins ~ burden10 +", cov2)), data = cc, family = binomial))

cat("=== MINS models (elective monitored) ===\n")
fmt(glm(mins ~ burden10, data = m0e, family = binomial), "M1 crude")
fmt(glm(as.formula(paste("mins ~ burden10 +", cov1)), data = m0e, family = binomial), "M2")
fmt(glm(as.formula(paste("mins ~ burden10 +", cov2)), data = m0e, family = binomial), "M3")
cat("Complete case M3   n =", e_cc["n"], "ev =", e_cc["ev"],
    " OR =", sprintf("%.2f (%.2f-%.2f)", e_cc["or"], e_cc["lo"], e_cc["hi"]),
    "P =", pfmt(e_cc["p"]), "\n\n")

a0e <- subset(el, !is.na(aki) & !is.na(burden10))
a_m1 <- getest(glm(aki ~ burden10, data = a0e, family = binomial))
a_m2 <- getest(glm(as.formula(paste("aki ~ burden10 +", cov1)), data = a0e, family = binomial))
a_m3 <- getest(glm(as.formula(paste("aki ~ burden10 +", cov2)), data = a0e, family = binomial))

cat("=== AKI models (elective full cohort) ===\n")
fmt(glm(aki ~ burden10, data = a0e, family = binomial), "AKI M1 crude")
fmt(glm(as.formula(paste("aki ~ burden10 +", cov1)), data = a0e, family = binomial), "AKI M2")
fmt(glm(as.formula(paste("aki ~ burden10 +", cov2)), data = a0e, family = binomial), "AKI M3\n")

# ---- emergency strata (recompute with n/ev) ----
mon <- prep(subset(d, monitored == 1 & !is.na(mins) & !is.na(burden10)))
e0s <- subset(mon, emergency == 0); e1s <- subset(mon, emergency == 1)
s_min_e <- getest(glm(as.formula(paste("mins ~ burden10 +", cov2)), data = e1s, family = binomial))
cat("Emergency MINS stratum n =", s_min_e["n"], "ev =", s_min_e["ev"],
    "OR =", cifmt(s_min_e), "P =", pfmt(s_min_e["p"]), "\n")

aki_all <- prep(subset(d, !is.na(aki) & !is.na(burden10)))
a0s <- subset(aki_all, emergency == 0); a1s <- subset(aki_all, emergency == 1)
s_aki_e <- getest(glm(as.formula(paste("aki ~ burden10 +", cov2)), data = a1s, family = binomial))
s_aki_0 <- getest(glm(as.formula(paste("aki ~ burden10 +", cov2)), data = a0s, family = binomial))
cat("Elective AKI stratum   n =", s_aki_0["n"], "ev =", s_aki_0["ev"],
    "OR =", cifmt(s_aki_0), "P =", pfmt(s_aki_0["p"]), "\n")
cat("Emergency AKI stratum  n =", s_aki_e["n"], "ev =", s_aki_e["ev"],
    "OR =", cifmt(s_aki_e), "P =", pfmt(s_aki_e["p"]), "\n\n")

# ---- incl-emergency + no-op_h ----
cov_noh <- "age + male + bmi + open_surgery + asa_f + scr_base + dm + htn + cad"
e_incl <- getest(glm(as.formula(paste("mins ~ burden10 + emergency +", cov2)),
                     data = mon, family = binomial))
e_noh  <- getest(glm(as.formula(paste("mins ~ burden10 + emergency +", cov_noh)),
                     data = mon, family = binomial))
cat("M3 incl emergency   n =", e_incl["n"], "ev =", e_incl["ev"],
    "OR =", cifmt(e_incl), "P =", pfmt(e_incl["p"]), "\n")
cat("M3 without op_h     n =", e_noh["n"], "ev =", e_noh["ev"],
    "OR =", cifmt(e_noh), "P =", pfmt(e_noh["p"]), "\n")

# interaction P values (from 58: LRT)
p_int_mins <- 0.4871
p_int_aki  <- 0.5305

# emergency monitored counts (for the assembly rows of Table S6)
em <- subset(d, emergency == 1)
n_mon_em  <- sum(em$monitored == 1)
ev_mon_em <- sum(em$mins[em$monitored == 1], na.rm = TRUE)

# ---------------- Table S6 CSV ----------------
hd <- "Item,n,Events,OR per 10% burden (95% CI),P"
ge <- intToUtf8(8805)  # >= sign
rows <- c(
  "\"Cohort assembly: general surgery, general anaesthesia, aged >18 years\",32943,,,",
  "\"Cohort assembly: therapeutic abdominal procedure (ICD-10-PCS 0D/0F)\",17772,,,",
  sprintf("\"Cohort assembly: operative duration %s120 min\",10069,,,", ge),
  sprintf("\"Cohort assembly: hospital stay %s3 days\",10048,,,", ge),
  "\"Elective operations (main analysis)\",9075,,,",
  "\"Emergency operations (sensitivity analysis)\",973,,,",
  "\"Monitored elective operations\",1074,,,",
  "\"MINS among monitored elective operations\",1074,328,,",
  sprintf("\"Monitored emergency operations\",%d,,,", n_mon_em),
  sprintf("\"MINS among monitored emergency operations\",%d,%d,,", n_mon_em, ev_mon_em),
  "\"Postoperative AKI, elective full cohort\",9075,954,,",
  sprintf("\"MINS, crude (monitored elective)\",%d,%d,%s,%s", e_m1["n"], e_m1["ev"], cifmt(e_m1), pfmt(e_m1["p"])),
  sprintf("\"MINS, adjusted for age, sex, BMI, approach, duration, ASA\",%d,%d,%s,%s", e_m2["n"], e_m2["ev"], cifmt(e_m2), pfmt(e_m2["p"])),
  sprintf("\"MINS, fully adjusted (M3)\",%d,%d,%s,%s", e_m3["n"], e_m3["ev"], cifmt(e_m3), pfmt(e_m3["p"])),
  sprintf("\"MINS, fully adjusted, complete case\",%d,%d,%s,%s", e_cc["n"], e_cc["ev"], cifmt(e_cc), pfmt(e_cc["p"])),
  sprintf("\"AKI, crude (elective full cohort)\",%d,%d,%s,%s", a_m1["n"], a_m1["ev"], cifmt(a_m1), pfmt(a_m1["p"])),
  sprintf("\"AKI, adjusted for age, sex, BMI, approach, duration, ASA\",%d,%d,%s,%s", a_m2["n"], a_m2["ev"], cifmt(a_m2), pfmt(a_m2["p"])),
  sprintf("\"AKI, fully adjusted (M3)\",%d,%d,%s,%s", a_m3["n"], a_m3["ev"], cifmt(a_m3), pfmt(a_m3["p"])),
  sprintf("\"MINS, emergency stratum\",%d,%d,%s,%s", s_min_e["n"], s_min_e["ev"], cifmt(s_min_e), pfmt(s_min_e["p"])),
  sprintf("\"AKI, elective stratum\",%d,%d,%s,%s", s_aki_0["n"], s_aki_0["ev"], cifmt(s_aki_0), pfmt(s_aki_0["p"])),
  sprintf("\"AKI, emergency stratum\",%d,%d,%s,%s", s_aki_e["n"], s_aki_e["ev"], cifmt(s_aki_e), pfmt(s_aki_e["p"])),
  sprintf("\"Interaction: emergency %s burden (MINS), LRT P\",,,,%.3f", intToUtf8(215), p_int_mins),
  sprintf("\"Interaction: emergency %s burden (AKI), LRT P\",,,,%.3f", intToUtf8(215), p_int_aki),
  sprintf("\"MINS, all operations incl. emergency (complete covariates)\",%d,%d,%s,%s", e_incl["n"], e_incl["ev"], cifmt(e_incl), pfmt(e_incl["p"])),
  sprintf("\"MINS, all operations, duration removed (complete covariates)\",%d,%d,%s,%s", e_noh["n"], e_noh["ev"], cifmt(e_noh), pfmt(e_noh["p"]))
)
csv <- paste(c(hd, rows), collapse = "\n")
csv <- paste0("\ufeff", csv, "\n")
dir.create("output/tables/en", showWarnings = FALSE, recursive = TRUE)
con <- file("output/tables/en/TableS6_abdo_parallel.csv", "wb")
writeBin(charToRaw(enc2utf8(csv)), con)
close(con)
cat("\nWrote output/tables/en/TableS6_abdo_parallel.csv\n")
