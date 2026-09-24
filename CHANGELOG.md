# Changelog

This repository is built in phases; each release records the state of the two papers and the data vintage the exhibits were produced on.

## Unreleased

### 2026-09-24 — the manuscripts embed the package's outputs and cite the repository (phase G5)

- **Both manuscripts now include the files this repository produces** — every figure PDF in `papers/<paper>/figures/` and every table in `papers/<paper>/tables/` — copied verbatim into their builds; those PDFs and `.tex` files are now committed (the PNG previews the scripts also write stay local), and each manuscript acknowledges *Replication code for every figure and table, and for the measures themselves, is available at https://github.com/skimeur/normalized-uncertainty*. The paper pages say so exhibit by exhibit.
- **Conventions the manuscripts adopted from the package on that occasion.** *Uncertain and Asymmetric Forecasts*: Figure 2 on the exact identity (mean individual variance plus disagreement, missing cells read as no mass, through the latest round) with the identity stated in Section 2; Figure 14 the current rendering with its caption rewritten to the panels as drawn; Table 3 prints $R^2 = 0.011$ and Table 5 $t = 8.9$, rounded once; Table 5's "old grid" row is the old grid before the 2012 announcement. *Tolerable Inflation, Intolerable Uncertainty*: Table 1's US row clustered by survey round, $(0.59)$ and $(2.67)$ (the Newey–West statistics of the stacked observations kept in the results file); Figure 3 and Appendix A.8 on the caption's denominator — respondents who reported a longer-term point (`DENOMINATOR = "reporting"`), so 39 to 52 respondents per round over the fit window, $r = 0.66$, RMSE 0.062, the expected-gap clock at $\eta = 0.18$ and $r = 0.58$, and the re-basing feedback numbers that follow (`fig03_benefit_of_doubt.rebasing_feedback` computes them); Table 5's extended rows on the December 2025 HICP vintage's tail closure ($+0.299$, $+0.226$; the respondent-filter check $+0.297$ against $+0.299$); the realized-shadow arm $0.377$; the share of the variation the distance explains printed $70\%$ (from 70.45, rounded once); Figure 2's excluded point 19.5, and the daily overlapping statistic quoted at sixty-three lags ($t \approx 13$) beside the one-lag $29$.
- `fig03_benefit_of_doubt.py` computes the re-basing feedback block of Appendix A.8 (the excess of re-based longer-term points over the target, the move at the crossing, the within-round difference, and the margin, multiplier, decay and half-lives on both clocks) and keeps the earlier all-rows denominator under `with_the_all_rows_denominator`; `tab01_arms_by_source.py` clusters the US row by round; `figA_abel2016_replication.py` also writes the appendix's reading of Abel et al.'s null through the law (the arms form on their window and on the full sample, fitted on their variance-based measure: $b_+ = +0.61$, the above-target regressor's spread 0.057 against 0.374, its sum 0.9 against 10.9 points), under `arms_form_on_their_measure`.

### 2026-09-24 — the public-data exhibits of *Tolerable Inflation, Intolerable Uncertainty* (phase G4)

- **Twelve scripts** in `papers/tolerable-inflation-intolerable-uncertainty/exhibits/`: seven figures, the appendix's replication figure with its table, three tables and `results_register.py` (every number of the survey law on one sample, from which the paper page's key-numbers table is generated); `run.py` rebuilds them in order. Checked against the manuscript: Figures 1, 3, 5, 6, 7 and Tables 1, 3, 6 identical; Figure 2 identical but for a hand-typed label; Figure 4 drawn from the printed market coefficients; the replication table identical on the authors' sample, one thousandth apart on the extended rows (HICP vintage of the tail closure).
- **Market legs carried as printed**: the swap and option numbers of Figures 1 and 4, Table 1 and Appendix A.8 are named constants flagged `computed: false` in the results files; `restricted/README.md` says so, exhibit by exhibit.
- **Inputs added**: FRED `T10YIE` and `CPILFESL`, the NY Fed workbooks under `nyfed/`, the Barro–Lee long file and the Global Macro Database under `crosscountry/` (`make data` reports them); the scenario matrices read from published PDFs travel with the repository as `inputs/nyfed_scenario_matrices_pdf_read.csv`, each row with its source. `tab03_cross_country.py` builds Barro's panel from the source when present and reads the panel it last built otherwise.
- Library: `io_ecb_spf.longer_term_points` / `longer_term_panel` (the four-to-five-years-ahead points of a round file), `exhibit.load_longer_term_points`; `law.kink_bootstrap` accepts a shared generator; `econometrics.wild_cluster_p` gains `add_one`.
- The retired subtitle of the tolerance paper removed from the package page and the library docstring.

### 2026-09-24 — the exhibits of *Uncertain and Asymmetric Forecasts* (phase G3)

