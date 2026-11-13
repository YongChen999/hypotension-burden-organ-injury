# -*- coding: utf-8 -*-
# 第三轮复查：从原始分析集用 R 独立重算全部发表数字（不依赖任何中间表）
# 用法: Rscript code/52_r_full_recompute.R
base <- Sys.getenv("STUDY_ROOT", unset = getwd())
rd <- function(p) read.csv(file.path(base, p), fileEncoding = "UTF-8-BOM", stringsAsFactors = FALSE)

ins <- rd("output/inspire_ortho_analytic.csv")
mov <- rd("output/mover_ortho_analytic.csv")
# 与 41_mins_analysis.py load() 同口径：BMI 用各自监测亚组中位数填补
ins$bmi[is.na(ins$bmi)] <- median(ins$bmi[ins$monitored == 1], na.rm = TRUE)
mov$bmi[is.na(mov$bmi)] <- median(mov$bmi[mov$monitored == 1], na.rm = TRUE)

COV <- c("age", "male", "bmi", "asa_class", "scr_base", "emergency", "dm", "htn", "chd")
COV1 <- c("age", "male")
usable <- function(d, vars) vars[vapply(vars, function(v) {
  x <- d[[v]]; length(unique(x[!is.na(x)])) > 1
}, logical(1))]

# 与 45_mins_tables.py 一致：先 dropna 建分析集，再剔除负荷前 1%
prep <- function(d, outcome, monitored_only = TRUE, trim_top = 0, drop_cov = character()) {
  if (monitored_only) d <- d[d$monitored == 1, ]
  use <- setdiff(COV, drop_cov)
  need <- unique(c(outcome, "burden_pct", "burden10", usable(d, use)))
  d <- d[complete.cases(d[need]), need]
  if (trim_top > 0) {
    cutv <- quantile(d$burden_pct, 1 - trim_top / 100, na.rm = TRUE)
    d <- d[d$burden_pct <= cutv, ]
  }
  d
}

fit_or <- function(d, outcome, label, covset = "full") {
  vars <- switch(covset,
                 crude = character(),
                 m1 = usable(d, COV1),
                 full = usable(d, COV))
  f <- if (length(vars)) as.formula(paste(outcome, "~ burden10 +", paste(vars, collapse = " + ")))
       else as.formula(paste(outcome, "~ burden10"))
  m <- glm(f, data = d, family = binomial)
  b <- coef(summary(m))["burden10", ]
  data.frame(label = label, n = nrow(d), events = sum(d[[outcome]] == 1),
             or = round(exp(b[1]), 2), lo = round(exp(b[1] - 1.96 * b[2]), 2),
             hi = round(exp(b[1] + 1.96 * b[2]), 2), p = round(b[4], 3), row.names = NULL)
}

fit_cat <- function(d, outcome, label) {
  cov <- paste(usable(d, COV), collapse = " + ")
  d$cat <- cut(d$burden_pct, breaks = c(-0.001, 0, 5, 10, 100),
               labels = c("0%", "0-5%", "5-10%", ">10%"))
  d$catn <- as.numeric(d$cat)
  m <- glm(as.formula(paste(outcome, "~ factor(cat) +", cov)), data = d, family = binomial)
  mt <- glm(as.formula(paste(outcome, "~ catn +", cov)), data = d, family = binomial)
  s <- coef(summary(m))
  out <- lapply(c("0-5%", "5-10%", ">10%"), function(lb) {
    k <- grep(lb, rownames(s), fixed = TRUE)[1]; b <- s[k, ]
    data.frame(label = paste0(label, ": ", lb, " vs 0%"), n = nrow(d),
               events = sum(d[[outcome]] == 1), or = round(exp(b[1]), 2),
               lo = round(exp(b[1] - 1.96 * b[2]), 2),
               hi = round(exp(b[1] + 1.96 * b[2]), 2), p = round(b[4], 3))
  })
  st <- coef(summary(mt))["catn", ]
  out[[4]] <- data.frame(label = paste0(label, ": P for trend"), n = nrow(d),
                         events = sum(d[[outcome]] == 1), or = NA, lo = NA, hi = NA,
                         p = round(st[4], 3))
  do.call(rbind, out)
}

