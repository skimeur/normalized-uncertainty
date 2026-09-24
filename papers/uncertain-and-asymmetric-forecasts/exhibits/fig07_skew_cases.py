#!/usr/bin/env python3
"""Figure 7 of *Uncertain and Asymmetric Forecasts*: coherent against incoherent asymmetry, four cases.

Paper: Vansteenberghe, E. (forthcoming), *Uncertain and Asymmetric Forecasts*,
working paper (``vansteenberghe2026uncertain``), Section 4, Figure 7
(``fig:skewed_distributions``).

An illustration with no data: four skew-normal densities (shape +10 or -10,
scale 1.5), each shifted so that its median sits 0.2 point above or below the
2 per cent target, drawn with their quartiles and the target. The two cases
where the sign of the skewness agrees with the sign of the median's deviation
from target are the coherent ones (a strong directional signal); the two
where they disagree are the incoherent ones. The manuscript arranges the four
panels in a 2 x 2 table; this script writes them as four files, numbered as
the manuscript numbers the cases:

    1  skewness > 0, median > target   (coherent)
    2  skewness > 0, median < target   (incoherent)
    3  skewness < 0, median > target   (incoherent)
    4  skewness < 0, median < target   (coherent)

Inputs:  none.
Outputs: ``figures/fig07_skew_cases_{1,2,3,4}.{pdf,png}``, ``results/fig07_skew_cases.{json,md}``.

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use
this code, cite the paper above.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import skewnorm

from nu_measures import conventions as cv
from nu_measures.exhibit import Exhibit

SCALE = 1.5
CASES = {
    1: dict(shape=10.0, median=2.2, xlim=(-1.0, 7.0), coherent=True),
    2: dict(shape=10.0, median=1.8, xlim=(-1.0, 7.0), coherent=False),
    3: dict(shape=-10.0, median=2.2, xlim=(-1.0, 4.0), coherent=False),
    4: dict(shape=-10.0, median=1.8, xlim=(-1.0, 4.0), coherent=True),
}


def draw_case(ex: Exhibit, number: int, shape: float, median: float, xlim: tuple[float, float]) -> dict:
    loc = median - skewnorm.median(shape, loc=0, scale=SCALE)
    x = np.linspace(xlim[0], xlim[1], 1000)
    y = skewnorm.pdf(x, shape, loc=loc, scale=SCALE)
    q1, q2, q3 = (skewnorm.ppf(p, shape, loc=loc, scale=SCALE) for p in (0.25, 0.5, 0.75))
    bowley = (q3 - 2 * q2 + q1) / (q3 - q1)
    fig, ax = plt.subplots()
    ax.plot(x, y, label="Distribution")
    ax.plot([q1, q1], [0, skewnorm.pdf(q1, shape, loc=loc, scale=SCALE)], "g--", label="Q1")
    ax.plot([q2, q2], [0, skewnorm.pdf(q2, shape, loc=loc, scale=SCALE)], "r--", label="Median (Q2)")
    ax.plot([q3, q3], [0, skewnorm.pdf(q3, shape, loc=loc, scale=SCALE)], "b--", label="Q3")
    ax.axhline(0, color="black", linestyle="-", linewidth=1)
    ax.axvline(cv.TARGET, color="black", linestyle="-", linewidth=1)
    ax.set_title("Skewed Normal Distribution with Q1, Median, and Q3")
    ax.set_xlabel(r"$\pi (\%)$")
    ax.set_ylabel("Density")
    ax.legend()
    ex.save_figure(fig, name=f"{ex.name}_{number}")
    return {"shape": shape, "scale": SCALE, "loc": float(loc), "Q1": float(q1), "median": float(q2), "Q3": float(q3),
            "bowley_skewness": float(bowley), "median_minus_target": float(q2 - cv.TARGET)}


def main() -> None:
    ex = Exhibit(__file__)
    plt.rcdefaults()  # an illustration on matplotlib's defaults, as in the manuscript
    plt.rcParams.update({"savefig.dpi": 300, "savefig.bbox": "tight"})
    results = {}
    for number, case in CASES.items():
        r = draw_case(ex, number, case["shape"], case["median"], case["xlim"])
        r["coherent"] = case["coherent"]
        coherent = (r["bowley_skewness"] > 0) == (r["median_minus_target"] > 0)
        if coherent != case["coherent"]:
            raise SystemExit(f"case {number}: the drawn density is not in the class the manuscript assigns it to")
        results[f"case_{number}"] = r
        ex.say(f"case {number}: skewness {r['bowley_skewness']:+.3f}, median - target {r['median_minus_target']:+.2f} "
               f"-> {'coherent' if coherent else 'incoherent'}")
    ex.write_results(results, "Figure 7 — coherent against incoherent asymmetry, four cases")


if __name__ == "__main__":
    main()
