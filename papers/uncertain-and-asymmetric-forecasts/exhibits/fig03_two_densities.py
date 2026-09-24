#!/usr/bin/env python3
"""Figure 3 of *Uncertain and Asymmetric Forecasts*: skewness of two densities against skewness of their average.

Paper: Vansteenberghe, E. (forthcoming), *Uncertain and Asymmetric Forecasts*,
working paper (``vansteenberghe2026uncertain``), Section 2, Figure 3
(``fig:two_SPD_skewness_illustration``).

An illustration with no data: two scaled beta densities, ``(a, b) = (7, 8)``
(right-skewed) and ``(5.5, 5)`` (mildly left-skewed), both rescaled by a
factor of 2, drawn with their quartiles; and their simple average, with the
average of the two sets of quartiles. Bowley's skewness (in per cent) is
printed in each panel. The point is that averaging densities obscures the
asymmetry each of them carries, which is why the paper works with individual
densities rather than the averaged one.

Inputs:  none.
Outputs: ``figures/fig03_two_densities.{pdf,png}``, ``results/fig03_two_densities.{json,md}``.

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use
this code, cite the paper above.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import beta

from nu_measures.exhibit import Exhibit

A_LEFT, B_LEFT = 5.5, 5.0  # mild negative skew
A_RIGHT, B_RIGHT = 7.0, 8.0  # stronger positive skew
SCALE = 2.0
X_RANGE = 1.0  # half-width of each panel around its median
FONTSIZE = 13


def bowley(q1: float, q2: float, q3: float) -> float:
    """Bowley's quartile skewness, in per cent."""
    return 100.0 * (q3 - 2.0 * q2 + q1) / (q3 - q1)


def main() -> None:
    ex = Exhibit(__file__)
    plt.rcdefaults()  # an illustration on matplotlib's defaults, as in the manuscript
    x = np.linspace(0, 2.5, 1000)
    y_left = beta.pdf(x / SCALE, A_LEFT, B_LEFT) / SCALE
    y_right = beta.pdf(x / SCALE, A_RIGHT, B_RIGHT) / SCALE
    y_avg = (y_left + y_right) / 2
    q_left = [beta.ppf(p, A_LEFT, B_LEFT) * SCALE for p in (0.25, 0.5, 0.75)]
    q_right = [beta.ppf(p, A_RIGHT, B_RIGHT) * SCALE for p in (0.25, 0.5, 0.75)]
    q_avg = [(a + b) / 2 for a, b in zip(q_left, q_right, strict=True)]
    skew = {"left": bowley(*q_left), "right": bowley(*q_right), "average": bowley(*q_avg)}
    for k, v in skew.items():
        ex.say(f"Bowley skewness, {k}: {v:.2f}")

    fig = plt.figure(figsize=(10, 10))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 2], width_ratios=[1, 1])
    panels = (
        (gs[0, 0], y_right, q_right, "Right-Skewed Distribution", "Right-Skewed Distribution (Beta)", "blue", skew["right"], FONTSIZE, "best"),
        (gs[0, 1], y_left, q_left, "Left-Skewed Distribution", "Left-Skewed Distribution (Beta)", "red", skew["left"], FONTSIZE, "best"),
        (gs[1, :], y_avg, q_avg, "Average of Both Distributions", "Average of Right and Left-Skewed Distributions", "green",
         skew["average"], FONTSIZE + 5, "upper left"),
    )
    for spec, y, (q1, q2, q3), label, title, colour, sk, size, loc in panels:
        ax = fig.add_subplot(spec)
        ax.plot(x, y, label=label, color=colour)
        ax.axvline(q1, color="purple", linestyle="--", label="Q1")
        ax.axvline(q2, color="black", linestyle="--", label="Median")
        ax.axvline(q3, color="orange", linestyle="--", label="Q3")
        ax.set_title(title)
        ax.set_xlabel(r"$\pi (\%)$")
        ax.set_ylabel("Density")
        ax.text(0.8, 0.85, f"Skewness: {sk:.2f}", transform=ax.transAxes, ha="center", color=colour, fontsize=size)
        ax.legend(loc=loc)
        ax.set_xlim(q2 - X_RANGE, q2 + X_RANGE)
    fig.tight_layout()
    ex.save_figure(fig)
    ex.write_results({"beta_parameters": {"left": [A_LEFT, B_LEFT], "right": [A_RIGHT, B_RIGHT], "scale": SCALE},
                      "quartiles": {"left": q_left, "right": q_right, "average_of_quartiles": q_avg},
                      "bowley_skewness_pct": skew},
                     "Figure 3 — skewness of two densities against skewness of their average")


if __name__ == "__main__":
    main()
