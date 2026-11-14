# 59_r_aki_cc_duration.R
# C2: AKI complete-case sensitivity (measured baseline creatinine only)
# C3: AKI / in-hospital death / MINS models additionally adjusted for
#     anaesthesia duration (ane_h)
# Output: output/tables/en/TableS7_aki_cc_duration.csv

OUT <- "output"
EN <- file.path(OUT, "tables", "en")
dir.create(EN, recursive = TRUE, showWarnings = FALSE)

COV <- c("age", "male", "bmi", "asa_class", "scr_base", "dm", "htn", "chd")

load_cohort <- function(path) {
  d <- read.csv(path, fileEncoding = "UTF-8-BOM", stringsAsFactors = FALSE)
  num <- c("bmi", "burden_pct", "ane_h", "aki", "death", "mins", "monitored",
           COV)
  for (v in intersect(num, names(d))) d[[v]] <- suppressWarnings(as.numeric(d[[v]]))
  # BMI imputed with the monitored-subgroup median, as in the primary pipeline
  med <- median(d$bmi[d$monitored == 1], na.rm = TRUE)
  d$bmi[is.na(d$bmi)] <- med
  d$burden10 <- d$burden_pct / 10
  d
}

fit_row <- function(d, outcome, covs, label, extra_drop = character(0)) {
  need <- c(outcome, "burden10", covs, extra_drop)
  need <- intersect(need, names(d))
  d <- d[stats::complete.cases(d[, need, drop = FALSE]), ]
  cov_use <- covs[vapply(d[, covs, drop = FALSE], function(x) length(unique(x)) > 1, logical(1))]
  f <- stats::as.formula(paste(outcome, "~ burden10 +", paste(cov_use, collapse = " + ")))
  m <- stats::glm(f, data = d, family = stats::binomial())
  b <- stats::coef(summary(m))["burden10", ]
  or <- exp(b["Estimate"]); lo <- exp(b["Estimate"] - 1.96 * b["Std. Error"])
  hi <- exp(b["Estimate"] + 1.96 * b["Std. Error"])
  p <- b["Pr(>|z|)"]
  data.frame(Analysis = label, n = nrow(d), Events = as.integer(sum(d[[outcome]] == 1)),
             OR = sprintf("%.2f (%.2f\u2013%.2f)", or, lo, hi),
             P = ifelse(p < 0.001, "<0.001", sprintf("%.3f", p)),
             stringsAsFactors = FALSE)
}

A <- load_cohort(file.path(OUT, "inspire_ortho_analytic.csv"))
B <- load_cohort(file.path(OUT, "mover_ortho_analytic.csv"))

rows <- list()

# ---- C2: AKI complete-case (measured baseline creatinine, no MDRD imputation) ----
for (nm in c("INSPIRE", "MOVER")) {
  d <- if (nm == "INSPIRE") A else B
  covs <- if (nm == "INSPIRE") c(COV, "emergency") else COV
  cc <- d[d$baseline_src %in% c("7d", "30d"), ]
  rows[[length(rows) + 1]] <- fit_row(
    cc, "aki", covs,
    sprintf("%s: postoperative AKI, complete-case (measured baseline and postoperative creatinine)\u2020", nm))
}

# ---- C3: models additionally adjusted for anaesthesia duration ----
for (nm in c("INSPIRE", "MOVER")) {
  d <- if (nm == "INSPIRE") A else B
  covs <- if (nm == "INSPIRE") c(COV, "emergency") else COV
  rows[[length(rows) + 1]] <- fit_row(
    d, "aki", c(covs, "ane_h"),
    sprintf("%s: postoperative AKI (full cohort), adjusted for anaesthesia duration\u2021", nm))
  rows[[length(rows) + 1]] <- fit_row(
    d, "death", c(covs, "ane_h"),
    sprintf("%s: in-hospital death (full cohort), adjusted for anaesthesia duration\u2021", nm))
  mon <- d[d$monitored == 1, ]
  rows[[length(rows) + 1]] <- fit_row(
    mon, "mins", c(covs, "ane_h"),
    sprintf("%s: MINS (monitored cohort), adjusted for anaesthesia duration\u2021", nm))
}

tab <- do.call(rbind, rows)
names(tab)[4] <- "OR per 10% (95% CI)"

# write with BOM and preserved UTF-8 bytes (en-dash, daggers)
q <- function(x) ifelse(grepl(",", x, fixed = TRUE), sprintf("\"%s\"", x), x)
lines_out <- vapply(seq_len(nrow(tab)), function(i) {
  paste(q(tab$Analysis[i]), tab$n[i], tab$Events[i], tab[["OR per 10% (95% CI)"]][i],
        tab$P[i], sep = ",")
}, character(1))
con_text <- paste(paste(names(tab), collapse = ","), paste(lines_out, collapse = "\n"), sep = "\n")
writeBin(c(charToRaw("\ufeff"), charToRaw(enc2utf8(con_text))),
         file.path(EN, "TableS7_aki_cc_duration.csv"))
print(tab, row.names = FALSE)
cat("\n[saved]", file.path(EN, "TableS7_aki_cc_duration.csv"), "\n")
