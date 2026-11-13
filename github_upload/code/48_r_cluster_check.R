# -*- coding: utf-8 -*-
# 敏感性核查：同一患者多次手术 → 聚类稳健 SE 与仅首台手术子集
# 用法: Rscript code/48_r_cluster_check.R
# 输出: output/tables/en/TableS_cluster_sensitivity.csv
suppressMessages(library(sandwich))

base <- Sys.getenv("STUDY_ROOT", unset = getwd())
cov_i <- "age + male + bmi + asa_class + scr_base + emergency + dm + htn + chd"
cov_m <- "age + male + bmi + asa_class + scr_base + dm + htn + chd"

ins <- read.csv(file.path(base, "output", "inspire_ortho_analytic.csv"), fileEncoding = "UTF-8-BOM")
mov <- read.csv(file.path(base, "output", "mover_ortho_analytic.csv"), fileEncoding = "UTF-8-BOM")
mm  <- read.csv(file.path(base, "data", "web", "mover_ortho_main.csv.gz"),
                colClasses = "character", fileEncoding = "UTF-8-BOM")[, c("log_id", "mrn")]
mov <- merge(mov, mm, by = "log_id", all.x = TRUE)
ins$clu <- ins$subject_id
mov$clu <- mov$mrn

# 与 41_mins_analysis.py load() 同口径：BMI 用各自监测亚组中位数填补
ins$bmi[is.na(ins$bmi)] <- median(ins$bmi[ins$monitored == 1], na.rm = TRUE)
mov$bmi[is.na(mov$bmi)] <- median(mov$bmi[mov$monitored == 1], na.rm = TRUE)

run <- function(d, y, covs, label, first_only = FALSE) {
  if (first_only) d <- d[!duplicated(d$clu), ]
  f <- as.formula(paste(y, "~ burden10 +", covs))
  dd <- d[complete.cases(d[all.vars(f)]), ]          # 与 glm 实际使用的行一致
  m <- glm(f, data = dd, family = binomial)
  est <- coef(m)["burden10"]
  se0 <- coef(summary(m))["burden10", "Std. Error"]
  V <- tryCatch(vcovCL(m, cluster = dd$clu), error = function(e) NULL)
  sec <- if (is.null(V)) NA_real_ else sqrt(V["burden10", "burden10"])
  mk <- function(or_, se) {
    lo <- exp(log(or_) - 1.96 * se); hi <- exp(log(or_) + 1.96 * se)
    p <- 2 * pnorm(-abs(log(or_) / se))
    c(or = round(or_, 3), lo = round(lo, 3), hi = round(hi, 3), p = signif(p, 3))
  }
  data.frame(label = label, first_only = first_only,
             n = nrow(dd), n_patient = length(unique(dd$clu)),
             events = sum(dd[[y]] == 1, na.rm = TRUE),
             t(mk(exp(est), se0)), t(mk(exp(est), sec)),
             check.names = FALSE)
}

res <- rbind(
  run(ins, "mins", cov_i, "INSPIRE MINS"),
  run(ins, "mins", cov_i, "INSPIRE MINS", TRUE),
  run(mov, "mins", cov_m, "MOVER MINS"),
  run(mov, "mins", cov_m, "MOVER MINS", TRUE),
  run(ins, "aki",  cov_i, "INSPIRE AKI"),
  run(ins, "aki",  cov_i, "INSPIRE AKI", TRUE),
  run(mov, "aki",  cov_m, "MOVER AKI"),
  run(mov, "aki",  cov_m, "MOVER AKI", TRUE),
  run(ins, "death", cov_i, "INSPIRE death"),
  run(ins, "death", cov_i, "INSPIRE death", TRUE),
  run(mov, "death", cov_m, "MOVER death"),
  run(mov, "death", cov_m, "MOVER death", TRUE)
)
colnames(res) <- c("label", "first_only", "n", "n_patient", "events",
                   "or_model", "lo_model", "hi_model", "p_model",
                   "or_clu", "lo_clu", "hi_clu", "p_clu")
out <- file.path(base, "output", "tables", "en", "TableS_cluster_sensitivity.csv")
write.csv(res, out, row.names = FALSE)
print(res)
cat("saved:", out, "\n")

# ---- 发表格式版（并入 Additional file Table S3）----
dash <- intToUtf8(8211)  # en-dash，C locale 安全
fmt_or <- function(or_, lo, hi) sprintf("%.2f (%.2f%s%.2f)", or_, lo, dash, hi)
fmt_p <- function(p) ifelse(p < 0.001, "<0.001", sprintf("%.3f", p))
lab <- c("INSPIRE MINS" = "INSPIRE: MINS",
         "INSPIRE AKI" = "INSPIRE: AKI",
         "INSPIRE death" = "INSPIRE: in-hospital death",
         "MOVER MINS" = "MOVER: MINS",
         "MOVER AKI" = "MOVER: AKI",
         "MOVER death" = "MOVER: in-hospital death")
res2 <- res
res2$Analysis <- lab[res2$label]
res2$Set <- ifelse(res2$first_only, "First operation", "All operations")
res2 <- res2[order(match(res2$label, names(lab)), res2$first_only), ]
pub <- data.frame(
  Analysis = res2$Analysis,
  Population = res2$Set,
  Operations = paste0(res2$n, " (", res2$n_patient, ")"),
  Events = as.character(res2$events),
  `OR per 10% (95% CI)` = fmt_or(res2$or_model, res2$lo_model, res2$hi_model),
  `P (model)` = fmt_p(res2$p_model),
  `P (clustered)` = fmt_p(res2$p_clu),
  check.names = FALSE)
out2 <- file.path(base, "output", "tables", "en", "TableS_cluster_sensitivity_pub.csv")
# C locale 下 write.csv 会把非 ASCII 毁成 <U+2013> 字面量 → 用 UTF-8 原始字节写
lines <- c(paste0('"', names(pub), '"', collapse = ","),
           apply(pub, 1, function(r) paste0('"', as.character(r), '"', collapse = ",")))
con <- file(out2, "wb")
writeBin(charToRaw(enc2utf8(paste(lines, collapse = "\n"))), con)
close(con)
cat("saved:", out2, "\n")
