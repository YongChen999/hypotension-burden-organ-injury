# 用 R/ggplot2 重绘全部统计图（Fig 2-4, Fig S1-S4），输出 300 dpi PNG 供投稿使用。
suppressPackageStartupMessages({
  library(readr); library(dplyr); library(tidyr); library(ggplot2)
  library(rms); library(patchwork); library(scales); library(jsonlite)
})

OUT <- "output"
FIG <- file.path(OUT, "figures", "submission")
dir.create(FIG, showWarnings = FALSE, recursive = TRUE)

COV1 <- c("age", "male", "bmi", "asa_class")
COV2 <- c(COV1, "scr_base", "open_surgery", "emergency", "dm", "htn")

theme_set(
  theme_bw(base_size = 11, base_family = "sans") +
    theme(panel.grid.minor = element_blank(),
          panel.grid.major = element_line(linewidth = 0.25, colour = "grey88"),
          axis.text = element_text(colour = "grey15"),
          axis.title = element_text(colour = "black"),
          strip.background = element_rect(fill = "grey95", colour = "grey60"),
          strip.text = element_text(face = "bold", size = 10),
          legend.key = element_blank(),
          plot.margin = margin(6, 10, 6, 6))
)

comorb <- function(codes) {
  s <- toupper(ifelse(is.na(codes), "", as.character(codes)))
  tok <- unlist(strsplit(s, "[,\n]"))
  tok <- substr(trimws(tok[nzchar(trimws(tok))]), 1, 5)
  hit <- function(pref) as.integer(any(Reduce(`|`, lapply(pref, function(p) startsWith(tok, p)))))
  c(dm = hit(c("E10", "E11", "E12", "E13", "E14", "250")),
    htn = hit(c("I10", "I11", "I12", "I13", "I15", "401", "402", "403", "404")))
}

prep <- function(file, code_col, bmi_med, evaluable = TRUE) {
  d <- suppressWarnings(read_csv(file.path(OUT, file), show_col_types = FALSE, progress = FALSE))
  if (all(c("weight_kg", "height") %in% names(d))) d$bmi <- d$weight_kg / (as.numeric(d$height) / 100)^2
  cm <- t(vapply(d[[code_col]], comorb, c(dm = 0, htn = 0)))
  d$dm <- cm[, 1]; d$htn <- cm[, 2]
  d$bmi <- ifelse(is.na(d$bmi), bmi_med, d$bmi)
  d$burden10 <- d$burden_pct / 10
  if (!"emergency" %in% names(d)) d$emergency <- 0
  if (evaluable && "evaluable" %in% names(d)) d <- d[d$evaluable == 1, ]
  d %>% filter(!is.na(aki), !is.na(burden_pct), !is.na(age), !is.na(male), !is.na(bmi),
               !is.na(asa_class), !is.na(scr_base), !is.na(open_surgery), !is.na(emergency),
               !is.na(dm), !is.na(htn))
}

raw <- suppressWarnings(read_csv(file.path(OUT, "inspire2_analytic.csv"), show_col_types = FALSE))
raw$bmi <- raw$weight_kg / (as.numeric(raw$height) / 100)^2
BMI_MED <- median(raw$bmi[raw$evaluable == 1], na.rm = TRUE)

der <- prep("inspire2_analytic.csv", "patient_diagnosis_codes", BMI_MED)
der$cat <- factor(cut(der$burden_pct, c(-0.001, 0, 5, 10, 100),
                      labels = c("0", "0-5", "5-10", ">10")),
                  levels = c("0", "0-5", "5-10", ">10"))

co <- jsonlite::fromJSON(file.path(OUT, "model_v3.json"))$coef
frozen_lp <- function(d) {
  with(d, co[["Intercept"]] + co[["burden10"]] * burden10 + co[["age"]] * age +
         co[["male"]] * male + co[["bmi"]] * bmi + co[["asa_class"]] * asa_class +
         co[["scr_base"]] * scr_base + co[["open_surgery"]] * open_surgery +
         co[["emergency"]] * emergency + co[["dm"]] * dm + co[["htn"]] * htn)
}

