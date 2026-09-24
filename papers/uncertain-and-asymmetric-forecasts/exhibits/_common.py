"""Shared pieces of the *Uncertain and Asymmetric Forecasts* exhibit scripts.

Not an exhibit itself (the leading underscore keeps it out of the runner).
Holds the figure style the manuscript's figures were validated with, and the
two constructions several exhibits share: the quarterly NU series joined
with the EPU basket, and the matched inflation--growth panel.
"""

from __future__ import annotations

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

from nu_measures import measures
from nu_measures.exhibit import load_ecb_panel, load_epu, load_growth_panel

#: Colours of the manuscript's figures: raw grey, fitted blue, calibrated red, growth purple.
C = {"raw": "#8c8c8c", "fit": "#1f4e79", "cal": "#c0504d", "third": "#4f8a3d", "ngu": "#7b4fa0"}
INK, REF = "#1f4e79", "#c0504d"


def style(titlesize: float | None = None, legend_fontsize: float | None = None) -> None:
    """The rc settings the figures of the paper use.

    The manuscript's figures were drawn on matplotlib's defaults with the
    settings below on top, so the defaults are restored first (this undoes the
    library's house style that :class:`nu_measures.exhibit.Exhibit` applies).
    Two settings varied across the manuscript's figures and are passed by each
    script: the axes title size and the legend font size (matplotlib's
    defaults, ``large`` and ``medium``, when not given).
    """
    matplotlib.use("Agg")
    plt.rcdefaults()
    plt.rcParams.update({
        "font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 150,
        "savefig.bbox": "tight", "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.5,
        "legend.frameon": False,
    })
    if titlesize is not None:
        plt.rcParams["axes.titlesize"] = titlesize
    if legend_fontsize is not None:
        plt.rcParams["legend.fontsize"] = legend_fontsize


def z(s: pd.Series) -> pd.Series:
    return measures.standardize(s)


def nu_quarterly(panel: pd.DataFrame | None = None) -> pd.DataFrame:
    """Round means of ``raw_sd``, ``NU_unit``, ``NU_fitted`` by survey quarter, with the EPU basket joined."""
    panel = load_ecb_panel() if panel is None else panel
    q = measures.quarterly(measures.nu_series(panel))
    return q.join(load_epu(), how="left")


def matched_panel(panel: pd.DataFrame | None = None) -> pd.DataFrame:
    """Forecaster-rounds reporting both an inflation and a growth density (keys: survey quarter, forecaster)."""
    panel = load_ecb_panel() if panel is None else panel
    p = measures.add_nu(panel)
    p["Q"] = (p["Date"] + pd.DateOffset(months=1)).dt.to_period("Q")
    p["FCT"] = p["FCT_SOURCE"].astype(str)
    g = load_growth_panel()
    g["Q"] = pd.to_datetime(g["Date"]).dt.to_period("Q")
    g["FCT"] = g["FCT_SOURCE"].astype(str)
    m = p[["Q", "FCT", "NU_fitted", "NU_unit"]].merge(g[["Q", "FCT", "NGU"]], on=["Q", "FCT"]).dropna()
    return m.sort_values(["Q", "FCT"]).reset_index(drop=True)


def growth_quarterly() -> pd.DataFrame:
    """Round means of the raw growth standard deviation and NGU by survey quarter."""
    g = load_growth_panel()
    g["Q"] = pd.to_datetime(g["Date"]).dt.to_period("Q")
    out = g.groupby("Q").agg(NGU=("NGU", "mean"), raw_sd=("Variance", lambda s: (s**0.5).mean()))
    return out.join(load_epu(), how="left")
