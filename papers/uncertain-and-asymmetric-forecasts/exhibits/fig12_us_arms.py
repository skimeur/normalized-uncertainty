#!/usr/bin/env python3
"""Figure 12 of *Uncertain and Asymmetric Forecasts*: the envelope in the US survey.

Paper: Vansteenberghe, E. (forthcoming), *Uncertain and Asymmetric Forecasts*,
working paper (``vansteenberghe2026uncertain``), Section 6, Figure 12
(``fig:us_arms``).

Panel (a): the round total variance of the two grid-stable core questions of
the Philadelphia Fed survey (core CPI, core PCE) against the signed distance
of the round's mean forecast from 2 per cent, after the FOMC's announcement
of a numerical target (2012Q1--), with the two-arm fits of Table 5. Panel (b):
the round total variance of the GDP price index question from the resumption
of the question in 1992Q1, the announcement marked by a dashed line and the
window of the halved grid (2014Q1--) shaded.

The question on the GDP price index was suspended after 1980Q2; of the rounds
before the suspension only one has a mean forecast inside the [-1, 6] window
the estimates are formed on, so the panel starts where the continuous record
starts. The fitted arms are asserted against the published rows of Table 5
before anything is written, so figure and table cannot drift apart.

Inputs:  ``SPFmicrodata.xlsx`` (sheets PRCCPI, PRCPCE, PRPGDP).
Outputs: ``figures/fig12_us_arms.{pdf,png}``, ``results/fig12_us_arms.{json,md}``.

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use
this code, cite the paper above.
"""

from __future__ import annotations

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from _common import style
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from nu_measures import io_us_spf, law
from nu_measures.exhibit import Exhibit, load_us_densities

ANNOUNCE = pd.Timestamp("2012-01-01")
GRID_CHANGE = pd.Timestamp("2014-01-01")
RESUMED = pd.Timestamp("1992-01-01")

#: Table 5, rows "after 2012": (n, b_-, t_-, b_+, t_+), the values the figure must reproduce.
PUBLISHED = {"PRCCPI": (58, 0.631, 7.6, 0.294, 6.7), "PRCPCE": (58, 0.316, 2.3, 0.357, 8.0)}
CPI, PCE, RAW = "#1f4e79", "#c0504d", "0.55"
STYLE = {
    "PRCCPI": dict(label="core CPI", color=CPI, marker="o", ls="-", facecolors=CPI, edgecolors="none", s=13, alpha=0.60),
    "PRCPCE": dict(label="core PCE", color=PCE, marker="^", ls=(0, (4, 2)), facecolors="none", edgecolors=PCE, s=16, alpha=0.85),
}


