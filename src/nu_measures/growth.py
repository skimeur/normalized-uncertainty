"""Normalized Growth Uncertainty: the ECB-SPF growth densities, potential growth, and NGU.

The growth block of the round files ("GROWTH EXPECTATIONS; YEAR-ON-YEAR CHANGE
IN REAL GDP") has changed its histogram grid several times, and a single round
can carry more than one grid. The authoritative builder resolves a density's
grid from its leftmost and rightmost filled bins (the five cases below), and
this module reproduces that rule and the outputs it feeds (``individual_ngu``,
``ngu``) exactly.

Potential growth is the annualised first difference of the Hodrick--Prescott
trend (``lambda = 1600``) of log real euro-area GDP, carried to the survey
quarter of each round; the denominator of NGU is symmetric in the distance of
the forecaster's mean from it (:func:`nu_measures.measures.ngu`).

Reference: Vansteenberghe (forthcoming), *Uncertain and Asymmetric Forecasts*
(``vansteenberghe2026uncertain``), Section 5.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from . import conventions as cv
from .io_ecb_spf import ROUND_FILE
from .measures import ngu as _ngu

__all__ = [
    "GDP_YOY_MIN", "GDP_YOY_MAX", "GROWTH_BIN_LABELS", "GROWTH_FLAT_COLUMNS",
    "read_round_growth", "read_rounds_growth", "flat_panel_growth",
    "potential_growth", "growth_densities", "ngu_panel", "ngu_series",
]

#: Realized year-on-year real GDP growth of the euro area (per cent), lowest and
#: highest values of the ECB series ``MNA.Q.Y.I9.W2.S1.S1.B.B1GQ._Z._Z._Z.EUR.LR.N``
#: (vintage of 28 July 2026; 1996Q1-2026Q1): they close the open tails of the
#: growth grids. Recompute them from a newer download with
#: :func:`gdp_extremes` when the sample is extended.
GDP_YOY_MIN: float = -13.913219372991081
GDP_YOY_MAX: float = 15.266103604497339

#: Column codes of the growth block mapped to the interval labels the panel carries.
GROWTH_BIN_LABELS: dict[str, str] = {
    "TN15_0": "]-inf,-15.0]", "TN6_0": "]-inf,-6.0]", "TN1_0": "]-inf,-1.0]", "T0_0": "]-inf,0.0]",
    "FN15_0TN13_1": "[-15.0,-13.1]", "FN13_0TN11_1": "[-13.0,-11.1]", "FN11_0TN9_1": "[-11.0,-9.1]",
    "FN9_0TN7_1": "[-9.0,-7.1]", "FN7_0TN5_1": "[-7.0,-5.1]", "FN6_0TN5_6": "[-6.0,-5.6]",
    "FN5_5TN5_1": "[-5.5,-5.1]", "FN5_0TN4_6": "[-5.0,-4.6]", "FN5_0TN3_1": "[-5.0,-3.1]",
    "FN4_5TN4_1": "[-4.5,-4.1]", "FN4_0TN3_6": "[-4.0,-3.6]", "FN3_5TN3_1": "[-3.5,-3.1]",
    "FN3_0TN2_6": "[-3.0,-2.6]", "FN3_0TN1_1": "[-3.0,-1.1]", "FN2_5TN2_1": "[-2.5,-2.1]",
    "FN2_0TN1_6": "[-2.0,-1.6]", "FN1_5TN1_1": "[-1.5,-1.1]", "FN1_0TN0_6": "[-1.0,-0.6]",
    "FN0_5TN0_1": "[-0.5,-0.1]", "F0_0T0_4": "[0.0,0.4]", "F0_5T0_9": "[0.5,0.9]",
    "F1_0T1_4": "[1.0,1.4]", "F1_5T1_9": "[1.5,1.9]", "F2_0T2_4": "[2.0,2.4]", "F2_5T2_9": "[2.5,2.9]",
    "F3_0T3_4": "[3.0,3.4]", "F3_5T3_9": "[3.5,3.9]", "F4_0T4_4": "[4.0,4.4]", "F4_5T4_9": "[4.5,4.9]",
    "F4_0T5_9": "[4.0,5.9]", "F6_0T7_9": "[6.0,7.9]", "F8_0T9_9": "[8.0,9.9]", "F4_0": "[4.0,+inf[",
    "F5_0": "[5.0,+inf[", "F10_0": "[10.0,+inf[",
}

GROWTH_FLAT_COLUMNS: tuple[str, ...] = (
    "Date", "FCT_SOURCE", "POINT", "]-inf,0.0]", "]-inf,-1.0]", "[-1.0,-0.6]",
    "[-0.5,-0.1]", "[0.0,0.4]", "[0.5,0.9]", "[1.0,1.4]", "[1.5,1.9]",
    "[2.0,2.4]", "[2.5,2.9]", "[3.0,3.4]", "[3.5,3.9]", "[4.0,5.9]",
    "[6.0,7.9]", "[8.0,9.9]", "[10.0,+inf[",
    "[4.0,+inf[", "]-inf,-15.0]", "[-15.0,-13.1]",
    "[-13.0,-11.1]", "[-11.0,-9.1]", "[-9.0,-7.1]", "[-7.0,-5.1]",
    "[-5.0,-3.1]", "[-3.0,-1.1]",
    "]-inf,-6.0]", "[-6.0,-5.6]", "[-5.5,-5.1]", "[-5.0,-4.6]",
    "[-4.5,-4.1]", "[-4.0,-3.6]", "[-3.5,-3.1]", "[-3.0,-2.6]",
    "[-2.5,-2.1]", "[-2.0,-1.6]", "[-1.5,-1.1]",
    "[4.0,4.4]", "[4.5,4.9]", "[5.0,+inf[",
)

_GROWTH_LABEL = "GROWTH EXPECTATIONS; YEAR-ON-YEAR CHANGE IN REAL GDP"
_TARGET = {1: (0, "Q3", 9), 2: (0, "Q4", 12), 3: (1, "Q1", 3), 4: (1, "Q2", 6)}


def read_round_growth(path: str | Path) -> pd.DataFrame:
    """The one-year-ahead growth block of one round file (target: the quarter three quarters ahead)."""
    path = Path(path)
    m = ROUND_FILE.match(path.name)
    if not m:
        raise ValueError(f"{path.name} is not named like a round file (YYYYQn.csv)")
    year, quarter = int(m.group(1)), int(m.group(2))
    raw = pd.read_csv(path, header=None, dtype=str)
    hits = raw.apply(lambda r: r.astype(str).str.strip().eq(_GROWTH_LABEL)).any(axis=1)
    if not hits.any():
        return pd.DataFrame()
    header_row = int(hits.idxmax()) + 1
    cols = raw.iloc[header_row, :].tolist()
    empties = raw[raw.isnull().all(axis=1) & (raw.index > header_row)].index
    end = int(empties[0]) if len(empties) else len(raw)
    df = raw.iloc[header_row + 1 : end, :].copy()
    df.columns = [c.strip() if isinstance(c, str) else c for c in cols]
    df = df.dropna(how="all", axis=1).dropna(how="all", axis=0)
    for col in df.columns:
        if col != "TARGET_PERIOD":
            df[col] = pd.to_numeric(df[col], errors="coerce")
    add, q, month = _TARGET[quarter]
    df = df.loc[df["TARGET_PERIOD"] == f"{year + add}{q}", :].copy()
    df["Year"] = year
    df["Q"] = quarter
    df["Date"] = pd.Timestamp(year=year + add, month=month, day=1)
    return df


def read_rounds_growth(directory: str | Path) -> pd.DataFrame:
    directory = Path(directory)
    files = sorted(p for p in directory.iterdir() if ROUND_FILE.match(p.name))
    frames = [read_round_growth(p) for p in files]
    frames = [f for f in frames if not f.empty]
    if not frames:
        raise FileNotFoundError(f"no growth blocks found in {directory}")
    return pd.concat(frames, ignore_index=True)


def flat_panel_growth(rounds: pd.DataFrame) -> pd.DataFrame:
    """The growth flat panel, laid out as the authoritative ``df_panel_gdp`` file."""
    df = rounds.dropna(how="all", axis=1).dropna(how="all", axis=0).rename(columns=GROWTH_BIN_LABELS)
    for c in GROWTH_FLAT_COLUMNS:
        if c not in df.columns:
            df[c] = np.nan
    return df.loc[:, list(GROWTH_FLAT_COLUMNS)].reset_index(drop=True)


def gdp_extremes(gdp_levels: pd.Series) -> tuple[float, float]:
    """Lowest and highest year-on-year growth of a quarterly level series (per cent)."""
    yoy = 100.0 * gdp_levels.astype(float).pct_change(4)
    return float(np.nanmin(yoy)), float(np.nanmax(yoy))


def potential_growth(gdp_levels: pd.Series, hp_lambda: float = cv.HP_LAMBDA) -> pd.Series:
    """Annualised growth of the Hodrick--Prescott trend of log real GDP, by quarter start."""
    from statsmodels.tsa.filters.hp_filter import hpfilter

    y = gdp_levels.astype(float).dropna()
    y.index = pd.to_datetime(y.index).to_period("Q").to_timestamp()
    y = y.sort_index()
    _, trend = hpfilter(np.log(y), lamb=hp_lambda)
    trend = trend.reindex(y.index)
    return (400.0 * trend.diff()).rename("g_potential")


# The grid rules of the authoritative builder: the leftmost filled bin picks the grid.
_BINS = [
    "]-inf,0.0]", "]-inf,-1.0]", "[-1.0,-0.6]", "[-0.5,-0.1]", "[0.0,0.4]", "[0.5,0.9]", "[1.0,1.4]",
    "[1.5,1.9]", "[2.0,2.4]", "[2.5,2.9]", "[3.0,3.4]", "[3.5,3.9]", "[4.0,5.9]", "[6.0,7.9]", "[8.0,9.9]",
    "[10.0,+inf[", "[4.0,+inf[", "]-inf,-15.0]", "[-15.0,-13.1]", "[-13.0,-11.1]", "[-11.0,-9.1]",
    "[-9.0,-7.1]", "[-7.0,-5.1]", "[-5.0,-3.1]", "[-3.0,-1.1]", "]-inf,-6.0]", "[-6.0,-5.6]", "[-5.5,-5.1]",
    "[-5.0,-4.6]", "[-4.5,-4.1]", "[-4.0,-3.6]", "[-3.5,-3.1]", "[-3.0,-2.6]", "[-2.5,-2.1]", "[-2.0,-1.6]",
    "[-1.5,-1.1]", "[4.0,4.4]", "[4.5,4.9]", "[5.0,+inf[",
]
_BINSORDER = [
    "]-inf,-15.0]", "[-15.0,-13.1]", "[-13.0,-11.1]", "[-11.0,-9.1]", "[-9.0,-7.1]", "[-7.0,-5.1]",
    "[-5.0,-3.1]", "[-3.0,-1.1]", "]-inf,-6.0]", "[-6.0,-5.6]", "[-5.5,-5.1]", "[-5.0,-4.6]", "[-4.5,-4.1]",
    "[-4.0,-3.6]", "[-3.5,-3.1]", "[-3.0,-2.6]", "[-2.5,-2.1]", "[-2.0,-1.6]", "[-1.5,-1.1]", "]-inf,-1.0]",
    "[-1.0,-0.6]", "[-0.5,-0.1]", "]-inf,0.0]", "[0.0,0.4]", "[0.5,0.9]", "[1.0,1.4]", "[1.5,1.9]", "[2.0,2.4]",
    "[2.5,2.9]", "[3.0,3.4]", "[3.5,3.9]", "[4.0,+inf[", "[4.0,4.4]", "[4.5,4.9]", "[5.0,+inf[", "[4.0,5.9]",
    "[6.0,7.9]", "[8.0,9.9]", "[10.0,+inf[",
]
_LEFT_G1 = {"[4.0,5.9]", "[6.0,7.9]", "[8.0,9.9]", "[10.0,+inf["}
_BINS_G1 = ["]-inf,0.0]", "[0.0,0.4]", "[0.5,0.9]", "[1.0,1.4]", "[1.5,1.9]", "[2.0,2.4]", "[2.5,2.9]",
            "[3.0,3.4]", "[3.5,3.9]", "[4.0,5.9]", "[6.0,7.9]", "[8.0,9.9]", "[10.0,+inf["]
_LEFT_G2 = {"]-inf,-15.0]", "[-15.0,-13.1]", "[-13.0,-11.1]", "[-11.0,-9.1]", "[-9.0,-7.1]", "[-7.0,-5.1]",
            "[-5.0,-3.1]", "[-3.0,-1.1]"}
_BINS_G2 = ["]-inf,-15.0]", "[-15.0,-13.1]", "[-13.0,-11.1]", "[-11.0,-9.1]", "[-9.0,-7.1]", "[-7.0,-5.1]",
            "[-5.0,-3.1]", "[-3.0,-1.1]", "[1.5,1.9]", "[2.0,2.4]", "[2.5,2.9]", "[3.0,3.4]", "[3.5,3.9]",
            "[4.0,5.9]", "[6.0,7.9]", "[8.0,9.9]", "[10.0,+inf["]
_LEFT_G3 = {"]-inf,-1.0]", "[-0.5,-0.1]", "[-1.0,-0.6]"}
_BINS_G3 = ["]-inf,-1.0]", "[-1.0,-0.6]", "[-0.5,-0.1]", "[0.0,0.4]", "[0.5,0.9]", "[1.0,1.4]", "[1.5,1.9]",
            "[2.0,2.4]", "[2.5,2.9]", "[3.0,3.4]", "[3.5,3.9]", "[4.0,+inf["]
_LEFT_G4 = {"]-inf,-6.0]", "[-6.0,-5.6]", "[-5.5,-5.1]", "[-5.0,-4.6]", "[-4.5,-4.1]", "[-4.0,-3.6]",
            "[-3.5,-3.1]", "[-3.0,-2.6]", "[-2.5,-2.1]", "[-2.0,-1.6]", "[-1.5,-1.1]"}
_BINS_G4 = ["]-inf,-6.0]", "[-6.0,-5.6]", "[-5.5,-5.1]", "[-5.0,-4.6]", "[-4.5,-4.1]", "[-4.0,-3.6]",
            "[-3.5,-3.1]", "[-3.0,-2.6]", "[-2.5,-2.1]", "[-2.0,-1.6]", "[-1.5,-1.1]", "[-1.0,-0.6]",
            "[-0.5,-0.1]", "[0.0,0.4]", "[0.5,0.9]", "[1.0,1.4]", "[1.5,1.9]", "[2.0,2.4]", "[2.5,2.9]",
            "[3.0,3.4]", "[3.5,3.9]", "[4.0,+inf["]
_LEFT_G5 = {"]-inf,0.0]", "[1.5,1.9]", "[1.0,1.4]", "[0.5,0.9]", "[0.0,0.4]", "[2.0,2.4]", "[2.5,2.9]",
            "[3.0,3.4]", "[4.0,5.9]", "[3.5,3.9]"}
_BINS_G5_BASE = ["]-inf,0.0]", "[0.0,0.4]", "[0.5,0.9]", "[1.0,1.4]", "[1.5,1.9]", "[2.0,2.4]", "[2.5,2.9]",
                 "[3.0,3.4]", "[3.5,3.9]"]
_TAIL_A = ["[4.0,4.4]", "[4.5,4.9]", "[5.0,+inf["]
_TAIL_B = ["[4.0,5.9]", "[6.0,7.9]", "[8.0,9.9]", "[10.0,+inf["]
_TAIL_ELSE = ["[4.0,+inf["]


def _edge_map(gmin: float, gmax: float) -> dict[str, tuple[float, float]]:
    edges = [
        (min(0, gmin), 0), (min(-1, gmin), -1), (-1, -0.5), (-0.5, 0), (0, 0.5), (0.5, 1), (1, 1.5),
        (1.5, 2), (2, 2.5), (2.5, 3), (3, 3.5), (3.5, 4), (4.0, 6), (6, 8), (8, 10), (10, gmax), (10, gmax),
        (min(-15, gmin), -15), (-15, -13), (-13, -11), (-11, -9), (-9, -7), (-7, -5), (-5, -3), (-3, -1),
        (min(-6, gmin), -6), (-6, -5.5), (-5.5, -5), (-5, -4.5), (-4.5, -4), (-4, -3.5), (-3.5, -3), (-3, -2.5),
        (-2.5, -2), (-2, -1.5), (-1.5, -1), (4, 4.5), (4.5, 5), (5, gmax),
    ]
    return dict(zip(_BINS, edges, strict=True))


def _choose_bins(left, right, available) -> list[str]:
    if pd.isna(left):
        return []
    if left in _LEFT_G1:
        case = _BINS_G1
    elif left in _LEFT_G2:
        case = _BINS_G2
    elif left in _LEFT_G3:
        case = _BINS_G3
    elif left in _LEFT_G4:
        case = _BINS_G4
    elif left in _LEFT_G5:
        if isinstance(right, str) and right in set(_TAIL_A):
            tail = _TAIL_A
        elif isinstance(right, str) and right in set(_TAIL_B):
            tail = _TAIL_B
        else:
            tail = _TAIL_ELSE
        case = _BINS_G5_BASE + tail
    else:
        return []
    return [b for b in case if b in available]


def growth_densities(flat: pd.DataFrame, gmin: float = GDP_YOY_MIN, gmax: float = GDP_YOY_MAX) -> pd.DataFrame:
    """Mean and variance of every growth density, the grid resolved from its filled bins.

    ``Date`` is shifted back eight months to the first month of the survey
    quarter, as the authoritative builder does. Returns ``Date``,
    ``FCT_SOURCE``, ``POINT``, ``Mean``, ``Variance``.
    """
    df = flat.copy()
    df["Date"] = (pd.to_datetime(df["Date"]) - pd.DateOffset(months=8)).dt.strftime("%Y-%m-%d")
    df.sort_values(by=["Date", "FCT_SOURCE"], inplace=True)
    df = df.loc[:, ["Date", "FCT_SOURCE", "POINT"] + _BINS]
    df[_BINS] = df[_BINS].div(df[_BINS].sum(axis=1), axis=0) * 100
    df.dropna(how="all", inplace=True, axis=1)
    df.dropna(subset=[b for b in _BINS if b in df.columns], how="all", inplace=True, axis=0)
    df.reset_index(inplace=True, drop=True)
    present = [c for c in _BINSORDER if c in df.columns]
    df = df[["Date", "FCT_SOURCE", "POINT"] + present]
    df[present] = df[present].apply(pd.to_numeric, errors="coerce")
    df[present] = df[present].replace(0, np.nan)
    df["left"] = df[present].apply(lambda row: row.first_valid_index(), axis=1)
    df["right"] = df[present].apply(lambda row: row.last_valid_index(), axis=1)
    edge_map = _edge_map(gmin, gmax)
    means, variances = [], []
    for _, row in df.iterrows():
        case = _choose_bins(row["left"], row["right"], present)
        if not case:
            means.append(np.nan)
            variances.append(np.nan)
            continue
        edges = [edge_map[b] for b in case]
        probs = pd.to_numeric(row[case], errors="coerce").to_numpy(dtype=float)
        probs[np.isnan(probs)] = 0
        probs[np.isposinf(probs) | np.isneginf(probs)] = 0
        mid = [(lo + hi) / 2 for (lo, hi) in edges]
        total = np.sum(probs)
        if total > 0:
            mean = np.dot(mid, probs) / total
            var = np.dot([(m - mean) ** 2 for m in mid], probs) / total
        else:
            mean, var = 0.0, np.nan
        means.append(mean)
        variances.append(var)
    df["Mean"] = means
    df["Variance"] = variances
    out = df[["Date", "FCT_SOURCE", "POINT", "Mean", "Variance"]].copy()
    out["Date"] = pd.to_datetime(out["Date"])
    return out


def ngu_panel(densities: pd.DataFrame, g_potential: pd.Series) -> pd.DataFrame:
    """Add potential growth (by survey quarter, carried forward) and ``NGU`` to the growth densities."""
    df = densities.copy()
    df["Qstart"] = pd.to_datetime(df["Date"]).dt.to_period("Q").dt.to_timestamp()
    pot = g_potential.rename("g_potential").to_frame().rename_axis("Qstart").reset_index()
    pot["Qstart"] = pd.to_datetime(pot["Qstart"]).dt.to_period("Q").dt.to_timestamp()
    df = df.merge(pot, on="Qstart", how="left")
    df["g_potential"] = df["g_potential"].ffill()
    df["NGU"] = _ngu(np.sqrt(df["Variance"]), df["Mean"], df["g_potential"])
    return df.drop(columns="Qstart")


def ngu_series(panel: pd.DataFrame) -> pd.DataFrame:
    """Round mean and interquartile range of the individual NGU, by survey quarter start (``Date``)."""
    piv = panel.pivot_table(index="Date", columns="FCT_SOURCE", values="NGU", aggfunc="mean")
    out = pd.DataFrame({"NGU_avg": piv.mean(axis=1), "NGU_Q1": piv.quantile(0.25, axis=1),
                        "NGU_Q3": piv.quantile(0.75, axis=1)})
    out.index = pd.to_datetime(out.index)
    raw = panel.pivot_table(index="Date", columns="FCT_SOURCE", values="Variance", aggfunc="mean")
    out["raw_sd_avg"] = np.sqrt(raw).mean(axis=1)
    return out


_ = re  # kept for symmetry with io_ecb_spf (round-file regex is imported from there)
