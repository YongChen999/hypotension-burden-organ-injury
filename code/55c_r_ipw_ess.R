# 55c_r_ipw_ess.R — effective sample size after 99th-percentile weight truncation
# Same propensity model and analytic sets as 55_r_ipw.R; reports ESS before/after truncation.
options(stringsAsFactors = FALSE)

OUT <- "output"

ipw_ess <- function(file, has_emerg) {
  d <- read.csv(file.path(OUT, file), fileEncoding = "UTF-8-BOM")
  d$monitored <- as.integer(d$monitored)
  ps_cov <- c("age", "male", "bmi", "asa_class", "scr_base", "dm", "htn", "chd", "ane_h")
  if (has_emerg) ps_cov <- c(ps_cov, "emergency")
  d$bmi_imp <- d$bmi; d$bmi_imp[is.na(d$bmi_imp)] <- median(d$bmi, na.rm = TRUE)
  ps_cov_all <- c("monitored", "age", "male", "bmi_imp", "asa_class",
                  "scr_base", "dm", "htn", "chd", "ane_h")
  if (has_emerg) ps_cov_all <- c(ps_cov_all, "emergency")
  psd <- d[stats::complete.cases(d[, ps_cov_all]), ]
  fml_ps <- as.formula(paste("monitored ~", paste(gsub("bmi_imp", "bmi", ps_cov), collapse = " + ")))
  names(psd)[names(psd) == "bmi_imp"] <- "bmi"
  ps_model <- glm(fml_ps, data = psd, family = binomial)
  p_mon <- mean(psd$monitored)

  covs <- c("age", "male", "bmi", "asa_class", "scr_base", "dm", "htn", "chd")
  if (has_emerg) covs <- c(covs, "emergency")
  a <- d[d$monitored == 1 & !is.na(d$ane_h) & d$ane_h > 0, ]
  a$bmi[is.na(a$bmi)] <- median(a$bmi, na.rm = TRUE)
  a <- a[stats::complete.cases(a[, c("mins", "below65", "ane_h", covs)]), ]
  psa <- predict(ps_model, newdata = a, type = "response")
  sw <- p_mon / psa
  wt99 <- quantile(sw, 0.99)
  sw_t <- pmin(sw, wt99)
  ess <- sum(sw)^2 / sum(sw^2)
  ess_t <- sum(sw_t)^2 / sum(sw_t^2)
  cat(sprintf("%s  n=%d  ESS=%.1f  ESS_truncated=%.1f  (%.0f%% / %.0f%% of n)\n",
              file, nrow(a), ess, ess_t, 100 * ess / nrow(a), 100 * ess_t / nrow(a)))
}
ipw_ess("inspire_ortho_analytic.csv", TRUE)
ipw_ess("mover_ortho_analytic.csv", FALSE)
