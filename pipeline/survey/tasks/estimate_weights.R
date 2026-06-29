# Per-(item, group) design-based statistics for the survey task answer keys.
# All the statistics live here (one auditable script); Python only prepares the
# long table, re-checks the results, and freezes them (TASK_PLAYBOOK Sec 2.4).
#
# in:  long CSV (item, group [2 levels], weight, stratum, y)
#        y = 0/1 for a prevalence item, or a numeric score for a mean item.
# out: CSV (item, group, n, n_pos, pct, design_pct, neff, fisher_p, wald_p, freqweight_p)
#        pct/design_pct are percentages for a 0/1 item, the raw/weighted mean for a score item.
#
# scale (optional, default 1) multiplies every weight: the survey-design p (wald_p) and the
# exact p (fisher_p) are INVARIANT; the frequency-weight chi-square (freqweight_p) collapses
# toward 0 — proving that our tests are design-based, not frequency-weighted.
#
# Usage:  Rscript estimate_weights.R <in.csv> <out.csv> [scale]

library(survey)
options(survey.lonely.psu = "adjust")            # a single-element stratum in a subset -> finite variance

args    <- commandArgs(trailingOnly = TRUE)
in_csv  <- args[1]
out_csv <- args[2]
scale   <- if (length(args) >= 3) as.numeric(args[3]) else 1.0

d        <- read.csv(in_csv)
d$weight <- d$weight * scale
d$group  <- factor(d$group)

# Stratified element design (ids = ~1); drop strata if a subset spans fewer than two.
design <- function(s) {
  if (length(unique(s$stratum)) > 1)
    svydesign(ids = ~1, strata = ~stratum, weights = ~weight, data = s)
  else
    svydesign(ids = ~1, weights = ~weight, data = s)
}

per_item <- function(it) {
  s       <- d[d$item == it, ]
  s$group <- droplevels(s$group)
  binary  <- all(s$y %in% c(0, 1))                # prevalence (0/1) vs mean (score) item
  des     <- design(s)
  dmean   <- svyby(~y, ~group, des, svymean)      # design-based group mean (svymean)

  fit    <- tryCatch(if (binary) svyglm(y ~ group, des, family = quasibinomial())
                     else        svyglm(y ~ group, des),
                     error = function(e) NULL)
  wald_p <- if (is.null(fit)) NA_real_ else coef(summary(fit))[2, "Pr(>|t|)"]

  yf           <- factor(s$y, levels = c(0, 1))   # exact + frequency-weight checks: binary items only
  fisher_p     <- if (binary) tryCatch(fisher.test(table(s$group, yf))$p.value,        error = function(e) NA_real_) else NA_real_
  freqweight_p <- if (binary) tryCatch(chisq.test(xtabs(weight ~ group + yf, data = s))$p.value, error = function(e) NA_real_) else NA_real_

  do.call(rbind, lapply(levels(s$group), function(g) {
    sg <- s[s$group == g, ]
    dm <- dmean[dmean$group == g, "y"]
    data.frame(item = it, group = g, n = nrow(sg),
               n_pos      = if (binary) sum(sg$y) else NA_integer_,
               pct        = round(if (binary) 100 * mean(sg$y) else mean(sg$y), 4),
               design_pct = round(if (binary) 100 * dm         else dm,         4),
               neff       = round(sum(sg$weight)^2 / sum(sg$weight^2), 4),
               fisher_p = fisher_p, wald_p = wald_p, freqweight_p = freqweight_p)
  }))
}

write.csv(do.call(rbind, lapply(unique(d$item), per_item)), out_csv, row.names = FALSE)
cat(sprintf("[R] survey %s: %d items -> %s\n",
            as.character(packageVersion("survey")), length(unique(d$item)), out_csv))