def main() -> None:
    ex = Exhibit(__file__)
    style(legend_fontsize=8)
    results: dict = {}
    fits = {}
    for sheet in ("PRCCPI", "PRCPCE"):
        A = io_us_spf.round_aggregates(load_us_densities(sheet))
        A = A[A.index >= ANNOUNCE]
        fit = law.arms_fit(A["T"].to_numpy(), A["gap"].to_numpy())
        fits[sheet] = (A, fit)
        got = (fit.n, round(fit.b_minus, 3), round(fit.t_b_minus, 1), round(fit.b_plus, 3), round(fit.t_b_plus, 1))
        ex.say(f"{sheet} after 2012: n {fit.n} b- {fit.b_minus:+.3f} ({fit.t_b_minus:.1f}) b+ {fit.b_plus:+.3f} ({fit.t_b_plus:.1f}) R2 {fit.r2:.3f}")
        if got != PUBLISHED[sheet]:
            raise SystemExit(f"{sheet}: the figure's fit {got} differs from Table 5 {PUBLISHED[sheet]}")
        results[f"{sheet}_post2012"] = fit.summary_row()
    ex.say("check: both arms reproduce Table 5")

    Ag = io_us_spf.round_aggregates(load_us_densities("PRPGDP"))
    dropped = Ag[Ag.index < RESUMED]
    Ag = Ag[Ag.index >= RESUMED]
    if Ag.index.to_series().diff().dt.days.max() > 100:
        raise SystemExit("a gap remains inside the drawn window of the GDP price index series")
    results["PRPGDP"] = {
        "rounds_drawn": int(len(Ag)), "first": str(Ag.index.min().date()), "last": str(Ag.index.max().date()),
        "variance_min": float(Ag["T"].min()), "variance_max": float(Ag["T"].max()),
        "rounds_before_1992_not_drawn": [str(x.date()) for x in dropped.index],
        "mean_variance_old_grid": float(Ag["T"][Ag.index < GRID_CHANGE].mean()),
        "mean_variance_new_grid": float(Ag["T"][Ag.index >= GRID_CHANGE].mean()),
    }
    ex.say(f"PRPGDP: {len(Ag)} rounds drawn, {Ag.index.min().date()}..{Ag.index.max().date()}; "
           f"{len(dropped)} earlier round(s) not drawn; mean variance old/new grid "
           f"{results['PRPGDP']['mean_variance_old_grid']:.3f} / {results['PRPGDP']['mean_variance_new_grid']:.3f}")

    fig, ax = plt.subplots(1, 2, figsize=(7.4, 3.0))
    # (a) marker shape and line pattern carry the identity, so the panel survives greyscale
    for sheet in ("PRCCPI", "PRCPCE"):
        A, fit = fits[sheet]
        st = STYLE[sheet]
        gv = A["gap"].to_numpy()
        ax[0].scatter(gv, A["T"], marker=st["marker"], s=st["s"], alpha=st["alpha"], linewidths=0.7,
                      facecolors=st["facecolors"], edgecolors=st["edgecolors"])
        xs = np.linspace(gv.min(), gv.max(), 200)
        ax[0].plot(xs, fit.a + fit.b_minus * np.maximum(-xs, 0) + fit.b_plus * np.maximum(xs, 0),
                   color=st["color"], ls=st["ls"], lw=1.6)
    ax[0].axvline(0, color="0.35", lw=0.7, ls=(0, (1, 2)))
    ax[0].legend(handles=[Line2D([], [], color=STYLE[s]["color"], ls=STYLE[s]["ls"], lw=1.6,
                                 marker=STYLE[s]["marker"], markersize=4.5,
                                 markerfacecolor=(STYLE[s]["color"] if s == "PRCCPI" else "none"),
                                 markeredgecolor=STYLE[s]["color"], label=STYLE[s]["label"])
                          for s in ("PRCCPI", "PRCPCE")],
                 loc="upper left", handlelength=2.6, borderaxespad=0.2)
    ax[0].set_xlabel("mean forecast $-$ 2 (pp)")
    ax[0].set_ylabel("round variance")
    ax[0].set_title("(a) grid-stable questions, post-2012", loc="left", fontsize=9)

    # (b) the grid change is a shaded window, the announcement a dashed line; both named in a legend
    ax[1].axvspan(GRID_CHANGE, Ag.index.max() + pd.DateOffset(years=2), color="0.88", lw=0, zorder=0)
    ax[1].plot(Ag.index, Ag["T"], color=RAW, lw=1.2, zorder=2)
    ax[1].axvline(ANNOUNCE, ymin=0.0, ymax=0.80, color="0.15", lw=1.1, ls=(0, (4, 2)), zorder=3)
    ax[1].set_ylim(0, Ag["T"].max() * 1.38)
    ax[1].set_xlim(Ag.index.min() - pd.DateOffset(years=1), Ag.index.max() + pd.DateOffset(years=1))
    ax[1].xaxis.set_major_locator(mdates.YearLocator(5))
    ax[1].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax[1].legend(handles=[Line2D([], [], color="0.15", lw=1.1, ls=(0, (4, 2)), label="announcement, 2012Q1"),
                          Patch(facecolor="0.88", edgecolor="none", label="new grid, from 2014Q1")],
                 loc="upper left", handlelength=1.9, borderaxespad=0.15, labelspacing=0.30, fontsize=7.5, handletextpad=0.5)
    ax[1].set_ylabel("round variance")
    ax[1].set_title("(b) the GDP price index question", loc="left", fontsize=9)
    fig.tight_layout()
    ex.save_figure(fig)
    ex.write_results(results, "Figure 12 — the envelope in the US survey")


if __name__ == "__main__":
    main()
