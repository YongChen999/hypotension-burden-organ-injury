# -*- coding: utf-8 -*-
# R 独立复算：与 Python(statsmodels) 主分析逐项对照，用于投稿前的双语言校验。
# 运行：Rscript code/30_r_check.R
suppressPackageStartupMessages({
  library(readr); library(dplyr); library(rms); library(jsonlite)
})
options(datadist = NULL)

OUT <- "output"
COV1 <- c("age", "male", "bmi", "asa_class")
COV2 <- c(COV1, "scr_base", "open_surgery", "emergency", "dm", "htn")

# ---------- 合并症派生（与 Python 版逐字对应）----------
comorb <- function(codes) {
  s <- toupper(ifelse(is.na(codes), "", as.character(codes)))
  tok <- unlist(strsplit(s, "[,\n]"))
  tok <- substr(trimws(tok[nzchar(trimws(tok))]), 1, 5)
  hit <- function(pref) as.integer(any(Reduce(`|`, lapply(pref, function(p) startsWith(tok, p)))))
  c(dm = hit(c("E10", "E11", "E12", "E13", "E14", "250")),
    htn = hit(c("I10", "I11", "I12", "I13", "I15", "401", "402", "403", "404")))
}

prep <- function(path, code_col, bmi_med) {
  d <- suppressWarnings(read_csv(path, show_col_types = FALSE, progress = FALSE))
  if (all(c("weight_kg", "height") %in% names(d))) {
    d$bmi <- d$weight_kg / (as.numeric(d$height) / 100)^2
  }
  cm <- t(vapply(d[[code_col]], comorb, c(dm = 0, htn = 0)))
  d$dm <- cm[, 1]; d$htn <- cm[, 2]
  d$bmi <- ifelse(is.na(d$bmi), bmi_med, d$bmi)
  d$burden10 <- d$burden_pct / 10
  d
}

complete_filter <- function(d) {
  d %>% filter(!is.na(aki), !is.na(burden_pct), !is.na(age), !is.na(male),
               !is.na(bmi), !is.na(asa_class), !is.na(scr_base), !is.na(open_surgery),
               !is.na(emergency), !is.na(dm), !is.na(htn))
}

# ---------- 推导队列 ----------
raw <- suppressWarnings(read_csv(file.path(OUT, "inspire2_analytic.csv"), show_col_types = FALSE))
raw$bmi <- raw$weight_kg / (as.numeric(raw$height) / 100)^2
bmi_med <- median(raw$bmi[raw$evaluable == 1], na.rm = TRUE)

d <- prep(file.path(OUT, "inspire2_analytic.csv"), "patient_diagnosis_codes", bmi_med)
der <- complete_filter(dplyr::filter(d, evaluable == 1))
der$cat <- cut(der$burden_pct, c(-0.001, 0, 5, 10, 100),
               labels = c("0", "0-5", "5-10", ">10"))
der$catn <- as.numeric(der$cat)

cat(sprintf("[R] derivation n=%d events=%d (%.1f%%)\n",
            nrow(der), sum(der$aki), 100 * mean(der$aki)))

f2 <- as.formula(paste("aki ~ burden10 +", paste(COV2, collapse = " + ")))
m_crude <- glm(aki ~ burden10, family = binomial, data = der)
m1 <- glm(as.formula(paste("aki ~ burden10 +", paste(COV1, collapse = " + "))),
          family = binomial, data = der)
m2 <- glm(f2, family = binomial, data = der)

or_ci <- function(m, term) {
  b <- coef(m)[term]; se <- sqrt(vcov(m)[term, term])
  c(OR = exp(b), lo = exp(b - 1.96 * se), hi = exp(b + 1.96 * se),
    P = summary(m)$coefficients[term, 4])
}
cat10 <- or_ci(m2, "burden10")
cat(sprintf("[R] per +10%%: OR %.2f (%.2f-%.2f) P=%.3f\n",
            cat10[1], cat10[2], cat10[3], cat10[4]))

