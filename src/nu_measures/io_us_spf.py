"""Reader for the Philadelphia Fed Survey of Professional Forecasters microdata.

One workbook, ``SPFmicrodata.xlsx``, one sheet per density question. The
questions used are the GDP price index (``PRPGDP``, from 1968, grid halved at
2014Q1) and the two core inflation questions (``PRCPCE`` and ``PRCCPI``, from
2007Q1, grid unchanged since), which carry the comparison across the FOMC's
announcement of a numerical target on 25 January 2012.

The bin tables were checked against the Philadelphia Fed's documentation
(Table 6 of the SPF documentation, read on 28 July 2026). Columns 1-10 are the
current year and 11-20 the next year, each block summing to 100 on its own;
the one-year-ahead object is the next-year block. **Column 1 is the highest
bin and the columns descend.** One-decimal reporting makes "3.5 to 3.9" the
interval [3.5, 4.0), midpoint 3.75; each open tail takes one bin width.

References: Vansteenberghe (2026), *Uncertain and Asymmetric
Forecasts*, Section 6; Vansteenberghe (2026), *Tolerable Inflation,
Intolerable Uncertainty*, Section 3 and Table 1.
"""

from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from . import conventions as cv

__all__ = ["MIDPOINTS", "BIN_WIDTHS", "EDGES_CORE", "read_sheet", "densities", "quartiles", "panel", "round_aggregates"]

#: Bin midpoints of the next-year block, highest bin first, by question and grid.
MIDPOINTS: dict[str, np.ndarray] = {
    "core": np.array([4.5, 3.75, 3.25, 2.75, 2.25, 1.75, 1.25, 0.75, 0.25, -0.25]),
    "prpgdp_pre2014": np.array([8.5, 7.5, 6.5, 5.5, 4.5, 3.5, 2.5, 1.5, 0.5, -0.5]),
    "prpgdp_post2014": np.array([4.5, 3.75, 3.25, 2.75, 2.25, 1.75, 1.25, 0.75, 0.25, -0.25]),
}

#: Closed intervals of the core questions' grid, ascending (the open tails one bin wide).
EDGES_CORE: tuple[tuple[float, float], ...] = tuple((x, x + 0.5) for x in np.arange(-0.5, 4.5, 0.5))

#: Interior bin widths, in percentage points.
BIN_WIDTHS: dict[str, float] = {"core": 0.5, "prpgdp_pre2014": 1.0, "prpgdp_post2014": 0.5}

_GRID_CHANGE_YEAR = int(cv.US_PRPGDP_GRID_CHANGE[:4])


def _stub_properties() -> None:
    """The workbook's document properties make ``openpyxl`` raise; skip them."""
    import openpyxl.reader.excel as _xr

    _xr.ExcelReader.read_properties = lambda self: None


def read_sheet(path: str | Path, sheet: str) -> pd.DataFrame:
    """A density sheet of the workbook, rounds with a year and a quarter only."""
    _stub_properties()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        d = pd.read_excel(path, sheet_name=sheet, engine="openpyxl")
    d = d.dropna(subset=["YEAR", "QUARTER"]).copy()
    d["YEAR"] = d["YEAR"].astype(int)
    d["QUARTER"] = d["QUARTER"].astype(int)
    return d


