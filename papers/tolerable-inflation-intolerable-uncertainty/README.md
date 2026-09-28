# Tolerable Inflation, Intolerable Uncertainty

**Eric Vansteenberghe** (Banque de France; Université Paris 1 Panthéon-Sorbonne)
Working paper, Banque de France, 2026 — arXiv [2609.31512](https://arxiv.org/abs/2609.31512) (v1, September 2026).

> Numerical inflation targets anchor beliefs. Across euro-area and US professional forecasts, inflation swaps and options, and realized inflation, uncertainty about inflation is compressed at the announced number and kinks exactly there. This paper identifies a cost of the same design that, to our knowledge, has not been shown before, and that appears in second moments only. Within the workhorse New Keynesian model, tolerating part of the inflation a supply shock produces is optimal, yet the optimal tolerated share is not identified: optimal look-through and an unwarranted drift of the effective target are observationally equivalent in the inflation history, so a central bank cannot demonstrate that a warranted deviation is warranted, ex post as much as in real time. Agents holding finite, heterogeneous patience then generate predictive variance that is flat below the target and rises linearly with the expected overshoot above it—an observational-equivalence bill, zero at the announced number and accumulating with the point-years inflation spends above it. The first-order benefit of the number stands; what the cost changes is how inflation uncertainty must be measured. The distance from target explains 70% of the variation in professional forecast variance, and the bill lies within that component; Normalized Uncertainty—to our knowledge the first such correction—removes it. The purge changes inference substantially: on French loan-level data, raw dispersion is unrelated to corporate loan rates, while one standard deviation of the purged measure is associated with rates 89 basis points higher, and cross-country growth and time-series results shift similarly. Conventional measures of inflation uncertainty partly record inflation's distance from its anchor rather than uncertainty about the outlook.

*Keywords:* Uncertainty, Tolerance, Observational Equivalence, Identification, Monetary Policy, Inflation. *JEL:* C18, D81, E31, E52, E58.

```bibtex
@unpublished{vansteenberghe2026tolerable, author = {Vansteenberghe, Eric}, title = {Tolerable Inflation, Intolerable Uncertainty}, note = {Working paper, Banque de France}, year = {2026}, eprint = {2609.31512}, archivePrefix = {arXiv}, url = {https://arxiv.org/abs/2609.31512}}
```

---

## Two routes through the evidence

The paper reads one law across several sources, and not all of them can travel. **The public route** — everything in this folder — is the survey and macroeconomic evidence: the euro-area and US professional forecasts, the realized-inflation series, the daily US breakeven, the cross-country growth panel and the dealer surveys. **The restricted route** is the part that rests on data which cannot be redistributed and whose code is therefore not published: the loan-level credit application and the inflation-swap and option legs of the market evidence. Both are described, specification and sample, in [`restricted/README.md`](restricted/README.md), so that a reader with the same access can rebuild them; neither is reproducible from this repository.

Where a published exhibit combines the two — Figure 1, Figure 4, Table 1 and one check of Appendix A.4 — the script here estimates the **survey legs** and carries the market numbers **as printed in the paper**, as named constants flagged `computed: false` in its results file. Nothing is silently dropped: each results file records which legs were computed and which were carried.

## Exhibits

Figure and table numbers are those of the current manuscript (76 pages, September 2026). One script per exhibit, in [`exhibits/`](exhibits/); each writes its figure or table **and** a results file (`results/<script>.json` and `.md`) recording every number it prints, with its sample. **The manuscript embeds these outputs**: the PDFs in [`figures/`](figures/) and the `.tex` files in [`tables/`](tables/) are the files the manuscript includes, copied verbatim, and every number the text quotes from them is the one the results files record. The *Check* column says what was verified before the swap; the notes record the conventions the manuscript adopted from the package on that occasion.

| # | Label | Script | What it shows | Data | Check |
|---|---|---|---|---|---|
| Figure 1 | `fig:kinkloc` | `fig01_kink_location.py` | where the kink sits: the profiled breakpoint on the average individual variance, its 95 % set and bootstrap | ECB SPF; swap estimate carried | embedded, pixel-identical to the earlier file |
| Figure 2 | `fig:usdaily` | `fig02_us_daily_breakeven.py` | the 2012 announcement in the daily market: five-year breakeven against forward realized variance, before and after; the footnote's numbers | FRED `T5YIE`, `T10YIE` | embedded; note (a) |
| Figure 3 | `fig:benefit` | `fig03_benefit_of_doubt.py` | the professionals' benefit of the doubt: the de-anchored share against the overshoot, the renewal law fitted; Appendix A.4's numbers | ECB SPF round files, HICP | embedded; note (b) |
| Figure 4 | `fig:lawfour` | `fig04_law_across_sources.py` | one law, four sources, on common axes (shape, not level) | ECB SPF, US SPF; market lines carried | embedded; note (c) |
| Figure 5 | `fig:nu` | `fig05_nu_purge.py` | **the purge at a = b = 1**: raw against NU in the euro-area series, and against an independent proxy | ECB SPF, EPU | embedded, pixel-identical to the earlier file |
| Figure 6 | `fig:rawnu` | `fig06_ip_response.py` | industrial production after an uncertainty shock, raw against purged, with and without the distance control; every VAR variant the text quotes | ECB SPF, ECB macro block, EPU | embedded, pixel-identical to the earlier file |
| Figure 7 | `fig:twounknowns` | `fig07_two_unknowns.py` | acting without identifying the slope or the composition (theory; no data) | — | embedded, pixel-identical to the earlier file |
| Figure 8, Table 5 | `fig:abel_scatter`, `tab:abel_replication` | `figA_abel2016_replication.py` | Abel, Rich, Song and Tracy (2016) replicated and extended | ECB SPF | embedded; note (d) |
| Table 1 | `tab:armsbysource` | `tab01_arms_by_source.py` | the arms specification, source by source | ECB SPF, US SPF; market rows carried | embedded; note (e) |
| Table 2 | `tab:credit` | — | uncertainty and the price of credit, raw against purged | **restricted** | not published; `restricted/README.md` |
| Table 3 | `tab:crosscountry` | `tab03_cross_country.py` | cross-country growth regressions, raw against purged volatility, with the wild-cluster bootstrap row | Barro–Lee, Global Macro Database | embedded, byte-identical to the earlier file; note (f) |
| Table 4 | `tab:ngu` | — | the credit discrimination between NU and NGU | **restricted**; the orthogonalisation is `measures.orthogonalize` | not published |
| Table 6 | `tab:spd_panel` | `tabA_nyfed_scenario_panel.py` | the perceived-rule band from the NY Fed scenario matrices | NY Fed survey workbooks; PDF-read instances in `inputs/` | embedded, byte-identical to the earlier file |
| — | Section 3 | `results_register.py` | every number of the survey law on one sample: the three objects, the tests, the kink, the realized shadow, the purge's own test | ECB SPF, ECB macro block | the key-numbers table below |

**Notes.** (a) The largest crisis-window variance in panel (a) is 19.55; the caption reads 19.5 (an earlier version printed 19.6, a double rounding). The footnote's daily overlapping statistics are both in the results file: $t \approx 13$ on the above arm with sixty-three Newey–West lags and $29$ with one; neither is used for inference. (b) The share's denominator is the caption's: respondents who reported a longer-term point (`DENOMINATOR = "reporting"`). The earlier convention counted every respondent present in the longer-term block, a density reported without a point counted as an anchored point; it is still computed and stored under `with_the_all_rows_denominator`. The manuscript's Figure 3, Section 3 and Appendix A.8 numbers are the reporting-denominator ones (39 to 52 respondents per round over the fit window, $r = 0.66$, RMSE 0.062, the expected-gap clock at $\eta = 0.18$ and $r = 0.58$, and the re-basing feedback that follows from them); the shares of exactly $3/40$ and $7/40$ are printed 0.08 and 0.18, rounded once from the exact value. (c) The market lines are drawn from the three-decimal coefficients printed in Table 1, so the curves differ from the earlier file below the resolution of the page. (d) The tail closure of the open bins follows the paper's panel (`HICP_MIN`, `HICP_MAX`, the December 2025 HICP vintage); the extended rows of Table 5 and the text that quotes them are now on that closure (an earlier version of the table used the March 2026 vintage's extremes, one thousandth apart). (e) The US row's $t$-statistics are clustered by survey round, as the table's note says; the Newey–West statistics of the stacked individual observations, which an earlier version of the table printed, are in the results file under `us_row_hac4_stacked`. (f) The Barro–Lee source is not in this repository's data layout yet; the script builds the panel from it when present and otherwise reads the panel it last built from `derived/`.

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
```

## Sample calendar

Rounds fielded through **2026Q2** enter every estimate: 109 after the $[-1, 5]$ round rule (2022Q4 is the round it removes). The **2026Q3** round was published on 24 July 2026, after the 30 June 2026 cutoff stamped in the paper, and is held out — it enters the published series and no estimate. Realized data stop at the same cutoff. Market and credit samples are stated in the restricted route.