mover_crc <- prep("mover2_analytic.csv", "visit_diagnosis_codes", BMI_MED)
insp_ugi  <- prep("inspire_ugi_analytic.csv", "patient_diagnosis_codes", BMI_MED)
mover_ugi <- prep("mover_ugi_analytic.csv", "visit_diagnosis_codes", BMI_MED)

val <- list("MOVER, colorectal" = mover_crc,
            "MOVER, upper GI" = mover_ugi,
            "INSPIRE, upper GI" = insp_ugi)
val <- lapply(val, function(d) { d$p <- plogis(frozen_lp(d)); d })

dash <- intToUtf8(8211)

wilson <- function(k, n, z = 1.96) {
  ph <- k / n
  den <- 1 + z^2 / n
  ctr <- (ph + z^2 / (2 * n)) / den
  hw <- z * sqrt(ph * (1 - ph) / n + z^2 / (4 * n^2)) / den
  c(lo = max(0, ctr - hw), hi = min(1, ctr + hw))
}

roc_pts <- function(y, p) {
  o <- order(p, decreasing = TRUE); y <- y[o]
  data.frame(fpr = c(0, cumsum(1 - y) / sum(1 - y)), tpr = c(0, cumsum(y) / sum(y)))
}
auc_r <- function(y, p) as.numeric(somers2(p, y)["C"])

# ------------------------------------------------------------------ Fig 2 RCS
dd <- datadist(der); options(datadist = "dd")
dd$limits["Adjust to", "burden_pct"] <- as.numeric(quantile(der$burden_pct, 0.10))
assign("dd", dd, envir = .GlobalEnv); options(datadist = "dd")
kn <- seq(quantile(der$burden_pct, 0.02), quantile(der$burden_pct, 0.98), length.out = 5)
f_rcs <- as.formula(paste("aki ~ rcs(burden_pct, kn) +", paste(COV2, collapse = " + ")))
m_rcs <- lrm(f_rcs, data = der, x = TRUE, y = TRUE)
cat("knots used:", round(kn, 2), "\n")
pr <- as.data.frame(Predict(m_rcs, burden_pct, ref.zero = TRUE, fun = exp))
names(pr)[names(pr) == "burden_pct"] <- "x"
an <- as.matrix(anova(m_rcs)); rn <- trimws(rownames(an))
P_NL <- as.numeric(an[which(rn == "Nonlinear")[1], "P"])
P_OV <- as.numeric(an[which(rn == "burden_pct")[1], "P"])
cat(sprintf("RCS overall P = %.3f ; non-linearity P = %.3f\n", P_OV, P_NL))
pr <- pr[pr$x <= 45, ]
xs <- c(5, 10, 15, 20, 25, 30, 35, 40)
kp <- data.frame(x = xs,
                 or = approx(pr$x, pr$yhat, xout = xs)$y,
                 lo = approx(pr$x, pr$lower, xout = xs)$y,
                 hi = approx(pr$x, pr$upper, xout = xs)$y)
kp$label <- sprintf("%.2f (%.2f-%.2f)", kp$or, kp$lo, kp$hi)
write.csv(kp, file.path(OUT, "tables", "rcs_key_points.csv"), row.names = FALSE)
write.csv(data.frame(knots = paste(round(kn, 2), collapse = "; "),
                     p_overall = round(P_OV, 3), p_nonlinear = round(P_NL, 3)),
          file.path(OUT, "tables", "rcs_r_summary.csv"), row.names = FALSE)

hist_df <- data.frame(x = der$burden_pct)
p_top <- ggplot(pr, aes(x = x, y = yhat)) +
  geom_ribbon(aes(ymin = lower, ymax = upper), fill = "#2C6E9B", alpha = 0.18) +
  geom_line(linewidth = 0.9, colour = "#1F4E6E") +
  geom_hline(yintercept = 1, linetype = "dashed", linewidth = 0.4, colour = "grey35") +
  scale_x_continuous(limits = c(0, 45), expand = expansion(mult = c(0, 0.02))) +
  scale_y_continuous(limits = c(0.4, 4.4), breaks = seq(0.5, 4, 0.5)) +
  labs(x = NULL, y = "Adjusted odds ratio for AKI") +
  annotate("text", x = 44, y = 3.9, label = sprintf("P for non-linearity = %.2f", P_NL),
           hjust = 1, size = 3.2, colour = "grey20") +
  theme(axis.text.x = element_blank(), axis.ticks.x = element_blank())

