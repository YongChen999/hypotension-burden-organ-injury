# 61_r_fig1_flow.R
# MINS 论文 Fig. 1 队列流程图 —— 43_mins_fig1.py 的 R/grid 移植版（2026-11-13）
# 文字口径：底部结局框为完整协变量模型队列，不要求肌钙蛋白监测；
# AKI 另需可评价的术前/术后肌酐。排除框内 BMI 插补行是保留而非排除原因。
suppressPackageStartupMessages(library(grid))

OUT <- "output"; FIG <- file.path(OUT, "figures", "submission")
dir.create(FIG, recursive = TRUE, showWarnings = FALSE)

BLUE <- "#1f5c8b"; AMBER <- "#8a6d3b"; GREY <- "#7a7a7a"
emdash <- intToUtf8(8212); endash <- intToUtf8(8211); bullet <- intToUtf8(8226); geq <- intToUtf8(8805)

LX <- 0.0; RX <- 5.55; W <- 4.75
MON_W <- 2.90; NOT_X <- 3.05; NOT_W <- 1.70

box <- function(x, y, w, h, text, fc = "#eef3f8", ec = BLUE, fs = 6.2, dashed = FALSE) {
  grid.roundrect(x = unit(x, "native"), y = unit(y, "native"),
                 width = unit(w, "native"), height = unit(h, "native"),
                 just = c("left", "bottom"), r = unit(1.6, "mm"),
                 gp = gpar(fill = fc, col = ec, lwd = 0.8,
                           lty = if (dashed) "dashed" else "solid"))
  grid.text(text, x = unit(x + w / 2, "native"), y = unit(y + h / 2, "native"),
            gp = gpar(fontsize = fs, col = "#111111", lineheight = 1.25))
}

varrow <- function(x, y1, y2, dashed = FALSE) {
  grid.segments(unit(x, "native"), unit(y1, "native"), unit(x, "native"), unit(y2, "native"),
                arrow = arrow(type = "closed", length = unit(1.4, "mm")),
                gp = gpar(col = if (dashed) GREY else "#555555", lwd = 0.8,
                          lty = if (dashed) "dashed" else "solid"))
}

elbow <- function(x0, y0, xm, y1, x1) {
  grid.segments(unit(c(x0, xm), "native"), unit(c(y0, y0), "native"),
                unit(c(xm, xm), "native"), unit(c(y0, y1), "native"),
                gp = gpar(col = "#555555", lwd = 0.9))
  grid.segments(unit(xm, "native"), unit(y1, "native"), unit(x1, "native"), unit(y1, "native"),
                arrow = arrow(type = "closed", length = unit(1.5, "mm")),
                gp = gpar(col = "#555555", lwd = 0.9))
}

column_ <- function(cx, top_text, mon_text, excl_text, anal_text, notmon_text, full_text) {
  box(cx, 7.28, W, 0.80, top_text, "#dbe8f2", BLUE, fs = 6.6)
  box(cx, 6.02, MON_W, 0.95, mon_text, "#eef3f8", BLUE, fs = 6.0)
  box(cx, 4.72, MON_W, 1.02, excl_text, "#f7f7f7", GREY, fs = 5.6)
  box(cx, 3.60, MON_W, 0.88, anal_text, "#dbe8f2", BLUE, fs = 6.2)
  grid.roundrect(x = unit(cx + NOT_X, "native"), y = unit(6.10, "native"),
                 width = unit(NOT_W, "native"), height = unit(0.80, "native"),
                 just = c("left", "bottom"), r = unit(1.3, "mm"),
                 gp = gpar(fill = "#f5f5f5", col = GREY, lwd = 0.7, lty = "dashed"))
  grid.text(notmon_text, x = unit(cx + NOT_X + NOT_W / 2, "native"), y = unit(6.50, "native"),
            gp = gpar(fontsize = 5.7, col = "#444444", lineheight = 1.2))
  varrow(cx + MON_W / 2, 7.26, 7.00)
  varrow(cx + MON_W / 2, 6.00, 5.76)
  varrow(cx + MON_W / 2, 4.70, 4.50)
  varrow(cx + NOT_X + NOT_W / 2, 7.26, 6.92, dashed = TRUE)
  if (cx == LX) elbow(cx, 7.68, -0.55, 2.72, cx) else elbow(cx + W, 7.68, cx + W + 0.55, 2.72, cx + W)
  box(cx, 2.28, W, 0.88, full_text, "#f4ece3", AMBER, fs = 6.0)
}