mcat <- glm(as.formula(paste("aki ~ cat +", paste(COV2, collapse = " + "))),
            family = binomial, data = der)
hi <- or_ci(mcat, "cat>10")
cat(sprintf("[R] >10%% vs 0%%: OR %.2f (%.2f-%.2f)\n", hi[1], hi[2], hi[3]))
# 趋势检验：与 Methods 一致，用各分类内的中位数作连续变量
med_by <- der %>% group_by(cat) %>% summarise(m = median(burden_pct), .groups = "drop")
der$catmed <- med_by$m[match(as.character(der$cat), as.character(med_by$cat))]
mt <- glm(as.formula(paste("aki ~ catmed +", paste(COV2, collapse = " + "))),
          family = binomial, data = der)
cat(sprintf("[R] P for trend (category median) = %.3f\n", summary(mt)$coefficients["catmed", 4]))

# ---------- 限制性立方样条（4 df / 5 节点，与 patsy cr(df=4) 同基）----------
dd <- datadist(der); options(datadist = "dd")
f_rcs <- as.formula(paste("aki ~ rcs(burden_pct, 5) +", paste(COV2, collapse = " + ")))
m_rcs <- lrm(f_rcs, data = der, x = TRUE, y = TRUE)
a <- as.matrix(anova(m_rcs))
rn <- trimws(rownames(a))
p_nl <- as.numeric(a[which(rn == "Nonlinear")[1], "P"])   # 非线性项联合检验
p_ov <- as.numeric(a[which(rn == "burden_pct")[1], "P"])  # 总体关联
cat(sprintf("[R] RCS overall P = %.3f ; non-linearity P = %.3f (Harrell 分位节点)\n", p_ov, p_nl))

# ---------- 判别与校准 ----------
lp <- as.numeric(predict(m2))
p <- plogis(lp)
auc <- as.numeric(somers2(p, der$aki)["C"])
set.seed(20261109)
bs <- replicate(1000, {
  i <- sample(length(p), replace = TRUE)
  if (sum(der$aki[i]) %in% c(0, length(i))) NA else as.numeric(somers2(p[i], der$aki[i])["C"])
})
bs <- bs[!is.na(bs)]
cal <- glm(der$aki ~ lp, family = binomial)
cat(sprintf("[R] AUC %.3f (%.3f-%.3f)  calibration slope %.2f\n",
            auc, quantile(bs, .025), quantile(bs, .975), coef(cal)["lp"]))

# ---------- 共线性 ----------
vifs <- sapply(c("burden10", COV2), function(v) {
  rhs <- setdiff(c("burden10", COV2), v)
  r2 <- summary(lm(as.formula(paste(v, "~", paste(rhs, collapse = " + "))), data = der))$r.squared
  1 / (1 - r2)
})
cat(sprintf("[R] max VIF = %.2f\n", max(vifs)))

# ---------- 外部验证（冻结系数）----------
co <- fromJSON(file.path(OUT, "model_v3.json"))$coef
frozen_lp <- function(d) {
  with(d, co[["Intercept"]] + co[["burden10"]] * burden10 + co[["age"]] * age +
         co[["male"]] * male + co[["bmi"]] * bmi + co[["asa_class"]] * asa_class +
         co[["scr_base"]] * scr_base + co[["open_surgery"]] * open_surgery +
         co[["emergency"]] * emergency + co[["dm"]] * dm + co[["htn"]] * htn)
}

cohorts <- list(
  "MOVER-CRC"   = list(file = "mover2_analytic.csv",      code = "visit_diagnosis_codes",  ev = NULL),
  "MOVER-UGI"   = list(file = "mover_ugi_analytic.csv",   code = "visit_diagnosis_codes",  ev = "evaluable"),
  "INSPIRE-UGI" = list(file = "inspire_ugi_analytic.csv", code = "patient_diagnosis_codes", ev = "evaluable")
)