p_bot <- ggplot(hist_df, aes(x = x)) +
  geom_histogram(aes(y = after_stat(density)), binwidth = 1, fill = "grey72",
                 colour = "white", linewidth = 0.15) +
  scale_x_continuous(limits = c(0, 45), expand = expansion(mult = c(0, 0.02))) +
  scale_y_continuous(expand = expansion(mult = c(0, 0.05))) +
  labs(x = "Hypotension burden (% of anaesthesia duration with MAP <65 mmHg)", y = "Density") +
  theme(axis.title.y = element_text(size = 8), axis.text.y = element_blank(),
        axis.ticks.y = element_blank(), panel.grid.major.y = element_blank())

p2 <- p_top / p_bot + plot_layout(heights = c(4, 1.1))
ggsave(file.path(FIG, "Fig2_rcs.png"), p2, width = 180, height = 150, units = "mm", dpi = 300)
cat("Fig2 done\n")

# ------------------------------------------------------------------ Fig 3 ROC
roc_all <- bind_rows(lapply(names(val), function(nm) {
  d <- val[[nm]]
  cbind(roc_pts(d$aki, d$p), cohort = nm)
}))
roc_all$cohort <- factor(roc_all$cohort, levels = names(val))
auc_map <- sapply(names(val), function(nm) auc_r(val[[nm]]$aki, val[[nm]]$p))
cols <- c("MOVER, colorectal" = "#1F4E6E", "MOVER, upper GI" = "#C0504D",
          "INSPIRE, upper GI" = "#4F8A5B")
labs <- setNames(sprintf("%s (AUC %.3f)", names(cols), auc_map[names(cols)]), names(cols))
minus <- intToUtf8(8722)

p3 <- ggplot(roc_all, aes(fpr, tpr, colour = cohort)) +
  geom_abline(slope = 1, intercept = 0, linetype = "dashed", linewidth = 0.4, colour = "grey45") +
  geom_step(linewidth = 0.85) +
  scale_colour_manual(values = cols, labels = labs) +
  scale_x_continuous(limits = c(0, 1), expand = expansion(mult = 0.01)) +
  scale_y_continuous(limits = c(0, 1), expand = expansion(mult = 0.01)) +
  coord_equal() +
  labs(x = paste0("1 ", minus, " specificity"), y = "Sensitivity", colour = NULL) +
  theme(legend.position = c(0.98, 0.02), legend.justification = c(1, 0),
        legend.background = element_rect(fill = alpha("white", 0.85), colour = NA),
        legend.text = element_text(size = 8.5), legend.key.height = unit(0.9, "lines"))
ggsave(file.path(FIG, "Fig3_roc.png"), p3, width = 120, height = 125, units = "mm", dpi = 300)
cat("Fig3 done\n")

# ------------------------------------------------------------------ Fig 4 calibration
cal_df <- bind_rows(lapply(names(val), function(nm) {
  d <- val[[nm]]
  d$grp <- cut(d$p, breaks = unique(quantile(d$p, probs = seq(0, 1, 1 / 8))),
               include.lowest = TRUE, labels = FALSE)
  d %>% group_by(grp) %>%
    summarise(pred = mean(p), obs = mean(aki), n = n(), .groups = "drop") %>%
    rowwise() %>%
    mutate(lo = wilson(round(obs * n), n)["lo"], hi = wilson(round(obs * n), n)["hi"]) %>%
    ungroup() %>% mutate(cohort = nm)
}))
cal_lab <- bind_rows(lapply(names(val), function(nm) {
  d <- val[[nm]]
  oe <- sum(d$aki) / sum(d$p)
  sl <- coef(glm(d$aki ~ log(d$p / (1 - d$p)), family = binomial))[2]
  data.frame(cohort = nm, lab = sprintf("O:E %.2f   slope %.2f", oe, sl))
}))
cal_df$cohort <- factor(cal_df$cohort, levels = names(val))
cal_lab$cohort <- factor(cal_lab$cohort, levels = names(val))

