#!/usr/bin/env python3
"""Figure 1 of *Uncertain and Asymmetric Forecasts*: the histogram grid, the realized series and the reported densities.

Paper: Vansteenberghe, E. (2026), *Uncertain and Asymmetric Forecasts*,
working paper (``vansteenberghe2026uncertain``), Section 2, Figure 1
(``fig:grid``) and the numbers of its note.

Panel (a): realized year-on-year euro-area HICP inflation and the round mean
of the individual one-year-ahead density means, the latter at the date its
forecast refers to; the interior of the grid, [-1, 5], and the two
realizations on which the open tails are closed. Panel (b): the reported
histogram averaged over every forecaster-round, on the grid as the panel
builder fixes it (historic open tails pooled, probabilities renormalized row
by row within the grid regime, each bin at the midpoint of its closed
interval), with the 2024Q4 grid superimposed. Panel (c): the realized series
binned on that same grid, against the average reported density.

Inputs:  the ECB-SPF round files (through the flat panel); the HICP index
         (``ecb/hicp_index.csv``) or the macro block's year-on-year series.
Outputs: ``figures/fig01_histogram_grid.{pdf,png}``, ``results/fig01_histogram_grid.{json,md}``.

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use
this code, cite the paper above.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from _common import C, style

from nu_measures import conventions as cv
from nu_measures.exhibit import Exhibit, load_flat_panel, load_hicp_yoy


def bin_on_grid(values, edges):
    """Mass of ``values`` in each closed bin of the fixed grid, in per cent."""
    cuts = [e[1] for e in edges[:-1]]
    idx = np.digitize(values, cuts, right=True)
    out = np.array([(idx == k).sum() for k in range(len(edges))], dtype=float)
    return 100.0 * out / out.sum()


def main() -> None:
    ex = Exhibit(__file__)
    style(titlesize=9, legend_fontsize=8)
    hicp = load_hicp_yoy()
    hicp_min, hicp_max = float(hicp.min()), float(hicp.max())
    ex.say(f"realized HICP {hicp.index.min().date()}..{hicp.index.max().date()}, n={len(hicp)}; min {hicp_min:.4f}, max {hicp_max:.4f}")

    df = load_flat_panel()
    df["Date"] = df["Date"] - pd.DateOffset(years=1)
    bins, binspost = list(cv.GRID_PRE_BINS), list(cv.GRID_POST_BINS)
    bin_edges = cv.grid_edges(post=False, hicp_min=hicp_min, hicp_max=hicp_max)
    bin_post_edges = cv.grid_edges(post=True, hicp_min=hicp_min, hicp_max=hicp_max)
    df["]-inf, - 1]"] = df.loc[:, list(cv.GRID_PRE_LEFT_SOURCES)].sum(axis=1)
    df["[5,+inf["] = df.loc[:, list(cv.GRID_PRE_RIGHT_SOURCES)].sum(axis=1)
    df = df.loc[:, ["Date", "FCT_SOURCE", "POINT"] + bins + binspost].copy()
    for cols in (bins, binspost):
        s = df[cols].sum(axis=1)
        df.loc[:, cols] = df[cols].div(s.replace(0, np.nan), axis=0) * 100.0
    df.dropna(subset=bins + binspost, how="all", inplace=True)
    cutoff = pd.Timestamp(cv.QUESTIONNAIRE_CHANGE_PANEL_DATE)
    pre = df.loc[df["Date"] < cutoff, ["Date"] + bins].dropna(subset=bins, how="all").copy()
    post = df.loc[df["Date"] >= cutoff, ["Date"] + binspost].dropna(subset=binspost, how="all").copy()
    pre[bins] = pre[bins].fillna(0.0)
    post[binspost] = post[binspost].fillna(0.0)
    ex.say(f"grid through 2024Q3: {len(pre)} forecaster-rounds over {pre['Date'].nunique()} rounds; revised grid: {len(post)} over {post['Date'].nunique()}")
    avg_pre = pre[bins].mean().to_numpy()
    avg_post = post[binspost].mean().to_numpy()
    rep_pre = np.array([(lo + hi) / 2.0 for lo, hi in bin_edges])
    rep_post = np.array([(lo + hi) / 2.0 for lo, hi in bin_post_edges])

    pre["mu"] = (pre[bins].to_numpy() / 100.0) @ rep_pre
    post["mu"] = (post[binspost].to_numpy() / 100.0) @ rep_post
    cons = pd.concat([pre[["Date", "mu"]], post[["Date", "mu"]]]).groupby("Date")["mu"].mean()
    cons.index = cons.index + pd.DateOffset(years=1)
    real_at_target = hicp.reindex(cons.index).dropna()
    real_hist = bin_on_grid(real_at_target.to_numpy(), bin_edges)
    top_by_round = pre.groupby("Date")[bins[-1]].mean()
    surge = top_by_round[(top_by_round.index >= "2021-06-01") & (top_by_round.index <= "2023-12-31")]
    ex.say(f"realized at the {len(real_at_target)} observed target quarters; top bin: forecast {avg_pre[-1]:.2f}% vs realized {real_hist[-1]:.2f}%")
    ex.say(f"top-bin mass by round: max {top_by_round.max():.1f}% ({top_by_round.idxmax().date()}); 2021Q3-2023Q4 mean {surge.mean():.1f}%")

    fig = plt.figure(figsize=(7.4, 5.4))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.05], hspace=0.45, wspace=0.28)
    a0 = fig.add_subplot(gs[0, :])
    a1 = fig.add_subplot(gs[1, 0])
    a2 = fig.add_subplot(gs[1, 1])
    a0.axhspan(-1, 5, color=C["fit"], alpha=0.10, lw=0, zorder=0)
    a0.plot(hicp.index, hicp.values, color=C["fit"], lw=1.0, zorder=3, label="realized year-on-year HICP")
    a0.plot(cons.index, cons.values, color=C["cal"], lw=1.2, zorder=4, label="mean of the individual density means, one year earlier")
    a0.axhline(hicp_max, color=C["raw"], lw=0.8, ls="--", zorder=2)
    a0.axhline(hicp_min, color=C["raw"], lw=0.8, ls="--", zorder=2)
    a0.annotate("$%.2f$" % hicp_max, xy=(pd.Timestamp("2027-06-01"), hicp_max), xytext=(0, -11), textcoords="offset points", color="#5a5a5a", fontsize=8, ha="right")
    a0.annotate("$%.2f$" % hicp_min, xy=(pd.Timestamp("2027-06-01"), hicp_min), xytext=(0, 4), textcoords="offset points", color="#5a5a5a", fontsize=8, ha="right")
    a0.annotate("grid interior, $[-1,5]$", xy=(pd.Timestamp("1999-09-01"), 4.15), color="#4d4d4d", fontsize=8)
    a0.set_title("(a) realized one-year euro-area inflation and the average density mean", loc="left")
    a0.set_ylabel("percent")
    a0.set_xlim(pd.Timestamp("1999-01-01"), pd.Timestamp("2027-09-01"))
    a0.set_ylim(-1.9, 11.6)
    a0.legend(loc="upper left", bbox_to_anchor=(0.005, 0.90), handlelength=1.6)
    wb = 0.42
    a1.bar(rep_pre[1:-1], avg_pre[1:-1], width=wb, color=C["fit"], lw=0, zorder=3, label="interior bins")
    a1.bar([rep_pre[0], rep_pre[-1]], [avg_pre[0], avg_pre[-1]], width=wb, color="white", edgecolor=C["cal"], lw=0.9, hatch="////", zorder=3, label="the two closed tails")
    a1.plot([bin_edges[-1][0], bin_edges[-1][1]], [avg_pre[-1] + 1.15] * 2, color=C["cal"], lw=0.7, marker="|", ms=4, zorder=3)
    a1.axvline(hicp_max, color=C["cal"], lw=0.7, ls=":", zorder=1)
    a1.annotate("top bin $[5,\\,%.2f]$,\nmass placed at $%.2f$" % (hicp_max, rep_pre[-1]), xy=(rep_pre[-1], avg_pre[-1] + 1.9), ha="center", va="bottom", color=C["cal"], fontsize=7.5)
    a1.annotate("bottom bin\nclosed at $-1$", xy=(rep_pre[0], avg_pre[0] + 0.4), xytext=(-1.95, 11.5), color=C["cal"], fontsize=7.5, ha="left",
                arrowprops=dict(arrowstyle="-", lw=0.6, color=C["cal"], shrinkA=3, shrinkB=2))
    a1.step(np.r_[rep_post[1:-1] - 0.25, rep_post[-2] + 0.25], np.r_[avg_post[1:-1], avg_post[-2]], where="post", color=C["ngu"], lw=0.8, zorder=4, label="the 2024Q4 grid")
    a1.plot(rep_post[[0, -1]], avg_post[[0, -1]], "s", ms=3, color=C["ngu"], zorder=4)
    a1.set_title("(b) average reported histogram, one year ahead", loc="left")
    a1.set_xlabel("inflation (percent)")
    a1.set_ylabel("probability mass (percent)")
    a1.set_xlim(-2.0, 11.3)
    a1.set_ylim(0, 36)
    a1.legend(loc="upper right", handlelength=1.3, borderaxespad=0.1, labelspacing=0.35, handletextpad=0.5)
    wc = 0.21
    a2.bar(rep_pre[:-1] - wc / 2, avg_pre[:-1], width=wc, color=C["fit"], lw=0, zorder=3, label="average reported density")
    a2.bar(rep_pre[:-1] + wc / 2, real_hist[:-1], width=wc, color=C["cal"], lw=0, zorder=3, label="realized outcomes, same grid")
    a2.bar([rep_pre[-1] - wc], [avg_pre[-1]], width=2 * wc, color=C["fit"], lw=0, zorder=3)
    a2.bar([rep_pre[-1] + wc], [real_hist[-1]], width=2 * wc, color=C["cal"], lw=0, zorder=3)
    a2.annotate("top bin:\n$%.1f$ vs $%.1f$" % (avg_pre[-1], real_hist[-1]), xy=(rep_pre[-1], real_hist[-1] + 0.8), xytext=(rep_pre[-1], 12.5),
                ha="center", color="#4d4d4d", fontsize=7.5, arrowprops=dict(arrowstyle="-", lw=0.6, color="#4d4d4d", shrinkA=3, shrinkB=2))
    a2.set_title("(c) the two histograms compared", loc="left")
    a2.set_xlabel("inflation (percent)")
    a2.set_ylabel("share (percent)")
    a2.set_xlim(-2.0, 11.3)
    a2.set_ylim(0, 36)
    a2.legend(loc="upper right", handlelength=1.3, borderaxespad=0.1, labelspacing=0.35, handletextpad=0.5)
    ex.save_figure(fig)
    ex.write_results({
        "hicp_min": hicp_min, "hicp_max": hicp_max, "rounds_old_grid": int(pre["Date"].nunique()), "forecaster_rounds_old_grid": len(pre),
        "rounds_new_grid": int(post["Date"].nunique()), "forecaster_rounds_new_grid": len(post),
        "target_quarters_realized": len(real_at_target), "top_bin_forecast_pct": float(avg_pre[-1]), "top_bin_realized_pct": float(real_hist[-1]),
        "top_bin_mass_2021Q3_2023Q4_mean_pct": float(surge.mean()), "top_bin_mass_max_pct": float(top_by_round.max()),
        "top_bin_mass_max_round": str((top_by_round.idxmax() + pd.DateOffset(months=1)).to_period("Q")),
        "average_histogram_old_grid": dict(zip(bins, avg_pre.tolist(), strict=True)),
        "average_histogram_new_grid": dict(zip(binspost, avg_post.tolist(), strict=True)),
        "realized_on_the_grid": dict(zip(bins, real_hist.tolist(), strict=True)),
    }, "Figure 1 — the histogram grid, the realized series and the reported densities")


if __name__ == "__main__":
    main()
