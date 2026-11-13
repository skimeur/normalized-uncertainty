# Tolerable Inflation, Intolerable Uncertainty

**Eric Vansteenberghe** (Banque de France; Université Paris 1 Panthéon-Sorbonne)
Working paper, Banque de France, 2026 — arXiv [2609.31512](https://arxiv.org/abs/2609.31512) (v1, September 2026). This page follows the **November 2026 version** (84 pages, appendices included); where it differs from v1, the notes below say so.

> How much of an inflation deviation a central bank should tolerate is a well-defined optimum in the New Keynesian model, but it cannot be identified: optimal accommodation of supply shocks and an unwarranted drift of the effective inflation target are observationally equivalent. This impossibility has a cost. A public that cannot verify the bank's intention prices each expected point of overshoot, so uncertainty about inflation is flat below the announced target and rises linearly above it: the observational-equivalence effect. Professional forecasts, swap and option markets and realized inflation all show this pattern, with the kink at the announced number. A second and larger effect produces the same shape: inflation is more volatile when it is high, and in realized inflation that level effect is mostly energy. Both effects load on the distance from the target, so the data admit the observational-equivalence effect without isolating it, and its cost cannot be estimated with the data at hand. We therefore cannot say how optimal monetary policy should change on its account, but three policy conclusions survive: in the textbook model, not observing the slope of the Phillips curve and the composition of shocks never calls for tolerating less; the announced target remains worth having, because it compresses beliefs at the target; and what the central bank can do is monitor the point-years inflation spends above target, on which the effect is charged, and read inflation uncertainty net of the distance from the target. Normalized Uncertainty provides that reading by purging the distance component of measured uncertainty. In French loan-level data, raw inflation uncertainty is unrelated to corporate loan rates after controls, whereas a one-standard-deviation increase in Normalized Uncertainty is associated with rates 89 basis points higher. The correction also reveals a negative association with growth in cross-country data and alters euro-area time-series results.

*Keywords:* Uncertainty, Tolerance, Observational Equivalence, Identification, Monetary Policy, Inflation. *JEL:* C18, D81, E31, E52, E58.

```bibtex
@unpublished{vansteenberghe2026tolerable, author = {Vansteenberghe, Eric}, title = {Tolerable Inflation, Intolerable Uncertainty}, note = {Working paper, Banque de France}, year = {2026}, eprint = {2609.31512}, archivePrefix = {arXiv}, url = {https://arxiv.org/abs/2609.31512}}
```

---

## Two routes through the evidence

The paper reads one law across several sources, and not all of them can travel. **The public route** — everything in this folder — is the survey and macroeconomic evidence: the euro-area and US professional forecasts, the realized-inflation series and its components, negotiated wages, the US breakeven, the cross-country growth panel and the dealer surveys. **The restricted route** is the part that rests on data which cannot be redistributed: the loan-level credit application and the inflation-swap and option legs of the market evidence, whose code is not published, and the reverse link of Section 4, whose code will be published here without its data (note (h)). Both are described, specification and sample, in [`restricted/README.md`](restricted/README.md), so that a reader with the same access can rebuild them; neither is reproducible from this repository.

Where a published exhibit combines the two — Figure 1, Figure 2, Table 1 and one check of the appendix on the benefit of the doubt — the script here estimates the **survey legs** and carries the market numbers **as printed in the paper**, as named constants flagged `computed: false` in its results file. Nothing is silently dropped: each results file records which legs were computed and which were carried.

## Exhibits

Figure and table numbers are those of the November 2026 version (89 pages). The script names keep the numbering of arXiv v1, under which the package was first published, so `fig03_benefit_of_doubt.py` writes what is now Figure 7. One script per exhibit, in [`exhibits/`](exhibits/); each writes its figure or table **and** a results file (`results/<script>.json` and `.md`) recording every number it prints, with its sample. **The manuscript embeds these outputs**: the PDFs in [`figures/`](figures/) and the `.tex` files in [`tables/`](tables/) are the files the manuscript includes, and every number the text quotes from them is the one the results files record. The scripts named `results_*` write no exhibit: they record numbers the text prints.

| # | Label | Script | What it shows | Data | Check |
|---|---|---|---|---|---|
| Figure 1 | `fig:kinkloc` | `fig01_kink_location.py` | where the kink sits: the profiled breakpoint on the average individual variance, its 95 % set and bootstrap | ECB SPF; swap estimate carried | pixel-identical to the paper's file |
| Figure 2 | `fig:lawfour` | `fig04_law_across_sources.py` | one law, four sources, on common axes (shape, not level) | ECB SPF, US SPF; market lines carried | pixel-identical; note (c) |
| Figure 3 | `fig:nu` | `fig05_nu_purge.py` | **the purge at a = b = 1**: raw against NU in the euro-area series, and against an independent proxy | ECB SPF, EPU | pixel-identical |
| Figure 4 | `fig:rawnu` | `fig06_ip_response.py` | industrial production after an uncertainty shock, raw against purged, with and without the distance control; every VAR variant the text quotes | ECB SPF, ECB macro block, EPU | pixel-identical |
| Figure 5 | `fig:dsge` | `fig07_tolerance_dsge.py` | no divine coincidence: the optimal tolerance with the slope and the shocks unobserved, and the price of tolerating less (theory; no data; the three-bank comparison is Table 10) | — | numbers identical (the paper's figure is this script's build) |
| Figure 6 | `fig:lgm-levelfree` | — | level-free uncertainty in the swap and policy-rate markets (Section 4) | market data | not yet in this repository; note (h) |
| Figure 7 | `fig:benefit` | `fig03_benefit_of_doubt.py` | the professionals' benefit of the doubt: the de-anchored share against the overshoot | ECB SPF round files, HICP | numbers identical; notes (b), (g) |
| Figure 8, Table 9 | `fig:abel_scatter`, `tab:abel_replication` | `figA_abel2016_replication.py` | Abel, Rich, Song and Tracy (2016) replicated and extended | ECB SPF | byte- and pixel-identical; note (d) |
| Figure 9 | `fig:lgm-m1` | — | realized inflation and its conditional standard deviation (Appendix B) | HICP | not yet in this repository; note (h) |
| Table 1 | `tab:armsbysource` | `tab01_arms_by_source.py` | the arms specification, source by source | ECB SPF, US SPF; market rows carried | byte-identical; note (e) |
| Table 2 | `tab:credit` | — | uncertainty and the price of credit, raw against purged | **restricted** | not published; `restricted/README.md` |
| Table 3 | `tab:crosscountry` | `tab03_cross_country.py` | cross-country growth regressions, raw against purged volatility, with the wild-cluster bootstrap row | Barro–Lee, Global Macro Database | byte-identical; note (f) |
| Tables 4–7, 12–18 | `tab:lgm-*` | — | the reverse link: the law in conditional variances, the predictive link, oil (Section 4, Appendix B) | swaps, OIS, HICP, oil | not yet in this repository; note (h) |
| Table 8 | `tab:ngu` | — | the credit discrimination between NU and NGU | **restricted**; the orthogonalisation is `measures.orthogonalize` | not published |
| Table 11 | `tab:spd_panel` | `tabA_nyfed_scenario_panel.py` | the perceived-rule band from the NY Fed scenario matrices | NY Fed survey workbooks; PDF-read instances in `inputs/` | byte-identical |
| — | Section 3 | `results_register.py` | every number of the survey law on one sample: the three objects, the tests, the kink, the realized shadow, the purge's own test | ECB SPF, ECB macro block | the key-numbers table below |
| — | Section 3, wages | `results_wages.py` | the in-text table: the arms of the gap on squared negotiated-wage surprises | ECB negotiated wages, HICP, ECB SPF | every printed number |
| — | Section 3, realized shadow | `results_energy_split.py` | the energy footnote: 66 % of the realized upper arm is energy, 8 % ex-energy | HICP headline, energy, ex-energy | every printed number |
| — | Section 3, realized shadow | `results_realized_persistence.py` | realized variance does not outlast the gap: ARMA–GARCH with the arms, its variants, and the survey's habituation | HICP (ECB, Eurostat), ECB SPF | every printed number |
| — | Appendix A, the United States | `results_us_appendix.py` | the US core-CPI arms by era, the placebo breaks, the post-2012 kink, the breakeven windows | US SPF, FRED `T5YIE` | every printed number |
| — | Appendix A, the label | `results_episodes.py` | the four euro-area hikes: the label, the gap, and the price per point | ECB SPF, ECB macro block | every printed number |
| (v1 only) | `fig:usdaily` | `fig02_us_daily_breakeven.py` | Figure 2 of arXiv v1: the 2012 announcement in the daily market. Not in the November version, whose US evidence is the half-page appendix above; kept for v1 | FRED `T5YIE`, `T10YIE` | pixel-identical to the v1 file; note (a) |

**Notes.** (a) The largest crisis-window variance in panel (a) is 19.55; the caption reads 19.5 (an earlier version printed 19.6, a double rounding). The footnote's daily overlapping statistics are both in the results file: $t \approx 13$ on the above arm with sixty-three Newey–West lags and $29$ with one; neither is used for inference. (b) The share's denominator is the caption's: respondents who reported a longer-term point (`DENOMINATOR = "reporting"`). The earlier convention counted every respondent present in the longer-term block, a density reported without a point counted as an anchored point; it is still computed and stored under `with_the_all_rows_denominator`. (c) The market lines are drawn from the three-decimal coefficients printed in Table 1. (d) The tail closure of the open bins follows the paper's panel (`HICP_MIN`, `HICP_MAX`, the December 2025 HICP vintage). (e) The US row's $t$-statistics are clustered by survey round, as the table's note says; the Newey–West statistics of the stacked individual observations are in the results file under `us_row_hac4_stacked`. (f) The panel is built from the Barro–Lee source when present; otherwise the script reads the panel it last built from `derived/`. (g) The PDFs of Figures 5 and 7 that the paper embeds were drawn with matplotlib 3.11; the locked environment (3.10.9) reproduces every number and lays the figures out a few pixels differently. (h) The reverse link of Section 4 and Appendix B rests on daily inflation swaps and €STR OIS, which cannot be redistributed; its code will be published here without the data, as the restricted route describes. Until then its specification and samples are in [`restricted/README.md`](restricted/README.md).

## The numbers the paper rests on

Generated from `results/results_register.json`, `results/fig01_kink_location.json` and `results/fig05_nu_purge.json`; every value is on the 109-round sample unless stated.

| quantity | value | sample |
|---|---|---|
| law on the average individual variance $W_t$: $a$, $b_-$, $b_+$ (s.e.) | 0.383 (0.063), +0.004 (0.097), +0.855 (0.070); $R^2$ 0.705 | rounds through 2026Q2, $n = 109$ |
| share of the variation the distance explains | 70.5 % | same |
| law on disagreement $D_t$: $b_-$ ($t$), $b_+$ ($t$), $R^2$ | +0.113 (2.36), +1.028 (8.93), 0.719 | same |
| law on the total mixture variance $T_t$: $a$, $b_-$, $b_+$, $R^2$ | 0.4204, 0.1173, 1.8825, 0.789 | same |
| individual share of the total | 73 % | same |
| the symmetric restriction $b_- = b_+$ on $T_t$, $p$ | 1.6e-25 | same |
| ratio $b_+/a$ on the average individual variance — the fitted calibration | 2.23 (0.49) | same |
| ratio $b_+/a$ on the total mixture variance (not the calibration) | 4.48 | same |
| estimated kink on $W_t$, its 95 % set, the bootstrap 90 % interval | 1.90, [1.76, 2.00], [1.78, 2.01] | same |
| realized shadow: AR(1) $\rho$, arms on the squared innovation $b_-$ (s.e.), $b_+$ (s.e.), $R^2$ | 0.93; 0.074 (0.065), 0.377 (0.080), 0.40 | quarterly HICP gap, $n = 109$ |
| agreement with the independent proxy, raw against purged (unit calibration, Figure 5) | 0.75 → 0.85 | 1999Q1–2026Q2 |

The level of the upper arm inherits the closure of the open top bin; the shape — flat below, rising above, kink at the announced number — does not. The bracket is in the companion paper's package. See [`../../docs/METHODS.md`](../../docs/METHODS.md) §2.

## Running it

```bash
export NU_DATA_DIR=/path/to/your/data     # see ../../data/README.md
make tolerable                            # or: python3 run.py
python3 run.py --only fig05_nu_purge      # one exhibit
make data                                 # which sources are present, and whether they are the paper's vintages
```

`results_realized_persistence.py` takes several minutes: its GARCH likelihoods are evaluated in plain Python from six starting points each.

## Sample calendar

Rounds fielded through **2026Q2** enter every estimate: 109 after the $[-1, 5]$ round rule (2022Q4 is the round it removes). The **2026Q3** round was published on 24 July 2026, after the 30 June 2026 cutoff stamped in the paper, and is held out — it enters the published series and no estimate. Realized data do not all stop there: each source is cut at the last observation of the download the paper used, as `nu_measures.conventions.PUBLISHED_EXTENT` records it (the HICP components and the headline index of Section 3 run to October 2026, Eurostat's index to September 2026, negotiated wages to 2025Q3, the macro block to its July 2026 fetch). `make data` compares your files with the paper's by checksum (`PUBLISHED_INPUT_MD5`): a later download is cut at the same date, but a provider's revisions to past values can move the numbers that read it. Market and credit samples are stated in the restricted route.