p4 <- ggplot(cal_df, aes(pred, obs)) +
  geom_abline(slope = 1, intercept = 0, linetype = "dashed", linewidth = 0.4, colour = "grey45") +
  geom_errorbar(aes(ymin = lo, ymax = hi), width = 0.006, colour = "grey35", linewidth = 0.4) +
  geom_point(size = 2, colour = "#1F4E6E") +
  geom_line(linewidth = 0.5, colour = "#1F4E6E", alpha = 0.7) +
  geom_text(data = cal_lab, aes(x = -Inf, y = Inf, label = lab), inherit.aes = FALSE,
            hjust = -0.05, vjust = 1.4, size = 2.9, colour = "grey20") +
  facet_wrap(~cohort, nrow = 1, scales = "free") +
  scale_x_continuous(labels = percent_format(accuracy = 1)) +
  scale_y_continuous(labels = percent_format(accuracy = 1), breaks = seq(0, 0.6, 0.1)) +
  labs(x = "Predicted risk of AKI", y = "Observed proportion with AKI")
ggsave(file.path(FIG, "Fig4_calibration.png"), p4, width = 180, height = 78, units = "mm", dpi = 300)
cat("Fig4 done\n")

# ------------------------------------------------------------------ Fig S1 dose-response
s1 <- der %>% group_by(cat) %>%
  summarise(n = n(), k = sum(aki), .groups = "drop") %>%
  rowwise() %>%
  mutate(p = k / n, lo = wilson(k, n)["lo"], hi = wilson(k, n)["hi"],
         lab = sprintf("%d/%d", k, n)) %>% ungroup()

pS1 <- ggplot(s1, aes(cat, p)) +
  geom_col(fill = "grey80", colour = "grey40", linewidth = 0.3, width = 0.6) +
  geom_errorbar(aes(ymin = lo, ymax = hi), width = 0.14, linewidth = 0.45) +
  geom_text(aes(label = lab, y = hi), vjust = -0.6, size = 3) +
  scale_y_continuous(labels = percent_format(accuracy = 1), breaks = seq(0, 0.12, 0.02),
                     limits = c(0, 0.125), expand = expansion(mult = c(0, 0.02))) +
  scale_x_discrete(labels = c("0%", paste0("0", dash, "5%"), paste0("5", dash, "10%"), ">10%")) +
  labs(x = "Hypotension burden (% of anaesthesia duration with MAP <65 mmHg)",
       y = "Postoperative AKI") +
  annotate("text", x = 0.55, y = 0.122, label = "P for trend = 0.002", hjust = 0, size = 3.2)
ggsave(file.path(FIG, "FigS1_dose_response.png"), pS1, width = 140, height = 95, units = "mm", dpi = 300)
cat("FigS1 done\n")

# ------------------------------------------------------------------ Fig S2 forest
s3 <- suppressWarnings(read_csv(file.path(OUT, "tables_en", "Table3_subgroups.csv"),
                                show_col_types = FALSE))
ci_num <- strsplit(trimws(gsub("[^0-9.]+", " ", s3$`95% CI`)), "\\s+")
s3 <- s3 %>% mutate(lo = as.numeric(sapply(ci_num, `[`, 1)),
                    hi = as.numeric(sapply(ci_num, `[`, 2)),
                    OR = as.numeric(OR)) %>%
  mutate(Subgroup = factor(Subgroup, levels = rev(unique(Subgroup))),
         row = paste0(Subgroup, ": ", Level))

dash <- intToUtf8(8211)
s3$row <- factor(s3$row, levels = rev(unique(s3$row)))
s3$lab <- sprintf("%.2f (%.2f%s%.2f)", s3$OR, s3$lo, dash, s3$hi)
pi_df <- s3 %>% group_by(Subgroup) %>% slice(1) %>% ungroup() %>%
  mutate(plab = ifelse(as.numeric(`P for interaction`) < 0.001, "<0.001",
                       sprintf("%.2f", as.numeric(`P for interaction`))))
top_y <- nrow(s3) + 0.9

