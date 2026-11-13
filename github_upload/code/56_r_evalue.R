# 56_r_evalue.R — B2: E-value（未测量混杂所需最小关联强度）
# OR->RR 转换用 Zhang-Yu（基线风险 p0 取最低暴露组即 0 负荷组的观察事件率）
options(stringsAsFactors = FALSE)
OUT <- "output"

or_to_rr <- function(or, p0) or / ((1 - p0) + p0 * or)
evalue <- function(rr) {
  if (rr < 1) rr <- 1 / rr
  rr + sqrt(rr * (rr - 1))
}

# ---- p0：0 负荷组事件率 ----
d <- read.csv(file.path(OUT, "inspire_ortho_analytic.csv"), fileEncoding = "UTF-8-BOM")
a <- d[d$monitored == 1 & !is.na(d$ane_h) & d$ane_h > 0 & !is.na(d$below65) & d$below65 == 0, ]
p0_mins_i <- mean(a$mins)
z <- d[!is.na(d$burden_pct) & d$burden_pct == 0, ]
p0_aki_i  <- mean(z$aki[!is.na(z$aki)])
p0_dth_i  <- mean(z$death)

d <- read.csv(file.path(OUT, "mover_ortho_analytic.csv"), fileEncoding = "UTF-8-BOM")
a <- d[d$monitored == 1 & !is.na(d$ane_h) & d$ane_h > 0 & !is.na(d$below65) & d$below65 == 0, ]
p0_mins_m <- mean(a$mins)
z <- d[!is.na(d$burden_pct) & d$burden_pct == 0, ]
p0_aki_m  <- mean(z$aki[!is.na(z$aki)])
p0_dth_m  <- mean(z$death)

cat(sprintf("p0 (zero-burden event rate): INSPIRE MINS=%.3f AKI=%.3f death=%.3f | MOVER MINS=%.3f AKI=%.3f death=%.3f\n",
            p0_mins_i, p0_aki_i, p0_dth_i, p0_mins_m, p0_aki_m, p0_dth_m))

est <- list(
  list(lbl = "INSPIRE MINS (null)",  or = 1.02, lo = 0.91, hi = 1.15, p0 = p0_mins_i),
  list(lbl = "MOVER MINS (borderline)", or = 1.33, lo = 0.97, hi = 1.83, p0 = p0_mins_m),
  list(lbl = "INSPIRE AKI",  or = 1.09, lo = 1.02, hi = 1.17, p0 = p0_aki_i),
  list(lbl = "MOVER AKI",    or = 1.08, lo = 0.98, hi = 1.20, p0 = p0_aki_m),
  list(lbl = "INSPIRE death", or = 1.18, lo = 1.05, hi = 1.32, p0 = p0_dth_i),
  list(lbl = "MOVER death",   or = 1.65, lo = 1.20, hi = 2.26, p0 = p0_dth_m))

cat(sprintf("%-26s %8s %10s %10s %10s\n", "estimate", "OR", "RR", "E(est)", "E(CI-far)"))
for (e in est) {
  rr <- or_to_rr(e$or, e$p0)
  # 离无效值最远的 CI 界（解释估计所需的 E 值）
  far <- if (abs(e$hi - 1) >= abs(e$lo - 1)) e$hi else e$lo
  cat(sprintf("%-26s %8.2f %10.3f %10.2f %10.2f\n", e$lbl, e$or, rr, evalue(rr), evalue(or_to_rr(far, e$p0))))
}
