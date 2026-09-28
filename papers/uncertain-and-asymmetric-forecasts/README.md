# Uncertain and Asymmetric Forecasts

**Eric Vansteenberghe** (Banque de France; Université Paris 1 Panthéon-Sorbonne)
Working paper, 2026. Current version: SSRN [4995675](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4995675) (revised 24 September 2026). Earlier versions: arXiv [2411.05938](https://arxiv.org/abs/2411.05938) (v1 November 2024, v2 January 2026, v3 March 2026).

> Survey density forecasts are summarized by their second and third moments, read as uncertainty and as the balance of risks. Neither can be read on its own. In the ECB Survey of Professional Forecasters the variance of an individual inflation density rises with the distance of that forecaster's central forecast from the official target, flat below it and rising above, so that raw dispersion mixes belief imprecision with the arithmetic of the level; and a third moment computed over a handful of bins is too noisy to identify directional risk unless it is read together with the location of the density. This paper builds, from the reported bins up, two measures that repair these defects. Normalized Uncertainty divides a density's standard deviation by the one the fitted variance–distance envelope predicts at the observed distance. Asymmetry Coherence retains directional risk only where the sign of the reported asymmetry agrees with the sign of the median's deviation from the target, weighted by that agreement. Both are carried to growth densities, where the reference is estimated rather than announced; to a simulation in which the latent objects are known; and to the US Survey of Professional Forecasters.

*Keywords:* Uncertainty, Asymmetry, Balance of Risks, Predictive Distributions, Survey of Professional Forecasters. *JEL:* C53, D81, D84, E31, E37.

```bibtex
@unpublished{vansteenberghe2026uncertain, author = {Vansteenberghe, Eric}, title = {Uncertain and Asymmetric Forecasts}, note = {Working paper}, year = {2026}, eprint = {2411.05938}, archivePrefix = {arXiv}, url = {https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4995675}}
```

The construction of NU is developed, and the law behind it estimated across sources, in the companion paper *Tolerable Inflation, Intolerable Uncertainty* (`vansteenberghe2026tolerable`, [package](../tolerable-inflation-intolerable-uncertainty/)); the unit calibration $a = b = 1$ this repository puts forward is the one both papers recommend.

---

## What this package covers

Every exhibit of the paper runs on **public data**: the ECB Survey of Professional Forecasters round files, the Philadelphia Fed Survey of Professional Forecasters microdata, ECB Data Portal series (HICP, real GDP), FRED (US core CPI) and the Economic Policy Uncertainty workbook as an outside check. There is no restricted route. No data ships with the repository: point `NU_DATA_DIR` at a folder laid out as [`../../data/README.md`](../../data/README.md) describes.

The paper is about the **construction of the measures** — Normalized Uncertainty, Normalized Growth Uncertainty with its orthogonalisation, and Asymmetry Coherence — their validation, and their comparison across the two surveys. One script per exhibit, in [`exhibits/`](exhibits/), each writing its figure or table **and** a results file (`results/<script>.json` and `.md`) recording every number it prints, with the sample it was computed on. Two helper modules carry what several scripts share: `_common.py` (the manuscript's figure style, the quarterly NU series, the matched inflation–growth panel) and `_simulation.py` (the Monte Carlo of Section 7). Everything else comes from the library, [`nu_measures`](../../src/nu_measures/).

## Exhibits

Figure and table numbers are those of the current manuscript. **The manuscript embeds these outputs**: the PDFs in [`figures/`](figures/) and the `.tex` files in [`tables/`](tables/) are the files the manuscript includes, copied verbatim. The *Check* column says what was verified before the swap: *identical* means the table file was byte-identical to the manuscript's earlier file or the figure's PDF rendered pixel for pixel the same; *illustration* means a figure with no data, regenerated from its parameters; the notes record the conventions the manuscript adopted from the package on that occasion.

| # | Label | Script | What it shows | Inputs | Check |
|---|---|---|---|---|---|
| Figure 1 | `fig:grid` | `fig01_histogram_grid.py` | the questionnaire's grid, before and after the 2024Q4 change, and the mass in the open tails | ECB SPF | identical |
| Figure 2 | `fig:var_decomposition` | `fig02_variance_decomposition.py` | the variance of the averaged density stacked as mean individual variance plus disagreement | ECB SPF | embedded; note (a) |
| Figure 3 | `fig:two_SPD_skewness_illustration` | `fig03_two_densities.py` | two beta densities of opposite skewness and their average | — | illustration |
| Figure 4 | `fig:arms_fit` | `fig04_arms_fit.py` | the round mean of individual variances against the consensus gap, with the two-arm fit; the individual densities with the pooled fit | ECB SPF | identical |
| Figure 5 | `fig:nu_series` | `fig05_nu_series.py` | raw dispersion, fitted NU and unit NU; the series against the EPU basket | ECB SPF, EPU | identical |
| Figure 6 | `fig:moments` | `fig06_moments_intervals.py` | the round mean and interquartile band of each individual moment | ECB SPF | identical |
| Figure 7 | `fig:skewed_distributions` | `fig07_skew_cases.py` | coherent against incoherent asymmetry, four skew-normal cases | — | illustration |
| Figure 8 | `fig:ac_map` | `fig08_ac_map.py` | the AC index over the (median gap, skewness) plane, with the panel's forecaster-rounds | ECB SPF | identical |
| Figure 9 | `fig:ac_series` | `fig09_ac_series.py` | the round AC series and its components | ECB SPF | identical |
| Figure 10 | `fig:ngu_series` | `fig10_ngu_series.py` | raw growth dispersion against NGU; NGU against the EPU basket | ECB SPF, ECB real GDP, EPU | identical |
| Figure 11 | `fig:nu_ngu_orth` | `fig11_nu_ngu_orthogonalization.py` | NU and NGU, and each orthogonalised on the other | ECB SPF, ECB real GDP | identical |
| Figure 12 | `fig:us_arms` | `fig12_us_arms.py` | the envelope in the US survey: the grid-stable core questions after 2012, and the GDP price index question across its change of grid | US SPF | identical |
| Figure 13 | `fig:ea_us` | `fig13_ea_us_comparison.py` | the euro area and the United States side by side: realized inflation, first moment, unit NU, AC | ECB SPF, US SPF, HICP, FRED | identical |
| Figure 14 | `fig:mc_decomposition` | `fig14_mc_decomposition.py` | the simulation: one long run, raw against corrected moments, and the exact decomposition of raw dispersion | — (simulated) | embedded; note (b) |
| Table 1 | `tab:arms` | `tab01_arms.py` | the envelope: two-arm law on the three round objects, the before-2020 window, Wald tests | ECB SPF | identical |
| Table 2 | `tab:momentscorr` | `tab02_moments_correlations.py` | how the moment-based measures relate to one another | ECB SPF | identical |
| Table 3 | `tab:skew_dev_regs` | `tab03_skewness_deviation.py` | asymmetry against the deviation of the central forecast, with and without round effects | ECB SPF | embedded; note (c) |
| Table 4 | `tab:ngu_orth` | `tab04_ngu_orthogonalization.py` | the orthogonalisation: correlations, own-slope and pooled-slope forecasters | ECB SPF, ECB real GDP | identical |
| Table 5 | `tab:us_arms` | `tab05_us_arms.py` | the envelope by US density question; the race between the 2012 announcement and the 2014 change of grid; the within-source ratios | US SPF, ECB SPF | embedded; note (c) |
| Table 6 | `tab:mc_simulation_summary` | `tab06_mc_summary.py` | the simulation summary: raw against corrected moments | — (simulated) | identical |

**Notes.** (a) Figure 2 draws the equal-weight average of the individual densities, every missing cell read as no mass (the panel builder's rule), so that the variance of the averaged density equals the mean individual variance plus the population variance of the individual means exactly; the script verifies the identity before drawing (largest gap of the order of $10^{-15}$) and runs through the latest round. The manuscript's earlier file was produced by a script that averaged the reported cells only and stopped at the 2026Q1 round, which overstated the upper band; the manuscript now embeds this figure and Section 2 states the identity. (b) The manuscript now embeds the current rendering of the simulation figure, with its caption rewritten to the panels as drawn; the earlier file was a stale rendering. (c) Two cells of the manuscript's earlier tables were rounded twice (a t-statistic of 8.947 printed as 9.0; an $R^2$ of 0.0115 printed as 0.012); the scripts round once, from the computed value, and the manuscript now prints 8.9 and 0.011 in the tables and the text.

Conventions worth knowing before reading Table 5: the "old grid" row of the GDP price index question is the old grid *before the January 2012 announcement* (1992Q1–2011Q4, 81 rounds); the eight old-grid rounds of 2012–2013 are reported in the results file only. The core questions have used one grid since 2007Q1.

## Running it

```bash
export NU_DATA_DIR=/path/to/your/data     # see ../../data/README.md
python3 run.py                            # every exhibit, in manuscript order
python3 run.py --only tab05               # one exhibit
python3 run.py --list
```

or `make uaf` from the repository root. The first run builds the ECB-SPF panels from the round files into `$NU_DATA_DIR/derived/` (a minute); every later run reads them back. The two simulation exhibits need no data.

## Sample

One vintage for the whole paper: the ECB-SPF rounds 1999Q1–2026Q3 (111 rounds; the 2026Q3 round is the latest complete one), the round-level estimates on the rounds through 2026Q2 with the consensus inside $[-1, 5]$ per cent (109 rounds; the rule removes 2022Q4), the individual fits on every density whose mean lies in the same interval; the US microdata through 2026Q2. The date convention (formation time, survey quarter) is in [`../../docs/METHODS.md`](../../docs/METHODS.md) §3. Before the sample is extended to a newer round, the numbers of the frozen sample are reproduced exactly — a change in magnitude is carried and reported, a change in sign or in significance class stops the rebuild.
