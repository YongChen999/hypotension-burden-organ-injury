# 骨科 MINS 论文图（R / ggplot2，300 dpi）
# 2026-11-13 修订：Fig S4 修复 cat 因子水平不匹配（曾致全部 NA 塌柱）；
# 输出文件名对齐最终图号（FigS3_rcs / FigS4_dose / Fig3_validation）；
# Fig S1 改并排柱避免半透明叠加误读；Fig 1 改由 61_r_fig1_flow.R（grid 移植）生成。
suppressPackageStartupMessages({library(ggplot2); library(scales); library(jsonlite); library(patchwork)})
OUT <- "output"; FIG <- file.path(OUT, "figures", "submission"); TAB <- file.path(OUT, "tables")
dir.create(FIG, recursive = TRUE, showWarnings = FALSE)
th <- theme_bw(base_size = 10) + theme(panel.grid.minor = element_blank(),
                                        plot.title = element_text(size = 10, face = "bold"))
dash <- intToUtf8(8211); minus <- intToUtf8(8722)
# Unicode 安全的 PNG 设备（†、破折号）
pngdev <- if (requireNamespace("ragg", quietly = TRUE)) ragg::agg_png else
          if (capabilities("cairo")) cairo_png else "png"

# ---------- Fig 2: RCS ----------
rcs <- read.csv(file.path(TAB, "mins_rcs_curve.csv"))
mj <- jsonlite::fromJSON(file.path(OUT, "model_mins.json"))
vm <- jsonlite::fromJSON(file.path(OUT, "validation_metrics.json"))
p2 <- ggplot(rcs, aes(x, or)) +
  geom_hline(yintercept = 1, linetype = "dashed", linewidth = 0.4, colour = "grey45") +
  geom_ribbon(aes(ymin = lo, ymax = hi), fill = "#1F4E6E", alpha = 0.15) +
  geom_line(linewidth = 0.9, colour = "#1F4E6E") +
  scale_x_continuous(limits = c(0, 45), expand = expansion(mult = c(0, 0.02))) +
  scale_y_continuous(trans = "log", limits = c(0.45, 2.8), breaks = c(0.5, 0.75, 1, 1.5, 2)) +
  annotate("text", x = 44, y = 2.55, hjust = 1, size = 3.0,
           label = sprintf("P for non-linearity = %.2f\n(reference: 0%% burden)", mj$p_nl)) +
  labs(x = "Hypotension burden (% of anaesthesia duration with MAP <65 mmHg)",
       y = "Adjusted odds ratio for MINS (log scale)") + th
ggsave(file.path(FIG, "MINS_FigS3_rcs.png"), p2, width = 180, height = 120, units = "mm", dpi = 300, device = pngdev)

# ---------- Fig S4: 分类别 MINS 率（两库） ----------
d3 <- read.csv(file.path(TAB, "mins_fig3_data.csv"))
d3$cat <- factor(d3$cat, levels = c("0", "0-5", "5-10", ">10"),
                 labels = c("0%", paste0("0", dash, "5%"), paste0("5", dash, "10%"), ">10%"))
p3 <- ggplot(d3, aes(cat, rate, fill = cohort)) +
  geom_col(position = position_dodge(0.8), width = 0.72, colour = "white", linewidth = 0.2) +
  geom_errorbar(aes(ymin = lo, ymax = hi), position = position_dodge(0.8), width = 0.25, linewidth = 0.45) +
  geom_text(aes(label = sprintf("%d/%d", ev, n), y = hi + 0.03), position = position_dodge(0.8),
            vjust = 0.4, size = 2.6) +
  scale_fill_manual(values = c(INSPIRE = "#1F4E6E", MOVER = "#C0504D")) +
  scale_y_continuous(labels = percent_format(accuracy = 1), limits = c(0, 0.72)) +
  labs(x = "Intraoperative hypotension burden", y = "MINS among troponin-monitored patients",
       fill = NULL) + th + theme(legend.position = "top")
ggsave(file.path(FIG, "MINS_FigS4_dose.png"), p3, width = 180, height = 120, units = "mm", dpi = 300, device = pngdev)

