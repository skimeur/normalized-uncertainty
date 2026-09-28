#!/usr/bin/env python3
"""Figure 8 of *Uncertain and Asymmetric Forecasts*: what the coherence weight does.

Paper: Vansteenberghe, E. (2026), *Uncertain and Asymmetric Forecasts*,
working paper (``vansteenberghe2026uncertain``), Section 4.2, Figure 8
(``fig:ac_map``).

Panel (a): contours of the AC index over the square its two normalised
components live in, the zero contour in bold and the quadrants where the
components agree in sign shaded; the dots are the individual densities of the
panel, the four marked points the cases of Figure 7. Panel (b): the index
against the plain average of the two components, as the asymmetry runs across
its range at two distances from target.

Inputs:  the ECB-SPF round files, through ``nu_measures.exhibit.load_ecb_panel``.
Outputs: ``figures/fig08_ac_map.{pdf,png}``, ``results/fig08_ac_map.{json,md}``.

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use
this code, cite the paper above.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from _common import INK, style

from nu_measures import asymmetry
from nu_measures.exhibit import Exhibit, load_ecb_panel

CASES = [(0.6, 0.6, "coherent\nupside"), (-0.6, -0.6, "coherent\ndownside"), (0.6, -0.3, "incoherent"), (-0.6, 0.3, "incoherent")]


def main() -> None:
    ex = Exhibit(__file__)
    style(titlesize=9, legend_fontsize=8)
    pan = asymmetry.ac_panel(load_ecb_panel()).dropna(subset=["Q_tilde", "A_tilde"])
    disagree = float((np.sign(pan["Q_tilde"]) * np.sign(pan["A_tilde"]) < 0).mean())
    ex.say(f"{len(pan)} forecaster-rounds; scales {pan.attrs['ac_iqr_scales']}")
    ex.say(f"share of densities whose asymmetry disagrees in sign with their median gap: {100 * disagree:.0f}%")
    ac_cases = {lab.replace("\n", " ") + f" ({q:+.1f}, {a:+.1f})": float(asymmetry.ac_index(q, a)) for q, a, lab in CASES}
    ex.say("AC at the four cases: " + ", ".join(f"{k}: {v:+.2f}" for k, v in ac_cases.items()))

    fig, ax = plt.subplots(1, 2, figsize=(7.4, 3.5))
    g = np.linspace(-1, 1, 401)
    Q, A = np.meshgrid(g, g)
    Z = asymmetry.ac_index(Q, A)
    a0 = ax[0]
    a0.fill_between([-1, 0], -1, 0, color="0.92", lw=0)
    a0.fill_between([0, 1], 0, 1, color="0.92", lw=0)
    a0.scatter(pan["Q_tilde"], pan["A_tilde"], s=1.4, color="0.40", alpha=0.11, lw=0, zorder=1)
    cs = a0.contour(Q, A, Z, levels=[-0.6, -0.4, -0.2, -0.05, 0.05, 0.2, 0.4, 0.6], colors="0.35", linewidths=0.7)
    a0.clabel(cs, fmt="%.2g", fontsize=7, inline=True)
    a0.contour(Q, A, Z, levels=[0.0], colors="black", linewidths=1.4)
    for q, a, lab in CASES:
        a0.plot([q], [a], "o", ms=4.5, color=INK, zorder=5)
        a0.annotate("%s\n$\\mathrm{AC}=%+.2f$" % (lab, asymmetry.ac_index(q, a)), xy=(q, a),
                    xytext=(0, 12 if a > 0 else -30), textcoords="offset points", ha="center", fontsize=7.5, color=INK,
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="0.7", lw=0.4))
    a0.axhline(0, color="0.5", lw=0.6)
    a0.axvline(0, color="0.5", lw=0.6)
    a0.set_xlabel("$\\tilde Q_t$: median minus target, normalized")
    a0.set_ylabel("$\\tilde A_t$: asymmetry, normalized")
    a0.set_title("(a) the index on the square its components live in", loc="left")
    a0.set_xlim(-1, 1)
    a0.set_ylim(-1, 1)
    a0.set_aspect("equal")
    a1 = ax[1]
    for q, ls, lab in ((0.6, "-", "$\\tilde Q_t=+0.6$"), (0.3, (0, (4, 2)), "$\\tilde Q_t=+0.3$")):
        a1.plot(g, asymmetry.ac_index(q, g), color=INK, ls=ls, lw=1.4, label="AC, " + lab)
        a1.plot(g, 0.5 * (q + g), color="0.45", ls=(0, (1, 2)), lw=1.2, label="plain average, " + lab if q == 0.6 else None)
    a1.axvline(0, color="0.5", lw=0.6)
    a1.axhline(0, color="0.5", lw=0.6)
    a1.annotate("signs disagree:\nthe weight damps", xy=(-0.55, asymmetry.ac_index(0.6, -0.55)), xytext=(-0.95, 0.30), fontsize=7.5, color="#4d4d4d",
                arrowprops=dict(arrowstyle="-", lw=0.6, color="#4d4d4d", shrinkA=2, shrinkB=3))
    a1.set_xlabel("$\\tilde A_t$")
    a1.set_ylabel("index value")
    a1.set_title("(b) what the coherence weight changes", loc="left")
    a1.legend(loc="upper left", handlelength=2.0)
    fig.tight_layout()
    ex.save_figure(fig)
    ex.write_results({"forecaster_rounds": len(pan), "share_signs_disagree": disagree, "ac_at_the_cases": ac_cases,
                      "iqr_scales": pan.attrs["ac_iqr_scales"]}, "Figure 8 — what the coherence weight does")


if __name__ == "__main__":
    main()
