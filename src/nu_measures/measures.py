"""The corrected measures: NU, NGU, and the orthogonalisation of one on the other.

The starting point is a fact about the data rather than a modelling choice: the
dispersion of a professional forecaster's inflation density is not constant in
the level of the forecast. It is flat while expected inflation sits at or below
the announced target and rises with the expected overshoot above it. A measure
of *uncertainty* that ignores this records, in part, how far inflation is from
its anchor.

**Normalized Uncertainty** divides the density's standard deviation by the
square root of the variance envelope, leaving the part of dispersion the
distance from target does not explain::

    NU_i = sigma_i / sqrt(1 + r * (mu_i - target)_+)

The default is the **unit calibration** ``r = 1`` (``a = b = 1`` in the law):
three numbers per forecaster and no estimate, so the value of a forecaster-round
is the same whatever the sample it is computed in. It does not depend on the
history or on the observation window, which is what makes it usable on any
density survey with an announced target. The **fitted** reading, ``r = b_+ / a``
from the two-arm law on the average individual variance (2.23 on the papers'
sample), is the papers' estimate and is available through ``r=NU_R_FITTED``.
The denominator is one-sided because the target is announced: below the number
there is nothing to explain away.

**Normalized Growth Uncertainty** applies the same correction to growth
densities, where the benchmark is potential growth. That benchmark is estimated
rather than announced, so the denominator is symmetric: a shortfall and an
overshoot are treated alike.

Asymmetry Coherence lives in :mod:`nu_measures.asymmetry`.

References: Vansteenberghe (forthcoming), *Uncertain and Asymmetric Forecasts*
(``vansteenberghe2026uncertain``), Sections 3 and 5 -- the construction;
Vansteenberghe (2026), *Tolerable Inflation, Intolerable Uncertainty*
(``vansteenberghe2026tolerable``), Sections 2-3 -- the law and the purge.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .conventions import CERTIFIED, NU_R_DEFAULT, NU_R_FITTED, NU_R_UNIT, TARGET

__all__ = [
    "normalizer",
    "nu",
    "nu_unit",
    "nu_fitted",
    "ngu",
    "add_nu",
    "nu_series",
    "quarterly",
    "standardize",
    "orthogonalize",
]


def normalizer(gap, r: float = NU_R_DEFAULT, one_sided: bool = True):
    """The square-root envelope that divides dispersion.

    Parameters
    ----------
    gap:
        Expected inflation minus the announced target (or expected growth minus
        potential growth), in percentage points.
    r:
        Slope of the envelope relative to its intercept: ``1`` (the default,
        the unit calibration) or :data:`~nu_measures.conventions.NU_R_FITTED`.
    one_sided:
        ``True`` uses the positive part of ``gap`` (inflation, where the target
        is announced); ``False`` uses its absolute value (growth).
    """
    if r < 0:
        raise ValueError("r must be non-negative")
    g = np.asarray(gap, dtype=float)
    d = np.clip(g, 0.0, None) if one_sided else np.abs(g)
    return np.sqrt(1.0 + r * d)


def nu(sigma, mean_forecast, target: float = TARGET, r: float = NU_R_DEFAULT, one_sided: bool = True):
    """Normalized Uncertainty of an inflation density forecast.

    Parameters
    ----------
    sigma:
        Standard deviation of the reported density.
    mean_forecast:
        Mean of the reported density, in per cent.
    target:
        The announced target the gap is measured from.
    r:
        See :func:`normalizer`; ``1`` by default.
    one_sided:
        Keep ``True`` for inflation against an announced target.
    """
    s = np.asarray(sigma, dtype=float)
    return s / normalizer(np.asarray(mean_forecast, dtype=float) - target, r=r, one_sided=one_sided)


def nu_unit(sigma, mean_forecast, target: float = TARGET):
    """:func:`nu` with the unit calibration ``r = 1`` (explicit alias)."""
    return nu(sigma, mean_forecast, target=target, r=NU_R_UNIT, one_sided=True)


def nu_fitted(sigma, mean_forecast, target: float = TARGET, r: float = NU_R_FITTED):
    """:func:`nu` with the fitted ratio of the papers' sample."""
    return nu(sigma, mean_forecast, target=target, r=r, one_sided=True)


def ngu(sigma, mean_forecast, potential_growth):
    """Normalized Growth Uncertainty.

    The denominator is symmetric in the distance from potential growth, and the
    calibration is the unit one: potential growth is an estimate, not an
    announced number, so there is no arm to estimate a ratio on.
    """
    s = np.asarray(sigma, dtype=float)
    gap = np.asarray(mean_forecast, dtype=float) - np.asarray(potential_growth, dtype=float)
    return s / normalizer(gap, r=NU_R_UNIT, one_sided=False)


# --------------------------------------------------------------------------
# From the individual panel to the round series
# --------------------------------------------------------------------------


