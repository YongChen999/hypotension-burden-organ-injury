# -*- coding: utf-8 -*-
# 全稿数字一致性复核：OR/CI/P 自洽 + 效能口径（R 4.6.2）
# 用法: Rscript code/51_r_consistency_check.R
base <- Sys.getenv("STUDY_ROOT", unset = getwd())

# C locale 下 read.csv 遇 en-dash 会报 "invalid input"；先按行读、转 ASCII 再解析
read_ascii <- function(p) {
  ln <- readLines(file.path(base, p), warn = FALSE, encoding = "UTF-8-BOM")
  ln <- iconv(ln, from = "UTF-8", to = "ASCII", sub = "-")
  read.csv(text = paste(ln, collapse = "\n"), stringsAsFactors = FALSE, check.names = FALSE)
}

p_from_ci <- function(or, lo, hi) {
  se <- (log(hi) - log(lo)) / (2 * 1.96)
  2 * pnorm(-abs(log(or) / se))
}
report <- function(label, or, lo, hi, p) {
  ph <- p_from_ci(or, lo, hi)
  bad <- abs(ph - p) > max(0.02, 0.15 * p)
  cat(sprintf("%-62s OR %.2f (%.2f-%.2f)  P %.3f / %.3f %s\n",
              substr(label, 1, 62), or, lo, hi, p, ph, if (bad) "<-- MISMATCH" else "ok"))
  bad
}

# 1) 森林图 14 行（分列纯数值）
f <- read_ascii("output/tables/mins_forest.csv")
cat("== Fig S2 / Table S2 forest data (", nrow(f), "rows ) ==\n")
bad <- mapply(report, f$analysis, f$or, f$lo, f$hi, f$p)
cat("mismatches:", sum(bad), "\n")

# 2) 正文 Table 2
t2 <- read_ascii("output/tables/en/Table2_models.csv")
cat("\n== Table 2 models ==\n")
x <- t(vapply(t2[["OR (95% CI)"]], function(s) {
  v <- as.numeric(regmatches(s, gregexpr("[0-9]+\\.?[0-9]*", s))[[1]])
  if (length(v) < 3) c(NA, NA, NA) else v[1:3]
}, numeric(3)))
bad2 <- 0
for (i in seq_len(nrow(t2))) {
  p <- suppressWarnings(as.numeric(t2$P[i]))
  if (anyNA(x[i, ]) || is.na(p)) next
  bad2 <- bad2 + report(paste(t2$Cohort[i], t2$Contrast[i]), x[i, 1], x[i, 2], x[i, 3], p)
}
cat("mismatches:", bad2, "\n")

# 3) 效能：由主模型 CI 反推 SE，80% power 双侧 alpha=.05 => exp(2.80*SE)
mde <- function(lo, hi) round(exp(2.80 * (log(hi) - log(lo)) / (2 * 1.96)), 3)
cat("\n== 最小可检出 OR per 10% (80% power) ==\n")
cat("INSPIRE MINS  1.02 (0.91-1.15):", mde(0.91, 1.15), "\n")
cat("MOVER   MINS  1.33 (0.97-1.83):", mde(0.97, 1.83), "\n")
cat("INSPIRE death 1.18 (1.05-1.32):", mde(1.05, 1.32), "\n")
cat("MOVER   death 1.65 (1.20-2.26):", mde(1.20, 2.26), "\n")

# 4) 分组人数加和
cat("\n== Cohort sums ==\n")
cat("INSPIRE 279+155 =", 279 + 155, "| MOVER 124+102 =", 124 + 102, "\n")
cat("INSPIRE 468+9534 =", 468 + 9534, "| MOVER 230+6710 =", 230 + 6710, "\n")
cat("INSPIRE 8306+317AKI? (rate) =", round(317 / 8306 * 100, 2), "% |",
    "MOVER", round(780 / 5351 * 100, 2), "%\n")
