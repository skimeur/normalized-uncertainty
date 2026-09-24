#!/usr/bin/env python3
"""Figure 14 of *Uncertain and Asymmetric Forecasts*: period-by-period anatomy of raw and corrected moments.

Paper: Vansteenberghe, E. (forthcoming), *Uncertain and Asymmetric Forecasts*,
working paper (``vansteenberghe2026uncertain``), Section 7, Figure 14
(``fig:mc_decomposition``).

Strategy E of the simulation in ``_simulation.py``: one extended run
(T = 400, seed 42) drawn in four panels -- the latent target and the median
forecast, with the artifact episodes shaded; raw individual uncertainty and
NU against genuine uncertainty; raw asymmetry and AC against the noise-free
coherent signal; and the exact decomposition of raw individual uncertainty
into its structural, genuine and idiosyncratic parts -- plus 200 replications
for the decomposition statistics written to the results file.

Inputs:  none (simulated).
Outputs: ``figures/fig14_mc_decomposition.{pdf,png}``, ``results/fig14_mc_decomposition.{json,md}``.

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use
this code, cite the paper above.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from _simulation import PARAMS, SEED, ols_r2, plot_E, strategy_E

from nu_measures.exhibit import Exhibit


def main() -> None:
    ex = Exhibit(__file__)
    plt.rcdefaults()  # the manuscript's figure was drawn on matplotlib's defaults
    plt.rcParams["savefig.bbox"] = "tight"
    ex.say(f"strategy E: one run of T = 400 and 200 replications, seed {SEED} ...")
    res = strategy_E(PARAMS)
    single = {"r2_rawIU_u": ols_r2(res["rIU"], res["u"]), "r2_NU_u": ols_r2(res["NU"], res["u"]),
              "r2_rawS_delta": ols_r2(res["rS"], res["delta"]), "r2_AC_delta": ols_r2(res["AC"], res["delta"]),
              "r2_rawS_nfAC": ols_r2(res["rS"], res["AC_nf"]), "r2_AC_nfAC": ols_r2(res["AC"], res["AC_nf"]),
              "mean_structural_share": float(np.mean(res["S"] / res["rIU"])),
              "structural_share_q05": float(np.quantile(res["S"] / res["rIU"], 0.05)),
              "structural_share_q95": float(np.quantile(res["S"] / res["rIU"], 0.95)),
              "artifact_episodes": [[int(s), int(e)] for s, e in res["episodes"]]}
    ex.say(f"single run: R2(raw IU, u) {single['r2_rawIU_u']:.3f}, R2(NU, u) {single['r2_NU_u']:.3f}; "
           f"R2(raw Bowley, AC nf) {single['r2_rawS_nfAC']:.3f}, R2(AC, AC nf) {single['r2_AC_nfAC']:.3f}; "
           f"structural share {single['mean_structural_share']:.0%} "
           f"({single['structural_share_q05']:.0%}-{single['structural_share_q95']:.0%}); {len(res['episodes'])} episodes")
    mc = {k: {"mean": float(v.mean()), "q05": float(np.percentile(v, 5)), "q95": float(np.percentile(v, 95))}
          for k, v in res["mc_stats"].items()}
    for k, v in mc.items():
        ex.say(f"  {k:<16} mean {v['mean']:.4f}  90% [{v['q05']:.4f}, {v['q95']:.4f}]")
    fig = plot_E(res)
    ex.save_figure(fig)
    ex.write_results({"parameters": PARAMS, "seed": SEED, "T": 400, "single_run": single, "replications": 200, "mc": mc},
                     "Figure 14 — period-by-period anatomy of raw and corrected moments")


if __name__ == "__main__":
    main()
