"""Reader for the ECB Data Portal (SDMX API): the macroeconomic series the exhibits merge with.

Every series is fetched by its key, and **a key's first segment is its
dataflow**: pairing a ``STBS…`` key with the ``STS`` flow returns HTTP 400,
and a fetcher that then falls back quietly reports success on a discontinued
series. The reader here derives the flow from the key, tries an ordered list
of candidate keys, and prints the coverage it obtained, so that the next
migration announces itself instead of ending a series in silence. Two have
already happened: ``ICP`` froze at December 2025 (the live series is in the
``HICP`` dataflow, item code ``4`` renamed ``4D0``), and ``STS`` was
discontinued (industrial production lives in ``STBS``, on a fixed euro-area
composition -- a definitional change, not a vintage refresh).

Nothing is cached in the repository: :func:`macro_block` writes the two CSV
files it builds under ``NU_DATA_DIR/ecb/`` and the exhibits read those.

Reference: Vansteenberghe (2026), *Tolerable Inflation, Intolerable
Uncertainty*, Section 3 (the activity responses) and Appendix (the level
regressions); the HICP series enters both papers' panels.
"""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pandas as pd

__all__ = ["ECB_API", "SERIES", "fetch", "probe", "macro_block", "hicp_yoy", "hicp_index", "real_gdp"]

ECB_API = "https://data-api.ecb.europa.eu/service/data"

#: The series of the macro block, each with its candidate keys in order of
#: preference: the live key first, the discontinued one after it.
SERIES: dict[str, tuple[str, ...]] = {
    "logS": ("FM.M.U2.EUR.DS.EI.DJES50I.HSTA",),  # EURO STOXX 50, monthly average of daily closes
    "DFR": ("FM.D.U2.EUR.4F.KR.DFR.LEV",),  # deposit facility rate, daily, read end-of-month
    "logIP": ("STBS.M.I10.Y.PROD.NS0020.4D0.N.IX", "STS.M.I9.Y.PROD.NS0020.4.000"),
    "UNRATE": ("LFSI.M.I9.S.UNEHRT.TOTAL0.15_74.T",),
    "HICP_YOY": ("HICP.M.U2.N.000000.4D0.ANR", "ICP.M.U2.N.000000.4.ANR"),
}

#: Monthly HICP index (2015 = 100), the input of the tail closures of the ECB-SPF panel.
HICP_INDEX_KEYS: tuple[str, ...] = ("HICP.M.U2.N.000000.4D0.INX", "ICP.M.U2.N.000000.4.INX")

#: Real GDP, chain-linked volumes, the input of the Hodrick-Prescott trend behind potential growth.
REAL_GDP_KEYS: tuple[str, ...] = ("MNA.Q.Y.I9.W2.S1.S1.B.B1GQ._Z._Z._Z.EUR.LR.N",)


def fetch(series_key: str, start: str = "1999-01", timeout: int = 60) -> pd.Series:
    """One ECB series as a float series indexed by period start; the dataflow is the key's first segment."""
    import requests

    flow, _, rest = series_key.partition(".")
    url = f"{ECB_API}/{flow}/{rest}"
    r = requests.get(url, params={"format": "csvdata", "startPeriod": start}, timeout=timeout)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text))
    df["TIME_PERIOD"] = pd.to_datetime(df["TIME_PERIOD"])
    return df.set_index("TIME_PERIOD")["OBS_VALUE"].astype(float).sort_index()


def probe(label: str, candidates, start: str = "1999-01", verbose: bool = True) -> tuple[str, pd.Series]:
    """Try each candidate key in order; report every one's coverage; return the first that works."""
    chosen = None
    if verbose:
        print(f"[{label}]")
    for key in candidates:
        try:
            s = fetch(key, start)
            mark = "  <= using" if chosen is None else ""
            if chosen is None:
                chosen = (key, s)
            if verbose:
                print(f"    {key:<42} {len(s):>5} obs   {s.index.min():%Y-%m} to {s.index.max():%Y-%m}{mark}")
        except Exception as exc:  # noqa: BLE001 - the point is to report every failure
            if verbose:
                print(f"    {key:<42} failed: {str(exc).split(' for url')[0]}")
    if chosen is None:
        raise RuntimeError(f"no candidate key worked for {label}")
    return chosen


def _to_month_start(s: pd.Series) -> pd.Series:
    out = s.copy()
    out.index = out.index.to_period("M").to_timestamp(how="start")
    return out


def macro_block(out_dir: str | Path | None = None, start: str = "1999-01", verbose: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The five-series monthly block: ``logS``, ``DFR``, ``UNRATE``, ``logIP``, ``HICP_YOY``.

    Returns the balanced panel (months where all five are present) and the
    unbalanced one (the union, ragged edge kept). With ``out_dir`` both are
    written as ``macro_block.csv`` and ``macro_block_unbalanced.csv``.
    """
    got = {}
    for name, keys in SERIES.items():
        s0 = "1999-01-01" if name == "DFR" else start
        _, s = probe(name, keys, start=s0, verbose=verbose)
        got[name] = s
    logS = _to_month_start(np.log(got["logS"]).rename("logS"))
    dfr = _to_month_start(got["DFR"].resample("ME").last().rename("DFR"))
    logIP = _to_month_start(np.log(got["logIP"]).rename("logIP"))
    unrate = _to_month_start(got["UNRATE"].rename("UNRATE"))
    hicp = _to_month_start(got["HICP_YOY"].rename("HICP_YOY"))
    full = pd.concat([logS, dfr, unrate, logIP, hicp], axis=1)
    bal = full.dropna()
    if verbose:
        for c in full.columns:
            col = full[c].dropna()
            print(f"    {c:<10} {col.index.min():%Y-%m} to {col.index.max():%Y-%m}   ({len(col)} obs)")
        print(f"    balanced: {bal.index.min():%Y-%m} to {bal.index.max():%Y-%m}, {len(bal)} rows")
    if out_dir is not None:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        bal.to_csv(out / "macro_block.csv", index_label="TIME_PERIOD")
        full.to_csv(out / "macro_block_unbalanced.csv", index_label="TIME_PERIOD")
    return bal, full


def hicp_yoy(start: str = "1997-01", verbose: bool = False) -> pd.Series:
    """Realized euro-area HICP inflation, year on year, monthly (per cent)."""
    _, s = probe("HICP year on year", SERIES["HICP_YOY"], start=start, verbose=verbose)
    return _to_month_start(s.rename("HICP_YOY"))


def hicp_index(start: str = "1997-01", verbose: bool = False) -> pd.Series:
    """The monthly HICP index, from which the panel's tail closures are computed."""
    _, s = probe("HICP index", HICP_INDEX_KEYS, start=start, verbose=verbose)
    return _to_month_start(s.rename("HICP_INDEX"))


def real_gdp(start: str = "1995-01", verbose: bool = False) -> pd.Series:
    """Euro-area real GDP, quarterly, chain-linked volumes."""
    _, s = probe("real GDP", REAL_GDP_KEYS, start=start, verbose=verbose)
    return s.rename("GDP")