# ---------- Fig 4: 冻结模型在 MOVER 的 ROC + 校准 ----------
vp <- read.csv(file.path(TAB, "mins_val_pred.csv"))
# ROC 必须按预测概率**降序**累积：阈值从高到低，TPR/FPR 才由 (0,0) 走向 (1,1)。
# 之前用升序，曲线整体落在对角线下方，与 AUC 0.682 矛盾。
roc <- function(y, p) { o <- order(p, decreasing = TRUE); y <- y[o]
  TPR <- cumsum(y)/sum(y); FPR <- cumsum(1-y)/sum(1-y)
  rbind(c(0,0), data.frame(fpr = FPR, tpr = TPR)) }
rr <- roc(vp$y, vp$p)
auc <- vm$auc_frozen
p4a <- ggplot(rr, aes(fpr, tpr)) + geom_step(linewidth = 0.85, colour = "#C0504D") +
  geom_abline(slope = 1, intercept = 0, linetype = "dashed", linewidth = 0.4, colour = "grey45") +
  coord_equal() + scale_x_continuous(limits = c(0,1), expand = c(0.01,0)) +
  scale_y_continuous(limits = c(0,1), expand = c(0.01,0)) +
  annotate("text", x = 0.98, y = 0.04, hjust = 1, size = 3.2,
           label = sprintf("AUC %.3f (%.2f%s%.2f)", auc, vm$auc_frozen_lo, dash, vm$auc_frozen_hi)) +
  labs(x = paste0("1 ", minus, " specificity"), y = "Sensitivity") + th
vp <- vp[order(vp$p), ]
# 十分位分组：已按 p 升序排列，必须按**位置**切成 10 个连续等长段。
# 错误的写法是 rep(1:10, length.out = n)：那是 1,2,...,10,1,2,... 的循环取模，
# 每组都横跨整个风险分布，导致 10 个校准点全部挤在均值附近（本研究曾出现此 bug）。
vp$g <- cut(seq_len(nrow(vp)), breaks = 10, labels = FALSE)
# 校准截距：与 41/45 号同法（logit(observed) ~ logit(predicted) 的截距）
.lp <- qlogis(pmin(pmax(vp$p, 1e-6), 1 - 1e-6))
.calreg <- glm(vp$y ~ .lp, family = binomial())
.cal_int <- unname(coef(.calreg)[1])
cal <- aggregate(cbind(p, y) ~ g, vp, mean)
cal <- cal[order(cal$p), ]
p4b <- ggplot(cal, aes(p, y)) +
  geom_abline(slope = 1, intercept = 0, linetype = "dashed", linewidth = 0.4, colour = "grey45") +
  geom_line(linewidth = 0.55, colour = "#C0504D", alpha = 0.65) +
  geom_point(size = 2.0, colour = "#C0504D") +
  annotate("text", x = 0.02, y = 0.97, hjust = 0, vjust = 1, size = 2.9,
           label = sprintf("O:E %.2f\ncalibration slope %.2f\nintercept %.2f",
                           vm$oe_frozen, vm$cal_slope_frozen, .cal_int)) +
  scale_x_continuous(labels = percent_format(accuracy = 1), limits = c(0, 1),
                     breaks = seq(0, 1, 0.2), expand = c(0.01, 0)) +
  scale_y_continuous(labels = percent_format(accuracy = 1), limits = c(0, 1),
                     breaks = seq(0, 1, 0.2), expand = c(0.01, 0)) +
  labs(x = "Predicted probability of MINS (frozen model)",
       y = "Observed MINS (deciles)") + th
p4 <- p4a + p4b + plot_annotation(tag_levels = "A")
ggsave(file.path(FIG, "MINS_Fig3_validation.png"), p4, width = 180, height = 95, units = "mm", dpi = 300, device = pngdev)