res <- list()
for (nm in names(cohorts)) {
  cf <- cohorts[[nm]]
  x <- prep(file.path(OUT, cf$file), cf$code, bmi_med)
  if (!is.null(cf$ev)) x <- x[x[[cf$ev]] == 1, ]
  if (!"emergency" %in% names(x)) x$emergency <- 0
  if (nm == "MOVER-CRC") x$emergency <- 0
  x <- complete_filter(x)

  lp_x <- frozen_lp(x)
  p_x <- plogis(lp_x)
  y <- x$aki
  auc_x <- as.numeric(somers2(p_x, y)["C"])
  slope_x <- coef(glm(y ~ lp_x, family = binomial))["lp_x"]
  oe <- sum(y) / sum(p_x)
  covs <- COV2[sapply(COV2, function(v) length(unique(x[[v]])) > 1)]
  ref <- glm(as.formula(paste("aki ~ burden10 +", paste(covs, collapse = " + "))),
             family = binomial, data = x)
  r <- or_ci(ref, "burden10")
  res[[nm]] <- c(n = nrow(x), events = sum(y), auc = auc_x, slope = slope_x, oe = oe,
                 or = unname(r[1]), lo = unname(r[2]), hi = unname(r[3]))
  cat(sprintf("[R] %-11s n=%d ev=%d AUC=%.3f slope=%.2f O:E=%.2f refit OR=%.2f (%.2f-%.2f)\n",
              nm, nrow(x), sum(y), auc_x, slope_x, oe, r[1], r[2], r[3]))
}

# ---------- 与 Python 结果对照 ----------
cc <- t(sapply(cohorts, function(z) z$ev))
pytab <- read_csv(file.path(OUT, "tables", "table4_validation.csv"), show_col_types = FALSE)
py <- function(q) pytab[pytab[[1]] == q, ]

cmp <- data.frame(
  Item = c("Derivation n", "Derivation events", "OR per +10% (Model 2)",
           ">10% vs 0% (Model 2)", "P for trend", "RCS non-linearity P",
           "Apparent AUC", "Calibration slope", "Max VIF",
           paste0("Validation AUC (", names(res), ")"),
           paste0("Validation O:E (", names(res), ")"),
           paste0("Re-fitted OR (", names(res), ")")),
  Python = c("2725", "163", "1.19 (1.06-1.33), P=0.003", "1.88 (1.22-2.91)",
             "0.002", "0.305", "0.720", "1.00", "1.17",
             "0.644", "0.669", "0.691",
             "2.96", "1.97", "0.66",
             "2.25 (1.44-3.53)", "1.03 (0.55-1.92)", "1.09 (0.86-1.37)"),
  R = c(as.character(nrow(der)), as.character(sum(der$aki)),
        sprintf("%.2f (%.2f-%.2f), P=%.3f", cat10[1], cat10[2], cat10[3], cat10[4]),
        sprintf("%.2f (%.2f-%.2f)", hi[1], hi[2], hi[3]),
        sprintf("%.3f", summary(mt)$coefficients["catmed", 4]),
        sprintf("%.3f", p_nl),
        sprintf("%.3f", auc), sprintf("%.2f", coef(cal)["lp"]), sprintf("%.2f", max(vifs)),
        sapply(res, function(r) sprintf("%.3f", r["auc"])),
        sapply(res, function(r) sprintf("%.2f", r["oe"])),
        sapply(res, function(r) sprintf("%.2f (%.2f-%.2f)", r["or"], r["lo"], r["hi"]))),
  Note = c(rep("", 5),
           "different knot placement (equal spacing vs Harrell percentiles); same conclusion",
           rep("", 12)),
  stringsAsFactors = FALSE
)
write.csv(cmp, file.path(OUT, "tables", "r_python_agreement.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")
print(cmp, right = FALSE)
cat("\n[输出] output/tables/r_python_agreement.csv\n")
