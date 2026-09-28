#!/usr/bin/env python3
"""Figure 2 of *Uncertain and Asymmetric Forecasts*: the variance decomposition of the averaged density.

Paper: Vansteenberghe, E. (2026), *Uncertain and Asymmetric Forecasts*,
working paper (``vansteenberghe2026uncertain``), Section 2, Figure 2
(``fig:var_decomposition``).

Round by round, the variance of the equal-weight average of the individual
one-year-ahead inflation densities (the solid line) is stacked as the
cross-sectional mean of the individual variances (the lower band) plus the
population variance of the individual means, disagreement (the upper band):
the identity of the paper's equation (var-mixture). Both bands carry a grey
value and a hatch direction, and are labelled inside the panel, so the figure
reads in black and white. The identity is verified numerically before the
figure is drawn (the largest stacking gap is written to the results file).
Every density enters, including the few single-bin ones with zero variance
that the law's estimation sample sets aside: the averaged density is the
equal-weight mixture of all of them.

Inputs:  the ECB-SPF round files, through ``load_flat_panel`` and ``load_ecb_panel``.
Outputs: ``figures/fig02_variance_decomposition.{pdf,png}``, ``results/fig02_variance_decomposition.{json,md}``.
Sample:  every round, 1999Q1--2026Q3.

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use
this code, cite the paper above.
"""

from __future__ import annotations

import matplotlib.pyplot as plt

from nu_measures import io_ecb_spf
from nu_measures.exhibit import Exhibit, load_ecb_panel, load_flat_panel


def main() -> None:
    ex = Exhibit(__file__)
    plt.rcdefaults()  # the manuscript's figure was drawn on matplotlib's defaults
    avg = io_ecb_spf.averaged_density(load_flat_panel())
    p = load_ecb_panel().dropna(subset=["Mean_spd", "Variance_spd"])
    agg = p.groupby("Date").agg(W=("Variance_spd", "mean"), D=("Mean_spd", lambda s: s.var(ddof=0)))
    t = avg.join(agg, how="inner").sort_index()
    gap = (t["Variance_avg"] - (t["W"] + t["D"])).abs().max()
    ex.say(f"{len(t)} rounds, {t.index.min().date()}..{t.index.max().date()}; largest stacking gap {gap:.3e}")
    if gap > 1e-9:
        raise SystemExit("the variance of the averaged density does not equal W + D")
    top = t["Variance_avg"].idxmax()
    ex.say(f"peak {t['Variance_avg'].max():.3f} at {top.date()}: W {t.loc[top, 'W']:.3f}, D {t.loc[top, 'D']:.3f}; "
           f"mean share of disagreement {(t['D'] / t['Variance_avg']).mean():.3f}")

    with plt.rc_context({"hatch.linewidth": 0.5, "font.size": 9}):
        fig, ax = plt.subplots(figsize=(7.4, 4.4))
        ax.set_axisbelow(True)
        ax.grid(axis="y", color="0.85", linewidth=0.5)
        bands = ax.stackplot(t.index, t["W"], t["D"], labels=["Average individual SPD variance", "Disagreement"],
                             colors=["0.88", "0.66"], edgecolor="black", linewidth=0.6)
        for band, hatch in zip(bands, ["///", "\\\\\\"], strict=True):
            band.set_hatch(hatch)
        ax.plot(t.index, t["Variance_avg"], linewidth=1.8, color="black", linestyle="-", zorder=5,
                label="Variance of the averaged SPD")
        # each band labelled in the calm middle of the panel, with a leader into it
        n = len(t)
        ytop = ax.get_ylim()[1]
        for pos, frac, base, series, text in ((0.22, 0.42, 0 * t["W"], t["W"], "Average individual\nSPD variance"),
                                              (0.50, 0.66, t["W"], t["D"], "Disagreement")):
            k = t.index[int(pos * n)]
            ax.annotate(text, xy=(k, base[k] + series[k] / 2), xytext=(k, frac * ytop), ha="center", va="center", fontsize=8.5,
                        bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="0.6", linewidth=0.5),
                        arrowprops=dict(arrowstyle="-", linewidth=0.6, color="0.35", shrinkA=2, shrinkB=1))
        ax.set_xlabel("Date", fontsize=10)
        ax.set_ylabel("Variance", fontsize=10)
        ax.set_title("Variance decomposition = average individual variance + disagreement", fontsize=10)
        ax.tick_params(labelsize=9)
        ax.legend(loc="upper left", fontsize=8.5, frameon=True, framealpha=0.9, edgecolor="0.6")
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
        fig.tight_layout()
        ex.save_figure(fig)
    ex.write_results({"rounds": int(len(t)), "first": str(t.index.min().date()), "last": str(t.index.max().date()),
                      "largest_stacking_gap": float(gap), "peak_round": str(top.date()),
                      "peak": {"T": float(t["Variance_avg"].max()), "W": float(t.loc[top, "W"]), "D": float(t.loc[top, "D"])},
                      "mean_share_of_disagreement": float((t["D"] / t["Variance_avg"]).mean()),
                      "series": {str(d.date()): {"W": float(r["W"]), "D": float(r["D"]), "T": float(r["Variance_avg"]), "n": int(r["n"])}
                                 for d, r in t.iterrows()}},
                     "Figure 2 — the variance decomposition of the averaged density")


if __name__ == "__main__":
    main()
