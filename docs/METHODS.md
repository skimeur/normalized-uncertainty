# Methods

What the measures are, on what sample they are computed, and the conventions that decide the numbers. Written for someone who has not seen the papers: everything here is implemented in `src/nu_measures/` and every constant is fixed in one place, `nu_measures.conventions`. The two papers are cited in every module: *Uncertain and Asymmetric Forecasts* (`vansteenberghe2026uncertain`) for the constructions, *Tolerable Inflation, Intolerable Uncertainty* (`vansteenberghe2026tolerable`) for the law, the purge and the policy results.

## 1. The object

A professional forecaster does not report a number; they report a distribution. The ECB's Survey of Professional Forecasters asks each respondent for the probability that inflation one year ahead falls in each of a fixed set of intervals. From that histogram come a mean $\mu_i$, a variance $V_i$, and higher moments — the raw material of every measure of *forecast uncertainty* in use.

The finding both papers start from is that these moments are not independent of one another. The variance of a forecaster's density is not constant in the level of their own forecast: it is flat while expected inflation sits at or below the central bank's announced target, and it rises with the expected overshoot above it. A measure of uncertainty read off the variance therefore records, in part, how far inflation is expected to be from its anchor — which is a fact about the first moment, not about how unsure anyone is.

## 2. Moments from a histogram

**Point masses at midpoints.** Each bin's probability is treated as a point mass at the midpoint of its interval. One-decimal reporting makes "3.5 to 3.9" the interval $[3.5, 4.0)$, so the midpoint is 3.75.

**Closed tails.** The bins at each end are open. The bottom is closed at $-1.0$ (the lower of $-1$ and the lowest realized inflation rate, $-0.618$ in July 2009). The top bin, "5.0 or more", is closed at $7.809$ — the midpoint of $[5.0, 10.618]$, the upper end being the highest euro-area inflation rate the sample contains (October 2022). Both realized rates are computed year on year from the ECB's HICP index and kept at full precision in `conventions.HICP_MIN` / `HICP_MAX`: rounding them moves the fourth decimal of every variance. The grid introduced with the 2024Q4 round is handled the same way (bottom closed at $-0.75$, top on $[4.75, 10.618]$).

**The closure is not innocent, and is disclosed.** The *level* of the upper arm of the variance law inherits this choice: across the four closures considered — the bin's lower edge, a quarter-point, the midpoint used here, and a uniform spread to the historical maximum — the fitted upper arm moves from roughly 0.28 to roughly 1.02 around the 0.855 of the midpoint closure. What does **not** move is the shape: the lower arm stays flat, the upper arm stays several standard errors from zero under the mildest closure, and the kink stays where it is. The papers therefore report the level as a bracket and rest the argument on the shape.

**Quantiles are interpolated.** Moments use point masses; quantiles cannot, or the median would jump between midpoints. The cumulative probability is interpolated linearly inside the bin that contains the quantile — the usual histogram convention, and the one the asymmetry measures use.

**Sheppard's correction** ($h^2/12$) is reported beside a variance, never applied silently: where a grid becomes both finer and narrower, it accounts for only part of the change in measured variance.

## 3. The date rule

The ECB labels a density with its **target period** — the quarter in which the twelve-month horizon ends. The panel built here carries

$$\text{Date} = \text{target period} - 1\ \text{year}, \qquad \text{survey quarter} = \text{Date} + 1\ \text{month},$$

so that the survey quarter is the quarter in which the round was actually fielded. The 2026Q2 round has `Date` 2026-03-01 and survey quarter 2026-04-01. Every merge with macroeconomic data is on the survey quarter. Getting this wrong misaligns every downstream merge by a year while leaving the code running.

## 4. The law

On the expected gap $d = \mu - \pi^\star$ from the announced target $\pi^\star = 2$,

$$V(d) \;=\; a \;+\; b_-\,(-d)_+ \;+\; b_+\,(d)_+ ,$$

estimated by ordinary least squares with HAC standard errors at four lags (the rounds are quarterly and overlap in what they forecast, so the residuals are serially correlated by construction). Two hypotheses are tested: $b_- = 0$, which is not rejected, and $b_- = b_+$, which is. The asymmetry is the point: the target is *announced*, so there is a side on which a deviation has to be explained and a side on which it does not.

Three objects obey the law with different coefficients, and the code keeps them apart. $W_t$, the round mean of the individual density variances — the **average individual variance**, the envelope of the object each density is — is what the papers estimate the law on: $a = 0.383$, $b_- = 0.004$, $b_+ = 0.855$, $R^2 = 0.71$ on the 109 rounds through 2026Q2. $D_t$, the cross-forecaster variance of the density means (**disagreement**), and $T_t = W_t + D_t$, the variance of the averaged density (**the total**, $0.4204$, $0.1173$, $1.8825$, $R^2 = 0.789$), are reported beside it. The ratio $b_+/a$ of the $W_t$ fit, $2.23$, is the fitted NU denominator; the total's ratio, $4.48$, is that object's own and not the calibration. `nu_measures.law.round_aggregates` builds the three series from the individual panel, `estimation_sample` applies the round rule and the cutoff, and `law_by_object` fits them.

