"""The two-arm law of the predictive variance, and the tests that go with it.

The measured object is

.. math:: V(d) = a + b_-\\,(-d)_+ + b_+\\,(d)_+ ,

the predictive variance of an inflation density against the expected gap from
the announced target. The specification has one point: it lets the data say
whether dispersion behaves the same way on the two sides of the number. It does
not. The lower arm is flat -- economically small and statistically
indistinguishable from zero -- while the upper arm is large and precisely
estimated, and the fitted upper arm is what the NU denominator divides by.

Inference is HAC with four lags throughout: the rounds are quarterly and
overlapping in what they forecast, so the residuals are serially correlated by
construction.

Two things this module deliberately does not do. It does not search for the
kink location and then test at the winner: :func:`kink_profile` maps the
residual sum of squares over candidate locations so the profile can be read,
and the announced target is where the law is estimated. And it does not choose
between the round-level and the individual-level reading: :func:`within_between`
reports both, because they answer different questions -- whether forecasters
disagree more when inflation is high, or whether each forecaster is himself
less sure.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import statsmodels.api as sm

__all__ = ["ArmsFit", "arms_design", "arms_fit", "wald_tests", "within_between", "kink_profile"]

HAC_LAGS = 4


def arms_design(gap, kink: float = 0.0) -> np.ndarray:
    """Design matrix ``[1, (kink - d)_+, (d - kink)_+]`` for the two-arm law."""
    d = np.asarray(gap, dtype=float)
    below = np.clip(kink - d, 0.0, None)
    above = np.clip(d - kink, 0.0, None)
    return np.column_stack([np.ones_like(d), below, above])


@dataclass
class ArmsFit:
    """Result of a two-arm fit, with the numbers the papers print."""

    n: int
    a: float
    b_minus: float
    b_plus: float
    t_a: float
    t_b_minus: float
    t_b_plus: float
    r2: float
    kink: float
    hac_lags: int
    result: object = field(repr=False, default=None)

    @property
    def r_plus(self) -> float:
        """Ratio of the upper arm to the intercept -- the NU calibration.

        It is the one quantity of the fit that is comparable across sources:
        the level of a variance depends on the units and the closure of each
        source, the ratio does not.
        """
        return self.b_plus / self.a if self.a else float("nan")

    def summary_row(self) -> dict[str, float]:
        return {
            "n": self.n,
            "a": self.a,
            "b_minus": self.b_minus,
            "b_plus": self.b_plus,
            "t_b_minus": self.t_b_minus,
            "t_b_plus": self.t_b_plus,
            "r2": self.r2,
            "r_plus": self.r_plus,
        }


def _fit_design(y, X, kink: float, hac_lags: int) -> ArmsFit:
    """Fit ``y`` on a three-column arms design with HAC standard errors."""
    y = np.asarray(y, dtype=float)
    X = np.asarray(X, dtype=float)
    ok = np.isfinite(y) & np.isfinite(X).all(axis=1)
    y, X = y[ok], X[ok]
    if y.size <= X.shape[1]:
        raise ValueError("not enough observations to fit the two-arm law")
    res = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": hac_lags})
    return ArmsFit(
        n=int(y.size),
        a=float(res.params[0]),
        b_minus=float(res.params[1]),
        b_plus=float(res.params[2]),
        t_a=float(res.tvalues[0]),
        t_b_minus=float(res.tvalues[1]),
        t_b_plus=float(res.tvalues[2]),
        r2=float(res.rsquared),
        kink=float(kink),
        hac_lags=int(hac_lags),
        result=res,
    )


def arms_fit(y, gap, kink: float = 0.0, hac_lags: int = HAC_LAGS) -> ArmsFit:
    """Fit the two-arm law by OLS with HAC standard errors.

    Parameters
    ----------
    y:
        The variance (or any dispersion measure) being explained.
    gap:
        Expected inflation minus the announced target.
    kink:
        Where the two arms meet, in gap units. Zero is the announced target.
    hac_lags:
        Newey-West lag truncation; four quarters by default.
    """
    return _fit_design(y, arms_design(gap, kink=kink), kink=kink, hac_lags=hac_lags)


#: Restrictions on ``[a, b_minus, b_plus]``.
_RESTRICTIONS = {
    "b_minus_zero": np.array([[0.0, 1.0, 0.0]]),
    "arms_equal": np.array([[0.0, 1.0, -1.0]]),
}


def wald_tests(fit: ArmsFit) -> dict[str, dict[str, float]]:
    """The two hypotheses the specification exists to test.

    ``b_minus_zero`` asks whether dispersion responds at all below the target;
    ``arms_equal`` asks whether one symmetric slope would do. On the euro-area
    survey the first is not rejected and the second is, which is the asymmetry
    the correction is built on.
    """
    if fit.result is None:
        raise ValueError("the fit does not carry its estimation result")
    out = {}
    for name, r_matrix in _RESTRICTIONS.items():
        test = fit.result.wald_test(r_matrix, scalar=True, use_f=False)
        out[name] = {"statistic": float(test.statistic), "p_value": float(test.pvalue)}
    return out


def within_between(
    panel: pd.DataFrame,
    value: str,
    gap: str,
    by: str = "forecaster",
    hac_lags: int = HAC_LAGS,
) -> dict[str, ArmsFit]:
    """Split the individual-level law into its within and between parts.

    ``within`` removes each forecaster's own average -- it is the same person,
    more or less sure as the overshoot moves. ``between`` keeps only the
    forecaster averages -- it is the comparison across people. The paper reports
    both because the mechanism claims the first.
    """
    for col in (value, gap, by):
        if col not in panel.columns:
            raise KeyError(f"column {col!r} is missing from the panel")
    df = panel[[by, value, gap]].dropna()
    if df.empty:
        raise ValueError("no observations")

    # The arms are built from the raw gap first: the kink must stay at the
    # announced target. Only then is the variation split, by demeaning the
    # regressors and the dependent variable within forecaster (within) or by
    # keeping the forecaster averages (between). Demeaning the gap itself
    # would move the target.
    X = arms_design(df[gap].to_numpy(), kink=0.0)
    work = pd.DataFrame(
        {"by": df[by].to_numpy(), "y": df[value].to_numpy(), "below": X[:, 1], "above": X[:, 2]}
    )
    g = work.groupby("by")
    cols = ["y", "below", "above"]
    demeaned = work[cols] - g[cols].transform("mean")
    grand = work[cols].mean()
    within = demeaned + grand
    between = g[cols].mean()

    def design(frame: pd.DataFrame) -> np.ndarray:
        return np.column_stack(
            [np.ones(len(frame)), frame["below"].to_numpy(), frame["above"].to_numpy()]
        )

    return {
        "pooled": _fit_design(work["y"], design(work), kink=0.0, hac_lags=hac_lags),
        "within": _fit_design(within["y"], design(within), kink=0.0, hac_lags=hac_lags),
        "between": _fit_design(between["y"], design(between), kink=0.0, hac_lags=hac_lags),
    }


def kink_profile(y, gap, grid=None, hac_lags: int = HAC_LAGS) -> pd.DataFrame:
    """Residual sum of squares of the two-arm law over candidate kink locations.

    The profile is the honest way to ask where the break sits: it is read, not
    optimised over and then tested at the winner. ``grid`` is in gap units, so
    zero is the announced target.
    """
    y = np.asarray(y, dtype=float)
    d = np.asarray(gap, dtype=float)
    if grid is None:
        lo, hi = np.nanpercentile(d, [5, 95])
        grid = np.round(np.arange(lo, hi + 1e-9, 0.05), 4)
    rows = []
    for c in np.asarray(grid, dtype=float):
        try:
            fit = arms_fit(y, d, kink=float(c), hac_lags=hac_lags)
        except ValueError:
            continue
        resid = fit.result.resid
        rows.append(
            {
                "kink": float(c),
                "rss": float(resid @ resid),
                "a": fit.a,
                "b_minus": fit.b_minus,
                "b_plus": fit.b_plus,
                "r2": fit.r2,
            }
        )
    out = pd.DataFrame(rows)
    return out.sort_values("kink").reset_index(drop=True)
