# 54_r_selection_table.R — A1: 正文新 Table 2（监测选择实证 + c-statistic）
# 人群：两库全队列（含未监测），BMI 缺失插补全队列中位数，其余协变量完整病例。
# 输出：output/tables/en/Table2_selection.csv + 控制台 c-statistic（2000 次 bootstrap 95% CI）
options(stringsAsFactors = FALSE)
set.seed(20261110)

OUT <- "output"
TAB <- file.path(OUT, "tables", "en")
EN <- intToUtf8(8211)  # en-dash

utf8_write <- function(txt, path) writeBin(charToRaw(enc2utf8(txt)), path)

prep <- function(file, has_emerg) {
  d <- read.csv(file.path(OUT, file), fileEncoding = "UTF-8-BOM")
  d$monitored <- as.integer(d$monitored)
  d$bmi[is.na(d$bmi)] <- median(d$bmi, na.rm = TRUE)   # 全队列中位数插补
  covs <- c("age", "male", "bmi", "asa_class", "scr_base", "dm", "htn", "chd", "ane_h")
  if (has_emerg) covs <- c(covs, "emergency")
  cc <- d[stats::complete.cases(d[, c("monitored", covs)]), ]
  list(d = d, cc = cc, covs = covs)
}
ins <- prep("inspire_ortho_analytic.csv", TRUE)
mov <- prep("mover_ortho_analytic.csv", FALSE)

# ---- c-statistic（是否被监测）+ bootstrap CI ----
cstat <- function(cc, covs, B = 2000) {
  fml <- as.formula(paste("monitored ~", paste(covs, collapse = " + ")))
  p <- as.numeric(predict(glm(fml, data = cc, family = binomial), type = "response"))
  auc0 <- as.numeric(pROC::auc(cc$monitored, p))
  aucs <- numeric(0)
  n <- nrow(cc)
  for (b in seq_len(B)) {
    i <- sample.int(n, n, replace = TRUE)
    y <- cc$monitored[i]
    if (length(unique(y)) < 2) next
    mb <- suppressWarnings(try(glm(fml, data = cc[i, ], family = binomial), silent = TRUE))
    if (inherits(mb, "try-error")) next
    a <- as.numeric(pROC::auc(y, as.numeric(predict(mb, type = "response"))))
    if (is.finite(a)) aucs <- c(aucs, a)
  }
  c(auc = auc0, lo = unname(quantile(aucs, 0.025, na.rm = TRUE)),
    hi = unname(quantile(aucs, 0.975, na.rm = TRUE)),
    n = n, ev = sum(cc$monitored), B = length(aucs))
}
ci <- cstat(ins$cc, ins$covs); cm <- cstat(mov$cc, mov$covs)
cat(sprintf("INSPIRE c-statistic %.3f (%.3f%s%.3f)  n=%d monitored=%d B=%d\n",
            ci["auc"], ci["lo"], EN, ci["hi"], ci["n"], ci["ev"], ci["B"]))
cat(sprintf("MOVER   c-statistic %.3f (%.3f%s%.3f)  n=%d monitored=%d B=%d\n",
            cm["auc"], cm["lo"], EN, cm["hi"], cm["n"], cm["ev"], cm["B"]))

# ---- 正文 Table 2 汇总行（按变量各自可用样本，与 Table S1 口径一致）----
fmt_med <- function(x) {
  x <- x[!is.na(x)]
  sprintf("%.1f (%.1f%s%.1f)", median(x), quantile(x, .25), EN, quantile(x, .75))
}
fmt_np <- function(x) sprintf("%d (%.1f)", sum(x, na.rm = TRUE), 100 * mean(x, na.rm = TRUE))
# 与 45 号口径一致：2x2 表一律 Fisher 精确检验（其 tab.size<5 条件对 2x2 恒真）
np_test <- function(y1, n1, y2, n2) fisher.test(matrix(c(y1, n1 - y1, y2, n2 - y2), ncol = 2))$p.value
med_p <- function(a, b) {
  a <- a[!is.na(a)]; b <- b[!is.na(b)]; wilcox.test(a, b)$p.value
}
np_p <- function(x1, x2) np_test(sum(x1, na.rm = TRUE), sum(!is.na(x1)),
                                  sum(x2, na.rm = TRUE), sum(!is.na(x2)))

