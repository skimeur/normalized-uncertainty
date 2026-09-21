# Changelog

This repository is built in phases; each release records the state of the two papers and the data vintage the exhibits were produced on.

## Unreleased

### 2026-09-21 — the fitted calibration aligned with the papers

- `NU_R_FITTED` is now 2.23, the ratio of the law on the average individual predictive variance (0.855/0.383): what the denominator divides is one forecaster's density. The round-mean total variance keeps its own ratio, 4.48, in `CERTIFIED` as `total_r_plus`; it is not the calibration. Both papers made the same change on 2026-09-21.
- `CERTIFIED` gains `W_r_plus` and `epu_corr_nu_fitted` (0.785). `corr_nu_ngu` is now the full-sample correlation, 0.66, with the credit-sample quarters' −0.06 beside it.
- The $[-1, 5]$ rule is described as coded: a round rule for the round-level law, which removes 2022Q4 through 2026Q2, and a per-density rule in the pooled individual fits.

### 2026-09-18 — repository opened (phase G1)

Skeleton and shared library started.

- Repository created, private. It becomes public when *Tolerable Inflation, Intolerable Uncertainty* is posted.
- Licences (MIT for code, CC BY 4.0 for produced exhibits), citation metadata (`CITATION.cff`, `codemeta.json`), packaging, `Makefile`, continuous integration.
- Public-safety gate (`scripts/check_public_safe.py`) active from the first commit: it refuses restricted code, redistributed data, local paths and internal working files. It runs in CI and as a test.
- Library: sample calendar and conventions (`calendar.py`), moments from binned density forecasts (`moments.py`), the NU and NGU measures and the orthogonalisation (`measures.py`), the two-arm variance law with its Wald tests and the kink profile (`law.py`), the house plotting style (`plotting.py`).
- Documentation: `docs/METHODS.md` (constructions, conventions, traps), `data/README.md` (every source with its keys, terms and download page), one page per paper with its exhibit map.
- No data is distributed, by design: the sources are downloaded from their official homes and the derived panels are built locally.

### Next

- **G2** — the readers for each public source (`io_*`), then the reproduction gates: the ECB-SPF individual panel, the US SPF panel and the certified law reproduced exactly before anything is extended.
- **G3** — the exhibits of *Uncertain and Asymmetric Forecasts* v4, produced on the pipeline extended to the latest survey round.
- **G4** — the public-data exhibits of *Tolerable Inflation, Intolerable Uncertainty*, once the manuscript's numbers are frozen.
- **G5–G6** — pre-publication audit, first public release, Zenodo DOI, and the repository URL added to both papers.

Pending from the author: the exact dependency lock, frozen when the reproduction gates first run end to end; the preferred citation switches to *Tolerable Inflation, Intolerable Uncertainty* when that paper is posted.
