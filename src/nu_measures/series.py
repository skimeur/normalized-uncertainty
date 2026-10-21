"""The ECB-SPF round series at the one-, two- and five-year horizons, in one call.

From the ECB's round files, :func:`ecb_spf_series` returns, round by round and
horizon by horizon, the series the papers read off the individual densities:

=========================  ===================================================
``level``                  mean of the individual density means (the consensus)
``disagreement``           cross-sectional s.d. of the density means, ``sqrt(D)``
``raw_uncertainty``        mean individual s.d. of the densities
``NU``                     mean Normalized Uncertainty, unit calibration
                           ``sigma / sqrt(1 + (mu - target)_+)``
``skewness``               mean individual Bowley skewness (unsmoothed)
``AC``                     Asymmetry Coherence, mean over forecasters
``n``                      forecasters with a usable density
``aggregate_uncertainty``  ``T = W + D``, the variance of the averaged density
``W``, ``D``               mean individual variance; variance of the means
``level_point``            mean of the point forecasts
``disagreement_point``     cross-sectional s.d. of the point forecasts
``n_point``                forecasters reporting a point
``Q_tilde``, ``A_tilde``,  the components of AC and its coherence weight
``coherence``
``Date``                   the formation date of the panels (see below)
=========================  ===================================================

Every series is built by the functions the papers' exhibits use --
:func:`nu_measures.io_ecb_spf.individual_panel`,
:func:`nu_measures.law.round_aggregates`, :func:`nu_measures.measures.nu_series`,
:func:`nu_measures.asymmetry.ac_panel` -- so at one year they are the papers'
numbers; nothing here is a new formula. Both cross-sectional standard
deviations are population ones (``ddof=0``), so that ``T = W + D`` holds
exactly. The density series are on the forecaster-rounds with a mean and a
positive variance; the point series on every respondent of the horizon who
reported a point, density or not.

Horizons and dates
------------------
``"1Y"`` and ``"2Y"`` are the rolling targets twelve and twenty-four months
after the last observed month; ``"5Y"`` the longer-term calendar year, four
and a quarter to five years ahead (:data:`nu_measures.conventions.HORIZONS`).
The output is indexed by ``horizon`` and the survey quarter ``round``; every
round of the files appears at every horizon, with ``n`` zero and the series
missing where the horizon was not asked (the longer term in 1999Q2-Q4 and
2000Q2-Q4). ``Date`` is the panels' formation date, the first month of the
quarter before the round, shared by the three horizons.

The AC scales
-------------
AC passes the median's distance to target and the smoothed skewness through
``tanh(x / IQR)``. By default (``ac_scales="1Y"``) the two IQRs are those of the
one-year panel at every horizon, so that AC is comparable along the term
structure: longer-term medians cluster near the target, and scales computed on
them would make a deviation of a tenth of a point read like one of a point at
one year. ``ac_scales="own"`` computes them horizon by horizon; a dict imposes
them. The scales used are in ``attrs['ac_iqr_scales']``, and ``ac_iqr_window``
freezes the window they are computed on, as in :func:`~nu_measures.asymmetry.ac_panel`.

Reference: Vansteenberghe (2026), *Uncertain and Asymmetric Forecasts*
(``vansteenberghe2026uncertain``), Sections 2-4.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import asymmetry, io_ecb_spf, law, measures
from . import conventions as cv

__all__ = ["SERIES_COLUMNS", "horizon_panels", "round_series", "ecb_spf_series", "to_long", "to_wide"]

#: Column order of :func:`ecb_spf_series`: the six series, then the rest.
SERIES_COLUMNS: tuple[str, ...] = (
    "level", "disagreement", "raw_uncertainty", "NU", "skewness", "AC",
    "n", "aggregate_uncertainty", "W", "D",
    "level_point", "disagreement_point", "n_point",
    "Q_tilde", "A_tilde", "coherence", "Date",
)


def _survey_quarter(formation: pd.Series | pd.DatetimeIndex) -> pd.PeriodIndex:
    return pd.PeriodIndex(pd.to_datetime(formation) + pd.DateOffset(months=1), freq="Q")


def horizon_panels(
    rounds_dir: str | Path,
    horizons=cv.HORIZONS,
    through: str | None = None,
    **kwargs,
) -> dict[str, tuple[pd.DataFrame, pd.DataFrame]]:
    """The flat and individual panels of each horizon, as ``{horizon: (flat, panel)}``.

    Keyword arguments go to :func:`~nu_measures.io_ecb_spf.individual_panel`
    (the tail closures, the target).
    """
    out = {}
    for h in horizons:
        flat = io_ecb_spf.flat_panel(io_ecb_spf.read_rounds(rounds_dir, through, horizon=h))
        flat["Date"] = pd.to_datetime(flat["Date"])
        out[h] = (flat, io_ecb_spf.individual_panel(flat, **kwargs))
    return out


def round_series(
    flat: pd.DataFrame,
    panel: pd.DataFrame,
    target: float = cv.TARGET,
    ac_scales: dict | None = None,
    ac_iqr_window: tuple[str, str] | None = cv.AC_IQR_WINDOW,
) -> pd.DataFrame:
    """The series of one horizon, indexed by survey quarter, from its two panels.

    ``ac_scales`` imposes the two AC scales (``None`` computes them on
    ``panel``); the scales used are in ``attrs['ac_iqr_scales']``.
    """
    A = law.round_aggregates(panel, target=target)
    S = pd.DataFrame(index=A.index)
    S["level"] = A["mu"]
    S["disagreement"] = np.sqrt(A["D"])
    S["raw_uncertainty"] = A["SD"]
    S["NU"] = measures.nu_series(panel, target=target)["NU_unit"]
    p = panel.dropna(subset=["Mean_spd", "Variance_spd"])
    p = p[p["Variance_spd"] > 0]
    S["skewness"] = p.groupby("Date")["Bowley_Skewness"].mean()
    S["n"] = A["n"]
    S["aggregate_uncertainty"] = A["T"]
    S["W"], S["D"] = A["W"], A["D"]

    pts = flat.dropna(subset=["POINT"]).copy()
    pts["Date"] = pd.to_datetime(pts["Date"]) - pd.DateOffset(years=1)
    P = pts.groupby("Date")["POINT"].agg(level_point="mean", disagreement_point=lambda s: s.std(ddof=0), n_point="size")
    S = S.join(P, how="outer")
    S["Date"] = S.index
    S.index = _survey_quarter(S.index)
    S.index.name = "round"

    acp = asymmetry.ac_panel(panel, target=target, iqr_window=ac_iqr_window, scales=ac_scales)
    ac = asymmetry.ac_series(acp)
    S = S.join(ac[["AC", "Q_tilde", "A_tilde", "coherence"]], how="left")
    S["n"] = S["n"].fillna(0).astype(int)
    S["n_point"] = S["n_point"].fillna(0).astype(int)
    S = S.loc[:, list(SERIES_COLUMNS)]
    S.attrs["ac_iqr_scales"] = acp.attrs["ac_iqr_scales"]
    return S


def ecb_spf_series(
    rounds_dir: str | Path,
    horizons=cv.HORIZONS,
    through: str | None = None,
    target: float = cv.TARGET,
    ac_scales: str | dict = "1Y",
    ac_iqr_window: tuple[str, str] | None = cv.AC_IQR_WINDOW,
    panels: dict | None = None,
) -> pd.DataFrame:
    """Every series of every horizon, indexed by ``(horizon, round)``.

    ``rounds_dir`` holds the ECB's round files ``YYYYQn.csv``; ``through``
    stops at a round. ``ac_scales`` is ``"1Y"`` (the one-year scales at every
    horizon, the default), ``"own"`` or a dict of the two scales. ``panels``
    -- the output of :func:`horizon_panels` -- skips the reading. The scales
    used, horizon by horizon, are in ``attrs['ac_iqr_scales']``.
    """
    horizons = tuple(horizons)
    bad = [h for h in horizons if h not in cv.HORIZONS]
    if bad:
        raise ValueError(f"unknown horizons {bad}; expected some of {cv.HORIZONS}")
    need = set(horizons) | ({"1Y"} if ac_scales == "1Y" else set())
    if panels is None:
        panels = horizon_panels(rounds_dir, [h for h in cv.HORIZONS if h in need], through, target=target)

    if ac_scales == "1Y":
        ref = asymmetry.ac_panel(panels["1Y"][1], target=target, iqr_window=ac_iqr_window)
        imposed = ref.attrs["ac_iqr_scales"]
    elif ac_scales == "own":
        imposed = None
    elif isinstance(ac_scales, dict):
        imposed = ac_scales
    else:
        raise ValueError('ac_scales must be "1Y", "own" or a dict of the two scales')

    rounds = pd.PeriodIndex([pd.Period(p.stem, freq="Q") for p in io_ecb_spf.round_files(rounds_dir, through)],
                            name="round")
    blocks, scales = [], {}
    for h in horizons:
        flat, panel = panels[h]
        S = round_series(flat, panel, target=target, ac_scales=imposed, ac_iqr_window=ac_iqr_window)
        scales[h] = S.attrs["ac_iqr_scales"]
        S = S.reindex(rounds)
        S["n"] = S["n"].fillna(0).astype(int)
        S["n_point"] = S["n_point"].fillna(0).astype(int)
        S["Date"] = rounds.to_timestamp() - pd.DateOffset(months=1)
        blocks.append(S.assign(horizon=h).set_index("horizon", append=True).reorder_levels(["horizon", "round"]))
    out = pd.concat(blocks)
    out.attrs["ac_iqr_scales"] = scales
    out.attrs["ac_scales"] = ac_scales if isinstance(ac_scales, str) else "imposed"
    out.attrs["target"] = target
    out.attrs["rounds"] = (str(rounds[0]), str(rounds[-1]))
    return out


def to_long(series: pd.DataFrame) -> pd.DataFrame:
    """One row per ``(round, horizon, series)``, with the ``value``; ``Date`` is dropped."""
    s = series.drop(columns="Date").astype(float)
    long = s.stack(future_stack=True).rename("value").reset_index()
    long = long.rename(columns={long.columns[2]: "series"})
    long["round"] = long["round"].astype(str)
    return long.loc[:, ["round", "horizon", "series", "value"]]


def to_wide(series: pd.DataFrame) -> pd.DataFrame:
    """One row per round, one column per ``<series>_<horizon>`` (``level_1Y``, ``NU_5Y``, ...)."""
    s = series.drop(columns="Date")
    w = s.unstack("horizon")
    horizons = list(dict.fromkeys(series.index.get_level_values("horizon")))
    w = w.reindex(columns=pd.MultiIndex.from_product([list(s.columns), horizons]))
    w.columns = [f"{c}_{h}" for c, h in w.columns]
    w.insert(0, "Date", series.xs(horizons[0], level="horizon")["Date"])
    w.index = w.index.astype(str)
    return w
