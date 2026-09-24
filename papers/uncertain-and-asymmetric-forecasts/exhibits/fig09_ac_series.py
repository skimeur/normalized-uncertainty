#!/usr/bin/env python3
"""Figure 9 of *Uncertain and Asymmetric Forecasts*: Asymmetry Coherence and the pieces it is made of.

Paper: Vansteenberghe, E. (forthcoming), *Uncertain and Asymmetric Forecasts*,
working paper (``vansteenberghe2026uncertain``), Section 4.3, Figure 9
(``fig:ac_series``) and the counts of its note.

Panel (a): the two normalised components, the median's distance from target
and the asymmetry. Panel (b): the coherence weight, below one half exactly
when the two disagree in sign. Panel (c): the index. All three are
cross-forecaster means of the individual values, on the round's own quarter.

Inputs:  the ECB-SPF round files, through ``nu_measures.exhibit.load_ecb_panel``.
Outputs: ``figures/fig09_ac_series.{pdf,png}``, ``results/fig09_ac_series.{json,md}``.

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use
this code, cite the paper above.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from _common import INK, REF, style

from nu_measures import asymmetry
from nu_measures.exhibit import Exhibit, load_ecb_panel


def main() -> None:
    ex = Exhibit(__file__)
    style(titlesize=9, legend_fontsize=8)
    pan = asymmetry.ac_panel(load_ecb_panel())
    S = asymmetry.ac_series(pan)
    ind = pan.dropna(subset=["coherence"])["coherence"]
    p5, p95 = float(np.percentile(ind, 5)), float(np.percentile(ind, 95))
    neg, pos, big = int((S["AC"] < 0).sum()), int((S["AC"] > 0).sum()), int((S["AC"].abs() > 0.1).sum())
    ex.say(f"{int(S['n'].sum())} forecaster-rounds over {len(S)} rounds; AC in [{S['AC'].min():.3f}, {S['AC'].max():.3f}]")
    ex.say(f"index negative in {neg} rounds, positive in {pos}; |AC| > 0.1 in {big}; round weight in [{S['coherence'].min():.2f}, {S['coherence'].max():.2f}]; individual weight 5th-95th percentile [{p5:.2f}, {p95:.2f}]")

    x = S.index.to_timestamp()
    fig, ax = plt.subplots(3, 1, figsize=(7.0, 6.2), sharex=True)
    ax[0].plot(x, S["Q_tilde"], color=INK, lw=1.3, label="$\\tilde Q_t$, median minus target")
    ax[0].plot(x, S["A_tilde"], color="0.35", lw=1.1, ls=(0, (4, 2)), label="$\\tilde A_t$, asymmetry")
    ax[0].axhline(0, color=REF, lw=0.9, ls=(0, (1, 2)))
    ax[0].set_title("(a) the two normalized components", loc="left")
    ax[0].set_ylabel("normalized")
    ax[0].legend(loc="upper left", ncol=2, handlelength=2.0)
    ax[1].plot(x, S["coherence"], color=INK, lw=1.3)
    ax[1].axhline(0.5, color=REF, lw=0.9, ls=(0, (1, 2)))
    ax[1].annotate("below $0.5$: the components disagree in sign", xy=(x[2], 0.575), fontsize=7.5, color=REF)
    ax[1].set_title("(b) the coherence weight $(1+\\tilde Q_t\\tilde A_t)/2$", loc="left")
    ax[1].set_ylabel("weight")
    ax[2].fill_between(x, 0, S["AC"], color="0.80", lw=0)
    ax[2].plot(x, S["AC"], color=INK, lw=1.4)
    ax[2].axhline(0, color=REF, lw=0.9, ls=(0, (1, 2)))
    ax[2].set_title("(c) Asymmetry Coherence", loc="left")
    ax[2].set_ylabel("index")
    ax[2].set_xlabel("survey round")
    fig.align_ylabels(ax)
    fig.subplots_adjust(hspace=0.42)
    ex.save_figure(fig)
    ex.write_results({"rounds": len(S), "forecaster_rounds": int(S["n"].sum()), "ac_negative_rounds": neg, "ac_positive_rounds": pos,
                      "ac_abs_above_0_1_rounds": big, "round_weight_range": [float(S["coherence"].min()), float(S["coherence"].max())],
                      "individual_weight_p5_p95": [p5, p95], "iqr_scales": pan.attrs["ac_iqr_scales"],
                      "series": S.reset_index().assign(Q=lambda d: d["Q"].astype(str)).to_dict("records")},
                     "Figure 9 — Asymmetry Coherence and its components")


if __name__ == "__main__":
    main()
