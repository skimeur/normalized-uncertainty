#!/usr/bin/env python3
"""Figure 15 of *Uncertain and Asymmetric Forecasts*: the six series at the one-, two- and five-year horizons.

Paper: Vansteenberghe, E. (2026), *Uncertain and Asymmetric Forecasts*,
working paper (``vansteenberghe2026uncertain``), Section 2.1 (the horizons)
and Section 8, Figure 15 (``fig:horizons``).

One panel per series -- level, disagreement, raw uncertainty, NU, skewness,
AC -- each a cross-forecaster statistic of the individual densities by survey
round, at the rolling one- and two-year horizons and the longer-term (five-year)
horizon. AC is on the one-year scales at every horizon, so the three lines are
comparable. The longer-term question was not asked in 1999Q2-Q4 and 2000Q2-Q4;
those rounds are gaps. ``nu_measures.series`` builds every number, and
``scripts/build_ecb_spf_series.py`` writes them to CSV.

Inputs:  the ECB-SPF round files through the published extent (2026Q3).
Outputs: ``figures/fig15_horizons.{pdf,png}``, ``results/fig15_horizons.{json,md}``.

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use
this code, cite the paper above.
"""

from __future__ import annotations

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from _common import INK, REF, style

from nu_measures import conventions as cv
from nu_measures import paths, series
from nu_measures.exhibit import Exhibit

PANELS = (
    ("level", "(a) level: mean of the density means", "per cent"),
    ("disagreement", "(b) disagreement: s.d. of the means", "percentage points"),
    ("raw_uncertainty", "(c) raw uncertainty: mean individual s.d.", "percentage points"),
    ("NU", "(d) Normalized Uncertainty, $a=b=1$", "percentage points"),
    ("skewness", "(e) mean individual Bowley skewness", "skewness"),
    ("AC", "(f) Asymmetry Coherence", "index"),
)
LINES = {"1Y": dict(color=INK, lw=1.3), "2Y": dict(color="0.45", lw=1.1, ls=(0, (4, 2))),
         "5Y": dict(color=REF, lw=1.1, ls=(0, (1, 1.5)))}
LABEL = {"1Y": "one year", "2Y": "two years", "5Y": "five years (longer term)"}


def main() -> None:
    ex = Exhibit(__file__)
    style(titlesize=9, legend_fontsize=8)
    S = series.ecb_spf_series(paths.require(paths.ecb_spf_rounds(), "the ECB-SPF round files"),
                              through=cv.PUBLISHED_EXTENT["ecb_spf"])
    names = [p[0] for p in PANELS]
    means = S.groupby(level="horizon")[names + ["n"]].mean()
    wide = S[names].unstack("horizon")
    corr = {k: {f"{a}-{b}": float(wide[k][a].corr(wide[k][b])) for a, b in (("1Y", "2Y"), ("1Y", "5Y"), ("2Y", "5Y"))}
            for k in names}
    missing = [str(r) for r in S.xs("5Y", level="horizon").query("n == 0").index]
    ex.say(f"rounds {S.attrs['rounds'][0]}-{S.attrs['rounds'][1]}; densities per round, mean: "
           + ", ".join(f"{h} {means.loc[h, 'n']:.1f}" for h in cv.HORIZONS))
    ex.say(f"five-year horizon not asked in {', '.join(missing)}")
    for k in names:
        ex.say(f"{k:16s} means " + "  ".join(f"{h} {means.loc[h, k]:+.3f}" for h in cv.HORIZONS)
               + "   corr " + "  ".join(f"{p} {v:.2f}" for p, v in corr[k].items()))

    fig, axes = plt.subplots(3, 2, figsize=(7.2, 7.4), sharex=True)
    for ax, (k, title, unit) in zip(axes.ravel(), PANELS, strict=True):
        for h in cv.HORIZONS:
            s = S.xs(h, level="horizon")[k]
            ax.plot(s.index.to_timestamp(), s.to_numpy(), label=LABEL[h], **LINES[h])
        if k in ("skewness", "AC"):
            ax.axhline(0, color="0.5", lw=0.8, ls=(0, (1, 2)))
        if k == "level":
            ax.axhline(cv.TARGET, color="0.5", lw=0.8, ls=(0, (1, 2)))
        ax.set_title(title, loc="left")
        ax.set_ylabel(unit)
    axes[0, 0].legend(loc="upper left", handlelength=2.4)
    for ax in axes[-1]:
        ax.set_xlabel("survey round")
        ax.xaxis.set_major_locator(mdates.YearLocator(5))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    fig.align_ylabels(axes[:, 0])
    fig.align_ylabels(axes[:, 1])
    fig.subplots_adjust(hspace=0.38, wspace=0.32)
    ex.save_figure(fig)

    rec = S.reset_index().assign(round=lambda d: d["round"].astype(str), Date=lambda d: d["Date"].dt.strftime("%Y-%m-%d"))
    ex.write_results({"rounds": list(S.attrs["rounds"]), "ac_iqr_scales": S.attrs["ac_iqr_scales"]["1Y"],
                      "five_year_not_asked": missing, "means_by_horizon": means.round(6).to_dict("index"),
                      "correlations_across_horizons": corr, "series": rec.to_dict("records")},
                     "Figure 15 — the six series at three horizons")


if __name__ == "__main__":
    main()
