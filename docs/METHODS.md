# Methods

What the measures are, on what sample they are computed, and the conventions that decide the numbers. Written for someone who has not seen the papers: everything here is implemented in `src/nu_measures/` and fixed in one place, `nu_measures.calendar`.

## 1. The object

A professional forecaster does not report a number; they report a distribution. The ECB's Survey of Professional Forecasters asks each respondent for the probability that inflation one year ahead falls in each of a fixed set of intervals. From that histogram come a mean $\mu_i$, a variance $V_i$, and higher moments — the raw material of every measure of *forecast uncertainty* in use.

The finding both papers start from is that these moments are not independent of one another. The variance of a forecaster's density is not constant in the level of their own forecast: it is flat while expected inflation sits at or below the central bank's announced target, and it rises with the expected overshoot above it. A measure of uncertainty read off the variance therefore records, in part, how far inflation is expected to be from its anchor — which is a fact about the first moment, not about how unsure anyone is.

## 2. Moments from a histogram

**Point masses at midpoints.** Each bin's probability is treated as a point mass at the midpoint of its interval. One-decimal reporting makes "3.5 to 3.9" the interval $[3.5, 4.0)$, so the midpoint is 3.75.

**Closed tails.** The bins at each end are open. The bottom is closed at $-1.0$. The top bin, "5.0 or more", is closed at $7.809$ — the midpoint of $[5.0, 10.618]$, the upper end being the highest euro-area inflation rate the sample contains (October 2022).

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

The same regression is read three ways, because they answer different questions. **Round level**, on consensus quantities: does the profession's dispersion widen when inflation is high? **Within forecaster**, demeaning each respondent: is the *same* person less sure as the overshoot grows? **Between forecasters**, on respondent averages: are some people simply more uncertain than others? The mechanism claims the within reading, so the within reading is what the correction is calibrated on. In `nu_measures.law.within_between` the arms are built from the raw gap *before* the variation is split, so that the kink stays at the announced target.

**The kink location is read, not optimised.** `kink_profile` maps the residual sum of squares over candidate locations; the law is estimated at the announced number.

## 5. The measures

### Normalized Uncertainty (NU)

$$\mathrm{NU}_i \;=\; \frac{\sigma_i}{\sqrt{1 + r\,(\mu_i - \pi^\star)_+}}$$

The denominator is the square root of the fitted envelope, so what remains is the dispersion the distance from target does not explain. It is **one-sided** because the target is announced: below the number there is nothing to purge.

Two calibrations are published on equal footing, and neither is presented as the correct one:

- the **fitted** reading, $r = b_+/a = 4.48$ on the estimation sample;
- the **unit** reading, $r = 1$, which needs no estimate at all.

They are highly correlated, and the choice does not drive any result in either paper.

### Normalized Growth Uncertainty (NGU)

$$\mathrm{NGU}_i \;=\; \frac{\sigma_i^g}{\sqrt{1 + \lvert \mu_i^g - g^{\mathrm{pot}}_t \rvert}}$$

where $g^{\mathrm{pot}}$ is $400 \times \Delta \log$ of the Hodrick–Prescott trend ($\lambda = 1600$) of log real euro-area GDP, carried forward to the survey rounds. The denominator is **symmetric**: growth has a benchmark but no announced target, so there is no side on which a deviation must be explained. The calibration is the unit one for the same reason — there is no announced number on which to estimate an arm.

### Asymmetry Coherence (AC)

Raw asymmetry in a density is too noisy to read as directional risk. AC keeps the directional signal only where the observed asymmetry is *coherent* with the central forecast, which is what "the balance of risks" means operationally. It is implemented with the reader for the asymmetry pipeline rather than reimplemented from memory; see the changelog for its phase.

### Orthogonalising one measure on the other

Inflation uncertainty and growth uncertainty move together: whoever is unsure about one tends to be unsure about the other. To ask what growth uncertainty carries *beyond* inflation uncertainty, the common component is removed **within the forecaster**, never in the aggregate — otherwise the composition of the panel does the work. Each respondent with at least ten matched rounds gets their own regression; the others keep their own intercept and borrow the pooled within-forecaster slope. Residuals are averaged by round and standardised.

## 6. The sample

- Individual density means outside $[-1, 5]$ per cent are dropped.
- Rounds fielded through **2026Q2** enter the estimation of the law: **109 rounds** after the trim.
- The **2026Q3** round was published on 24 July 2026, after the 30 June 2026 data cutoff stamped in the papers. It enters the published series and is held out of every estimate — it is a genuine out-of-sample observation, not a pseudo one.
- The questionnaire changed with the 2024Q4 round; before it, a fixed half-point grid.

## 7. The United States

The Philadelphia Fed's survey is used for the comparison across the FOMC's January 2012 announcement of a numerical target, which the euro-area sample cannot provide — the ECB's number predates the series.

Columns 1–10 are the current year, 11–20 the next; the one-year-ahead object is the next-year block; **column 1 is the highest bin and the columns descend**. The GDP price index question changed grid in 2014Q1, which halves measured variance and enters any regression spanning the change with a larger *t*-statistic than any economic term — so the comparison is run on the core PCE and core CPI questions, whose grid has never changed since they began in 2007Q1.

## 8. Traps worth stating once

- **A key's first segment is its dataflow** (ECB Data Portal). Mismatching them returns HTTP 400; a fetcher that falls back quietly then reports success on a discontinued series.
- **`ICP` is frozen and `STS` is discontinued.** Their replacements are `HICP` and `STBS`, and the industrial-production switch is a *definitional* change (changing to fixed composition), not a vintage refresh.
- **Check column and country composition after every third-party download**, not just the dates.
- **The asymmetry index is not comparable across vintages**: it normalises by a full-sample interquartile range, so a new round rescales the entire history.
- **`openpyxl` raises on the US workbook's document properties**; the reader stubs them.
- **Determinism is a requirement.** Seeds are fixed in the calendar module, inputs are sorted, and no timestamp enters a results file: a rebuild reproduces a results file byte for byte, or something moved.
