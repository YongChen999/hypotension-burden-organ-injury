# 骨科 MINS 论文 Fig.2（双联）：AKI 与院内死亡的剂量-反应曲线
suppressPackageStartupMessages({library(ggplot2); library(scales); library(patchwork)})
OUT <- "output"; FIG <- file.path(OUT, "figures", "submission"); TAB <- file.path(OUT, "tables")
rcs <- read.csv(file.path(TAB, "organ_rcs_curve.csv"))
rcs <- rcs[!(rcs$db == "MOVER" & rcs$outcome == "death"), ]
rcs$db <- factor(rcs$db, c("INSPIRE", "MOVER"))
cat("aki rows:", sum(rcs$outcome == "aki"), " death rows:", sum(rcs$outcome == "death"), "\n")
cat("or range:", range(rcs$or), " lo min:", min(rcs$lo), " hi max:", max(rcs$hi), "\n")
th <- theme_bw(base_size = 10) + theme(panel.grid.minor = element_blank(),
                                        plot.title = element_text(size = 10, face = "bold"))
cols <- c(INSPIRE = "#1F4E6E", MOVER = "#C0504D")
labx <- "Hypotension burden\n(% of anaesthesia duration with MAP <65 mmHg)"

pA <- ggplot(rcs[rcs$outcome == "aki", ], aes(x, or, color = db)) +
  geom_hline(yintercept = 1, linetype = "dashed", linewidth = 0.4, colour = "grey50") +
  geom_ribbon(aes(ymin = lo, ymax = hi, fill = db), alpha = 0.15, colour = NA) +
  geom_line(linewidth = 0.9) +
  scale_color_manual(values = cols) + scale_fill_manual(values = cols) +
  scale_x_continuous(limits = c(0, 45)) +
  scale_y_continuous(trans = "log", limits = c(0.4, 3.0), breaks = c(0.5, 0.75, 1, 1.5, 2, 3)) +
  labs(x = NULL, y = "Adjusted odds ratio (log scale)", title = "A. Acute kidney injury") +
  th + theme(legend.position = "top", legend.title = element_blank())

pB <- ggplot(rcs[rcs$outcome == "death", ], aes(x, or, color = db)) +
  geom_hline(yintercept = 1, linetype = "dashed", linewidth = 0.4, colour = "grey50") +
  geom_ribbon(aes(ymin = lo, ymax = hi, fill = db), alpha = 0.15, colour = NA) +
  geom_line(linewidth = 0.9) +
  scale_color_manual(values = cols) + scale_fill_manual(values = cols) +
  scale_x_continuous(limits = c(0, 45)) +
  scale_y_continuous(trans = "log", limits = c(0.4, 3.0), breaks = c(0.5, 0.75, 1, 1.5, 2, 3)) +
  labs(x = labx, y = "Adjusted odds ratio (log scale)", title = "B. In-hospital death") +
  annotate("text", x = 20, y = 2.45, label = "MOVER omitted:\n20 deaths", size = 3, hjust = 0.5,
           colour = "grey40") +
  th + theme(legend.position = "none")

p <- pA + pB
ggsave(file.path(FIG, "MINS_Fig2_organ_rcs.png"), p, width = 180, height = 105, units = "mm", dpi = 300)
cat("organ fig done\n")
