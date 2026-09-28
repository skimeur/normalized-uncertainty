#!/usr/bin/env python3
"""Figure 6 of *Uncertain and Asymmetric Forecasts*: the moments of the reported densities, round by round.

Paper: Vansteenberghe, E. (2026), *Uncertain and Asymmetric Forecasts*,
working paper (``vansteenberghe2026uncertain``), Section 4, Figure 6
(``fig:moments``) and the counts of its note.

Cross-forecaster mean of (a) the individual density means, (b) the individual
Bowley skewness, (c) the raw individual variance -- the object W the envelope
is fitted on -- and (d) Normalized Uncertainty at a = b = 1, with the fitted
series dotted beside it; the shaded band is the 95 per cent interval for the
round mean, mean +/- t(0.975, N-1) s / sqrt(N), and the dashed lines are the
quartiles of the forecasters reporting that round. Densities with a
degenerate variance are dropped; the round rule is not applied (it governs the
envelope, not these moments).

Inputs:  the ECB-SPF round files, through ``nu_measures.exhibit.load_ecb_panel``.
Outputs: ``figures/fig06_moments_intervals.{pdf,png}``, ``results/fig06_moments_intervals.{json,md}``.

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use
this code, cite the paper above.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from _common import INK, REF, style
from scipy import stats

from nu_measures import conventions as cv
from nu_measures import measures
from nu_measures.exhibit import Exhibit, load_ecb_panel


def band(pan: pd.DataFrame, col: str) -> pd.DataFrame:
    g = pan.dropna(subset=[col]).groupby("Q")[col]
    d = pd.DataFrame({"m": g.mean(), "sd": g.std(ddof=1), "n": g.size(), "q1": g.quantile(0.25), "q3": g.quantile(0.75)})
    d["se"] = d["sd"] / np.sqrt(d["n"])
    d["t"] = stats.t.ppf(0.975, d["n"] - 1)
    d["lo"], d["hi"] = d["m"] - d["t"] * d["se"], d["m"] + d["t"] * d["se"]
    return d


def main() -> None:
    ex = Exhibit(__file__)
    style(titlesize=9, legend_fontsize=8)
    pan = measures.add_nu(load_ecb_panel())
    pan["Q"] = (pan["Date"] + pd.DateOffset(months=1)).dt.to_period("Q")
    ex.say(f"panel {len(pan)} forecaster-rounds, {pan['Q'].nunique()} rounds, {pan['Q'].min()}..{pan['Q'].max()}")
    M, S = band(pan, "Mean_spd"), band(pan, "Bowley_Skewness")
    V, NC, NF = band(pan, "Variance_spd"), band(pan, "NU_unit"), band(pan, "NU_fitted")
    mu_excl = int(((M["lo"] > cv.TARGET) | (M["hi"] < cv.TARGET)).sum())
    mu_below = int((M["hi"] < cv.TARGET).sum())
    sk_excl = int(((S["lo"] > 0) | (S["hi"] < 0)).sum())
    base = (V.index >= pd.Period("2015Q1")) & (V.index <= pd.Period("2019Q4"))
    peak = (V.index >= pd.Period("2022Q1")) & (V.index <= pd.Period("2023Q4"))
    ratio_raw = float(V.loc[peak, "m"].max() / V.loc[base, "m"].mean())
    ratio_nu = float(NC.loc[peak, "m"].max() / NC.loc[base, "m"].mean())
    ex.say(f"forecasters per round {int(M['n'].min())}..{int(M['n'].max())}")
    ex.say(f"first moment: interval excludes the target in {mu_excl} rounds ({mu_below} below); third moment: excludes zero in {sk_excl}")
    ex.say(f"2022-2023 peak against the 2015-2019 average: raw variance x{ratio_raw:.1f}, NU (a=b=1) x{ratio_nu:.2f}")

    fig, ax = plt.subplots(4, 1, figsize=(7.0, 7.0), sharex=True)
    x = M.index.to_timestamp()
    panels = (
        (ax[0], M, "(a) the individual first moment: mean of $\\mu_{i,t}$ across forecasters", "percent", cv.TARGET, "target, 2%"),
        (ax[1], S, "(b) the individual third moment: mean of Bowley's skewness $A_{i,t}$", "skewness coefficient", 0.0, None),
        (ax[2], V, "(c) the raw individual variance: mean of $\\sigma^2_{i,t}$ across forecasters", "variance", None, None),
        (ax[3], NC, "(d) Normalized Uncertainty: mean of $\\mathrm{NU}^{\\mathrm{cal}}_{i,t}$ across forecasters", "standard deviation", None, None),
    )
    for a, d, title, ylab, ref, reflab in panels:
        a.fill_between(x, d["lo"], d["hi"], color="0.45", alpha=0.35, lw=0, label="95% interval for the mean")
        a.plot(x, d["q1"], color="0.35", lw=0.7, ls=(0, (3, 2)), label="forecaster quartiles")
        a.plot(x, d["q3"], color="0.35", lw=0.7, ls=(0, (3, 2)))
        a.plot(x, d["m"], color=INK, lw=1.4, label="round mean", zorder=4)
        if ref is not None:
            a.axhline(ref, color=REF, lw=0.9, ls=(0, (1, 2)), zorder=1)
        if reflab:
            a.annotate(reflab, xy=(x[2], ref), xytext=(0, 3), textcoords="offset points", color=REF, fontsize=8)
        a.set_title(title, loc="left")
        a.set_ylabel(ylab)
    ax[3].plot(x, NF["m"], color=INK, lw=1.0, ls=(0, (1, 1.6)), zorder=5, label="$\\mathrm{NU}^{\\mathrm{fit}}$, round mean")
    ax[0].legend(loc="upper left", ncol=3, handlelength=1.6, borderaxespad=0.2, columnspacing=1.4)
    ax[3].legend(loc="upper left", handlelength=1.6, borderaxespad=0.2)
    ax[3].set_xlabel("survey round")
    fig.align_ylabels(ax)
    fig.subplots_adjust(hspace=0.38)
    ex.save_figure(fig)
    ex.write_results({"forecaster_rounds": len(pan), "rounds": int(pan["Q"].nunique()),
                      "forecasters_per_round": [int(M["n"].min()), int(M["n"].max())],
                      "first_moment_interval_excludes_target": mu_excl, "of_which_below": mu_below,
                      "third_moment_interval_excludes_zero": sk_excl,
                      "peak_2022_2023_over_2015_2019_raw_variance": ratio_raw, "peak_2022_2023_over_2015_2019_nu_unit": ratio_nu},
                     "Figure 6 — the moments of the reported densities, round by round")


if __name__ == "__main__":
    main()
