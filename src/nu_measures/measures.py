"""The corrected measures: NU, NGU, and the orthogonalisation of one on the other.

The starting point is a fact about the data rather than a modelling choice: the
dispersion of a professional forecaster's inflation density is not constant in
the level of the forecast. It is flat while expected inflation sits at or below
the announced target and rises with the expected overshoot above it. A measure
of *uncertainty* that ignores this records, in part, how far inflation is from
its anchor.

**Normalized Uncertainty** divides the density's standard deviation by the
square root of the fitted variance envelope, leaving the part of dispersion the
distance from target does not explain::

    NU_i = sigma_i / sqrt(1 + r * (mu_i - target)_+)

with ``r = b_plus / a`` from the two-arm law of :mod:`nu_measures.law`. Two
readings are published on equal footing: the fitted ``r`` estimated on the
sample, and the unit calibration ``r = 1``, which needs no estimate. The
denominator is one-sided because the target is announced: below the number
there is nothing to explain away.

**Normalized Growth Uncertainty** applies the same correction to growth
densities, where the benchmark is potential growth. That benchmark is estimated
rather than announced, so the denominator is symmetric: a shortfall and an
overshoot are treated alike.

Asymmetry Coherence (AC) is added with the reader for the asymmetry pipeline;
it is not reimplemented here from memory.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .calendar import CERTIFIED, NU_R_FITTED, NU_R_UNIT, TARGET

__all__ = ["normalizer", "nu", "ngu", "orthogonalize"]


def normalizer(gap, r: float = NU_R_FITTED, one_sided: bool = True):
    """The square-root envelope that divides dispersion.

    Parameters
    ----------
    gap:
        Expected inflation minus the announced target (or expected growth minus
        potential growth), in percentage points.
    r:
        Slope of the envelope relative to its intercept. :data:`NU_R_FITTED`
        estimates it from the two-arm law; :data:`NU_R_UNIT` is the
        calibration-free reading.
    one_sided:
        ``True`` uses the positive part of ``gap`` (inflation, where the target
        is announced); ``False`` uses its absolute value (growth).
    """
    if r < 0:
        raise ValueError("r must be non-negative")
    g = np.asarray(gap, dtype=float)
    d = np.clip(g, 0.0, None) if one_sided else np.abs(g)
    return np.sqrt(1.0 + r * d)


def nu(sigma, mean_forecast, target: float = TARGET, r: float = NU_R_FITTED, one_sided: bool = True):
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
        See :func:`normalizer`. Pass :data:`NU_R_UNIT` for the unit calibration.
    one_sided:
        Keep ``True`` for inflation against an announced target.
    """
    s = np.asarray(sigma, dtype=float)
    return s / normalizer(np.asarray(mean_forecast, dtype=float) - target, r=r, one_sided=one_sided)


def nu_unit(sigma, mean_forecast, target: float = TARGET):
    """:func:`nu` with the calibration-free denominator ``r = 1``."""
    return nu(sigma, mean_forecast, target=target, r=NU_R_UNIT, one_sided=True)


def ngu(sigma, mean_forecast, potential_growth):
    """Normalized Growth Uncertainty.

    The denominator is symmetric in the distance from potential growth, and the
    calibration is the unit one: potential growth is an estimate, not an
    announced number, so there is no arm to estimate a ratio on.
    """
    s = np.asarray(sigma, dtype=float)
    gap = np.asarray(mean_forecast, dtype=float) - np.asarray(potential_growth, dtype=float)
    return s / normalizer(gap, r=NU_R_UNIT, one_sided=False)


def orthogonalize(
    panel: pd.DataFrame,
    y: str,
    x: str,
    by: str = "forecaster",
    period: str = "period",
    min_obs: int = CERTIFIED["orthogonalisation_min_obs"],
    standardize: bool = True,
) -> tuple[pd.Series, pd.DataFrame]:
    """Residualise one measure on the other, forecaster by forecaster.

    Inflation uncertainty and growth uncertainty move together: a forecaster who
    is uncertain about one tends to be uncertain about the other. To ask what
    growth uncertainty carries *beyond* inflation uncertainty, the common part
    is removed within the forecaster, not in the aggregate -- otherwise the
    composition of the panel does the work.

    Each forecaster with at least ``min_obs`` matched rounds gets their own
    regression of ``y`` on ``x``. Forecasters below that threshold keep their
    own intercept but borrow the pooled within-forecaster slope, which is
    estimated on the demeaned panel. Residuals are then averaged by round.

    Returns
    -------
    series:
        The round-level residual series, standardised when ``standardize``.
    detail:
        One row per forecaster: number of matched rounds, the slope used, and
        whether it is the forecaster's own or the pooled one.
    """
    for col in (y, x, by, period):
        if col not in panel.columns:
            raise KeyError(f"column {col!r} is missing from the panel")

    df = panel[[by, period, x, y]].dropna().copy()
    if df.empty:
        raise ValueError("no matched observations")

    # Pooled within-forecaster slope, on the demeaned panel.
    g = df.groupby(by)
    xd = df[x] - g[x].transform("mean")
    yd = df[y] - g[y].transform("mean")
    denom = float((xd**2).sum())
    if denom <= 0:
        raise ValueError("no within-forecaster variation in the regressor")
    b_fe = float((xd * yd).sum() / denom)

    rows, residuals = [], []
    for name, sub in df.groupby(by, sort=False):
        n = len(sub)
        own = False
        if n >= min_obs and float(((sub[x] - sub[x].mean()) ** 2).sum()) > 0:
            b = float(
                ((sub[x] - sub[x].mean()) * (sub[y] - sub[y].mean())).sum()
                / ((sub[x] - sub[x].mean()) ** 2).sum()
            )
            own = True
        else:
            b = b_fe
        a = float(sub[y].mean() - b * sub[x].mean())
        res = sub[y] - a - b * sub[x]
        residuals.append(pd.DataFrame({period: sub[period].to_numpy(), "residual": res.to_numpy()}))
        rows.append({by: name, "n": n, "slope": b, "own_slope": own, "intercept": a})

    detail = pd.DataFrame(rows).sort_values(by).reset_index(drop=True)
    series = pd.concat(residuals).groupby(period)["residual"].mean().sort_index()
    if standardize:
        sd = float(series.std(ddof=1))
        if sd > 0:
            series = (series - float(series.mean())) / sd
    series.name = f"{y}_orth_{x}"
    return series, detail
