#!/usr/bin/env python3
"""Figure 4 of *Tolerable Inflation, Intolerable Uncertainty*: one law, four sources.

Paper: Vansteenberghe, E. (2026), *Tolerable Inflation, Intolerable Uncertainty*,
working paper, Banque de France (``vansteenberghe2026tolerable``), Section 3,
Figure 4 (``fig:lawfour``).

The fitted two-arm law of each source, drawn relative to its value at the
target so that only the shape is compared: flat below the announced target,
rising to the right of it. Estimated here: the ECB SPF line (the average
individual predictive variance, 109 rounds through 2026Q2) and the US SPF
line (individual core-CPI densities after January 2012), the survey rows of
Table 1. Carried as printed in Table 1, not computed: the inflation-swap and
the inflation-option lines, which rest on licensed daily data
(``../restricted/README.md``). The results file records which lines were
computed.

Inputs:  the ECB-SPF round files; ``SPFmicrodata.xlsx`` (sheet PRCCPI).
Outputs: ``figures/fig04_law_across_sources.{pdf,png}``, ``results/fig04_law_across_sources.{json,md}``.

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use
this code, cite the paper above.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from _common import GREY, LAW_RC, LS, MK, PAL, style
from tab01_arms_by_source import us_individual_post2012

from nu_measures import conventions as cv
from nu_measures import law
from nu_measures.exhibit import Exhibit, load_ecb_panel

#: The market lines, as printed in Table 1 of the paper; licensed data, not computed here.
CARRIED = {
    "Inflation swaps": {"a": 0.451, "b_minus": -0.078, "b_plus": 1.606, "computed": False,
                        "source": "inflation-linked swaps, 2y, 63-day realized variance; Table 1 as printed"},
    "Options, adjusted": {"a": 0.380, "b_minus": -0.089, "b_plus": 0.680, "computed": False,
                          "source": "inflation options, premium-adjusted; Table 1 as printed"},
}


def main() -> None:
    ex = Exhibit(__file__)
    style(LAW_RC)
    S = law.estimation_sample(law.round_aggregates(load_ecb_panel()))
    ecb = law.arms_fit(S["W"].to_numpy(), S["gap"].to_numpy())
    u = us_individual_post2012()
    us = law.arms_fit(u["Variance"].to_numpy(), u["Mean"].to_numpy() - cv.TARGET)
    lines = {
        "ECB SPF, average individual variance": {"a": ecb.a, "b_minus": ecb.b_minus, "b_plus": ecb.b_plus, "computed": True, "n": ecb.n},
        "Inflation swaps": CARRIED["Inflation swaps"],
        "Options, adjusted": CARRIED["Options, adjusted"],
        "US SPF, individual": {"a": us.a, "b_minus": us.b_minus, "b_plus": us.b_plus, "computed": True, "n": us.n},
    }
    for k, p in lines.items():
        ex.say(f"{k}: a {p['a']:.3f} b- {p['b_minus']:+.3f} b+ {p['b_plus']:+.3f} ({'computed' if p['computed'] else 'carried as printed'})")

    fig, ax = plt.subplots(figsize=(6.4, 3.7), constrained_layout=True)
    gg = np.linspace(-1.3, 1.8, 400)
    for i, (k, p) in enumerate(lines.items()):
        v = (p["a"] + p["b_minus"] * np.maximum(-gg, 0) + p["b_plus"] * np.maximum(gg, 0)) / p["a"]
        ax.plot(gg, v, lw=1.6, color=PAL[i], ls=LS[i], label=k, zorder=3)
        j = np.argmin(np.abs(gg - 1.2))
        ax.plot(gg[j], v[j], MK[i], ms=5, color=PAL[i], zorder=4)
    ax.axvline(0, lw=0.6, ls=":", color=GREY)
    ax.axhline(1, lw=0.6, ls=":", color=GREY)
    ax.set_xlabel("distance of expected inflation from the announced target (pp)")
    ax.set_ylabel("variance relative to its value at the target")
    ax.set_title("One law, four sources: flat below, rising above", fontsize=9)
    ax.legend(frameon=False, fontsize=7, loc="upper left")
    ax.text(0.05, ax.get_ylim()[1] * 0.97, "announced target", fontsize=6.5, color=GREY, va="top", rotation=90)
    ex.save_figure(fig)
    ex.write_results({"lines": lines, "ecb_fit": ecb.summary_row(), "us_fit": us.summary_row()}, "Figure 4 — one law, four sources")


if __name__ == "__main__":
    main()
