# Normalized Uncertainty

**Two measures for anyone with a survey of density forecasts and an announced target — Normalized Uncertainty (NU) and Asymmetry Coherence (AC) — and the code behind the two working papers that introduce and apply them**, by **Eric Vansteenberghe** (Banque de France; Université Paris 1 Panthéon-Sorbonne).

Raw forecast dispersion is not a measure of uncertainty. A large part of it records how far expected inflation sits from the central bank's announced target: the variance of a forecaster's density is flat while expected inflation is at or below the target and rises with the expected overshoot above it. NU removes that arithmetic; AC reads directional risk only where the asymmetry of a density is coherent with its central forecast.

> **Status — private, under construction.** The repository becomes public when *Tolerable Inflation, Intolerable Uncertainty* is posted. Both manuscripts embed the figures and tables produced here and point to this repository as their replication code. See [CHANGELOG.md](CHANGELOG.md).

---

## The measures

For a forecaster *i* reporting a density with mean $\mu_i$ and standard deviation $\sigma_i$ in round *t*, with the announced target $\pi^\star$ (2 per cent for the ECB):

### Normalized Uncertainty, $a = b = 1$

$$\mathrm{NU}_i \;=\; \frac{\sigma_i}{\sqrt{1 + (\mu_i - \pi^\star)_+}}$$

Three numbers per forecaster and **no estimate**: the value of a forecaster-round is the same whatever the sample it is computed in, so the measure does not depend on the history or on the observation window. A series computed today and one computed after ten more survey rounds agree on every common round. The round's NU is the mean across forecasters.

The denominator is one-sided because the target is announced: below the number there is nothing to explain away. It comes from the law of the predictive variance measured in the papers,

$$V(d) \;=\; a \;+\; b_-\,(-d)_+ \;+\; b_+\,(d)_+ , \qquad d = \mu - \pi^\star,$$

flat below the announced number and rising above it. The **fitted** reading, $\sigma_i/\sqrt{1 + r\,(\mu_i-\pi^\star)_+}$ with $r = b_+/a = 2.23$ estimated on the euro-area panel through 2026Q2, is the papers' own estimate and stays available as an option (`r=NU_R_FITTED`); the unit calibration is the default of every function in this library.

### Asymmetry Coherence

For each forecaster, the median of the density minus the target, $Q$, and the Bowley skewness of the density smoothed over two rounds, $A$, are each scaled by an interquartile range and passed through $\tanh$ so that they live in $(-1,1)$; the individual index is

$$\mathrm{AC} \;=\; \frac{\tilde Q + \tilde A}{2}\cdot\frac{1 + \tilde Q \tilde A}{2} \;\in\; [-1, 1],$$

and the round's AC is its mean across forecasters. The first factor is the signed directional signal; the second, the *coherence weight*, is above one half when the two components agree in sign and below it when they disagree. The interquartile ranges are the one thing to decide before using AC across vintages: computed on the sample at hand they rescale the whole history when rounds are added, so every function here takes the normalisation window as an explicit argument and reports the scales it used.

### The growth analogue

**Normalized Growth Uncertainty** applies the same correction to growth densities, $\mathrm{NGU}_i = \sigma^g_i / \sqrt{1 + |\mu^g_i - g^{\mathrm{pot}}_t|}$, with potential growth (a Hodrick–Prescott trend) in place of the announced target and a symmetric denominator, since a benchmark that is estimated rather than announced has no side on which a deviation must be explained.

## Use them in five lines

```python
from nu_measures import io_ecb_spf, measures, asymmetry

flat  = io_ecb_spf.flat_panel(io_ecb_spf.read_rounds("ecb_spf/rounds"))  # the ECB's round files
panel = io_ecb_spf.individual_panel(flat)                                 # moments of every density
nu    = measures.nu_series(panel)                                          # raw_sd, NU_unit, NU_fitted by round
ac    = asymmetry.ac_series(asymmetry.ac_panel(panel))                     # components, weight, AC by round
```

On any other survey, `measures.nu(sigma, mean, target)` needs only the three numbers. [`examples/nu_and_ac_from_ecb_spf.py`](examples/nu_and_ac_from_ecb_spf.py) does the above from the round files, prints the latest rounds and draws both series; [`examples/quickstart.py`](examples/quickstart.py) runs on synthetic inputs and needs no data.

---

## The papers

### Uncertain and Asymmetric Forecasts