# ---------- Fig S1: 监测 vs 未监测的负荷分布 ----------
a <- read.csv(file.path(OUT, "inspire_ortho_analytic.csv"))
b <- read.csv(file.path(OUT, "mover_ortho_analytic.csv"))
a <- a[!is.na(a$burden_pct), ]; b <- b[!is.na(b$burden_pct), ]
# 截断到 60% 以下的最后一档（pmin 到 60 会落在 [60,65) 箱而出界被丢）
da <- rbind(data.frame(burden = pmin(a$burden_pct[a$monitored == 1], 59.9), who = "Monitored", db = "INSPIRE"),
            data.frame(burden = pmin(a$burden_pct[a$monitored == 0], 59.9), who = "Not monitored", db = "INSPIRE"),
            data.frame(burden = pmin(b$burden_pct[b$monitored == 1], 59.9), who = "Monitored", db = "MOVER"),
            data.frame(burden = pmin(b$burden_pct[b$monitored == 0], 59.9), who = "Not monitored", db = "MOVER"))
da$who <- factor(da$who, c("Monitored", "Not monitored"))
pS1 <- ggplot(da, aes(burden, fill = who)) +
  geom_histogram(aes(y = after_stat(density * 5 * 100)), binwidth = 5, boundary = 0,
                 position = position_dodge(), alpha = 0.85, colour = "white", linewidth = 0.15) +
  facet_wrap(~db, nrow = 1) +
  scale_fill_manual(values = c("#C0504D", "grey55")) +
  scale_x_continuous(limits = c(0, 60)) +
  scale_y_continuous(limits = c(0, 65)) +   # 零负荷柱最高达 63%，不能再用 32 截顶
  labs(x = "Hypotension burden (%), truncated at 60%", y = "Patients per 5% bin (% of group)", fill = NULL) +
  th + theme(legend.position = "top")
ggsave(file.path(FIG, "MINS_FigS1_selection.png"), pS1, width = 180, height = 100, units = "mm", dpi = 300, device = pngdev)

# ---------- Fig S2: 敏感性森林 ----------
# 注：fileEncoding 会转码到 GBK 丢 †，encoding 连接在 C locale 下读取失败；
# 改用原始字节读入、手工剥 BOM、标记 UTF-8 后解析
.forest_path <- file.path(TAB, "mins_forest.csv")
.forest_raw <- readBin(.forest_path, "raw", file.info(.forest_path)$size)
if (identical(.forest_raw[1:3], charToRaw("\xef\xbb\xbf"))) .forest_raw <- .forest_raw[-(1:3)]
.forest_txt <- rawToChar(.forest_raw); Encoding(.forest_txt) <- "UTF-8"
ts <- read.csv(text = .forest_txt, stringsAsFactors = FALSE)
ts$lab <- sprintf("%s  (n=%s, events=%s)", ts$analysis, ts$n, ts$ev)
ts <- ts[order(ts$or), ]
ts$lab <- factor(ts$lab, levels = ts$lab)
pS2 <- ggplot(ts, aes(or, lab)) +
  geom_vline(xintercept = 1, linetype = "dashed", linewidth = 0.4, colour = "grey45") +
  geom_errorbar(aes(xmin = lo, xmax = hi), width = 0.22, linewidth = 0.45, colour = "#1F4E6E") +
  geom_point(aes(colour = grepl("AKI|death", analysis)), size = 2.1) +
  scale_colour_manual(values = c("TRUE" = "#C0504D", "FALSE" = "#1F4E6E"), guide = "none") +
  geom_text(aes(x = 3.05, label = sprintf("%.2f (%.2f%s%.2f)", or, lo, dash, hi)),
            hjust = 0, size = 2.5, colour = "grey20") +
  scale_x_log10(limits = c(0.55, 5.6), breaks = c(0.6, 0.8, 1, 1.25, 1.6, 2.2)) +
  labs(x = "Adjusted OR per 10% burden (log scale)", y = NULL) +
  th + theme(axis.text.y = element_text(size = 6.6))
ggsave(file.path(FIG, "MINS_FigS2_sensitivity.png"), pS2, width = 180, height = 95, units = "mm", dpi = 300, device = pngdev)

cat("figures done\n")