def _grid_for(sheet: str, years: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    if sheet.upper() == "PRPGDP":
        post = years >= _GRID_CHANGE_YEAR
        mid = np.where(post[:, None], MIDPOINTS["prpgdp_post2014"][None, :], MIDPOINTS["prpgdp_pre2014"][None, :])
        width = np.where(post, BIN_WIDTHS["prpgdp_post2014"], BIN_WIDTHS["prpgdp_pre2014"])
    else:
        mid = np.tile(MIDPOINTS["core"], (len(years), 1))
        width = np.full(len(years), BIN_WIDTHS["core"])
    return mid, width


def densities(
    path: str | Path,
    sheet: str,
    block: str = "next",
    total_bounds: tuple[float, float] = (95.0, 105.0),
    min_bins: int = 3,
) -> pd.DataFrame:
    """Every valid density of ``sheet``: mean, variance, filled bins, grid, and the date.

    A response is valid when its probabilities sum inside ``total_bounds`` and
    at least ``min_bins`` bins are filled; probabilities are then renormalised
    to one. ``block`` selects the next-year (one-year-ahead) or current-year
    columns. Moments use point masses at the midpoints; ``Variance_sheppard``
    subtracts ``h**2 / 12`` for the grid's width, and ``grid`` names the
    regime. ``Date`` is the first month of the survey quarter.
    """
    d = read_sheet(path, sheet)
    idx = range(11, 21) if block == "next" else range(1, 11)
    cols = [f"{sheet}{i}" for i in idx]
    for c in cols:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    P = d[cols].to_numpy(dtype=float)
    tot = np.nansum(P, axis=1)
    lo, hi = total_bounds
    ok = (tot > lo) & (tot < hi) & (np.isfinite(P).sum(axis=1) >= min_bins)
    d, P, tot = d[ok].copy(), P[ok], tot[ok]
    Pn = np.nan_to_num(P) / tot[:, None]
    mid, width = _grid_for(sheet, d["YEAR"].to_numpy())
    mean = (Pn * mid).sum(axis=1)
    var = (Pn * (mid - mean[:, None]) ** 2).sum(axis=1)
    out = pd.DataFrame(
        {
            "YEAR": d["YEAR"].to_numpy(),
            "QUARTER": d["QUARTER"].to_numpy(),
            "ID": d["ID"].to_numpy(),
            "Mean": mean,
            "Variance": var,
            "Variance_sheppard": np.maximum(var - width**2 / 12.0, 1e-6),
            "bins_filled": (Pn > 0).sum(axis=1),
            "grid": np.where(width == 1.0, "pre2014", "post2014") if sheet.upper() == "PRPGDP" else "core",
        }
    )
    out["Date"] = pd.to_datetime(dict(year=out["YEAR"], month=out["QUARTER"] * 3 - 2, day=1))
    return out.sort_values(["Date", "ID"]).reset_index(drop=True)


def panel(path: str | Path, target: float = cv.TARGET) -> pd.DataFrame:
    """The one-year-ahead GDP price index panel, as the papers' archived file lays it out.

    Validity bounds (50, 150) on the probability total, rounds from 1992 on,
    the archived column names (``Mean_1Y``, ``Variance_1Y``,
    ``Variance_1Y_sheppard``) and ``d_t = Mean_1Y - target``. The rebuild
    reproduces the archived panel to 1.8e-15 on the overlap.
    """
    d = densities(path, "PRPGDP", block="next", total_bounds=(50.0, 150.0))
    d = d.rename(columns={"Mean": "Mean_1Y", "Variance": "Variance_1Y", "Variance_sheppard": "Variance_1Y_sheppard"})
    d["d_t"] = d["Mean_1Y"] - target
    d = d[d["YEAR"] >= 1992].sort_values(["Date", "ID"]).reset_index(drop=True)
    return d[["YEAR", "QUARTER", "ID", "Mean_1Y", "Variance_1Y", "Variance_1Y_sheppard", "bins_filled", "grid", "Date", "d_t"]]


def round_aggregates(dens: pd.DataFrame, lo: float = -1.0, hi: float = 6.0, target: float = cv.TARGET) -> pd.DataFrame:
    """Round series of a density question: ``W``, ``D``, ``T``, ``mu`` and ``gap``, consensus inside ``[lo, hi]``."""
    gb = dens.groupby("Date")
    A = pd.concat([gb["Variance"].mean(), gb["Mean"].var(ddof=0), gb["Mean"].mean(), gb["Mean"].size()], axis=1)
    A.columns = ["W", "D", "mu", "n"]
    A = A.dropna()
    A["T"] = A["W"] + A["D"]
    A["gap"] = A["mu"] - target
    return A[(A["mu"] >= lo) & (A["mu"] <= hi)].sort_index()


def quartiles(path: str | Path, sheet: str, block: str = "next", total_bounds: tuple[float, float] = (95.0, 105.0),
              min_bins: int = 3) -> pd.DataFrame:
    """Quartiles and Bowley skewness of every valid density of a core question, interpolated inside the bin.

    The columns descend (column 1 is the highest bin), so they are reversed onto
    the ascending grid :data:`EDGES_CORE` before the cumulative probability is
    read. Returns the columns of :func:`densities` plus ``Q1``, ``Q2``, ``Q3``
    and ``Bowley``.
    """
    from .moments import bowley_skewness, quantile

    if sheet.upper() == "PRPGDP":
        raise ValueError("quartiles are implemented for the grid-stable core questions")
    d = read_sheet(path, sheet)
    idx = range(11, 21) if block == "next" else range(1, 11)
    cols = [f"{sheet}{i}" for i in idx]
    for c in cols:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    P = d[cols].to_numpy(dtype=float)
    tot = np.nansum(P, axis=1)
    lo, hi = total_bounds
    ok = (tot > lo) & (tot < hi) & (np.isfinite(P).sum(axis=1) >= min_bins)
    d, P = d[ok].copy(), np.nan_to_num(P[ok])
    Pn = P / P.sum(axis=1, keepdims=True)
    edges = np.array([EDGES_CORE[0][0]] + [e[1] for e in EDGES_CORE])
    asc = Pn[:, ::-1]
    q1 = np.array([quantile(row, edges, 0.25) for row in asc])
    q2 = np.array([quantile(row, edges, 0.50) for row in asc])
    q3 = np.array([quantile(row, edges, 0.75) for row in asc])
    bow = np.array([bowley_skewness(row, edges) for row in asc])
    out = densities(path, sheet, block=block, total_bounds=total_bounds, min_bins=min_bins)
    out = out.sort_values(["Date", "ID"]).reset_index(drop=True)
    key = d.assign(Date=pd.to_datetime(dict(year=d["YEAR"], month=d["QUARTER"] * 3 - 2, day=1)))[["Date", "ID"]]
    key = key.assign(Q1=q1, Q2=q2, Q3=q3, Bowley=bow).sort_values(["Date", "ID"]).reset_index(drop=True)
    return out.merge(key, on=["Date", "ID"], how="left")