pS2 <- ggplot(s3, aes(x = OR, y = row)) +
  geom_vline(xintercept = 1, linetype = "dashed", linewidth = 0.4, colour = "grey45") +
  geom_errorbar(aes(xmin = lo, xmax = hi), width = 0.18, linewidth = 0.45) +
  geom_point(size = 2, colour = "#1F4E6E") +
  geom_text(aes(x = hi, label = lab), hjust = -0.12, size = 2.7) +
  geom_text(data = pi_df, aes(x = 5, y = row, label = plab), inherit.aes = FALSE,
            hjust = 0, size = 2.7, colour = "grey20") +
  annotate("text", x = 5, y = top_y, label = "P for interaction", hjust = 0, vjust = 0,
           size = 2.7, fontface = "bold", colour = "grey20") +
  scale_x_log10(breaks = c(0.6, 0.8, 1, 1.5, 2), labels = c("0.6", "0.8", "1.0", "1.5", "2.0"),
                limits = c(0.6, 12)) +
  scale_y_discrete(expand = expansion(add = c(0.6, 1.4))) +
  labs(x = "Adjusted odds ratio per 10% increase in burden (log scale)", y = NULL) +
  theme(panel.grid.major.y = element_blank())
ggsave(file.path(FIG, "FigS2_forest.png"), pS2, width = 170, height = 135, units = "mm", dpi = 300)
cat("FigS2 done\n")

# ------------------------------------------------------------------ Fig S3 DCA
dca_df <- function(y, p, nm) {
  th <- seq(0.01, 0.30, by = 0.01)
  n <- length(y); prev <- mean(y)
  nb <- sapply(th, function(t) {
    tp <- sum(p >= t & y == 1); fp <- sum(p >= t & y == 0)
    tp / n - fp / n * (t / (1 - t))
  })
  rbind(data.frame(th = th, nb = nb, what = "Model", cohort = nm),
        data.frame(th = th, nb = prev - (1 - prev) * (th / (1 - th)), what = "Treat all", cohort = nm),
        data.frame(th = th, nb = 0, what = "Treat none", cohort = nm))
}
dca_all <- bind_rows(lapply(names(val), function(nm) dca_df(val[[nm]]$aki, val[[nm]]$p, nm)))
dca_all$cohort <- factor(dca_all$cohort, levels = names(val))

pS3 <- ggplot(dca_all, aes(th, nb, linetype = what, colour = what)) +
  geom_line(linewidth = 0.7) +
  facet_wrap(~cohort, nrow = 1, scales = "free") +
  scale_linetype_manual(values = c("Model" = "solid", "Treat all" = "dashed", "Treat none" = "dotted")) +
  scale_colour_manual(values = c("Model" = "#1F4E6E", "Treat all" = "grey35", "Treat none" = "grey55")) +
  scale_x_continuous(labels = percent_format(accuracy = 1)) +
  labs(x = "Threshold probability", y = "Net benefit", linetype = NULL, colour = NULL) +
  theme(legend.position = "bottom")
ggsave(file.path(FIG, "FigS3_dca.png"), pS3, width = 180, height = 80, units = "mm", dpi = 300)
cat("FigS3 done\n")

# ------------------------------------------------------------------ Fig S4 distribution
dist_df <- bind_rows(
  data.frame(x = pmin(der$burden_pct, 60), cohort = "Derivation (INSPIRE, colorectal)"),
  data.frame(x = pmin(mover_crc$burden_pct, 60), cohort = "Validation (MOVER, colorectal)")
)
pS4 <- ggplot(dist_df, aes(x = x, fill = cohort, colour = cohort)) +
  geom_histogram(aes(y = after_stat(density * 2 * 100)), position = "identity", binwidth = 2,
                 alpha = 0.45, linewidth = 0.4) +
  scale_fill_manual(values = c("#1F4E6E", "#C0504D")) +
  scale_colour_manual(values = c("#1F4E6E", "#C0504D")) +
  labs(x = "Hypotension burden (%), truncated at 60%",
       y = "Patients per 2% bin (%)", fill = NULL, colour = NULL) +
  theme(legend.position = c(0.98, 0.95), legend.justification = c(1, 1),
        legend.background = element_rect(fill = alpha("white", 0.85), colour = NA),
        legend.text = element_text(size = 8.5))
ggsave(file.path(FIG, "FigS4_distribution.png"), pS4, width = 150, height = 95, units = "mm", dpi = 300)
cat("FigS4 done\n")

cat("\nAll R figures written to", FIG, "\n")
