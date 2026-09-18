#!/usr/bin/env python3
"""What the correction does, in forty lines and with no data to download.

Two forecasters report densities of the same width. One expects inflation at
the target, the other expects an overshoot. Raw dispersion calls them equally
uncertain; it should not, because part of the second forecaster's width is the
predictable consequence of where they put the first moment.

Run it: ``python3 examples/quickstart.py``
"""

from __future__ import annotations

from nu_measures import measures, moments
from nu_measures.calendar import NU_R_FITTED, NU_R_UNIT, TARGET

# A half-point grid, the shape the survey uses.
EDGES = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
SUPPORT = moments.midpoints(EDGES)

# The same five-bin shape, centred two percentage points apart: identical
# dispersion, one forecaster below the target and one well above it.
AT_TARGET = [0, 10, 20, 40, 20, 10, 0, 0, 0, 0]
OVERSHOOT = [0, 0, 0, 0, 0, 10, 20, 40, 20, 10]


def main() -> None:
    print(f"{'forecaster':<12}{'mean':>8}{'sd':>8}{'NU (fitted)':>14}{'NU (unit)':>12}")
    for label, probs in (("at target", AT_TARGET), ("overshoot", OVERSHOOT)):
        mean = moments.mean(probs, SUPPORT)
        sd = moments.std(probs, SUPPORT)
        nu_fitted = float(measures.nu(sd, mean, r=NU_R_FITTED))
        nu_unit = float(measures.nu(sd, mean, r=NU_R_UNIT))
        print(f"{label:<12}{mean:>8.2f}{sd:>8.3f}{nu_fitted:>14.3f}{nu_unit:>12.3f}")

    print(
        "\nThe two densities have exactly the same width, so raw dispersion ranks them\n"
        f"alike. The first expects inflation below the announced target of {TARGET:.0f}%, where\n"
        "the correction does nothing at all -- NU is the standard deviation itself. The\n"
        "second expects an overshoot, and the part of the width that follows from that\n"
        "distance is divided out: once it is, the second forecaster is the less uncertain\n"
        "of the two about the outlook.\n"
        "\nThe two calibrations differ in how much they remove, never in the ranking.\n"
        "See docs/METHODS.md for the law the denominator comes from."
    )


if __name__ == "__main__":
    main()
