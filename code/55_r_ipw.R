# 55_r_ipw.R — A2: 用逆概率加权（IPW）把监测亚组加权回全队列，定量评估选择偏倚
# PS 模型：与 54 号相同（全队列、BMI 插补全队列中位数、完整病例、含 ane_h）。
# 加权后模型：MINS ~ burden/10 + Model 2 协变量（BMI 用监测队列中位数插补，与主分析一致）。
# 权重：稳定化 sw = P(monitored)/PS。稳健三明治（HC0）标准误。
# 输出：控制台结果 + 更新 TableS_sensitivity.csv / mins_forest.csv（插在 MOVER 定义行之后）。
options(stringsAsFactors = FALSE)
suppressPackageStartupMessages(library(sandwich))

OUT <- "output"
TAB <- file.path(OUT, "tables", "en")
EN <- intToUtf8(8211)
utf8_write <- function(txt, path) writeBin(charToRaw(enc2utf8(txt)), path)

m2cov <- function(has_emerg) {
  v <- c("age", "male", "bmi", "asa_class", "scr_base", "dm", "htn", "chd")
  if (has_emerg) v <- c(v, "emergency")
  v
}

ipw_one <- function(file, has_emerg) {
  d <- read.csv(file.path(OUT, file), fileEncoding = "UTF-8-BOM")
  d$monitored <- as.integer(d$monitored)
  # --- PS 模型（全队列）---
  ps_cov <- c("age", "male", "bmi", "asa_class", "scr_base", "dm", "htn", "chd", "ane_h")
  if (has_emerg) ps_cov <- c(ps_cov, "emergency")
  d$bmi_imp <- d$bmi; d$bmi_imp[is.na(d$bmi_imp)] <- median(d$bmi, na.rm = TRUE)
  ps_cov_all <- c("monitored", "age", "male", "bmi_imp", "asa_class",
                  "scr_base", "dm", "htn", "chd", "ane_h")
  if (has_emerg) ps_cov_all <- c(ps_cov_all, "emergency")
  psd <- d[stats::complete.cases(d[, ps_cov_all]), ]
  fml_ps <- as.formula(paste("monitored ~", paste(gsub("bmi_imp", "bmi", ps_cov), collapse = " + ")))
  names(psd)[names(psd) == "bmi_imp"] <- "bmi"
  ps <- predict(glm(fml_ps, data = psd, family = binomial), type = "response")
  p_mon <- mean(psd$monitored)

  # --- 主分析集（监测、Model 2 完整病例、BMI 插补监测队列中位数）---
  covs <- m2cov(has_emerg)
  a <- d[d$monitored == 1 & !is.na(d$ane_h) & d$ane_h > 0, ]
  a$bmi[is.na(a$bmi)] <- median(a$bmi, na.rm = TRUE)
  a <- a[stats::complete.cases(a[, c("mins", "below65", "ane_h", covs)]), ]
  a$b10 <- 100 * a$below65 / (a$ane_h * 60) / 10
  # PS 取值（主分析集 ⊂ PS 完整病例）
  psa <- predict(glm(fml_ps, data = psd, family = binomial),
                 newdata = a, type = "response")
  sw <- p_mon / psa

  fit_w <- function(w) {
    fml <- as.formula(paste("mins ~ b10 +", paste(covs, collapse = " + ")))
    m <- glm(fml, data = a, family = quasibinomial(), weights = w)
    s <- sandwich::vcovHC(m, type = "HC0")
    est <- unname(coef(m)["b10"]); se <- unname(sqrt(s["b10", "b10"]))
    c(or = exp(est), lo = exp(est - 1.96 * se), hi = exp(est + 1.96 * se),
      p = 2 * pnorm(-abs(est / se)))
  }
  r0 <- fit_w(sw)
  ess <- sum(sw)^2 / sum(sw^2)
  wt99 <- quantile(sw, 0.99)
  r99 <- fit_w(pmin(sw, wt99))
  # 加权前后协变量分布变化（加权均值 vs 全队列均值，age 示例）
  cat(sprintf("%s  analytic n=%d events=%d\n", file, nrow(a), sum(a$mins)))
  cat(sprintf("  weights: min=%.2f max=%.2f ESS=%.0f  99th pct=%.2f  n(w>99pct)=%d\n",
              min(sw), max(sw), ess, wt99, sum(sw > wt99)))
  cat(sprintf("  IPW Model 2 OR = %.2f (%.2f%s%.2f) P=%.3f\n", r0["or"], r0["lo"], EN, r0["hi"], r0["p"]))
  cat(sprintf("  IPW truncated@99pct OR = %.2f (%.2f%s%.2f) P=%.3f\n", r99["or"], r99["lo"], EN, r99["hi"], r99["p"]))
  cat(sprintf("  unweighted Model 2 for reference: see Table 2\n"))
  list(n = nrow(a), ev = sum(a$mins), or = r0["or"], lo = r0["lo"], hi = r0["hi"], p = r0["p"],
       ess = ess, or99 = r99["or"], lo99 = r99["lo"], hi99 = r99["hi"], p99 = r99["p"])
}
ri <- ipw_one("inspire_ortho_analytic.csv", TRUE)
rmv <- ipw_one("mover_ortho_analytic.csv", FALSE)

# ---- 写 ASCII 结果文件（由 55b_merge_ipw.py 负责合并进表，避免 C locale 毁 en-dash）----
res <- data.frame(
  analysis = c("INSPIRE: inverse-probability-of-monitoring weighted",
               "MOVER: inverse-probability-of-monitoring weighted"),
  n = c(ri$n, rmv$n), ev = c(ri$ev, rmv$ev),
  or = c(ri$or, rmv$or), lo = c(ri$lo, rmv$lo), hi = c(ri$hi, rmv$hi), p = c(ri$p, rmv$p),
  ess = c(ri$ess, rmv$ess),
  or99 = c(ri$or99, rmv$or99), lo99 = c(ri$lo99, rmv$lo99),
  hi99 = c(ri$hi99, rmv$hi99), p99 = c(ri$p99, rmv$p99))
write.csv(res, file.path(OUT, "tables", "ipw_results.csv"), row.names = FALSE, fileEncoding = "ASCII")
cat("saved output/tables/ipw_results.csv\n")