def add_nu(panel: pd.DataFrame, target: float = TARGET, r_fitted: float = NU_R_FITTED) -> pd.DataFrame:
    """The individual panel with ``gap``, ``NU_unit`` and ``NU_fitted`` columns.

    Keeps the forecaster-rounds with a mean and a positive variance, the
    sample every round series is built on.
    """
    p = panel.dropna(subset=["Mean_spd", "Variance_spd"])
    p = p[p["Variance_spd"] > 0].copy()
    p["gap"] = p["Mean_spd"] - target
    sigma = np.sqrt(p["Variance_spd"].to_numpy())
    p["NU_unit"] = nu(sigma, p["Mean_spd"].to_numpy(), target=target, r=NU_R_UNIT)
    p["NU_fitted"] = nu(sigma, p["Mean_spd"].to_numpy(), target=target, r=r_fitted)
    return p


def nu_series(panel: pd.DataFrame, target: float = TARGET, r_fitted: float = NU_R_FITTED) -> pd.DataFrame:
    """Round means of the raw standard deviation and of the two NU readings.

    Indexed by the panel ``Date`` (formation time) with the survey quarter in
    ``Q``: ``raw_sd`` is the round mean of the individual standard deviations,
    ``NU_unit`` and ``NU_fitted`` the round means of the individual measures,
    ``n`` the forecasters counted.
    """
    p = add_nu(panel, target=target, r_fitted=r_fitted)
    p["raw_sd"] = np.sqrt(p["Variance_spd"])
    S = p.groupby("Date").agg(raw_sd=("raw_sd", "mean"), NU_unit=("NU_unit", "mean"),
                              NU_fitted=("NU_fitted", "mean"), n=("raw_sd", "size"))
    S["Q"] = (S.index + pd.DateOffset(months=1)).to_period("Q")
    return S.sort_index()


def quarterly(series: pd.DataFrame, columns=None) -> pd.DataFrame:
    """Re-index a ``Date``-indexed round series by its survey quarter ``Q``."""
    cols = list(columns) if columns is not None else [c for c in series.columns if c != "Q"]
    return series.groupby("Q")[cols].mean()


def standardize(x: pd.Series) -> pd.Series:
    """``(x - mean) / sd`` with the sample standard deviation."""
    return (x - x.mean()) / x.std()


def orthogonalize(
    panel: pd.DataFrame,
    y: str,
    x: str,
    by: str = "forecaster",
    period: str = "period",
    min_obs: int = CERTIFIED["orthogonalisation_min_obs"],
    standardize_result: bool = True,
) -> tuple[pd.Series, pd.DataFrame]:
    """Residualise one measure on the other, forecaster by forecaster.

    Inflation uncertainty and growth uncertainty move together: a forecaster who
    is uncertain about one tends to be uncertain about the other. To ask what
    growth uncertainty carries *beyond* inflation uncertainty, the common part
    is removed within the forecaster, not in the aggregate -- otherwise the
    composition of the panel does the work.

    Each forecaster with at least ``min_obs`` matched rounds gets their own
    regression of ``y`` on ``x``. The others keep their own intercept and
    borrow one within-forecaster slope, estimated on their demeaned
    observations pooled together. Residuals are averaged by period and, by
    default, standardised.

    Returns
    -------
    series:
        The period-level residual series.
    detail:
        One row per forecaster: matched rounds, the slope used, whether it is
        the forecaster's own.
    """
    for col in (y, x, by, period):
        if col not in panel.columns:
            raise KeyError(f"column {col!r} is missing from the panel")
    df = panel[[by, period, x, y]].dropna().copy()
    if df.empty:
        raise ValueError("no matched observations")
    counts = df.groupby(by).size()
    big_ids = counts[counts >= min_obs].index
    big, small = df[df[by].isin(big_ids)], df[~df[by].isin(big_ids)]

    rows, residuals = [], []
    for name, sub in big.groupby(by, sort=False):
        X = np.column_stack([np.ones(len(sub)), sub[x].to_numpy(dtype=float)])
        bb = np.linalg.lstsq(X, sub[y].to_numpy(dtype=float), rcond=None)[0]
        residuals.append(pd.DataFrame({period: sub[period].to_numpy(), "residual": sub[y].to_numpy() - X @ bb}))
        rows.append({by: name, "n": len(sub), "slope": float(bb[1]), "own_slope": True, "intercept": float(bb[0])})
    if len(small):
        g = small.groupby(by)
        xd = small[x] - g[x].transform("mean")
        yd = small[y] - g[y].transform("mean")
        bw = float(np.polyfit(xd.to_numpy(dtype=float), yd.to_numpy(dtype=float), 1)[0])
        for name, sub in small.groupby(by, sort=False):
            a = float(sub[y].mean() - bw * sub[x].mean())
            e = sub[y] - a - bw * sub[x]
            residuals.append(pd.DataFrame({period: sub[period].to_numpy(), "residual": e.to_numpy()}))
            rows.append({by: name, "n": len(sub), "slope": bw, "own_slope": False, "intercept": a})

    detail = pd.DataFrame(rows).sort_values(by).reset_index(drop=True)
    series = pd.concat(residuals).groupby(period)["residual"].mean().sort_index()
    if standardize_result:
        series = standardize(series)
    series.name = f"{y}_orth_{x}"
    return series, detail
