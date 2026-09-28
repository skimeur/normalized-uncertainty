"""Readers for the ECB Survey of Professional Forecasters: from the round files to the panels.

The ECB publishes one CSV file per quarterly round, each holding every
respondent's point forecast and probability distribution for several variables
and horizons. This module turns those files into the two panels the papers
run on, with the conventions of the authoritative builder reproduced line for
line -- the rebuilt individual panel is byte-identical to the certified one on
every moment (``tests/test_certified_panel.py``).

Reference: Vansteenberghe, E. (2026), *Uncertain and Asymmetric
Forecasts*, working paper (``vansteenberghe2026uncertain``), Section 2, which
documents the four conventions implemented here: renormalization within the
grid regime, tails closed on the realized range of inflation, bin midpoints for
the moments, linear interpolation for the quartiles.

Pipeline
--------
``read_rounds(directory)``      one-year-ahead inflation block of every round
``flat_panel(rounds)``          one row per forecaster and round, probabilities in per cent
``individual_panel(flat)``      moments, quartiles, Bowley skewness, the unit
                                symmetric NIU, the individual AC (``ACI``)

Dates
-----
A round file ``YYYYQn.csv`` is named by the quarter in which the round was
fielded. Its one-year-ahead inflation forecast targets December of that year
(Q1), March (Q2), June (Q3) or September (Q4) of the next year. The flat panel
carries that **target period** as ``Date``; the individual panel shifts it back
one year to the **formation time**, so that its ``Date`` is the first month of
the quarter preceding the round -- the 2022Q4 round has ``Date`` 2022-09-01 --
and the survey quarter is ``Date`` plus one month.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from . import conventions as cv

__all__ = [
    "ROUND_FILE",
    "target_period",
    "read_round",
    "read_rounds",
    "longer_term_points",
    "longer_term_panel",
    "flat_panel",
    "individual_panel",
    "averaged_density",
    "build_panels",
    "hicp_extremes",
    "hicp_yoy_from_index",
    "INDIVIDUAL_PANEL_COLUMNS",
]

#: File name of a round: the survey quarter, e.g. ``2022Q4.csv``.
ROUND_FILE = re.compile(r"^(\d{4})Q([1-4])\.csv$")

#: Column order of the individual panel, as the authoritative file lays it out.
INDIVIDUAL_PANEL_COLUMNS: tuple[str, ...] = (
    "Date", "FCT_SOURCE", "POINT",
    "Mean_spd", "Variance_spd", "sigma_spd",
    "Q2_median_spd", "Bowley_Skewness",
    "NIU", "ACI", "coherence",
    "bins_filled", "entropy_norm", "I_informativeness",
    "sigma_resid",
)

_MONTH = {1: (0, "Dec", 12), 2: (1, "Mar", 3), 3: (1, "Jun", 6), 4: (1, "Sep", 9)}


def target_period(year: int, quarter: int) -> tuple[str, pd.Timestamp]:
    """The one-year-ahead target period of a round, as label and date.

    Forecasters answering in the first quarter know December's realized
    inflation and are asked about the next December; in the second quarter,
    March's and the following March; and so on.
    """
    if quarter not in _MONTH:
        raise ValueError("quarter must be 1, 2, 3 or 4")
    add, name, month = _MONTH[quarter]
    return f"{year + add}{name}", pd.Timestamp(year=year + add, month=month, day=1)


def read_round(path: str | Path) -> pd.DataFrame:
    """The one-year-ahead HICP inflation block of one round file.

    The file starts with the inflation block; the first row with no value at
    all separates it from the next variable. Everything but ``TARGET_PERIOD``
    is read as a number, and only the rows of the one-year-ahead target period
    are kept. Adds ``Year``, ``Q`` and ``Date`` (the target period).
    """
    path = Path(path)
    m = ROUND_FILE.match(path.name)
    if not m:
        raise ValueError(f"{path.name} is not named like a round file (YYYYQn.csv)")
    year, quarter = int(m.group(1)), int(m.group(2))
    df = pd.read_csv(path, header=1)
    empty = df[df.isnull().all(axis=1)].index
    if len(empty):
        df = df.iloc[: int(empty[0]), :]
    df = df.copy()
    for col in df.columns:
        if col != "TARGET_PERIOD":
            df[col] = pd.to_numeric(df[col], errors="coerce")
    label, date = target_period(year, quarter)
    df = df.loc[df["TARGET_PERIOD"] == label, :].copy()
    df["Year"] = year
    df["Q"] = quarter
    df["Date"] = date
    return df


def longer_term_points(path: str | Path, keep_missing: bool = False) -> pd.DataFrame:
    """The longer-term HICP point forecasts of one round file.

    The inflation block of a round file lists, after the rolling horizons,
    calendar-year targets; the longer-term forecast (four to five years
    ahead) is the bare-year target with the largest year in that block, which
    ends where the next variable's header (``... EXPECTATIONS ...``) starts.
    Returns ``FCT_SOURCE`` and ``POINT`` for every respondent who reported a
    point, with ``Year`` and ``Q`` of the survey round; with ``keep_missing``
    the respondents present in the block without a point (a density only)
    are kept, their ``POINT`` missing.
    """
    path = Path(path)
    m = ROUND_FILE.match(path.name)
    if not m:
        raise ValueError(f"{path.name} is not named like a round file (YYYYQn.csv)")
    raw = pd.read_csv(path, header=1, dtype=str)
    raw.columns = [c.strip() for c in raw.columns]
    tp = raw["TARGET_PERIOD"].fillna("").astype(str).str.strip()
    brk = raw.index[tp.str.contains("EXPECTATIONS", na=False)]
    if len(brk):
        raw, tp = raw.iloc[: brk[0]], tp.iloc[: brk[0]]
    years = sorted({int(t) for t in tp if re.fullmatch(r"\d{4}", t)})
    if not years:
        return pd.DataFrame(columns=["FCT_SOURCE", "POINT", "Year", "Q"])
    sec = raw[tp == str(years[-1])]
    out = pd.DataFrame({"FCT_SOURCE": pd.to_numeric(sec["FCT_SOURCE"], errors="coerce"),
                        "POINT": pd.to_numeric(sec["POINT"], errors="coerce")})
    out = out.dropna(subset=["FCT_SOURCE"]) if keep_missing else out.dropna()
    out["FCT_SOURCE"] = out["FCT_SOURCE"].astype(int)
    out["Year"], out["Q"] = int(m.group(1)), int(m.group(2))
    return out.reset_index(drop=True)


def round_files(directory: str | Path, through: str | None = None) -> list[Path]:
    """The round files ``YYYYQn.csv`` of ``directory`` in chronological order.

    ``through`` -- a round label such as ``"2026Q3"`` -- drops the files of later
    rounds; ``None`` keeps them all.
    """
    directory = Path(directory)
    files = sorted(p for p in directory.iterdir() if ROUND_FILE.match(p.name))
    if through is not None:
        last = pd.Period(through, freq="Q")
        files = [p for p in files if pd.Period(p.stem, freq="Q") <= last]
    return files


def longer_term_panel(directory: str | Path, keep_missing: bool = False, through: str | None = None) -> pd.DataFrame:
    """The longer-term points of every round file of ``directory`` (up to ``through``), with the survey quarter ``round``."""
    directory = Path(directory)
    files = round_files(directory, through)
    if not files:
        raise FileNotFoundError(f"no round files (YYYYQn.csv) in {directory}")
    lt = pd.concat([longer_term_points(p, keep_missing=keep_missing) for p in files], ignore_index=True)
    lt["round"] = pd.PeriodIndex(lt["Year"].astype(str) + "Q" + lt["Q"].astype(str), freq="Q")
    return lt


def read_rounds(directory: str | Path, through: str | None = None) -> pd.DataFrame:
    """Every round file of ``directory`` (up to the round ``through``), in chronological order, concatenated."""
    directory = Path(directory)
    files = round_files(directory, through)
    if not files:
        raise FileNotFoundError(f"no round files (YYYYQn.csv) in {directory}")
    return pd.concat([read_round(p) for p in files], ignore_index=True)


def flat_panel(rounds: pd.DataFrame) -> pd.DataFrame:
    """One row per forecaster and round, probabilities in per cent, ECB bins relabelled.

    Columns entirely missing and rows entirely missing are dropped, the bin
    codes are renamed to interval labels and the columns ordered as in the
    authoritative flat panel. ``Date`` is the target period.
    """
    df = rounds.dropna(how="all", axis=1).dropna(how="all", axis=0)
    df = df.rename(columns=cv.ECB_BIN_LABELS)
    missing = [c for c in cv.FLAT_PANEL_COLUMNS if c not in df.columns]
    for c in missing:
        df[c] = np.nan
    return df.loc[:, list(cv.FLAT_PANEL_COLUMNS)].reset_index(drop=True)


def hicp_yoy_from_index(index: pd.Series) -> pd.Series:
    """Year-on-year inflation, in per cent, from a monthly HICP index series."""
    s = index.astype(float)
    return 100.0 * (s - s.shift(12)) / s.shift(12)


def hicp_extremes(yoy: pd.Series) -> tuple[float, float]:
    """Lowest and highest realized inflation, the two numbers that close the tails."""
    y = yoy.dropna()
    return float(y.min()), float(y.max())


def _find_percentile(percentile: float, edges, cumulative):
    """Quantile of the interval distribution, interpolated inside its bin (the builder's rule)."""
    for i, cum_prob in enumerate(cumulative):
        if cum_prob >= percentile:
            lower_edge, upper_edge = edges[i]
            previous = 0.0 if i == 0 else cumulative[i - 1]
            denom = cum_prob - previous
            if denom <= 0:
                return None
            w = (percentile - previous) / denom
            return lower_edge + w * (upper_edge - lower_edge)
    return None


def _iqr_scale(x: pd.Series) -> float:
    x = x[np.isfinite(x)]
    s = float(x.quantile(0.75) - x.quantile(0.25)) if len(x) else 1.0
    return s if s != 0 else 1.0


def _prepare(flat: pd.DataFrame, hicp_min: float, hicp_max: float):
    """The flat panel at formation time, tails pooled, rows renormalized to 100 within their grid regime.

    Returns the frame, the pre- and post-change bin columns present, and the two
    sets of closed bin edges. Rows with no probability in either grid are dropped.
    """
    df = flat.copy()
    df["Date"] = pd.to_datetime(df["Date"]) - pd.DateOffset(years=1)

    bins, binspost = list(cv.GRID_PRE_BINS), list(cv.GRID_POST_BINS)
    bin_edges = cv.grid_edges(post=False, hicp_min=hicp_min, hicp_max=hicp_max)
    bin_post_edges = cv.grid_edges(post=True, hicp_min=hicp_min, hicp_max=hicp_max)

    left = list(cv.GRID_PRE_LEFT_SOURCES)
    right = list(cv.GRID_PRE_RIGHT_SOURCES)
    if all(c in df.columns for c in left):
        df["]-inf, - 1]"] = df.loc[:, left].sum(axis=1)
    if all(c in df.columns for c in right):
        df["[5,+inf["] = df.loc[:, right].sum(axis=1)

    keep = ["Date", "FCT_SOURCE", "POINT"] + [c for c in bins if c in df.columns] + [
        c for c in binspost if c in df.columns
    ]
    df = df.loc[:, keep].copy()
    for c in keep[3:]:
        df[c] = df[c].astype(float)

    def _normalize_rowwise(frame: pd.DataFrame, cols) -> None:
        cols = [c for c in cols if c in frame.columns]
        if not cols:
            return
        s = frame[cols].sum(axis=1)
        frame.loc[:, cols] = frame[cols].div(s.replace(0, np.nan), axis=0) * 100.0

    _normalize_rowwise(df, bins)
    _normalize_rowwise(df, binspost)
    df.dropna(
        subset=[c for c in bins if c in df.columns] + [c for c in binspost if c in df.columns],
        how="all",
        inplace=True,
    )
    df.sort_values(["Date", "FCT_SOURCE"], inplace=True)
    df.reset_index(drop=True, inplace=True)

    pre_cols = [c for c in bins if c in df.columns]
    post_cols = [c for c in binspost if c in df.columns]
    return df, pre_cols, post_cols, bin_edges, bin_post_edges


def averaged_density(
    flat: pd.DataFrame,
    hicp_min: float = cv.HICP_MIN,
    hicp_max: float = cv.HICP_MAX,
    grid_change: pd.Timestamp | str = cv.QUESTIONNAIRE_CHANGE_PANEL_DATE,
) -> pd.DataFrame:
    """Round by round, the equal-weight average of the individual densities and its moments.

    Every forecaster's density is renormalized to one (a missing cell read as
    no mass, as the panel builder reads it) before the average is taken, so
    the averaged density is the equal-weight mixture of the individual ones and
    its variance is, by the law of total variance, the round mean of the
    individual variances plus the population variance of the individual
    means -- the objects ``W`` and ``D`` of :func:`nu_measures.law.round_aggregates`.

    Returns a frame indexed by formation ``Date`` with ``n`` (forecasters),
    ``Mean_avg`` and ``Variance_avg``, computed with the same closed bins as
    the individual moments.
    """
    grid_change = pd.Timestamp(grid_change)
    df, pre_cols, post_cols, bin_edges, bin_post_edges = _prepare(flat, hicp_min, hicp_max)
    rows = []
    for date, g in df.groupby("Date", sort=True):
        if date >= grid_change:
            prob_cols, edges = post_cols, bin_post_edges
        else:
            prob_cols, edges = pre_cols, bin_edges
        P = g[prob_cols].to_numpy(dtype=float)
        P = np.where(np.isfinite(P), P, 0.0)
        tot = P.sum(axis=1)
        P = P[tot > 0] / tot[tot > 0][:, None]
        if len(P) == 0:
            continue
        pbar = P.mean(axis=0)
        mid = np.array([(lo + hi) / 2.0 for (lo, hi) in edges], dtype=float)
        mu = float(np.dot(mid, pbar))
        rows.append({"Date": date, "n": int(len(P)), "Mean_avg": mu, "Variance_avg": float(np.dot((mid - mu) ** 2, pbar))})
    return pd.DataFrame(rows).set_index("Date")


def individual_panel(
    flat: pd.DataFrame,
    hicp_min: float = cv.HICP_MIN,
    hicp_max: float = cv.HICP_MAX,
    target: float = cv.TARGET,
    grid_change: pd.Timestamp | str = cv.QUESTIONNAIRE_CHANGE_PANEL_DATE,
    hicp_yoy: pd.Series | None = None,
    loess_frac: float = 0.3,
    ac_iqr_window: tuple[str, str] | None = cv.AC_IQR_WINDOW,
) -> pd.DataFrame:
    """The individual panel: moments of every density, and the individual measures.

    Reproduces the authoritative builder exactly. For every forecaster-round:

    * the historic open tails are pooled into the two end bins of the grid in
      force through 2024Q3, and probabilities are renormalized to 100 within
      the grid regime of the round;
    * mean and variance are computed with each bin's mass at the midpoint of
      its closed interval, the bottom bin closed at ``min(edge, hicp_min)`` and
      the top bin on ``[edge, hicp_max]``;
    * the quartiles are interpolated linearly inside their bin, and Bowley's
      skewness is their normalized difference (set to -0.1 or +0.1 when more
      than 25 per cent of the mass sits in an open tail of the old grid);
    * ``NIU`` is the symmetric unit correction ``sigma / sqrt(1 + |mean - target|)``;
    * ``ACI`` is the individual Asymmetry Coherence, from the median's distance
      to target and the forecaster's skewness smoothed over two rounds, each
      passed through ``tanh(x / IQR)`` -- the IQRs on the whole panel unless
      ``ac_iqr_window`` freezes them on a ``(start, end)`` range of ``Date``;
    * ``bins_filled``, the normalized entropy and the informativeness index
      (zero when a single bin is filled) describe how finely the density is
      resolved.

    ``sigma_resid`` -- the residual of a LOESS of ``sigma_spd`` on realized
    inflation at formation time -- is computed only when ``hicp_yoy`` (a
    monthly series indexed by month start) is given; it is not used by any
    published exhibit.

    ``Date`` is shifted back one year to the formation time.
    """
    grid_change = pd.Timestamp(grid_change)
    df, pre_cols, post_cols, bin_edges, bin_post_edges = _prepare(flat, hicp_min, hicp_max)

    means, variances, q1s, q2s, q3s, bowleys = [], [], [], [], [], []
    filled, entropies, informativeness = [], [], []
    for _, row in df.iterrows():
        date = pd.to_datetime(row["Date"])
        if date >= grid_change:
            prob_cols, edges, K = post_cols, bin_post_edges, len(bin_post_edges)
        else:
            prob_cols, edges, K = pre_cols, bin_edges, len(bin_edges)
        if not prob_cols:
            for lst in (means, variances, q1s, q2s, q3s, bowleys, filled, entropies, informativeness):
                lst.append(np.nan)
            continue
        probs_pct = pd.to_numeric(row[prob_cols], errors="coerce").fillna(0.0).to_numpy(dtype=float)
        probs_pct = np.where(np.isfinite(probs_pct), probs_pct, 0.0)
        total = probs_pct.sum()
        if total <= 0:
            for lst in (means, variances, q1s, q2s, q3s, bowleys, entropies):
                lst.append(np.nan)
            filled.append(0)
            informativeness.append(0.0)
            continue
        pvec = probs_pct / total
        S = int(np.sum(pvec > 0.0))
        filled.append(S)
        ppos = pvec[pvec > 0]
        H = float(-np.sum(ppos * np.log(ppos)))
        h = float(H / np.log(K)) if K > 1 else np.nan
        entropies.append(h)
        informativeness.append(0.0 if S == 1 else h)

        mid = np.array([(lo + hi) / 2.0 for (lo, hi) in edges], dtype=float)
        mu = float(np.dot(mid, probs_pct) / total)
        var = float(np.dot((mid - mu) ** 2, probs_pct) / total)
        cdf = np.cumsum(probs_pct)
        q1 = _find_percentile(25.0, edges, cdf)
        q2 = _find_percentile(50.0, edges, cdf)
        q3 = _find_percentile(75.0, edges, cdf)
        if (q1 is None) or (q2 is None) or (q3 is None) or (q3 == q1):
            bow = np.nan
            q1, q2, q3 = np.nan, np.nan, np.nan
        else:
            bow = ((q3 - q2) - (q2 - q1)) / (q3 - q1)
        means.append(mu)
        variances.append(var)
        q1s.append(q1)
        q2s.append(q2)
        q3s.append(q3)
        bowleys.append(bow)

    df["Mean_spd"] = means
    df["Variance_spd"] = variances
    df["sigma_spd"] = np.sqrt(df["Variance_spd"])
    df["Q1"] = q1s
    df["Q2_median_spd"] = q2s
    df["Q3"] = q3s
    df["Bowley_Skewness"] = bowleys
    df["bins_filled"] = filled
    df["entropy_norm"] = entropies
    df["I_informativeness"] = informativeness

    if "]-inf, - 1]" in df.columns:
        df.loc[df["]-inf, - 1]"] > cv.AC_TAIL_MASS_LIMIT, "Bowley_Skewness"] = -cv.AC_TAIL_SKEWNESS
    if "[5,+inf[" in df.columns:
        df.loc[df["[5,+inf["] > cv.AC_TAIL_MASS_LIMIT, "Bowley_Skewness"] = cv.AC_TAIL_SKEWNESS

    # The symmetric unit correction, as the authoritative panel carries it.
    d = (df["Mean_spd"] - target).abs()
    D = (1.0 + 1.0 * d).pow(0.5)
    df["NIU"] = np.sqrt(df["Variance_spd"]) / D.replace(0, np.nan)

    # Individual Asymmetry Coherence.
    df["Bowley_Skewness_smoothed"] = (
        df.sort_values(["FCT_SOURCE", "Date"])
        .groupby("FCT_SOURCE")["Bowley_Skewness"]
        .transform(lambda s: s.rolling(window=cv.AC_SMOOTHING_ROUNDS, min_periods=1).mean())
    )
    if ac_iqr_window is None:
        ref = df
    else:
        lo, hi = pd.Timestamp(ac_iqr_window[0]), pd.Timestamp(ac_iqr_window[1])
        ref = df[(df["Date"] >= lo) & (df["Date"] <= hi)]
    scale_med = _iqr_scale(ref["Q2_median_spd"] - target)
    scale_skw = _iqr_scale(ref["Bowley_Skewness_smoothed"])
    df["Q2_norm"] = np.tanh((df["Q2_median_spd"] - target) / scale_med)
    df["A_norm"] = np.tanh(df["Bowley_Skewness_smoothed"] / scale_skw)
    df["ACI"] = 0.5 * (df["Q2_norm"] + df["A_norm"]) * 0.5 * (1.0 + df["Q2_norm"] * df["A_norm"])
    df["coherence"] = 0.5 * (1.0 + df["Q2_norm"] * df["A_norm"])
    scales = {"median_gap": scale_med, "skewness": scale_skw}

    # Optional residual of sigma on realized inflation at formation time.
    df["sigma_resid"] = np.nan
    if hicp_yoy is not None:
        from statsmodels.nonparametric.smoothers_lowess import lowess

        infl = hicp_yoy.dropna().rename("inflation").rename_axis("Date").reset_index()
        infl["Date"] = pd.to_datetime(infl["Date"]).dt.to_period("M").dt.to_timestamp()
        tmp = df[["Date", "FCT_SOURCE", "sigma_spd"]].merge(infl, on="Date", how="left")
        mask = tmp["inflation"].notna() & tmp["sigma_spd"].notna()
        if mask.any():
            fitted = lowess(
                endog=tmp.loc[mask, "sigma_spd"],
                exog=tmp.loc[mask, "inflation"],
                frac=loess_frac,
                return_sorted=False,
            )
            tmp.loc[mask, "sigma_resid"] = tmp.loc[mask, "sigma_spd"] - fitted
            df = df.drop(columns="sigma_resid").merge(
                tmp.loc[:, ["Date", "FCT_SOURCE", "sigma_resid"]], on=["Date", "FCT_SOURCE"], how="left"
            )

    out = df.loc[:, list(INDIVIDUAL_PANEL_COLUMNS)].copy()
    out.sort_values(["Date", "FCT_SOURCE"], inplace=True)
    out.reset_index(drop=True, inplace=True)
    out.attrs["ac_iqr_scales"] = scales
    return out


def build_panels(rounds_dir: str | Path, out_dir: str | Path, through: str | None = None, **kwargs) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The pipeline step: rounds -> ``flat_panel.csv`` -> ``individual_panel.csv`` under ``out_dir``.

    The flat panel is written and read back before the individual panel is
    built, as the authoritative builder does; the round trip through the file
    is what makes the rebuilt individual panel byte-identical to the certified
    one. ``through`` stops at a round (see :func:`round_files`). Other keyword
    arguments go to :func:`individual_panel`.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    flat = flat_panel(read_rounds(rounds_dir, through))
    flat_path = out / "flat_panel.csv"
    flat.to_csv(flat_path, index=False)
    flat = pd.read_csv(flat_path)
    flat["Date"] = pd.to_datetime(flat["Date"])
    panel = individual_panel(flat, **kwargs)
    panel.to_csv(out / "individual_panel.csv", index=False)
    return flat, panel