**Inference is a named convention.** Newey–West standard errors with four lags and Bartlett weights, with the small-sample factor $n/(n-k)$ on the whole sandwich (`nu_measures.econometrics.hac_ols`); the pooled individual-level fits use White standard errors with the same factor. Another package's default gives the same coefficients and slightly different $t$-statistics — the tests check that `statsmodels` with `use_correction=True` agrees to machine precision.

**The kink location is read, not optimised.** `kink_profile` maps the residual sum of squares over candidate locations (the central ninety per cent of the consensus forecast's range, in steps of 0.01) and reports the profile-likelihood 95 per cent set; `kink_bootstrap` resamples rounds (2,000 draws, seed 20260728) for a 90 per cent interval. On $W_t$ the profiled kink is $1.90$, the set $[1.76, 2.00]$ and the bootstrap interval $[1.78, 2.01]$; the law is estimated at the announced number.

## 5. The measures

### Normalized Uncertainty (NU)

$$\mathrm{NU}_i \;=\; \frac{\sigma_i}{\sqrt{1 + r\,(\mu_i - \pi^\star)_+}}$$

The denominator is the square root of the variance envelope, so what remains is the dispersion the distance from target does not explain. It is **one-sided** because the target is announced: below the number there is nothing to purge.

The **unit calibration**, $r = 1$ ($a = b = 1$ in the law), is the default of every function in the library and the reading the papers put forward for use: it needs no estimate, so the value of a forecaster-round is the same whatever the sample it is computed in — it does not depend on the history or on the observation window, and it can be computed on any density survey with an announced target from three numbers per forecaster. On the euro-area panel its agreement with the independent text-based index is $0.848$, against $0.746$ for the raw series.

The **fitted** reading, $r = b_+/a = 0.855/0.383 = 2.23$ from the law on the average individual variance through 2026Q2, is the papers' own estimate and is available through `r=NU_R_FITTED` (the code carries the ratio of the fit at full precision, $2.2322$, as the papers' scripts do). It is a dated object: fitted on the rounds before 2020 the same ratio is $1.50$ (standard error $0.63$), because the consensus rarely sat above target then. The two series correlate at $0.95$; the one result whose sign depends on the choice — the association of AC with NU in *Uncertain and Asymmetric Forecasts* (§4.3) — is reported under each.

### Normalized Growth Uncertainty (NGU)

$$\mathrm{NGU}_i \;=\; \frac{\sigma_i^g}{\sqrt{1 + \lvert \mu_i^g - g^{\mathrm{pot}}_t \rvert}}$$

