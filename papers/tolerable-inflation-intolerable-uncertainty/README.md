# Tolerable Inflation, Intolerable Uncertainty

### The Unidentifiable Optimum of Monetary Policy

**Eric Vansteenberghe** (Banque de France; Université Paris 1 Panthéon-Sorbonne)
Working paper, September 2026. Links added when the paper is posted.

> Numerical inflation targets anchor beliefs. Across euro-area and US professional forecasts, inflation swaps and options, and realized inflation, uncertainty about inflation is compressed at the announced number and kinks exactly there. This paper identifies a cost of the same design that, to our knowledge, has not been shown before, and that appears in second moments only. Within the workhorse New Keynesian model, tolerating part of the inflation a supply shock produces is optimal, yet the optimal tolerated share is not identified: optimal look-through and an unwarranted drift of the effective target are observationally equivalent in the inflation history, so a central bank cannot demonstrate that a warranted deviation is warranted, ex post as much as in real time. Agents holding finite, heterogeneous patience then generate predictive variance that is flat below the target and rises linearly with the expected overshoot above it—an observational-equivalence bill, zero at the announced number and accumulating with the point-years inflation spends above it. The first-order benefit of the number stands; what the cost changes is how inflation uncertainty must be measured. The distance from target explains 71% of the variation in professional forecast variance, and the bill lies within that component; Normalized Uncertainty—to our knowledge the first such correction—removes it. The purge changes inference substantially: on French loan-level data, raw dispersion is unrelated to corporate loan rates, while one standard deviation of the purged measure is associated with rates 75 basis points higher, and cross-country growth and time-series results shift similarly. Conventional measures of inflation uncertainty partly record inflation's distance from its anchor rather than uncertainty about the outlook.

*Keywords:* Uncertainty, Tolerance, Observational Equivalence, Identification, Monetary Policy, Inflation. *JEL:* C18, D81, E31, E52, E58.

```bibtex
@unpublished{vansteenberghe2026tolerable,
  author = {Vansteenberghe, Eric},
  title  = {Tolerable Inflation, Intolerable Uncertainty: The Unidentifiable Optimum of Monetary Policy},
  note   = {Working paper},
  year   = {2026}
}
```

---

## Two routes through the evidence

The paper reads one law across several sources, and not all of them can travel. **The public route** — everything in this folder — is the survey and macroeconomic evidence: the euro-area and US professional forecasts, the realized-inflation series, the daily US breakeven, the cross-country growth panel and the dealer surveys. **The restricted route** is the part that rests on data which cannot be redistributed and whose code is therefore not published: the loan-level credit application and the inflation-swap and option legs of the market evidence. Both are described, specification and sample, in [`restricted/README.md`](restricted/README.md), so that a reader with the same access can rebuild them; neither is reproducible from this repository.

Where a published exhibit combines the two — Figure 1, Figure 4 and Table 1 each show market sources beside the surveys — the script here rebuilds the **survey legs only**, and says so in the exhibit's caption and results file. Nothing is silently dropped: the results file records which legs were computed and which were not.

## Exhibits

Figure and table numbers are those of the current manuscript (76 pages, 18 September 2026).

| # | Label | What it shows | Data | Status |
|---|---|---|---|---|
| Figure 1 | `fig:kinkloc` | where the kink sits, against the announced target | ECB SPF *(published version adds a swap profile)* | planned |
| Figure 2 | `fig:usdaily` | the announcement in the daily market: five-year breakeven and forward realized variance | FRED `T5YIE` | planned |
| Figure 3 | `fig:benefit` | the professionals' benefit of the doubt: the de-anchored share against the overshoot | ECB SPF, HICP | planned |
| Figure 4 | `fig:lawfour` | one law, several sources, on common axes (shape, not level) | ECB SPF, US SPF *(published version adds swaps and options)* | planned |
| Figure 5 | `fig:nu` | the purge in the euro-area series: raw against NU, and against an independent proxy | ECB SPF, EPU | planned |
| Figure 6 | `fig:rawnu` | industrial production after an uncertainty shock, raw against purged | ECB SPF, ECB macro block | planned |
| Figure 7 | `fig:twounknowns` | acting without identifying the slope or the composition (theory; no data) | — | planned |
| Figure 8 | `fig:abel_scatter` | the level–uncertainty replication in the appendix | ECB SPF, HICP | planned |
| Table 1 | `tab:armsbysource` | the arms specification, source by source | ECB SPF, US SPF *(published version adds swaps and options)* | planned |
| Table 2 | `tab:credit` | uncertainty and the price of credit, raw against purged | **restricted** | not published |
| Table 3 | `tab:crosscountry` | cross-country growth regressions, raw against purged volatility | Barro–Lee, Global Macro Database | planned |
| Table 4 | `tab:spd_panel` | the perceived-rule band from the dealer scenario matrices | New York Fed surveys | planned |

Each script writes its exhibit to `figures/` or `tables/` **and** a results file to `results/` recording every number it prints, with its sample. The key-numbers table below is generated from those files.

## The numbers the paper rests on

| quantity | value | sample |
|---|---|---|
| law on the average individual variance: intercept, lower arm, upper arm | 0.383, 0.004, 0.855 | rounds through 2026Q2, $n = 109$ |
| share of the variation the distance explains | 71% | same |
| estimated kink, and its set | 1.90, [1.76, 2.00] | same |
| law on the round-mean total variance | 0.4204, 0.1173, 1.8825 ($R^2$ 0.789) | same |
| ratio $b_+/a$ — the NU calibration | 4.48 | same |
| agreement with the independent proxy, raw against purged | 0.75 → 0.85 | 1999Q1–2026Q3 |

The level of the upper arm inherits the closure of the open top bin and is reported as a bracket (roughly 0.28 to 1.02 around 0.855); the shape — flat below, rising above, kink at the announced number — does not. See [`../../docs/METHODS.md`](../../docs/METHODS.md) §2.

## Running it

```bash
export NU_DATA_DIR=/path/to/your/data     # see ../../data/README.md
make tolerable                            # or: python3 run.py
python3 run.py --only fig05_nu_purge      # one exhibit
```

## Sample calendar

Rounds fielded through **2026Q2** enter every estimate: 109 after the individual-mean trim of $[-1, 5]$. The **2026Q3** round was published on 24 July 2026, after the 30 June 2026 cutoff stamped in the paper, and is held out — it enters the published series and no estimate. Market and credit samples are stated in the restricted route.
