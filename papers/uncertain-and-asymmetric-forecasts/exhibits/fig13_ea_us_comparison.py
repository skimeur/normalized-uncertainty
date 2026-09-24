#!/usr/bin/env python3
"""Figure 13 of *Uncertain and Asymmetric Forecasts*: the euro area and the United States side by side.

Paper: Vansteenberghe, E. (forthcoming), *Uncertain and Asymmetric Forecasts*,
working paper (``vansteenberghe2026uncertain``), Section 6, Figure 13
(``fig:ea_us``).

Four stacked panels over the period the two surveys share (the grid-stable US
core questions begin in 2007Q1): (a) realized year-on-year inflation, each
block's own target variable (euro-area HICP, US core CPI); (b) the first
moment, the cross-forecaster mean of the individual density means, with the
2 per cent line; (c) NU with a = b = 1, sigma / sqrt(1 + (mu - 2)_+), round
mean; (d) AC, each block normalized on its own sample (the interquartile
ranges of the median gap and of the two-round-smoothed Bowley skewness are
those of each block's whole panel). The cross-block correlation over the
common rounds is printed in each panel's right-hand title.

The two surveys do not ask the same question -- one-year-ahead headline HICP
against one-year-ahead core CPI -- and the figure says so rather than hiding
it. The euro-area AC rebuilt here is checked against the ``ACI`` column of the
panel before the figure is drawn.

Inputs:  the ECB-SPF round files (through ``load_ecb_panel``), ``SPFmicrodata.xlsx``
         (sheet PRCCPI), the HICP index, FRED ``CPILFESL``.
Outputs: ``figures/fig13_ea_us_comparison.{pdf,png}``, ``results/fig13_ea_us_comparison.{json,md}``.

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use
this code, cite the paper above.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from _common import style

from nu_measures import asymmetry, io_other, measures
from nu_measures import conventions as cv
from nu_measures.exhibit import Exhibit, load_ecb_panel, load_fred, load_hicp_yoy, load_us_quartiles

START = pd.Timestamp("2007-01-01")
END = pd.Timestamp("2026-10-01")
EAC, USC, REF = "#1f4e79", "#c0504d", "0.45"
EAS, USS = "-", (0, (4, 2))  # solid / dashed: the blocks stay apart in greyscale


def euro_area() -> pd.DataFrame:
    """Forecaster-rounds with the four moments, NU (a = b = 1) and AC on the euro-area panel."""
    ea = load_ecb_panel().dropna(subset=["Mean_spd", "Variance_spd", "Q2_median_spd", "Bowley_Skewness"])
    ea = ea[ea["Variance_spd"] > 0].copy()
    ea["Q"] = (ea["Date"] + pd.DateOffset(months=1)).dt.to_period("Q")
    ea["NU"] = measures.nu_unit(ea["sigma_spd"], ea["Mean_spd"])
    return asymmetry.ac_panel(ea)


def united_states() -> pd.DataFrame:
    """Forecaster-rounds of the US core CPI question with NU (a = b = 1) and AC on its own sample."""
    us = load_us_quartiles("PRCCPI")
    us = us[us["Variance"] > 0].dropna(subset=["Mean", "Variance", "Q2"]).copy()
    us["Q"] = us["Date"].dt.to_period("Q")
    us["NU"] = measures.nu_unit(np.sqrt(us["Variance"]), us["Mean"])
    return asymmetry.ac_panel(us, median="Q2", skewness="Bowley", by="ID")


def main() -> None:
    ex = Exhibit(__file__)
    style(titlesize=9, legend_fontsize=8)
    ea_inf = load_hicp_yoy()
    # the missing month of a skipped release stays missing, so the line breaks there rather than bridging it
    us_inf = io_other.monthly_yoy(load_fred("CPILFESL"))
    ex.say(f"realizations: EA {ea_inf.index.min().date()}..{ea_inf.index.max().date()}; "
           f"US core {us_inf.dropna().index.min().date()}..{us_inf.dropna().index.max().date()}")

    ea, us = euro_area(), united_states()
    ex.say(f"US PRCCPI: {len(us)} forecaster-rounds, {us['Q'].min()}..{us['Q'].max()}, {us['Q'].nunique()} rounds")
    ex.say(f"EA       : {len(ea)} forecaster-rounds, {ea['Q'].min()}..{ea['Q'].max()}, {ea['Q'].nunique()} rounds")
    check = float(ea["AC"].corr(ea["ACI"])) if "ACI" in ea.columns else float("nan")
    ex.say(f"check: EA AC rebuilt here vs the panel's ACI column, corr {check:.6f}")

    E = ea.groupby("Q").agg(mu=("Mean_spd", "mean"), NU=("NU", "mean"), AC=("AC", "mean"), n=("NU", "size"))
    U = us.groupby("Q").agg(mu=("Mean", "mean"), NU=("NU", "mean"), AC=("AC", "mean"), n=("NU", "size"))
    E, U = E[E.index.to_timestamp() >= START], U[U.index.to_timestamp() >= START]
    J = E.join(U, lsuffix="_ea", rsuffix="_us", how="inner")
    ex.say(f"common rounds {len(J)} ({J.index.min()}..{J.index.max()}); forecasters per round: "
           f"EA {E['n'].min()}-{E['n'].max()}, US {U['n'].min()}-{U['n'].max()}")
    rho, results = {}, {"common_rounds": int(len(J)), "first_common": str(J.index.min()), "last_common": str(J.index.max()),
                        "forecasters_per_round": {"EA": [int(E["n"].min()), int(E["n"].max())], "US": [int(U["n"].min()), int(U["n"].max())]},
                        "ea_ac_vs_panel_aci_corr": check, "ea_ac_iqr_scales": ea.attrs["ac_iqr_scales"],
                        "us_ac_iqr_scales": us.attrs["ac_iqr_scales"]}
    for k in ("mu", "NU", "AC"):
        rho[k] = float(J[f"{k}_ea"].corr(J[f"{k}_us"]))
        results[k] = {"corr_ea_us": rho[k], "mean_ea": float(J[f"{k}_ea"].mean()), "mean_us": float(J[f"{k}_us"].mean())}
        ex.say(f"  corr(EA, US) {k:<3} = {rho[k]:+.3f} ; means EA {results[k]['mean_ea']:.3f} US {results[k]['mean_us']:.3f}")
    i_ea, i_us = ea_inf[ea_inf.index >= START], us_inf[us_inf.index >= START]
    com = pd.concat([i_ea.rename("ea"), i_us.rename("us")], axis=1).dropna()
    rho["inf"] = float(com["ea"].corr(com["us"]))
    results["realized"] = {"corr_ea_us": rho["inf"], "mean_ea": float(com["ea"].mean()), "mean_us": float(com["us"].mean()),
                           "peak_ea": [float(com["ea"].max()), str(com["ea"].idxmax().date())],
                           "peak_us": [float(com["us"].max()), str(com["us"].idxmax().date())]}
    ex.say(f"  corr(EA, US) realized = {rho['inf']:+.3f} ; means EA {com['ea'].mean():.2f} US {com['us'].mean():.2f} ; "
           f"peaks EA {com['ea'].max():.2f} ({com['ea'].idxmax().date()}) US {com['us'].max():.2f} ({com['us'].idxmax().date()})")

    fig, ax = plt.subplots(4, 1, figsize=(7.0, 7.4), sharex=True)
    t_ea, t_us = E.index.to_timestamp(), U.index.to_timestamp()
    ax[0].plot(i_ea.index, i_ea.values, color=EAC, ls=EAS, lw=1.3, label="euro area, HICP")
    ax[0].plot(i_us.index, i_us.values, color=USC, ls=USS, lw=1.3, label="United States, core CPI")
    ax[0].axhline(cv.TARGET, color=REF, lw=0.8, ls=(0, (1, 2)))
    ax[0].set_title("(a) realized year-on-year inflation", loc="left")
    ax[0].set_ylabel("percent")
    ax[0].legend(ncol=2, loc="upper left", handlelength=2.0)
    ax[1].plot(t_ea, E["mu"], color=EAC, ls=EAS, lw=1.3)
    ax[1].plot(t_us, U["mu"], color=USC, ls=USS, lw=1.3)
    ax[1].axhline(cv.TARGET, color=REF, lw=0.8, ls=(0, (1, 2)))
    ax[1].set_title("(b) the first moment, averaged across forecasters", loc="left")
    ax[1].set_ylabel("percent")
    ax[1].set_yticks([1, 2, 3, 4, 5])
    ax[2].plot(t_ea, E["NU"], color=EAC, ls=EAS, lw=1.3)
    ax[2].plot(t_us, U["NU"], color=USC, ls=USS, lw=1.3)
    ax[2].set_title("(c) Normalized Uncertainty, calibrated series", loc="left")
    ax[2].set_ylabel("standard deviation")
    ax[3].plot(t_ea, E["AC"], color=EAC, ls=EAS, lw=1.3)
    ax[3].plot(t_us, U["AC"], color=USC, ls=USS, lw=1.3)
    ax[3].axhline(0.0, color=REF, lw=0.8, ls=(0, (1, 2)))
    ax[3].set_title("(d) Asymmetry Coherence", loc="left")
    ax[3].set_ylabel("index")
    ax[3].set_xlabel("survey round")
    for a, k in zip(ax, ("inf", "mu", "NU", "AC"), strict=True):
        a.set_title("across blocks: %+.2f" % rho[k], loc="right", fontsize=8, color="0.30")
    for a in ax:
        a.set_xlim(START, END)
    fig.align_ylabels(ax)
    fig.subplots_adjust(hspace=0.40)
    ex.save_figure(fig)
    ex.write_results(results, "Figure 13 — the euro area and the United States side by side")


if __name__ == "__main__":
    main()
