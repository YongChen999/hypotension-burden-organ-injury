# A1 feasibility check: c-statistic for "being monitored" (troponin), both cohorts
options(stringsAsFactors=FALSE)
base <- file.path(Sys.getenv("STUDY_ROOT", unset = getwd()), "output")
run_one <- function(path, has_emerg){
  d <- read.csv(path, fileEncoding="UTF-8-BOM")
  d$monitored <- as.integer(d$monitored)
  covs <- c("age","male","bmi","asa_class","dm","htn","chd","hf","ckd","ane_h")
  if (has_emerg) covs <- c(covs,"emergency")
  fml <- as.formula(paste("monitored ~", paste(covs, collapse=" + ")))
  cc <- d[stats::complete.cases(d[,c("monitored",covs)]),]
  m <- glm(fml, data=cc, family=binomial)
  p <- as.numeric(predict(m, type="response"))
  auc <- as.numeric(pROC::auc(cc$monitored, p))
  pct <- round(100*mean(cc$monitored),1)
  n <- nrow(cc); ev <- sum(cc$monitored)
  # death rate by monitored (A1 Table 3 numbers check)
  dr <- tapply(cc$death, cc$monitored, mean)
  cat(sprintf("n=%d monitored=%d (%.1f%%) | AUC=%.3f | death: unmon=%.1f%% mon=%.1f%%\n",
      n, ev, pct, auc, 100*dr["0"], 100*dr["1"]))
  invisible(auc)
}
cat("INSPIRE ortho: "); run_one(file.path(base,"inspire_ortho_analytic.csv"), TRUE)
cat("MOVER   ortho: "); run_one(file.path(base,"mover_ortho_analytic.csv"), FALSE)
