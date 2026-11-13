# Abdominal cohort: emergency-by-burden interaction tests
# Rebuild from platform raw exports (see 57_abdo_rebuild.py).
# Models follow the pre-specified M3 specification:
#   mins/aki ~ burden10 + age + male + bmi + open_surgery + op_h + asa(factor)
#              + scr_base(median-imputed) + dm + htn + cad [+ emergency + burden10:emergency]

d <- read.csv("output/abdo_full_cohort.csv", fileEncoding = "UTF-8-BOM")
cat("Cohort n =", nrow(d), "\n")
cat("Monitored =", sum(d$monitored == 1),
    "| MINS =", sum(d$mins, na.rm = TRUE), "\n")
cat("Elective monitored =", sum(d$monitored == 1 & d$emergency == 0),
    "| MINS =", sum(d$mins[d$emergency == 0], na.rm = TRUE), "\n")
cat("Emergency monitored =", sum(d$monitored == 1 & d$emergency == 1),
    "| MINS =", sum(d$mins[d$emergency == 1], na.rm = TRUE), "\n")
cat("AKI =", sum(d$aki, na.rm = TRUE), "of", sum(!is.na(d$aki)), "\n\n")

prep <- function(x) {
  x$asa_f <- factor(x$asa)
  x$scr_base[is.na(x$scr_base)] <- median(x$scr_base, na.rm = TRUE)
  x
}

fmt <- function(m, lab) {
  s <- summary(m)
  b <- s$coefficients["burden10", ]
  ci <- suppressMessages(confint.default(m)["burden10", ])
  cat(sprintf("%-22s OR=%.2f (%.2f-%.2f)  P=%.3g\n", lab,
              exp(b[1]), exp(ci[1]), exp(ci[2]), b[4]))
}

covars_main <- "age + male + bmi + open_surgery + op_h + asa_f + scr_base + dm + htn + cad"
covars_emer <- paste(covars_main, "+ emergency")

# ---------------- MINS interaction (monitored) ----------------
cat("=== MINS (monitored population) ===\n")
mon <- prep(subset(d, monitored == 1 & !is.na(mins)))
f_main <- as.formula(paste("mins ~ burden10 +", covars_emer))
f_int  <- as.formula(paste("mins ~ burden10 * emergency +", covars_main))
m0 <- glm(f_main, data = mon, family = binomial)
m1 <- glm(f_int,  data = mon, family = binomial)
fmt(m0, "Overall (no interx)")
fmt(m1, "With interx term")
lt <- anova(m0, m1, test = "LRT")
cat(sprintf("P interaction (LRT) = %.4g\n\n", lt$`Pr(>Chi)`[2]))

cat("Stratified:\n")
e0 <- prep(subset(mon, emergency == 0)); e1 <- prep(subset(mon, emergency == 1))
fmt(glm(as.formula(paste("mins ~ burden10 +", covars_main)), data = e0, family = binomial),
    "  Elective")
fmt(glm(as.formula(paste("mins ~ burden10 +", covars_main)), data = e1, family = binomial),
    "  Emergency")

# crude and emergency-only check
fmt(glm(mins ~ burden10 * emergency, data = mon, family = binomial), "Crude w/ interx")

# ---------------- AKI interaction (full cohort) ----------------
cat("\n=== AKI (full cohort incl emergency) ===\n")
aki <- prep(subset(d, !is.na(aki) & !is.na(burden10)))
a0 <- glm(as.formula(paste("aki ~ burden10 +", covars_emer)), data = aki, family = binomial)
a1 <- glm(as.formula(paste("aki ~ burden10 * emergency +", covars_main)), data = aki, family = binomial)
fmt(a0, "Overall (no interx)")
fmt(a1, "With interx term")
lt2 <- anova(a0, a1, test = "LRT")
cat(sprintf("P interaction (LRT) = %.4g\n\n", lt2$`Pr(>Chi)`[2]))
ae0 <- prep(subset(aki, emergency == 0)); ae1 <- prep(subset(aki, emergency == 1))
fmt(glm(as.formula(paste("aki ~ burden10 +", covars_main)), data = ae0, family = binomial),
    "  Elective")
fmt(glm(as.formula(paste("aki ~ burden10 +", covars_main)), data = ae1, family = binomial),
    "  Emergency")

# ---------------- replicate the archived elective M3 ----------------
cat("\n=== Replication: elective-only M3 (target OR 1.03, 0.99-1.07) ===\n")
fmt(glm(as.formula(paste("mins ~ burden10 +", covars_main)), data = e0, family = binomial),
    "Elective M3")
cat("\n=== Replication: elective-only AKI (target OR 1.22, 1.18-1.26) ===\n")
fmt(glm(as.formula(paste("aki ~ burden10 +", covars_main)), data = ae0, family = binomial),
    "Elective AKI M3")

# ---------------- sensitivity: drop op_h ----------------
cat("\n=== Sensitivity: M3 without op_h (archive M2b 1.06) ===\n")
cov_noh <- "age + male + bmi + open_surgery + asa_f + scr_base + dm + htn + cad"
fmt(glm(as.formula(paste("mins ~ burden10 + emergency +", cov_noh)), data = mon, family = binomial),
    "Overall no-op_h")
