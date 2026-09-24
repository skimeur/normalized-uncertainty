#!/usr/bin/env python3
"""Figure 4 of *Uncertain and Asymmetric Forecasts*: the variance--distance envelope on the euro-area panel.

Paper: Vansteenberghe, E. (forthcoming), *Uncertain and Asymmetric Forecasts*,
working paper (``vansteenberghe2026uncertain``), Section 3, Figure 4
(``fig:arms_fit``).

Panel (a): the round mean of the individual one-year-ahead inflation density
variances against the signed distance of the consensus forecast from the 2 per
cent target, with the two-arm fit over every round inside the [-1, 5] round
rule (the 2022Q4 round excluded). Panel (b): the individual densities inside
the same interval, with the pooled fit (White standard errors).

Inputs:  the ECB-SPF round files, through ``nu_measures.exhibit.load_ecb_panel``.
Outputs: ``figures/fig04_arms_fit.{pdf,png}``, ``results/fig04_arms_fit.{json,md}``.
Sample:  rounds 1999Q1--2026Q3.

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use
this code, cite the paper above.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from _common import C, style

from nu_measures import conventions as cv
from nu_measures import law
from nu_measures.exhibit import Exhibit, load_ecb_panel


def main() -> None:
    ex = Exhibit(__file__)
    style()
    panel = load_ecb_panel()
    A = law.round_aggregates(panel)
    S = law.estimation_sample(A, max_date=None)
    fit = law.arms_fit(S["W"].to_numpy(), S["gap"].to_numpy())
    pooled = law.pooled_individual(panel, max_date=None)
    ex.say(f"round fit on W, n={fit.n}: a {fit.a:.4f} b- {fit.b_minus:+.4f} b+ {fit.b_plus:.4f} R2 {fit.r2:.3f}")
    ex.say(f"pooled individual fit, n={pooled.n}: a {pooled.a:.4f} b- {pooled.b_minus:+.4f} b+ {pooled.b_plus:.4f}")

    g = S["gap"].to_numpy()
    fig, ax = plt.subplots(1, 2, figsize=(7.4, 3.0))
    ax[0].scatter(g, S["W"], s=13, color=C["fit"], alpha=0.65, lw=0)
    xs = np.linspace(g.min(), g.max(), 200)
    ax[0].plot(xs, fit.a + fit.b_minus * np.maximum(-xs, 0) + fit.b_plus * np.maximum(xs, 0), color=C["cal"], lw=1.8)
    ax[0].axvline(0, color="k", lw=0.6, ls=":")
    ax[0].set_xlabel("consensus forecast $-$ target (pp)")
    ax[0].set_ylabel("round mean of individual variances")
    ax[0].set_title("(a) survey rounds, two-arm fit", loc="left", fontsize=9)

    p = panel.dropna(subset=["Mean_spd", "Variance_spd"])
    p = p[p["Variance_spd"] > 0]
    lo, hi = cv.INDIVIDUAL_MEAN_TRIM
    tr = p["Mean_spd"].between(lo, hi).to_numpy()
    gi = (p["Mean_spd"] - cv.TARGET).to_numpy()
    ax[1].scatter(gi[tr], p["Variance_spd"].to_numpy()[tr], s=3, color=C["raw"], alpha=0.25, lw=0)
    ax[1].plot(xs, pooled.a + pooled.b_minus * np.maximum(-xs, 0) + pooled.b_plus * np.maximum(xs, 0), color=C["cal"], lw=1.8)
    ax[1].axvline(0, color="k", lw=0.6, ls=":")
    ax[1].set_ylim(0, 6)
    ax[1].set_xlabel("forecaster's mean $-$ target (pp)")
    ax[1].set_ylabel("density variance")
    ax[1].set_title("(b) individual densities", loc="left", fontsize=9)
    ex.save_figure(fig)
    ex.write_results({"round_fit_W": fit.summary_row(), "pooled_individual_fit": pooled.summary_row(),
                      "rounds": len(S), "individual_densities_drawn": int(tr.sum())},
                     "Figure 4 — the envelope on the euro-area panel")


if __name__ == "__main__":
    main()
