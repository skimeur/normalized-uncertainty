# Data

**Nothing in this repository is a copy of someone else's data.** Every source below is downloaded from its own home, by you, under that provider's terms; the code here reads it and builds the panels the exhibits need. That keeps the licensing question simple — you are the downloader, and no provider's file is re-published — and it keeps the repository honest about vintages: a panel rebuilt today from a later survey round is a different object from the one the papers report, and the code says so rather than shipping a frozen copy.

## Where to put it

```bash
export NU_DATA_DIR=/path/to/your/data
make data          # reports which sources are present and which are missing
```

Expected layout under `NU_DATA_DIR`:

```
ecb_spf/rounds/1999Q1.csv ... 2026Q3.csv     individual density forecasts, one file per round
ecb_spf/ECB_SPF_individual_NIU_ACI_1Y.csv     optional: the authoritative individual panel, for the identity test
ecb/macro_block.csv                          written by the fetcher (nu_measures.io_ecb_data_portal.macro_block)
ecb/macro_block_unbalanced.csv               written by the fetcher (the union, ragged edge kept)
ecb/real_gdp.csv                             written by the fetcher (real GDP, quarterly)
ecb/hicp_index.csv                           the monthly HICP index: optional for the law; UAF Figures 1 and 13 read realized inflation from it
us_spf/SPFmicrodata.xlsx                      the Philadelphia Fed workbook, as distributed
fred/T5YIE.csv, fred/T10YIE.csv               five- and ten-year breakeven inflation rates (FRED CSV downloads)
fred/CPILFESL.csv                             US core CPI index, monthly (FRED CSV download)
epu/All_Country_Data.xlsx                     Economic Policy Uncertainty, country workbook
nyfed/<instance>-data.xlsx                    NY Fed survey workbooks: sep-2023, apr-may-2024, sep-2024, jul-2025, apr-2026
crosscountry/barlee_long.csv                  Barro–Lee data set, long form (SHCODE, year, the block variables; ISO3 crosswalk)
crosscountry/gmd*.parquet | gmd*.csv          Global Macro Database (columns ISO3, year, infl)
derived/                                      what the library builds (the panels, the series); never committed
```

The `ecb/` files are produced by the ECB reader in this repository, which reads the ECB Data Portal's SDMX API; everything else is a manual download. `nu_measures.paths` maps every one of these to a function, so no script spells a path.

## The sources, named exactly

### ECB Survey of Professional Forecasters — individual density forecasts

The core of both papers: one file per quarterly round, each respondent's probability distribution for inflation one year ahead. Published by the ECB on its [SPF page](https://www.ecb.europa.eu/stats/ecb_surveys/survey_of_professional_forecasters/html/index.en.html). Save each round as `ecb_spf/rounds/<YYYY>Q<n>.csv`, named by the **survey quarter**, not the target period.

*Used by:* every exhibit of both papers.

### ECB Data Portal (SDMX API)

Fetched by the ECB reader; no manual download. The keys, and the two migrations that have already caught this project out:

| column | series key | note |
|---|---|---|
| `HICP_YOY` | `HICP.M.U2.N.000000.4D0.ANR` | the old `ICP.M.U2.N.000000.4.ANR` **froze at December 2025**; the live series is in the new `HICP` dataflow |
| `DFR` | `FM.D.U2.EUR.4F.KR.DFR.LEV` | deposit facility rate, daily, read end-of-month |
| `logS` | `FM.M.U2.EUR.DS.EI.DJES50I.HSTA` | EURO STOXX 50, monthly **average of daily closes**, not month-end |
| `logIP` | `STBS.M.I10.Y.PROD.NS0020.4D0.N.IX` | industrial production, **euro area 21, fixed composition**; the discontinued `STS.M.I9…` was changing composition — a definitional difference, not a vintage refresh |
| `UNRATE` | `LFSI.M.I9.S.UNEHRT.TOTAL0.15_74.T` | unemployment rate |
| real GDP | `MNA.Q.Y.I9.W2.S1.S1.B.B1GQ._Z._Z._Z.EUR.LR.N` | the input to the Hodrick–Prescott trend behind potential growth |

**A key's first segment is its dataflow.** Pairing a `STBS…` key with the `STS` flow returns HTTP 400, and a fetcher that then falls back quietly reports success while reading a discontinued series. The reader here derives the flow from the key, probes an ordered list of candidates and prints the coverage it obtained, so a future migration announces itself.

### Philadelphia Fed Survey of Professional Forecasters — microdata