The construction of the measures: NU, NGU and AC, the law they rest on, and the evidence that the corrected series agree better with an independent text-based index of uncertainty than the raw ones.
arXiv: [2411.05938](https://arxiv.org/abs/2411.05938) · SSRN: [4995675](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4995675) — package: [`papers/uncertain-and-asymmetric-forecasts/`](papers/uncertain-and-asymmetric-forecasts/), every exhibit on public data.

```bibtex
@unpublished{vansteenberghe2026uncertain,
  author = {Vansteenberghe, Eric},
  title  = {Uncertain and Asymmetric Forecasts},
  note   = {Working paper},
  year   = {forthcoming}
}
```

### Tolerable Inflation, Intolerable Uncertainty

The principal application: the law of the predictive variance around an announced target measured across sources, what a numerical target does to second moments, and what the purge changes in the transmission of uncertainty to credit and activity. Links are added when the paper is posted — package: [`papers/tolerable-inflation-intolerable-uncertainty/`](papers/tolerable-inflation-intolerable-uncertainty/), the public-data exhibits, with the market numbers carried as printed and flagged; the credit legs are described, not reproduced.

```bibtex
@unpublished{vansteenberghe2026tolerable,
  author = {Vansteenberghe, Eric},
  title  = {Tolerable Inflation, Intolerable Uncertainty},
  note   = {Working paper, Banque de France},
  year   = {2026}
}
```

Cite the paper whose result you use — *Uncertain and Asymmetric Forecasts* for the construction of the measures, *Tolerable Inflation, Intolerable Uncertainty* for the law, the identification results and the purge — and, if you use the code itself, this repository ([CITATION.cff](CITATION.cff); a DOI is minted at the first public release).

---

## What is here, and what is not

**Here.** `src/nu_measures/` — the library: the readers for each public source (the ECB-SPF round files to the flat and individual panels, the Philadelphia Fed microdata, the ECB Data Portal, FRED, the EPU workbook), the moments of a binned density, NU / NGU / AC, the two-arm law with its tests, the estimators with the papers' conventions named, and the house plotting style. `papers/<paper>/exhibits/` — one script per figure and table of each paper, each writing its exhibit *and* a results file recording every number it prints. `docs/METHODS.md` — the constructions, the sample and the conventions, for someone who has not read the papers. `tests/` — unit tests on synthetic inputs, and reproduction tests that run when the data is present.

**Not here: data.** No third-party file is redistributed. Every source is named in [`data/README.md`](data/README.md) with its keys, its download page and its terms; `make data` reports which ones are present locally. Point `NU_DATA_DIR` at the folder holding them.

**Not here: restricted material.** Two parts of *Tolerable Inflation, Intolerable Uncertainty* rest on data that cannot be redistributed and whose code is not published: the loan-level credit application (AnaCredit, Banque de France internal) and the inflation-swap and option legs of the market evidence (licensed Bloomberg exports). Both are documented, specification and sample, in [`papers/tolerable-inflation-intolerable-uncertainty/restricted/README.md`](papers/tolerable-inflation-intolerable-uncertainty/restricted/README.md). Where a published exhibit combines the two, the script here computes the survey part and carries the market coefficients as printed in the paper, flagged as not computed.

## Reproduction, and what "certified" means

The individual panel rebuilt from the ECB's round files is byte-identical to the authoritative panel the papers run on (4,638 forecaster-rounds, 111 rounds, 1999Q1–2026Q3); the law on it prints the papers' numbers ($a = 0.383$, $b_- = 0.004$, $b_+ = 0.855$, $R^2 = 0.71$ on the average individual variance; $0.4204$, $0.1173$, $1.8825$, $0.789$ on the total; $n = 109$); the kink profile, the bootstrap, the AC index and the agreement with the independent proxy (raw $0.746$, NU $0.848$) reproduce to their printed digits. These are the tests of `tests/test_reproduction.py`, run with the data present; `nu_measures.conventions.CERTIFIED` lists the numbers.

## Quick start

```bash
git clone https://github.com/skimeur/normalized-uncertainty.git
cd normalized-uncertainty
python3 -m pip install -e ".[dev]"

make test          # unit tests on synthetic inputs; no data needed
make data          # which of the sources in data/README.md are present
export NU_DATA_DIR=/path/to/your/data
python3 examples/nu_and_ac_from_ecb_spf.py     # NU (a = b = 1) and AC from the round files
make uaf           # rebuild the exhibits of the first paper
make tolerable     # rebuild the public-data exhibits of the second
```

## Related work by the author

- **Monetary Policy, Uncertainty, and Credit Supply**, arXiv [2512.12255](https://arxiv.org/abs/2512.12255), 2025.
- **Inflation and growth: professional forecasters continue to express high levels of uncertainty**, [Banque de France Eco Notepad No. 436](https://www.banque-france.fr/en/publications-and-statistics/publications/inflation-and-growth-professional-forecasters-continue-express-high-levels-uncertainty), 27 February 2026.
- **Seventy Years of Identifying the Phillips Curve and the Policy Rule**, working paper.
- **Pioneer Detection Method**, an expert-aggregation method that weights the experts others converge toward: [github.com/skimeur/pioneer-detection-method](https://github.com/skimeur/pioneer-detection-method).

Full list: [Google Scholar](https://scholar.google.com/citations?user=KInXUlUAAAAJ) · [ORCID 0009-0004-4566-4043](https://orcid.org/0009-0004-4566-4043) · [Banque de France](https://www.banque-france.fr/en/eric-vansteenberghe).

## Licence and disclaimer

Code: [MIT](LICENSE). Figures, tables and results files: [CC BY 4.0](LICENSE-DATA). Third-party data stays with its provider under that provider's terms ([`data/README.md`](data/README.md)).

The views expressed here are those of the author and do not necessarily reflect those of the Banque de France or the Eurosystem.

Contact: eric.vansteenberghe@banque-france.fr
