"""Readers for the smaller public sources: FRED, the EPU workbook, and the files they yield.

References: Vansteenberghe (2026), *Tolerable Inflation, Intolerable
Uncertainty*, Figures 2 and 5; Vansteenberghe (forthcoming), *Uncertain and
Asymmetric Forecasts*, Figures 5 and 10.
"""

from __future__ import annotations

import warnings
from pathlib import Path

import pandas as pd

from . import conventions as cv

__all__ = ["fred_csv", "fred_fetch", "monthly_yoy", "epu_countries", "epu_basket"]


def fred_csv(path: str | Path, series: str | None = None) -> pd.Series:
    """A FRED download (``observation_date`` or ``DATE`` and the series column) as a daily series."""
    df = pd.read_csv(path)
    date_col = "observation_date" if "observation_date" in df.columns else df.columns[0]
    value_col = series if series and series in df.columns else [c for c in df.columns if c != date_col][0]
    s = pd.Series(pd.to_numeric(df[value_col], errors="coerce").to_numpy(), index=pd.to_datetime(df[date_col]), name=value_col)
    return s.dropna().sort_index()


def monthly_yoy(series: pd.Series) -> pd.Series:
    """Year-on-year change of a monthly series, in per cent, lagged by calendar month.

    The series is first placed on a complete month-start calendar, so a month
    missing from the file (FRED publishes a blank when a release is skipped)
    yields a missing value for itself and for the month a year later, instead
    of silently shifting the lag by one observation.
    """
    s = pd.Series(series.to_numpy(dtype=float), index=pd.DatetimeIndex(series.index).to_period("M").to_timestamp())
    s = s[~s.index.duplicated()].sort_index().asfreq("MS")
    return (100.0 * (s - s.shift(12)) / s.shift(12)).rename(series.name)


def fred_fetch(series: str = "T5YIE", timeout: int = 60) -> pd.Series:
    """Fetch a FRED series through its CSV endpoint (no key needed)."""
    import io

    import requests

    r = requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv", params={"id": series}, timeout=timeout)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text))
    s = pd.Series(pd.to_numeric(df[series], errors="coerce").to_numpy(), index=pd.to_datetime(df.iloc[:, 0]), name=series)
    return s.dropna().sort_index()


def epu_countries(path: str | Path, sheet: str = "EPU") -> list[str]:
    """The country columns present in the workbook -- check them after every download."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        epu = pd.read_excel(path, sheet_name=sheet, nrows=5)
    return [c for c in epu.columns if c not in ("Year", "Month")]


def epu_basket(path: str | Path, basket=cv.EPU_BASKET, sheet: str = "EPU", strict: bool = True) -> pd.Series:
    """The euro-area Economic Policy Uncertainty basket, quarterly.

    Monthly country indices are averaged to quarters country by country, then
    across the countries of ``basket``. With ``strict`` every basket country
    must be present in the workbook (the 2026 vintage dropped Sweden, which is
    why the basket is fixed and checked rather than read off the file).
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        epu = pd.read_excel(path, sheet_name=sheet)
    have = [c for c in basket if c in epu.columns]
    missing = [c for c in basket if c not in epu.columns]
    if strict and missing:
        raise ValueError(f"EPU workbook lacks basket countries {missing}; columns: {list(epu.columns)}")
    epu = epu.dropna(subset=["Year", "Month"]).copy()
    epu["Year"] = epu["Year"].astype(int)
    epu["Month"] = epu["Month"].astype(int)
    epu["date"] = pd.to_datetime(dict(year=epu["Year"], month=epu["Month"], day=1))
    epu["Q"] = epu["date"].dt.to_period("Q")
    out = epu.groupby("Q")[have].mean().mean(axis=1).rename("EPU")
    out.attrs["countries"] = have
    out.attrs["span"] = (str(epu["date"].min().date()), str(epu["date"].max().date()))
    return out
