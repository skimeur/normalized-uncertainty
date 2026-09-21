# Normalized Uncertainty

Measures of uncertainty and directional risk built from survey density forecasts, and the code behind two working papers by **Eric Vansteenberghe** (Banque de France; Université Paris 1 Panthéon-Sorbonne).

Raw forecast dispersion is not a measure of uncertainty: a large part of it records how far expected inflation sits from the central bank's announced target. **Normalized Uncertainty (NU)** removes that predictable component; **Normalized Growth Uncertainty (NGU)** does the same for growth, where a benchmark exists but no announced target; **Asymmetry Coherence (AC)** extracts directional risk only where observed asymmetry is coherent with the central forecast. This repository holds the implementation of those measures and the scripts that produce the exhibits of the two papers below from public data.

> **Status — private, under construction.** The measure library and the two paper packages are being built phase by phase; the reproduction gates against the authoritative survey panels run before the first release. The repository becomes public when *Tolerable Inflation, Intolerable Uncertainty* is posted. See [CHANGELOG.md](CHANGELOG.md).

---

## The papers

### Uncertain and Asymmetric Forecasts

**Eric Vansteenberghe** (Banque de France; Université Paris 1 Panthéon-Sorbonne)
arXiv: [2411.05938](https://arxiv.org/abs/2411.05938) · SSRN: [4995675](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4995675) · versions: v1 8 November 2024, v2 19 January 2026, v3 19 March 2026 (v4 in preparation)

> Forecasts uncertainty and directional risk are commonly proxied by the second and third moments of forecast distributions. We show that these proxies can be improved by incorporating interactions with the first moment, though the mechanisms differ fundamentally across the two. Using individual density forecasts from the ECB Survey of Professional Forecasters, this paper shows that 42% of the variation in raw forecast variance is explained by the distance of expected inflation from target—a mechanical level effect—while raw asymmetry is too noisy to identify directional risk unless disciplined by the central forecast. We propose two complementary corrections grounded in micro-founded mechanisms. *Normalized Uncertainty* (NU) separates the first from the second moment by purging dispersion of its predictable component driven by the distance of forecasts from a policy anchor, thus isolating genuine belief imprecision. *Asymmetry Coherence* (AC) re-entangles the first and third moments by extracting directional risk only when observed asymmetry is coherent with the central forecast, providing an operational formalization of the balance of risks.

*Keywords:* Uncertainty, Asymmetry, Balance of Risks, Predictive Distributions, Monetary Policy, Growth. *JEL:* C53, D81, D84, E31, E37, E43, E52.

Package: [`papers/uncertain-and-asymmetric-forecasts/`](papers/uncertain-and-asymmetric-forecasts/) — all exhibits run on public data.

```bibtex
@unpublished{vansteenberghe2026uncertain,
  author = {Vansteenberghe, Eric},
  title  = {Uncertain and Asymmetric Forecasts},
  note   = {arXiv:2411.05938},
  year   = {2026},
  url    = {https://arxiv.org/abs/2411.05938}
}
```

### Tolerable Inflation, Intolerable Uncertainty

**Eric Vansteenberghe** (Banque de France; Université Paris 1 Panthéon-Sorbonne)
Working paper, September 2026 — links added when the paper is posted.

> Numerical inflation targets anchor beliefs. Across euro-area and US professional forecasts, inflation swaps and options, and realized inflation, uncertainty about inflation is compressed at the announced number and kinks exactly there. This paper identifies a cost of the same design that, to our knowledge, has not been shown before, and that appears in second moments only. Within the workhorse New Keynesian model, tolerating part of the inflation a supply shock produces is optimal, yet the optimal tolerated share is not identified: optimal look-through and an unwarranted drift of the effective target are observationally equivalent in the inflation history, so a central bank cannot demonstrate that a warranted deviation is warranted, ex post as much as in real time. Agents holding finite, heterogeneous patience then generate predictive variance that is flat below the target and rises linearly with the expected overshoot above it—an observational-equivalence bill, zero at the announced number and accumulating with the point-years inflation spends above it. The first-order benefit of the number stands; what the cost changes is how inflation uncertainty must be measured. The distance from target explains 71% of the variation in professional forecast variance, and the bill lies within that component; Normalized Uncertainty—to our knowledge the first such correction—removes it.

*Keywords:* Uncertainty, Tolerance, Observational Equivalence, Identification, Monetary Policy, Inflation. *JEL:* C18, D81, E31, E52, E58.

Package: [`papers/tolerable-inflation-intolerable-uncertainty/`](papers/tolerable-inflation-intolerable-uncertainty/) — public-data exhibits; the market and credit legs are described but not reproducible here (see below).

```bibtex
@unpublished{vansteenberghe2026tolerable,
  author = {Vansteenberghe, Eric},
  title  = {Tolerable Inflation, Intolerable Uncertainty: The Unidentifiable Optimum of Monetary Policy},
  note   = {Working paper},
  year   = {2026}
}
```

---

## What is here, and what is not

**Here.** `src/nu_measures/` — the shared library: moments from binned density forecasts, the NU / NGU / AC measures, the two-arm variance law with its tests, the readers for each public source, and the plotting style. `papers/<paper>/exhibits/` — one script per figure and per table, each writing its exhibit *and* a results file recording every number it prints. `docs/METHODS.md` — the constructions, the sample conventions and the traps, written to be read by someone who has never seen this project.

**Not here: data.** No third-party file is redistributed. Every source is named in [`data/README.md`](data/README.md) with its series keys, its download page and its terms, and `make data` reports which ones are present locally. Point `NU_DATA_DIR` at the folder holding them.

**Not here: restricted material.** Two parts of *Tolerable Inflation, Intolerable Uncertainty* rest on data that cannot be redistributed and whose code is therefore not published: the loan-level credit application (AnaCredit, Banque de France internal) and the inflation-swap and option legs of the market evidence (licensed Bloomberg exports). Both are documented, specification and sample, in [`papers/tolerable-inflation-intolerable-uncertainty/restricted/README.md`](papers/tolerable-inflation-intolerable-uncertainty/restricted/README.md), so that a reader with the same access can rebuild them. The survey legs of the same exhibits are published and run here.

---

## Quick start

```bash
git clone https://github.com/skimeur/normalized-uncertainty.git
cd normalized-uncertainty
python3 -m pip install -e ".[dev]"

make test          # unit tests on synthetic inputs; no data needed
make data          # which of the sources in data/README.md are present
export NU_DATA_DIR=/path/to/your/data
make tolerable     # rebuild the public-data exhibits of the second paper
make uaf           # rebuild the exhibits of the first
```

## The measures

For a forecaster *i* reporting a density with standard deviation $\sigma_i$ and mean $\mu_i$ in round *t*, with the central bank's announced target $\pi^\star$ and the expected gap $d_i = \mu_i - \pi^\star$:

| | definition | why |
|---|---|---|
| **NU** (fitted) | $\mathrm{NU}_i = \sigma_i / \sqrt{1 + r\,(d_i)_+}$ | dispersion rises with the *overshoot* only; $r = b_+/a$ is estimated from the two-arm law on the average individual variance (2.23) |
| **NU** (unit) | $\mathrm{NU}_i = \sigma_i / \sqrt{1 + (d_i)_+}$ | the calibration-free reading; both are published on equal footing |
| **NGU** | $\mathrm{NGU}_i = \sigma_i^g / \sqrt{1 + \lvert \mu_i^g - g^{\mathrm{pot}}_t\rvert}$ | growth has a benchmark but no announced number, so the denominator is symmetric |
| **AC** | directional risk retained where asymmetry is coherent with the central forecast | raw asymmetry alone is too noisy to signal the balance of risks |

The denominator comes from the measured law of the predictive variance on the expected gap,

$$V(d) \;=\; a \;+\; b_-\,(-d)_+ \;+\; b_+\,(d)_+ ,$$

flat below the announced number and rising above it. [`docs/METHODS.md`](docs/METHODS.md) gives the estimation sample, the bin conventions, the date rule and the closure of the open top bin.

## How to cite

Cite the paper whose result you are using — *Uncertain and Asymmetric Forecasts* for the construction of the measures, *Tolerable Inflation, Intolerable Uncertainty* for the law, the identification results and the purge — and, if you use the code itself, this repository (see [CITATION.cff](CITATION.cff); a DOI is minted at the first public release).

## Related work by the author

- **Monetary Policy, Uncertainty, and Credit Supply**, arXiv [2512.12255](https://arxiv.org/abs/2512.12255), 2025.
- **Inflation and growth: professional forecasters continue to express high levels of uncertainty**, [Banque de France Eco Notepad No. 436](https://www.banque-france.fr/en/publications-and-statistics/publications/inflation-and-growth-professional-forecasters-continue-express-high-levels-uncertainty), 27 February 2026.
- **Seventy Years of Claimed Identification: The Phillips Curve and the Policy Rule**, working paper.

Full list: [Google Scholar](https://scholar.google.com/citations?user=KInXUlUAAAAJ) · [ORCID 0009-0004-4566-4043](https://orcid.org/0009-0004-4566-4043) · [Banque de France](https://www.banque-france.fr/en/eric-vansteenberghe).

## Licence and disclaimer

Code: [MIT](LICENSE). Figures, tables and results files: [CC BY 4.0](LICENSE-DATA). Third-party data stays with its provider under that provider's terms ([`data/README.md`](data/README.md)).

The views expressed here are those of the author and do not necessarily reflect those of the Banque de France or the Eurosystem.

Contact: eric.vansteenberghe@banque-france.fr
