#!/usr/bin/env python3
"""Figure 7 of *Tolerable Inflation, Intolerable Uncertainty*: acting without identifying slope or composition.

Paper: Vansteenberghe, E. (2026), *Tolerable Inflation, Intolerable Uncertainty*,
working paper, Banque de France (``vansteenberghe2026tolerable``), Section 4,
Figure 7 (``fig:twounknowns``).

Exact curves of the static block; no data. Panel (a): the loss of tolerating
nothing relative to tolerating fully, s^2 / (chi + (1 - s)^2) - 1, on the
unit interval of supply shares s, at the low and the high end of the
published euro-area slope range (chi = 0.10 and 0.39); zero tolerance is the
costlier corner exactly where s > (1 + chi) / 2, the dashed verticals mark
that boundary at the range's ends, and the bracket marks the published
readings of the surge's supply share, [0.50, 0.75]. Panel (b): the
unidentifiable optimum lambda* = iota s over the calibrated intensity band
iota in [0.72, 0.91]; its image at the published surge shares is the band
[0.36, 0.68] of the paper's proposition.

Inputs:  none.
Outputs: ``figures/fig07_two_unknowns.{pdf,png}``, ``results/fig07_two_unknowns.{json,md}``.

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use
this code, cite the paper above.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from _common import style

from nu_measures.exhibit import Exhibit

#: The published euro-area slope range chi = kappa x epsilon (kappa 0.017--0.038, epsilon 6--10): its exact ends,
#: which place the dominance boundaries, and the two rounded values the curves are drawn at.
CHI_RANGE = (0.0989, 0.3889)
CHI_DRAWN = [(0.10, "#2166ac", "$\\chi=0.10$ (published range, low end)"), (0.39, "#e08214", "$\\chi=0.39$ (published range, high end)")]
SURGE_SHARE = (0.50, 0.75)  # the published readings of the surge's supply share
INTENSITY = (0.72, 0.91)  # the calibrated intensity band iota
RC = {"font.family": "serif", "font.serif": ["DejaVu Serif"], "mathtext.fontset": "cm", "font.size": 9.0, "axes.linewidth": 0.6}


def loss_ratio(s: np.ndarray, chi: float) -> np.ndarray:
    """L(no tolerance) / L(full tolerance) - 1."""
    return s**2 / (chi + (1 - s) ** 2) - 1


def boundary(chi: float) -> float:
    """The supply share above which zero tolerance is the costlier corner."""
    return (1 + chi) / 2


def main() -> None:
    ex = Exhibit(__file__)
    style(RC)
    s = np.linspace(0.0, 1.0, 400)
    b_lo, b_hi = boundary(CHI_RANGE[0]), boundary(CHI_RANGE[1])
    s_lo, s_hi = SURGE_SHARE
    i_lo, i_hi = INTENSITY
    lam_lo, lam_hi = i_lo * s_lo, i_hi * s_hi
    ex.say(f"dominance boundaries (1 + chi) / 2 at the range's ends: {b_lo:.3f}, {b_hi:.3f}; "
           f"the optimum's band at the surge shares: [{lam_lo:.4f}, {lam_hi:.4f}]")

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(6.6, 2.95))
    ax.axhspan(-1.05, 0, color="0.955", zorder=0)
    ax.axvspan(b_hi, 1.0, color="#2166ac", alpha=0.10, zorder=0)
    ax.axvspan(0.0, b_lo, color="#b2182b", alpha=0.07, zorder=0)
    for chi, col, lab in CHI_DRAWN:
        ax.plot(s, loss_ratio(s, chi), color=col, lw=1.4, label=lab)
    ax.axhline(0, color="0.4", lw=0.8)
    ax.set_yscale("symlog", linthresh=1.0)
    ax.set_ylim(-1.05, 12)
    ax.set_yticks([-1, -0.5, 0, 0.5, 1, 3, 10])
    ax.set_yticklabels(["$-1$", "$-0.5$", "$0$", "$0.5$", "$1$", "$3$", "$10$"])
    ax.annotate("", xy=(s_hi, -0.86), xytext=(s_lo, -0.86), arrowprops=dict(arrowstyle="|-|,widthA=0.22,widthB=0.22", color="0.25", lw=1.1))
    ax.text((s_lo + s_hi) / 2 - 0.07, -0.76, "published surge\nshare readings", fontsize=6.3, ha="center", color="0.25")
    for bx in (b_lo, b_hi):
        ax.axvline(bx, color="0.55", lw=0.7, ls=(0, (2, 2)))
        ax.text(bx, 12.6, f"{bx:.2f}", fontsize=6.2, ha="center", color="0.4")
    ax.set_xlabel("supply share $s$ of the impulse", fontsize=8.4)
    ax.set_ylabel("$L(\\mathrm{no\\ tol.})/L(\\mathrm{full\\ tol.})-1$", fontsize=8.4)
    ax.set_title("(a) tolerating nothing against tolerating fully", fontsize=8.6)
    ax.legend(fontsize=6.4, loc="upper left", frameon=False)
    ax.set_xlim(0, 1)
    ax.tick_params(labelsize=7.8)

    ax2.fill_between(s, i_lo * s, i_hi * s, color="#2166ac", alpha=0.18, lw=0, label="$\\lambda^{*}=\\iota\\,s$, $\\iota\\in[0.72,0.91]$")
    ax2.plot(s, i_lo * s, color="#2166ac", lw=1.0)
    ax2.plot(s, i_hi * s, color="#2166ac", lw=1.0)
    ax2.axvspan(s_lo, s_hi, color="0.88", alpha=0.55, zorder=0)
    ax2.annotate("", xy=(0.033, lam_hi), xytext=(0.033, lam_lo), arrowprops=dict(arrowstyle="|-|,widthA=0.22,widthB=0.22", color="#e08214", lw=1.3))
    ax2.text(0.055, (lam_lo + lam_hi) / 2, "$[0.36,\\,0.68]$\nthe published band", fontsize=6.6, color="#e08214", va="center")
    for xx in (s_lo, s_hi):
        ax2.plot([xx, xx], [i_lo * xx, i_hi * xx], color="0.35", lw=1.2)
    ax2.plot([s_lo, 0.045], [lam_lo, lam_lo], color="0.6", lw=0.6, ls=":")
    ax2.plot([s_hi, 0.045], [lam_hi, lam_hi], color="0.6", lw=0.6, ls=":")
    ax2.text((s_lo + s_hi) / 2, 0.035, "surge share readings", fontsize=6.3, ha="center", color="0.3")
    ax2.set_xlabel("supply share $s$ of the impulse", fontsize=8.4)
    ax2.set_ylabel("optimal tolerated share $\\lambda^{*}$", fontsize=8.4)
    ax2.set_title("(b) the optimum, and the band publications leave", fontsize=8.6)
    ax2.legend(fontsize=6.4, loc="upper left", frameon=False)
    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1)
    ax2.tick_params(labelsize=7.8)
    fig.tight_layout(pad=0.6)
    plt.rcParams["savefig.bbox"] = "tight"
    ex.save_figure(fig)
    ex.write_results({"chi_range": list(CHI_RANGE), "chi_drawn": [c[0] for c in CHI_DRAWN], "dominance_boundaries": [b_lo, b_hi],
                      "surge_share_readings": list(SURGE_SHARE), "intensity_band": list(INTENSITY), "optimum_band": [lam_lo, lam_hi]},
                     "Figure 7 — acting without identifying slope or composition")


if __name__ == "__main__":
    main()