- **Twenty scripts** in `papers/uncertain-and-asymmetric-forecasts/exhibits/`, one per figure and table of the manuscript (14 figures, 6 tables), each writing its exhibit and a results file; `run.py` rebuilds them in manuscript order. Checked against the manuscript: the six table files byte-identical but for two cells the manuscript had rounded twice (Table 3, $R^2$ 0.0115 printed 0.012; Table 5, $t = 8.947$ printed 9.0), eleven figures pixel-identical, two illustrations regenerated from their parameters (Figures 3 and 7), Figure 14 identical to the current output of the simulation code.
- **Figure 2** draws the equal-weight average of the individual densities with every missing cell read as no mass, so that the variance of the averaged density equals $W + D$ exactly (`io_ecb_spf.averaged_density`, the panel builder's preprocessing factored into `_prepare`); the manuscript's file, produced by an older script that averaged the reported cells only, overstated disagreement.
- `_common.style()` restores matplotlib's defaults before applying the manuscript's settings (the library's house style, which `Exhibit` applies, was leaking into the paper's figures); title and legend sizes are per-figure arguments.
- `_simulation.py`: the Monte Carlo of Section 7 (DGP, measures, strategies A, B, E, the four-panel figure), transcribed from the internal script with the same seed and draw order.
- `io_other.monthly_yoy`: year-on-year change lagged by calendar month, so a month skipped by a release (FRED's October 2025 CPI) does not shift the lag; `exhibit.load_us_quartiles` for the core questions' quartiles.
- Table 5's "old grid" row documented as the old grid before the 2012 announcement (81 rounds); the eight old-grid rounds of 2012–2013 go to the results file.
- Lint: `UP031` (printf-style formatting) ignored — the LaTeX cell templates read better that way.

### 2026-09-24 — the library completed (phase G2): readers, the certified pipeline, AC, NU at a = b = 1 by default

- **NU defaults to the unit calibration**, $r = 1$ ($a = b = 1$): no estimate, hence the same value for a forecaster-round whatever the sample; the fitted reading stays available through `r=NU_R_FITTED`, which now carries the ratio of the certified fit at full precision (2.2322, printed 2.23), as the papers' scripts do. `README.md`, `docs/METHODS.md` and the paper pages lead with the unit form.
- **Readers.** `io_ecb_spf` (the ECB round files to the flat and individual panels, the authoritative builder reproduced line for line; `build_panels` is the pipeline step), `growth` (the growth block, potential growth, NGU), `io_us_spf` (the Philadelphia Fed workbook), `io_ecb_data_portal` (the macro block, HICP, real GDP; the dataflow derived from the key, candidates probed, coverage printed), `io_other` (FRED, the EPU basket), `paths` (`NU_DATA_DIR`).
- **`asymmetry`**: Asymmetry Coherence, individual and by round, with the normalisation window an explicit argument and the scales reported.
- **`econometrics`**: the estimators with the papers' conventions named — Newey–West with the $n/(n-k)$ factor, White, cluster-robust, the restricted wild-cluster bootstrap, Wald; tests check them against `statsmodels`.
- **`law`**: round aggregates ($W$, $D$, $T$), the estimation sample, the law by object, the delta-method ratio, the split test, the kink profile and its bootstrap; the individual within/between split of the first commit, which no paper reports, is removed.
- **Reproduction tests** (`tests/test_reproduction.py`, run with the data present): the rebuilt individual panel byte-identical to the certified one; the law, the kink, AC and the EPU agreement at their printed digits; the US panel rebuilt to $10^{-15}$.
- `calendar.py` renamed `conventions.py` (the old name shadowed the standard library's `calendar` when Python was started inside the package folder); exact tail closures (`HICP_MIN`, `HICP_MAX`), the grid tables of both questionnaires, the AC conventions and `NU_R_DEFAULT` added.
- Citation blocks of both papers as the author gives them (`vansteenberghe2026tolerable`: "Working paper, Banque de France", 2026; `vansteenberghe2026uncertain`: "Working paper", forthcoming) in the README, the paper pages, `CITATION.cff` and `codemeta.json`; the retired subtitle of the tolerance paper removed everywhere.
- `examples/nu_and_ac_from_ecb_spf.py`: NU ($a = b = 1$) and AC from the round files in five steps, the AC window frozen on the papers' sample.

### 2026-09-21 — the fitted calibration aligned with the papers

- `NU_R_FITTED` is now 2.23, the ratio of the law on the average individual predictive variance (0.855/0.383): what the denominator divides is one forecaster's density. The round-mean total variance keeps its own ratio, 4.48, in `CERTIFIED` as `total_r_plus`; it is not the calibration. Both papers made the same change on 2026-09-21.
- `CERTIFIED` gains `W_r_plus` and `epu_corr_nu_fitted` (0.785). `corr_nu_ngu` is now the full-sample correlation, 0.66, with the credit-sample quarters' −0.06 beside it.
- The $[-1, 5]$ rule is described as coded: a round rule for the round-level law, which removes 2022Q4 through 2026Q2, and a per-density rule in the pooled individual fits.

### 2026-09-18 — repository opened (phase G1)

Skeleton and shared library started.

- Repository created, private. It becomes public when *Tolerable Inflation, Intolerable Uncertainty* is posted.
- Licences (MIT for code, CC BY 4.0 for produced exhibits), citation metadata (`CITATION.cff`, `codemeta.json`), packaging, `Makefile`, continuous integration.
- Public-safety gate (`scripts/check_public_safe.py`) active from the first commit: it refuses restricted code, redistributed data, local paths and internal working files. It runs in CI and as a test.
- Library: sample calendar and conventions (`conventions.py`), moments from binned density forecasts (`moments.py`), the NU and NGU measures and the orthogonalisation (`measures.py`), the two-arm variance law with its Wald tests and the kink profile (`law.py`), the house plotting style (`plotting.py`).
- Documentation: `docs/METHODS.md` (constructions, conventions, traps), `data/README.md` (every source with its keys, terms and download page), one page per paper with its exhibit map.
- No data is distributed, by design: the sources are downloaded from their official homes and the derived panels are built locally.

### Next

- **G6** — pre-publication audit, first public release, Zenodo DOI.

Pending from the author: the exact dependency lock, frozen when the reproduction gates first run end to end; the preferred citation switches to *Tolerable Inflation, Intolerable Uncertainty* when that paper is posted.
