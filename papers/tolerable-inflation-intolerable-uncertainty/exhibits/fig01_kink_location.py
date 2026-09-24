#!/usr/bin/env python3
"""Figure 1 of *Tolerable Inflation, Intolerable Uncertainty*: where the kink sits.

Paper: Vansteenberghe, E. (2026), *Tolerable Inflation, Intolerable Uncertainty*,
working paper, Banque de France (``vansteenberghe2026tolerable``), Section 3,
Figure 1 (``fig:kinkloc``).

The residual sum of squares of the two-arm law on the average individual
predictive variance of the ECB SPF, as the breakpoint c is profiled over the
central ninety per cent of the consensus forecast's range (step 0.01),
normalised by its minimum; the profile-likelihood 95 per cent set (shaded)
and, in the results file, a nonparametric bootstrap over rounds (2,000
draws, seed 20260728) of the profiled optimum. The free-anchor estimate of
the daily inflation-swap market, 1.96, is drawn as a vertical line: it rests
on licensed data and is carried as printed in the paper, not computed here.

Inputs:  the ECB-SPF round files, through ``nu_measures.exhibit.load_ecb_panel``.
Outputs: ``figures/fig01_kink_location.{pdf,png}``, ``results/fig01_kink_location.{json,md}``.
Sample:  rounds through 2026Q2 with the consensus inside [-1, 5] (n = 109).

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use
this code, cite the paper above.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
from _common import GREY, LAW_RC, LS, MK, PAL, style

from nu_measures import conventions as cv
from nu_measures import law
from nu_measures.exhibit import Exhibit, load_ecb_panel

#: The swap market's free-anchor estimate, as printed in the paper (Section 3); not computed here.
SWAP_FREE_ANCHOR = {"value": 1.96, "computed": False, "source": "inflation-linked swaps, licensed daily data; carried as printed"}


def main() -> None:
    ex = Exhibit(__file__)
    style(LAW_RC)
    S = law.estimation_sample(law.round_aggregates(load_ecb_panel()))
    ex.say(f"{len(S)} rounds, {S.index.min().date()}..{S.index.max().date()}")
    fits = law.law_by_object(S)
    for k in ("W", "D", "T"):
        f = fits[k]
        ex.say(f"law on {k}: a {f.a:.4f} b- {f.b_minus:+.4f} ({f.t_b_minus:.2f}) b+ {f.b_plus:.4f} ({f.t_b_plus:.2f}) R2 {f.r2:.3f}")
    prof = law.kink_profile(S["W"].to_numpy(), S["mu"].to_numpy())
    boot = law.kink_bootstrap(S["W"].to_numpy(), S["mu"].to_numpy(), prof["grid"])
    prof_T = law.kink_profile(S["T"].to_numpy(), S["mu"].to_numpy())
    ex.say(f"kink on W: c_hat {prof['c_hat']:.3f}; 95% set [{prof['set95'][0]:.2f}, {prof['set95'][1]:.2f}]; "
           f"bootstrap 90% [{boot['interval90'][0]:.2f}, {boot['interval90'][1]:.2f}] (median {boot['median']:.3f}); "
           f"RSS gain from freeing c {prof['gain_pct']:.2f}%; LR {prof['lr']:.2f}; T profile c_hat {prof_T['c_hat']:.3f}")

    grid, rss, chat = prof["grid"], prof["rss"], prof["c_hat"]
    lo95, hi95 = prof["set95"]
    fig, ax = plt.subplots(figsize=(6.4, 3.4), constrained_layout=True)
    ax.plot(grid, rss / rss.min(), lw=1.6, color=PAL[0], zorder=3, label="ECB SPF profile, average individual variance")
    ax.axvline(cv.TARGET, lw=1.0, ls="--", color="0.25", zorder=2, label="announced target, 2.00")
    ax.plot([chat], [1.0], MK[0], ms=6, color=PAL[0], zorder=5)
    ax.annotate(f"survey $\\hat c={chat:.2f}$", (chat, 1.0), (chat - 0.45, 1.055), fontsize=7, color=PAL[0],
                arrowprops=dict(arrowstyle="-", lw=0.6, color=PAL[0]))
    ax.axvline(SWAP_FREE_ANCHOR["value"], lw=1.4, ls=LS[1], color=PAL[1], zorder=4,
               label=f"swaps, free anchor {SWAP_FREE_ANCHOR['value']:.2f}")
    ax.axvspan(lo95, hi95, color=PAL[0], alpha=0.10, lw=0, zorder=1)
    ax.text(lo95 - 0.02, 1.0 + 0.45 * (rss.max() / rss.min() - 1.0), "95% set for the survey break", fontsize=6.5,
            color=GREY, rotation=90, va="center", ha="right")
    ax.set_xlabel("candidate breakpoint $c$ (pp)")
    ax.set_ylabel("residual sum of squares, relative to its minimum")
    ax.set_title("The kink sits at, or just below, the announced target", fontsize=9)
    ax.legend(frameon=False, fontsize=7, loc="upper right")
    ex.save_figure(fig)
    ex.write_results({
        "sample": {"rounds": int(len(S)), "first": str(S.index.min().date()), "last": str(S.index.max().date())},
        "law": {k: fits[k].summary_row() for k in ("W", "D", "T")},
        "kink_W": {"c_hat": chat, "set95": list(prof["set95"]), "bootstrap90": list(boot["interval90"]),
                   "bootstrap_median": boot["median"], "bootstrap_draws": 2000, "seed": 20260728,
                   "gain_pct_over_target": prof["gain_pct"], "lr": prof["lr"], "grid": [float(grid.min()), float(grid.max())],
                   "b_at_c_hat": prof["b_at_c_hat"], "b_at_target": prof["b_at_target"]},
        "kink_T_c_hat": prof_T["c_hat"],
        "swap_free_anchor": SWAP_FREE_ANCHOR,
    }, "Figure 1 — where the kink sits")


if __name__ == "__main__":
    main()
