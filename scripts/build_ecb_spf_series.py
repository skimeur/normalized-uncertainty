#!/usr/bin/env python3
"""Build the ECB-SPF round series at the one-, two- and five-year horizons.

From the ECB's round files ``YYYYQn.csv`` (``NU_DATA_DIR/ecb_spf/rounds/``),
writes under ``--out`` (default ``NU_DATA_DIR/derived/series/``):

``ecb_spf_series_wide.csv``     one row per survey round, one column per
                                ``<series>_<horizon>`` (``level_1Y``, ``NU_5Y``, ...)
``ecb_spf_series_long.csv``     one row per round, horizon and series
``individual_panel_<h>.csv``    the moments of every density at horizon ``h``,
                                with NU and the AC components on the scales used
``series_metadata.json``        the rounds, the target, the AC scales, the version

The series -- level, disagreement, raw uncertainty, NU, skewness, AC, and the
counts, aggregate uncertainty and point-forecast versions beside them -- are
defined in ``nu_measures.series`` and in the README's column dictionary. AC is
on the one-year scales at every horizon unless ``--ac-scales own``; the scales
are computed on the papers' sample (1999Q1-2026Q3) so that the index of a
round does not move when rounds are added, unless ``--iqr-window none``.

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use the
series, cite Vansteenberghe (2026), *Uncertain and Asymmetric Forecasts*.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from nu_measures import __version__, asymmetry, measures, paths, series
from nu_measures import conventions as cv

PAPERS_SAMPLE = ("1998-12-01", "2026-06-01")  # panel dates of the 1999Q1 and 2026Q3 rounds


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--rounds", type=Path, default=None, help="folder of the round files (default: NU_DATA_DIR/ecb_spf/rounds)")
    ap.add_argument("--out", type=Path, default=None, help="output folder (default: NU_DATA_DIR/derived/series)")
    ap.add_argument("--horizons", default=",".join(cv.HORIZONS), help="comma-separated, among 1Y,2Y,5Y")
    ap.add_argument("--through", default=None, help="last round to read, e.g. 2026Q3 (default: all)")
    ap.add_argument("--ac-scales", default="1Y", choices=["1Y", "own"], help="AC scales: the one-year ones (default) or each horizon's own")
    ap.add_argument("--iqr-window", default="papers", help="'papers' (default), 'none', or 'YYYY-MM-DD,YYYY-MM-DD' on the panel Date")
    args = ap.parse_args(argv)

    rounds = args.rounds or paths.ecb_spf_rounds()
    if not Path(rounds).is_dir():
        print(f"no round files at {rounds}: download them from the ECB (see data/README.md)", file=sys.stderr)
        return 1
    out = args.out or paths.derived_dir() / "series"
    out.mkdir(parents=True, exist_ok=True)
    horizons = tuple(h.strip() for h in args.horizons.split(",") if h.strip())
    window = {"papers": PAPERS_SAMPLE, "none": None}.get(args.iqr_window)
    if window is None and args.iqr_window not in ("none",):
        window = tuple(args.iqr_window.split(","))

    need = [h for h in cv.HORIZONS if h in horizons or (h == "1Y" and args.ac_scales == "1Y")]
    panels = series.horizon_panels(rounds, need, args.through)
    S = series.ecb_spf_series(rounds, horizons, args.through, ac_scales=args.ac_scales,
                              ac_iqr_window=window, panels=panels)

    series.to_wide(S).to_csv(out / "ecb_spf_series_wide.csv", index_label="round")
    series.to_long(S).to_csv(out / "ecb_spf_series_long.csv", index=False)
    for h in horizons:
        p = asymmetry.ac_panel(measures.add_nu(panels[h][1]), scales=S.attrs["ac_iqr_scales"][h])
        p.to_csv(out / f"individual_panel_{h}.csv", index=False)
    meta = {
        "package_version": __version__,
        "rounds": S.attrs["rounds"],
        "horizons": list(horizons),
        "target": S.attrs["target"],
        "ac_scales": args.ac_scales,
        "ac_iqr_window": window,
        "ac_iqr_scales": S.attrs["ac_iqr_scales"],
        "nu_calibration": "unit, a = b = 1, one-sided",
    }
    (out / "series_metadata.json").write_text(json.dumps(meta, indent=2, default=str) + "\n")

    cols = ["level", "disagreement", "raw_uncertainty", "NU", "skewness", "AC", "n"]
    print(f"rounds {meta['rounds'][0]}-{meta['rounds'][1]}, horizons {', '.join(horizons)}; AC on the {args.ac_scales} scales")
    last = S.index.get_level_values("round").max()
    print(S.xs(last, level="round")[cols].round(3).to_string())
    print(f"written under {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
