# Uncertain and Asymmetric Forecasts

**Eric Vansteenberghe** (Banque de France; Université Paris 1 Panthéon-Sorbonne)
arXiv: [2411.05938](https://arxiv.org/abs/2411.05938) · SSRN: [4995675](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4995675)
Versions: v1 8 November 2024 · v2 19 January 2026 · v3 19 March 2026 · **v4 in preparation**

> Forecasts uncertainty and directional risk are commonly proxied by the second and third moments of forecast distributions. We show that these proxies can be improved by incorporating interactions with the first moment, though the mechanisms differ fundamentally across the two. Using individual density forecasts from the ECB Survey of Professional Forecasters, this paper shows that 42% of the variation in raw forecast variance is explained by the distance of expected inflation from target—a mechanical level effect—while raw asymmetry is too noisy to identify directional risk unless disciplined by the central forecast. We propose two complementary corrections grounded in micro-founded mechanisms. *Normalized Uncertainty* (NU) separates the first from the second moment by purging dispersion of its predictable component driven by the distance of forecasts from a policy anchor, thus isolating genuine belief imprecision. *Asymmetry Coherence* (AC) re-entangles the first and third moments by extracting directional risk only when observed asymmetry is coherent with the central forecast, providing an operational formalization of the balance of risks.

*Keywords:* Uncertainty, Asymmetry, Balance of Risks, Predictive Distributions, Monetary Policy, Growth. *JEL:* C53, D81, D84, E31, E37, E43, E52.

```bibtex
@unpublished{vansteenberghe2026uncertain,
  author = {Vansteenberghe, Eric},
  title  = {Uncertain and Asymmetric Forecasts},
  note   = {arXiv:2411.05938},
  year   = {2026},
  url    = {https://arxiv.org/abs/2411.05938}
}
```

---

## What this package covers

Every exhibit of this paper runs on **public data**: the ECB Survey of Professional Forecasters, the Philadelphia Fed survey, ECB Data Portal series, and the Economic Policy Uncertainty workbook as an outside check. There is no restricted route here.

The fourth version narrows the paper to what it does best — **the construction of the measures**: Normalized Uncertainty, Normalized Growth Uncertainty with its orthogonalisation, and Asymmetry Coherence. The policy applications that filled the earlier versions move out; the measures, their validation and their comparison stay. The scripts in this folder are written against that version, and every number in it is produced by one of them.

Two consequences for a reader comparing with v3. First, the abstract's "42%" belongs to the earlier sample and the symmetric distance specification; it is replaced by the number the corresponding regression produces on the current sample. Second, the measures are named NU, NGU, AC and ACG throughout — the earlier names NIU and ACI are the same objects under older labels.

## Exhibits

The map below is the target of the rebuild; nothing is produced yet.

| # | Label | What it shows | Status |
|---|---|---|---|
| F1 | `fig:var_decomposition` | the decomposition of dispersion in the averaged density | planned |
| F2 | `fig:two_spd_skew` | two densities with the same variance and opposite directional content | illustration, kept as is |
| F3 | `fig:arms_fit` | the variance against the consensus gap, with the two-arm fit | planned |
| F4 | `fig:nu_series` | raw, fitted NU and unit NU; and the series against an independent proxy | planned |
| F5 | `fig:skewed_distributions` | strong and weak directional signals, four cases | planned |
| F6 | `fig:ac_series` | upside and downside risk around the median | planned |
| F7 | `fig:ngu_series` | raw growth dispersion against NGU, and NGU against the proxy | planned |
| F8 | `fig:nu_ngu_orth` | the two measures and their orthogonalised components | planned |
| F9 | `fig:us_arms` | the US questions: core measures, and the GDP-price grid change marked | planned |
| F10 | `fig:mc_decomposition` | the simulation: what the correction recovers that raw moments do not | planned |
| T1 | `tab:arms` | the envelope: symmetric against two-arm; within and between; Wald tests | planned |
| T2 | `tab:nu_raw_regs` | what the normalisation removes | planned |
| T3 | `tab:skew_dev_regs` | asymmetry against the deviation of the central forecast | planned |
| T4 | `tab:momentscorr` | how the moment-based measures relate to one another | planned |
| T5 | `tab:mc_summary` | the simulation summary | planned |
| T6 | `tab:ngu_orth` | the orthogonalisation: correlations, own-slope and pooled-slope forecasters | planned |
| T7 | `tab:us_arms` | the arms by US question, with and without the grid control | planned |

Each script writes its exhibit **and** a results file recording every number it prints, with the sample it was computed on. The paper quotes numbers from those files and nowhere else.

## Running it

```bash
export NU_DATA_DIR=/path/to/your/data     # see ../../data/README.md
make uaf                                  # or: python3 run.py
```

## Sample

One vintage for the whole paper: the latest complete survey round at the time of the rebuild, stated once in the text and in every table note. The $[-1, 5]$ per cent rule applies to the round consensus in round-level estimates (it removes 2022Q4) and to each density in pooled fits; the date convention is in [`../../docs/METHODS.md`](../../docs/METHODS.md) §3. Before the sample is extended to a newer round, the numbers of the frozen sample are reproduced exactly — a change in magnitude is carried and reported, a change in sign or in significance class stops the rebuild.