One workbook, [SPF microdata](https://www.philadelphiafed.org/surveys-and-data/real-time-data-research/survey-of-professional-forecasters). Sheets used: `PRPGDP` (GDP price index), `PRCPCE` (core PCE), `PRCCPI` (core CPI).

Columns 1–10 are the current year and 11–20 the next year, each block summing to 100 on its own; the one-year-ahead object is the next-year block. **Column 1 is the highest bin and the columns descend** — read the other way, every forecast is silently inverted. One-decimal reporting makes "3.5 to 3.9" the interval [3.5, 4.0), midpoint 3.75; open tails take one bin width. `PRPGDP` changed grid at 2014Q1 (ten 1.0-point bins to ten 0.5-point bins), which halves measured variance and enters a regression spanning it with a larger *t* than any economic term; the core sheets begin in 2007Q1 and never change, which is why they carry the comparison across the FOMC's January 2012 announcement.

*Trap:* the workbook carries a document-properties field that makes `openpyxl` raise on open. Every reader in this repository stubs the properties reader before loading it.

### FRED — breakeven inflation rates and US core CPI

Series `T5YIE` and `T10YIE` from the [St. Louis Fed](https://fred.stlouisfed.org/series/T5YIE), daily, for the daily-market figure of the second paper (the five-year series is the primary one; the ten-year is the check in its footnote); and `CPILFESL`, the monthly core CPI index, for the euro-area–US comparison of the first paper. A FRED CSV carries `.` on holidays and a blank where a release was skipped (October 2025): the readers drop the former and, for year-on-year changes, lag by calendar month so that the latter does not shift the lag (`io_other.monthly_yoy`).

### Economic Policy Uncertainty

The country workbook from [policyuncertainty.com](https://www.policyuncertainty.com/). Used only as an *independent* proxy, to ask whether the corrected measures agree better with an outside indicator than the raw ones do.

**Check the country columns after every download.** The July 2026 vintage dropped Sweden, taking the euro-area basket from six countries to five; Greece was materially revised at the same time. Sweden is not a euro-area member, so its removal is arguably a correction, but it is a composition change and it moves the series. The basket is fixed in the conventions module and the reader verifies it.

### New York Fed — Survey of Primary Dealers and Survey of Market Participants

The [scenario-matrix results](https://www.newyorkfed.org/markets/primarydealer_survey_questions), which since 2023 ask respondents for the policy rate they expect under stated macroeconomic outcomes. Save each instance's data workbook as `nyfed/<instance>-data.xlsx` (`sep-2023`, `apr-may-2024`, `sep-2024`, `jul-2025`, `apr-2026`). The March 2023 instance predates the workbook format and the two 2024 workbooks carry zeroed scenario cells; those matrices were read from the published results PDFs and are committed with this repository, each row with its source, in `papers/tolerable-inflation-intolerable-uncertainty/inputs/nyfed_scenario_matrices_pdf_read.csv` — a transcription of published numbers, not a redistribution of a data product.

### Barro–Lee panel and the Global Macro Database

The cross-country growth regressions of the second paper. The Barro–Lee data set (the 1994 distribution, one row per country and year with the five-year block variables replicated down the rows, the `SHCODE` country code, and the ISO3 crosswalk either in the file or in `barlee_selected_x_gmd_1960_1990.csv` beside it) supplies Barro's regressors; the [Global Macro Database](https://www.globalmacrodata.com/) (Müller et al., 2025; only `ISO3`, `year` and `infl` are read) supplies the inflation moments. Both are public research datasets with their own citation requirements — cite them where you use them. The script writes the panel it builds to `derived/crosscountry_panel.csv` and reads it back when the Barro–Lee source is absent.

## The extent the published exhibits use

The exhibits of both papers were produced from the downloads below. The loaders of `nu_measures.exhibit` stop every source at the observation in the middle column (`nu_measures.conventions.PUBLISHED_EXTENT`), so a later download — which will hold more rounds, days and months — reproduces the published numbers; pass `published=False` to a loader to read everything. What no pin can undo is a provider's revision of past values (national accounts, a re-estimated policy-uncertainty index, a rebased price index): with a later vintage those can move the last digits.

| Source | Last observation the exhibits use | Download behind the published exhibits |
|---|---|---|
| ECB-SPF round files | round 2026Q3 (111 rounds, 1999Q1–2026Q3; estimates on the rounds through 2026Q2) | July 2026 |
| Philadelphia Fed SPF microdata | 2026Q2 | 28 July 2026 |
| FRED `T5YIE`, `T10YIE` | 14 August 2026 | 17 August 2026 |
| FRED `CPILFESL` | April 2026 | 30 May 2026 |
| EPU country workbook | June 2026 (basket: Germany, France, Italy, Spain, Greece) | 28 July 2026 |
| ECB real GDP | 2026Q1 | 28 July 2026 |
| ECB macro block | by column: `logS` 2026-07, `DFR` 2026-08, `UNRATE` 2026-06, `logIP` 2026-05, `HICP_YOY` 2026-07 | fetch of 28 July 2026 |
| ECB HICP index (`ICP.M.U2.Y.000000.3.INX`) | November 2025 | 30 December 2025 (the vintage the tail closures `HICP_MIN`, `HICP_MAX` come from) |
| NY Fed survey workbooks | the five instances listed above | as published |
| Global Macro Database | release 2025_12 | — |
| Barro–Lee | the 1994 distribution | — |

## Vintages and comparability

Three properties of this data are not bugs and must be stated wherever a number is:

1. **The estimation sample is frozen.** Rounds fielded through 2026Q2 enter the fit (109 rounds after the $[-1, 5]$ round rule); the 2026Q3 round, published after the cutoff, is held out. A refresh must not pull it in quietly.
2. **The asymmetry index normalises by a full-sample interquartile range**, so adding a round rescales the whole history. Two extra rounds moved the scale by 8.3%. Any statement about a historical level of that index is conditional on the sample it was computed in.
3. **A grid change is a measurement change.** Where a questionnaire changes width, measured variance moves for reasons that have nothing to do with beliefs; Sheppard's correction removes part of it, never all.

## Licences

The code in this repository is MIT. The exhibits it produces are CC BY 4.0. **The data is not covered by either**: each provider sets its own terms, which you accept when you download the file. Cite the data sources as well as the papers.
