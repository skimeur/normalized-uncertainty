# The restricted route

Two parts of the paper rest on data that cannot be redistributed, and whose code is therefore not published here. This page is what replaces the code: enough of the specification, the sample and the construction for a reader holding the same data to rebuild the result, and enough for a reader without it to see exactly what was done.

Nothing on this page is needed to reproduce any other exhibit. The measures themselves — NU, NGU, the law — are public, and the survey evidence stands on its own.

---

## 1. Loan-level credit (Table 2)

**The data.** Loan-level new business in overdraft facilities, from the euro-area credit register held at the Banque de France, extended to March 2026. It is supervisory data: access is granted to researchers under the institution's own procedure, and neither the file nor the query that builds it is published.

**The question.** Whether measured inflation uncertainty is related to the price of corporate credit, and whether the answer changes once the distance-from-target component is purged out of the measure. This is the application where the correction matters most visibly: the raw measure shows no relation, the purged one does.

**The specification.** Loan rates on new overdraft business are regressed on the uncertainty measure — raw dispersion in one column, NU in another — with the controls, fixed effects and clusterings reported in the table's own notes in the paper. Standard errors are reported under two clusterings because the regressor is a constructed, time-varying series common to all borrowers in a quarter, and inference has to be matched to that.

**The result, in one line.** One standard deviation of the purged measure is associated with corporate loan rates about 89 basis points higher; the raw measure is unrelated to them. The paper states this as an association, not as a causal estimate.

**To rebuild it.** With register access: build the quarterly NU series from the public code in this repository, merge it on the survey quarter (see `docs/METHODS.md` §3 — the date rule is where this goes wrong silently), and estimate the specification in the paper's table notes. Everything upstream of the merge is public.

**The appendix table on the two measures (Table 4).** The same loan-level regression run with NU and NGU orthogonalised on each other. The orthogonalisation itself is public — `nu_measures.measures.orthogonalize`, the construction Figure 11 and Table 4 of the companion paper use on survey data alone — and its output series can be rebuilt from this repository; only the regression on the register is not.

---

## 2. Market legs of the law (Figures 1 and 4, Table 1, Appendix A.8)

**The data.** Euro inflation-linked swap quotes and the option (cap and floor) surface, exported from a commercial terminal under a licence that does not permit redistribution — neither of the raw quotes nor of series derived from them.

**What they contribute.** Two further readings of the same law, on instruments rather than surveys: realized variance of the swap rate over a forward window, against the level of the swap rate; and a premium-adjusted second moment from the option surface. They matter because they are priced, not reported — the law is not an artefact of how a questionnaire is filled in. The unadjusted option reading is shown beside the adjusted one in the paper, because the adjustment is what makes the comparison meaningful.

**What the published exhibits here do.** The survey legs are estimated; the market legs are *carried as printed in the paper*, as named constants flagged `computed: false` in each results file, so that the exhibits reproduce the published figures and table in full while making plain which numbers this repository can and cannot regenerate: the swap market's free-anchor estimate drawn in Figure 1 (`fig01_kink_location.py`), the swap and option lines of Figure 4 (`fig04_law_across_sources.py`), the swap and option rows of Table 1 (`tab01_arms_by_source.py`), and the swap-window curvature check of Appendix A.8 (`fig03_benefit_of_doubt.py`). A reader holding equivalent data replaces the constants with an estimate under the conventions below.

**Conventions, for a reader holding equivalent data.** The market readings use a forward realized-variance window of 63 trading days, non-overlapping windows for inference, and exclude the 2008–09 dislocation; the comparison across sources is made on the ratio of the upper arm to the intercept, never on the level of a variance, because levels depend on units and on the closure of each source.

---

## Why it is drawn this way

The alternative — publishing the market code behind a flag, with the schema of an export a reader would have to supply — was considered and rejected: it publishes the shape of a licensed product without publishing anything anyone can run. The line drawn here is simpler and easier to hold: code that cannot be run by a reader of this repository is described, not shipped.
