#!/usr/bin/env python3
"""Normalized Uncertainty (a = b = 1) and Asymmetry Coherence from the ECB-SPF round files.

The shortest route from the ECB's published files to the two measures:

1. read the round files ``YYYYQn.csv`` (``NU_DATA_DIR/ecb_spf/rounds/``);
2. build the individual panel (moments of every reported density);
3. compute, for every forecaster-round, NU at the unit calibration --
   ``sigma / sqrt(1 + (mean - 2)_+)`` -- and the individual Asymmetry
   Coherence, and average them by round;
4. print the latest rounds and draw both series.

NU at ``a = b = 1`` needs no estimate: the value of a forecaster-round is the
same whatever the sample, so a series computed today and one computed after
ten more rounds agree on every common round. AC is normalised by two
interquartile ranges; the script freezes them on the papers' sample
(1999Q1-2026Q3) so that the index stays comparable when rounds are added --
pass ``--iqr-window none`` to normalise on the sample at hand instead.

References
----------
Vansteenberghe, E. (forthcoming). Uncertain and Asymmetric Forecasts. Working
paper.  (the construction of NU, NGU and AC)
Vansteenberghe, E. (2026). Tolerable Inflation, Intolerable Uncertainty.
Working paper, Banque de France.  (the law behind the denominator)

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use
this code, cite the paper whose measure you use.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from nu_measures import asymmetry, conventions, io_ecb_spf, measures, paths, plotting  # noqa: E402

PAPERS_SAMPLE = ("1998-12-01", "2026-06-01")  # panel dates of the 1999Q1 and 2026Q3 rounds


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--rounds", type=Path, default=None, help="folder of the round files (default: NU_DATA_DIR/ecb_spf/rounds)")
    ap.add_argument("--out", type=Path, default=Path("nu_and_ac"), help="output stem for the CSV and the figure")
    ap.add_argument("--iqr-window", default="papers", help="'papers' (default), 'none', or 'YYYY-MM-DD,YYYY-MM-DD'")
    args = ap.parse_args(argv)

    rounds = args.rounds or paths.ecb_spf_rounds()
    if not Path(rounds).is_dir():
        print(f"no round files at {rounds}: download them from the ECB (see data/README.md)", file=sys.stderr)
        return 1

    flat = io_ecb_spf.flat_panel(io_ecb_spf.read_rounds(rounds))
    panel = io_ecb_spf.individual_panel(flat)

    # NU, unit calibration: three numbers per forecaster, no estimate.
    nu = measures.nu_series(panel)  # round means of raw_sd, NU_unit, NU_fitted

    # AC, with the normalisation window made explicit.
    if args.iqr_window == "papers":
        window = PAPERS_SAMPLE
    elif args.iqr_window == "none":
        window = None
    else:
        window = tuple(args.iqr_window.split(","))
    ac = asymmetry.ac_series(asymmetry.ac_panel(panel, iqr_window=window))

    out = nu.set_index("Q")[["raw_sd", "NU_unit"]].join(ac[["AC", "coherence"]])
    out.index.name = "survey_quarter"
    out.to_csv(f"{args.out}.csv")

    print(f"{len(out)} rounds, {out.index.min()} to {out.index.max()}; target {conventions.TARGET}%")
    print("AC scales (IQR of the median gap, IQR of the smoothed skewness):", ac.attrs["ac_iqr_scales"])
    print(out.tail(6).round(3).to_string())

    plotting.style()
    fig, ax = plt.subplots(2, 1, figsize=(7.0, 5.0), sharex=True)
    x = out.index.to_timestamp()
    ax[0].plot(x, out["raw_sd"], label="raw dispersion (mean individual s.d.)", **plotting.series_kwargs(1), markevery=8)
    ax[0].plot(x, out["NU_unit"], label="Normalized Uncertainty, a = b = 1", **plotting.series_kwargs(0), markevery=8)
    ax[0].set_ylabel("percentage points")
    ax[0].legend(loc="upper left")
    ax[1].fill_between(x, 0, out["AC"], color="0.85", lw=0)
    ax[1].plot(x, out["AC"], label="Asymmetry Coherence", **plotting.series_kwargs(2), markevery=8)
    ax[1].axhline(0, color="0.4", lw=0.8)
    ax[1].set_ylabel("index in [-1, 1]")
    ax[1].legend(loc="upper left")
    plotting.save(fig, args.out.name, args.out.parent)
    print(f"written {args.out}.csv, {args.out}.pdf, {args.out}.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