row_block <- function(d) {
  mon <- d[d$monitored == 1, ]; un <- d[d$monitored == 0, ]
  ak_m <- mon[!is.na(mon$aki), ]; ak_u <- un[!is.na(un$aki), ]
  list(
    "Age, years"                      = c(fmt_med(mon$age), fmt_med(un$age), med_p(mon$age, un$age)),
    "Male sex"                        = c(fmt_np(mon$male), fmt_np(un$male), np_p(mon$male, un$male)),
    "ASA physical status \u22653"     = c(fmt_np(as.integer(mon$asa_class >= 3)),
                                          fmt_np(as.integer(un$asa_class >= 3)),
                                          np_p(as.integer(mon$asa_class >= 3), as.integer(un$asa_class >= 3))),
    "Anaesthesia duration, h"         = c(fmt_med(mon$ane_h), fmt_med(un$ane_h), med_p(mon$ane_h, un$ane_h)),
    "Coronary heart disease"          = c(fmt_np(mon$chd), fmt_np(un$chd), np_p(mon$chd, un$chd)),
    "Hypotension burden, %"           = c(fmt_med(mon$burden_pct), fmt_med(un$burden_pct),
                                          med_p(mon$burden_pct, un$burden_pct)),
    "Postoperative AKI"               = c(fmt_np(ak_m$aki), fmt_np(ak_u$aki), np_p(ak_m$aki, ak_u$aki)),
    "In-hospital death"               = c(fmt_np(mon$death), fmt_np(un$death), np_p(mon$death, un$death)))
}
ri <- row_block(ins$d); rmv <- row_block(mov$d)

fixp <- function(v) { v <- as.numeric(v); ifelse(v < 0.001, "<0.001", sprintf("%.3f", v)) }
nm_in <- sum(ins$d$monitored == 1); nm_un <- sum(ins$d$monitored == 0)
mv_in <- sum(mov$d$monitored == 1); mv_un <- sum(mov$d$monitored == 0)
cat("AKI evaluable denominators: INSPIRE", sum(ins$d$monitored == 1 & !is.na(ins$d$aki)),
    "+", sum(ins$d$monitored == 0 & !is.na(ins$d$aki)),
    "; MOVER", sum(mov$d$monitored == 1 & !is.na(mov$d$aki)),
    "+", sum(mov$d$monitored == 0 & !is.na(mov$d$aki)), "\n")

hdr <- c("Characteristic",
  sprintf("INSPIRE monitored (n=%d)", nm_in), sprintf("INSPIRE not monitored (n=%d)", nm_un), "P",
  sprintf("MOVER monitored (n=%d)", mv_in), sprintf("MOVER not monitored (n=%d)", mv_un), "P")
lines <- paste0(hdr, collapse = ",")
keys <- c("Age, years", "Male sex", "ASA physical status \u22653", "Anaesthesia duration, h",
          "Coronary heart disease", "Hypotension burden, %", "Postoperative AKI", "In-hospital death")
for (k in keys) {
  v <- c(ri[[k]][1:3], rmv[[k]][1:3])
  v[3] <- fixp(v[3]); v[6] <- fixp(v[6])
  lines <- c(lines, paste0('"', k, '",', paste0('"', v, '"', collapse = ",")))
}
cst_in <- sprintf("%.2f (%.2f%s%.2f)", ci["auc"], ci["lo"], EN, ci["hi"])
cst_mv <- sprintf("%.2f (%.2f%s%.2f)", cm["auc"], cm["lo"], EN, cm["hi"])
lines <- c(lines, paste0('"C-statistic for being monitored (95% CI)","', cst_in, '","","","',
                         cst_mv, '","",""'))
utf8_write(paste0("\ufeff", paste(lines, collapse = "\n"), "\n"), file.path(TAB, "Table2_selection.csv"))
cat("saved Table2_selection.csv\n")