auc_w <- function(y, p) {
  n1 <- sum(y == 1); n0 <- sum(y == 0)
  (sum(rank(p)[y == 1]) - n1 * (n1 + 1) / 2) / (n1 * n0)
}

der <- prep(ins, "mins"); val <- prep(mov, "mins", drop_cov = "emergency")
val$emergency <- 0
m2 <- glm(as.formula(paste("mins ~ burden10 +", paste(usable(der, COV), collapse = " + "))),
          data = der, family = binomial)
# 冻结系数迁移（与 41 号 co = 系数 × val 各列 + 截距）
co <- coef(m2)
lpv <- co["(Intercept)"] + as.numeric(as.matrix(val[names(co)[-1]]) %*% co[-1])
pv <- 1 / (1 + exp(-lpv))
pder <- predict(m2, type = "response")
mref <- glm(as.formula(paste("mins ~ burden10 +", paste(usable(val, COV), collapse = " + "))),
            data = val, family = binomial)
pref <- predict(mref, type = "response")
lg <- log(pmin(pmax(pv, 1e-6), 1 - 1e-6) / (1 - pmin(pmax(pv, 1e-6), 1 - 1e-6)))
slope_f <- coef(glm(val$mins ~ lg, family = binomial))["lg"]
oe <- sum(val$mins) / sum(pv)
perf <- data.frame(
  metric = c("derivation apparent AUC", "frozen validation AUC", "frozen O:E",
             "frozen calibration slope", "MOVER refit AUC"),
  value = round(c(auc_w(der$mins, pder), auc_w(val$mins, pv), oe, slope_f,
                  auc_w(val$mins, pref)), 3))

res <- rbind(
  fit_or(der, "mins", "INSPIRE MINS Crude", "crude"),
  fit_or(der, "mins", "INSPIRE MINS Model 1", "m1"),
  fit_or(der, "mins", "INSPIRE MINS Model 2", "full"),
  fit_or(val, "mins", "MOVER MINS Crude", "crude"),
  fit_or(val, "mins", "MOVER MINS Model 1", "m1"),
  fit_or(val, "mins", "MOVER MINS Model 2", "full"),
  fit_cat(der, "mins", "INSPIRE categories"),
  fit_cat(val, "mins", "MOVER categories"),
  fit_or(prep(ins, "mins_04"), "mins_04", "INSPIRE thr0.04"),
  fit_or(prep(ins, "mins_10"), "mins_10", "INSPIRE thr0.10"),
  fit_or(prep(ins, "mins7"),  "mins7",  "INSPIRE 7-day"),
  fit_or(prep(mov, "mins_04", drop_cov = "emergency"), "mins_04", "MOVER thr0.04"),
  fit_or(prep(mov, "mins_10", drop_cov = "emergency"), "mins_10", "MOVER thr0.10"),
  fit_or(prep(ins, "aki", FALSE), "aki", "INSPIRE AKI"),
  fit_or(prep(mov, "aki", FALSE, drop_cov = "emergency"), "aki", "MOVER AKI"),
  fit_or(prep(ins, "death", FALSE), "death", "INSPIRE death"),
  fit_or(prep(ins, "death", FALSE, 1), "death", "INSPIRE death trim1%"),
  fit_or(prep(mov, "death", FALSE, drop_cov = "emergency"), "death", "MOVER death"),
  fit_or(prep(mov, "death", FALSE, 1, "emergency"), "death", "MOVER death trim1%")
)
out <- file.path(base, "output/tables/en/recomputed_full.csv")
write.csv(res, out, row.names = FALSE)
cat("== R 独立重算：模型 ==\n"); print(res, row.names = FALSE)
cat("\n== R 独立重算：判别与校准 ==\n"); print(perf, row.names = FALSE)
cat("saved:", out, "\n")