png(file.path(FIG, "MINS_Fig1_flow.png"), width = 7.4, height = 5.9,
    units = "in", res = 300, type = "cairo")
grid.newpage()
# y 下限留到 1.20，给 5 行底注留出空间（grid 不画视口外内容）
pushViewport(viewport(xscale = c(-1.15, 11.70), yscale = c(1.20, 8.45)))

grid.text("Derivation cohort", x = unit(LX, "native"), y = unit(8.30, "native"),
          just = c("left", "center"), gp = gpar(fontsize = 7.8, fontface = "bold"))
grid.text("External validation cohort", x = unit(RX, "native"), y = unit(8.30, "native"),
          just = c("left", "center"), gp = gpar(fontsize = 7.8, fontface = "bold"))

# ---------------- INSPIRE ----------------
column_(LX,
  paste0("INSPIRE registry (single centre, Seoul)\n",
         "Orthopaedic operations (department\n",
         "= Orthopedic Surgery): n = 10,002"),
  paste0("Postoperative troponin\n",
         "monitored (", geq, "1 cTnI, 0", endash, "72 h\n",
         "after surgery)\nn = 468 (4.7%)"),
  paste0("Excluded (n = 34):\n",
         bullet, " missing ASA class (n = 33)\n",
         bullet, " missing baseline creatinine (n = 1)\n",
         "(retained: BMI imputed, n = 12)"),
  paste0("Primary MINS analysis\n",
         "n = 434 monitored patients\n",
         "MINS 155 (35.7%)"),
  "Not monitored\nn = 9,534 (95.3%)\nMINS not\nascertainable",
  paste0("Secondary-outcome model cohorts\n",
         "(complete covariates; no troponin required):\n",
         "AKI n = 8,306, 317 events (3.8%);\n",
         "in-hospital death n = 9,491, 94 events (1.0%)"))

# ---------------- MOVER ----------------
column_(RX,
  paste0("MOVER registry (single centre, UC Irvine)\n",
         "Orthopaedic operations\n",
         "(184 OP procedure codes): n = 6,940"),
  paste0("Postoperative troponin\n",
         "monitored (platform MINS\n",
         "flag; peak hs-TnI)\nn = 230 (3.3%)"),
  paste0("Excluded (n = 4):\n",
         bullet, " no intraoperative MAP record\n",
         "   (burden unavailable)\n",
         "(retained: BMI imputed, n = 21)"),
  paste0("Primary MINS analysis\n",
         "n = 226 monitored patients\n",
         "MINS 102 (45.1%)"),
  "Not monitored\nn = 6,710 (96.7%)\nMINS not\nascertainable",
  paste0("Secondary-outcome model cohorts\n",
         "(complete covariates; no troponin required):\n",
         "AKI n = 5,351, 780 events (14.6%);\n",
         "in-hospital death n = 6,199, 20 events (0.3%)"))

grid.text(paste0("MINS = myocardial injury after noncardiac surgery (INSPIRE: peak cTnI >0.026 ng/mL within 72 h;\n",
                 "MOVER: platform-derived MINS flag). AKI = KDIGO stage 1+ within 7 days. MAP = mean arterial pressure.\n",
                 "Troponin was measured at the discretion of the treating team, not per protocol; the primary analysis is\n",
                 "restricted to the monitored branch. Secondary-outcome model samples require complete covariates but not\n",
                 "troponin monitoring; AKI additionally requires evaluable pre- and postoperative creatinine."),
          x = unit(LX, "native"), y = unit(2.02, "native"), just = c("left", "top"),
          gp = gpar(fontsize = 5.6, col = "#444444", lineheight = 1.3))

dev.off()
cat("-> MINS_Fig1_flow.png (R/grid port)\n")