where $g^{\mathrm{pot}}$ is $400 \times \Delta \log$ of the Hodrick–Prescott trend ($\lambda = 1600$) of log real euro-area GDP, carried forward to the survey rounds (`nu_measures.growth`, which also reads the growth block of the round files and resolves the several histogram grids it has used from each density's filled bins). The denominator is **symmetric**: growth has a benchmark but no announced target, so there is no side on which a deviation must be explained. The calibration is the unit one for the same reason — there is no announced number on which to estimate an arm.

### Asymmetry Coherence (AC)

Raw asymmetry in a density is too noisy to read as directional risk. AC keeps the directional signal only where the observed asymmetry is *coherent* with the central forecast, which is what "the balance of risks" means operationally. For each forecaster-round, the median of the density minus the target, $Q$, and the Bowley skewness smoothed over the forecaster's last two rounds, $A$, are scaled by an interquartile range and passed through $\tanh$:

$$\tilde Q = \tanh\!\big((Q-\pi^\star)/\mathrm{IQR}(Q-\pi^\star)\big), \qquad \tilde A = \tanh\!\big(A/\mathrm{IQR}(A)\big), \qquad \mathrm{AC} = \frac{\tilde Q+\tilde A}{2}\cdot\frac{1+\tilde Q\tilde A}{2}.$$

The second factor, the coherence weight, is above one half when the two components agree in sign and below it when they disagree; the round's index is the mean of the individual values. Two conventions of the authoritative panel are kept: a density that puts more than 25 per cent of its mass in an open tail of the old grid has its skewness set to $\mp 0.1$ (its quartiles sit inside a bin whose width is a closure, not a measurement), and the smoothing is a trailing mean over two rounds, one round where only one exists.

**The normalisation window.** The two interquartile ranges are computed on the sample at hand, so the index of a given round changes when rounds are added — the whole history is rescaled (two rounds moved the scale by 8 per cent in July 2026). `nu_measures.asymmetry.ac_panel` therefore takes the window the IQRs are computed on as an explicit argument and records the scales it used; the papers' convention is the whole panel, and a user who extends the sample and wants a comparable index freezes the window on the papers' sample (`examples/nu_and_ac_from_ecb_spf.py` does).

### Orthogonalising one measure on the other

Inflation uncertainty and growth uncertainty move together: whoever is unsure about one tends to be unsure about the other. To ask what growth uncertainty carries *beyond* inflation uncertainty, the common component is removed **within the forecaster**, never in the aggregate — otherwise the composition of the panel does the work. Each respondent with at least ten matched rounds gets their own regression (86 of the 107 matched forecasters); the others keep their own intercept and borrow one within-forecaster slope, estimated on their demeaned observations pooled together. Residuals are averaged by round and standardised.

## 6. The sample

- The $[-1, 5]$ per cent rule is a **round** rule for the round-level law: a round whose consensus lies outside it is excluded, which through 2026Q2 removes exactly one round, 2022Q4 (consensus 5.01). The 17 individual densities above 5 in other rounds stay in their rounds' averages; the fits that pool forecaster-rounds apply the rule to each density instead. Applied to densities rather than rounds, it leaves the headline where it is (70.6% of the variation explained, against 70.5%).
- Rounds fielded through **2026Q2** enter the estimation of the law: **109 rounds** after the round rule.
- The **2026Q3** round was published on 24 July 2026, after the 30 June 2026 data cutoff stamped in the papers. It enters the published series and is held out of every estimate — it is a genuine out-of-sample observation, not a pseudo one.
- The questionnaire changed with the 2024Q4 round; before it, a fixed half-point grid.

## 7. The pipeline, and what is certified

`nu_measures.io_ecb_spf.build_panels` runs the ECB side end to end: the round files are read (the inflation block, the one-year-ahead target period), laid out as the flat panel, written to a file and read back — the authoritative builder reads the flat panel from a file, and the round trip is what makes the result byte-identical — and the individual panel is built from it. The rebuilt individual panel (4,638 forecaster-rounds, 111 rounds, 1999Q1–2026Q3) is identical to the authoritative one on every column but the optional LOESS residual; the law on it prints the numbers above; the kink profile, the bootstrap, the AC index and the agreement with the independent proxy reproduce to their printed digits (`tests/test_reproduction.py`, run when `NU_DATA_DIR` holds the round files). The US panel rebuilt from the Philadelphia Fed workbook reproduces the archived panel to $10^{-15}$. `nu_measures.conventions.CERTIFIED` lists every certified number.

Three further readers sit beside the pipeline. `io_ecb_spf.averaged_density` averages the individual densities of a round with equal weights, a missing cell read as no mass, so that the variance of the averaged density equals the mean individual variance plus the population variance of the individual means exactly (the decomposition figure of the first paper verifies the identity to $10^{-15}$; an average that skips blank cells overstates disagreement). `io_ecb_spf.longer_term_points` reads the four-to-five-years-ahead point forecasts of a round file — the bare-year target with the largest year in the inflation block — for the de-anchored share of the second paper; a respondent present in that block without a point is excluded unless asked for. `io_other.monthly_yoy` lags a monthly series by calendar month, so that a month a release skipped (FRED's October 2025 CPI) yields a missing value rather than shifting the lag.

## 8. The United States

The Philadelphia Fed's survey is used for the comparison across the FOMC's January 2012 announcement of a numerical target, which the euro-area sample cannot provide — the ECB's number predates the series.

Columns 1–10 are the current year, 11–20 the next; the one-year-ahead object is the next-year block; **column 1 is the highest bin and the columns descend**. The GDP price index question changed grid in 2014Q1, which halves measured variance and enters any regression spanning the change with a larger *t*-statistic than any economic term — so the comparison is run on the core PCE and core CPI questions, whose grid has never changed since they began in 2007Q1.

## 9. Traps worth stating once

- **A key's first segment is its dataflow** (ECB Data Portal). Mismatching them returns HTTP 400; a fetcher that falls back quietly then reports success on a discontinued series.
- **`ICP` is frozen and `STS` is discontinued.** Their replacements are `HICP` and `STBS`, and the industrial-production switch is a *definitional* change (changing to fixed composition), not a vintage refresh.
- **Check column and country composition after every third-party download**, not just the dates.
- **The asymmetry index is not comparable across vintages**: it normalises by a full-sample interquartile range, so a new round rescales the entire history.
- **`openpyxl` raises on the US workbook's document properties**; the reader stubs them.
- **Round twice and the last digit moves.** A statistic printed from a two-decimal intermediate (8.95 → 9.0) is not the statistic rounded once (8.947 → 8.9). Every table here prints from the computed value; the results files carry it in full.
- **The figures of a paper carry their own rc settings.** The library's house style is for new work; each paper's `_common.style` restores matplotlib's defaults and applies what the manuscript's figures were drawn with, so a regenerated figure renders pixel for pixel like the published one.
- **Determinism is a requirement.** Seeds are fixed in the conventions module, inputs are sorted, and no timestamp enters a results file: a rebuild reproduces a results file byte for byte, or something moved.
