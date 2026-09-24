"""The two-arm law of the predictive variance, and the tests that go with it.

The measured object is

.. math:: V(d) = a + b_-\\,(-d)_+ + b_+\\,(d)_+ ,

the predictive variance of an inflation density against the expected gap from
the announced target. The specification has one point: it lets the data say
whether dispersion behaves the same way on the two sides of the number. It does
not. The lower arm is flat -- economically small and statistically
indistinguishable from zero -- while the upper arm is large and precisely
estimated. Its ratio to the intercept, ``b_+ / a``, is the fitted NU
denominator; the unit calibration ``a = b = 1`` needs no fit at all.

Inference is Newey--West with four lags throughout (:mod:`nu_measures.econometrics`):
the rounds are quarterly and overlap in what they forecast, so the residuals
are serially correlated by construction.

Three objects obey the law with different coefficients, and the module keeps
them apart: ``W`` is the round mean of the individual density variances (the
average individual variance, the envelope the measure divides by), ``D`` the
cross-forecaster variance of the density means (disagreement), and ``T = W + D``
the variance of the averaged density (the total). The papers estimate the law
on ``W``; the total's law is reported beside it.

The kink location is read, not optimised over and then tested at the winner:
:func:`kink_profile` maps the residual sum of squares over candidate
locations, and the law is estimated at the announced number.

References: Vansteenberghe (2026), *Tolerable Inflation, Intolerable
Uncertainty*, Section 3 and Table 1; Vansteenberghe (forthcoming), *Uncertain
and Asymmetric Forecasts*, Section 3 and Table 1.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import conventions as cv
from .econometrics import OLSResult, chi2_p, hac_ols, wald

__all__ = [
    "ArmsFit",
    "arms_design",
    "arms_fit",
    "wald_tests",
    "round_aggregates",
    "estimation_sample",
    "law_by_object",
    "ratio_se",
    "split_test",
    "pooled_individual",
    "kink_profile",
    "kink_bootstrap",
]

HAC_LAGS = 4


def arms_design(gap, kink: float = 0.0) -> np.ndarray:
    """Design matrix ``[(kink - d)_+, (d - kink)_+]`` of the two arms (no constant)."""
    d = np.asarray(gap, dtype=float)
    below = np.clip(kink - d, 0.0, None)
    above = np.clip(d - kink, 0.0, None)
    return np.column_stack([below, above])


@dataclass
class ArmsFit:
    """Result of a two-arm fit, with the numbers the papers print."""

    n: int
    a: float
    b_minus: float
    b_plus: float
    se_a: float
    se_b_minus: float
    se_b_plus: float
    r2: float
    kink: float
    hac_lags: int
    cov: np.ndarray
    result: OLSResult

    @property
    def t_a(self) -> float:
        return self.a / self.se_a

    @property
    def t_b_minus(self) -> float:
        return self.b_minus / self.se_b_minus

    @property
    def t_b_plus(self) -> float:
        return self.b_plus / self.se_b_plus

    @property
    def params(self) -> np.ndarray:
        return np.array([self.a, self.b_minus, self.b_plus])

    @property
    def r_plus(self) -> float:
        """Ratio of the upper arm to the intercept.

        On the average individual variance it is the fitted NU denominator;
        on the round-mean total variance it is that object's own ratio, which
        is not the calibration. It is the one quantity of the fit comparable
        across sources: the level of a variance depends on the units and on
        the closure of each source, the ratio does not.
        """
        return self.b_plus / self.a if self.a else float("nan")

    @property
    def r_plus_se(self) -> float:
        """Delta-method standard error of :attr:`r_plus`."""
        return ratio_se(self.params, self.cov)

    def summary_row(self) -> dict[str, float]:
        return {
            "n": self.n,
            "a": self.a,
            "b_minus": self.b_minus,
            "b_plus": self.b_plus,
            "se_a": self.se_a,
            "se_b_minus": self.se_b_minus,
            "se_b_plus": self.se_b_plus,
            "t_b_minus": self.t_b_minus,
            "t_b_plus": self.t_b_plus,
            "r2": self.r2,
            "r_plus": self.r_plus,
            "r_plus_se": self.r_plus_se,
        }


def _from_result(res: OLSResult, kink: float, lags: int) -> ArmsFit:
    return ArmsFit(
        n=res.n,
        a=float(res.params[0]),
        b_minus=float(res.params[1]),
        b_plus=float(res.params[2]),
        se_a=float(res.se[0]),
        se_b_minus=float(res.se[1]),
        se_b_plus=float(res.se[2]),
        r2=float(res.r2),
        kink=float(kink),
        hac_lags=int(lags),
        cov=res.cov,
        result=res,
    )


def arms_fit(y, gap, kink: float = 0.0, hac_lags: int = HAC_LAGS) -> ArmsFit:
    """Fit the two-arm law by OLS with Newey--West standard errors.

    Parameters
    ----------
    y:
        The variance (or any dispersion measure) being explained.
    gap:
        Expected inflation minus the announced target, in percentage points.
    kink:
        Where the two arms meet, in gap units; zero is the announced target.
    hac_lags:
        Newey--West lag truncation, four quarters in the papers; ``0`` gives
        White standard errors, the convention of the pooled individual fits.
    """
    res = hac_ols(y, arms_design(gap, kink=kink), lags=hac_lags, names=("b_minus", "b_plus"))
    return _from_result(res, kink, hac_lags)


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
    out = {}
    for name, R in _RESTRICTIONS.items():
        stat = wald(fit.params, fit.cov, R)
        out[name] = {"statistic": stat, "p_value": chi2_p(stat, 1)}
    return out


def ratio_se(params, cov) -> float:
    """Delta-method standard error of ``b_plus / a`` from ``[a, b_minus, b_plus]``."""
    b = np.asarray(params, dtype=float)
    V = np.asarray(cov, dtype=float)
    J = np.array([-b[2] / b[0] ** 2, 0.0, 1.0 / b[0]])
    return float(np.sqrt(J @ V @ J))


# --------------------------------------------------------------------------
# From the individual panel to the round series
# --------------------------------------------------------------------------


def round_aggregates(panel: pd.DataFrame, target: float = cv.TARGET) -> pd.DataFrame:
    """The round series the law is estimated on, from the individual panel.

    Drops forecaster-rounds without a mean or a positive variance, then by
    ``Date`` (formation time): ``W`` the mean individual variance, ``D`` the
    population variance of the individual means, ``T = W + D``, ``mu`` the
    consensus (the mean of the individual means), ``SD`` the mean individual
    standard deviation, ``gap = mu - target``, ``n`` the forecasters counted,
    and ``Q`` the survey quarter.
    """
    p = panel.rename(columns={"Mean_spd": "M", "Variance_spd": "V"}).dropna(subset=["M", "V"])
    p = p[p["V"] > 0].copy()
    if "sigma_spd" not in p.columns:
        p["sigma_spd"] = np.sqrt(p["V"])
    A = p.groupby("Date").agg(
        W=("V", "mean"),
        D=("M", lambda s: s.var(ddof=0)),
        mu=("M", "mean"),
        SD=("sigma_spd", "mean"),
        n=("M", "size"),
    )
    A["T"] = A["W"] + A["D"]
    A["gap"] = A["mu"] - target
    A["Q"] = (A.index + pd.DateOffset(months=1)).to_period("Q")
    return A.sort_index()


def estimation_sample(
    aggregates: pd.DataFrame,
    trim: tuple[float, float] = cv.INDIVIDUAL_MEAN_TRIM,
    max_date: pd.Timestamp | str | None = cv.FIT_MAX_PANEL_DATE,
) -> pd.DataFrame:
    """The rounds that enter a fit: consensus inside ``trim`` and ``Date`` before ``max_date``.

    With the papers' constants this keeps 109 rounds through 2026Q2 (the
    round rule removes 2022Q4, consensus 5.01); ``max_date=None`` keeps every
    round inside the interval.
    """
    lo, hi = trim
    keep = aggregates["mu"].between(lo, hi)
    if max_date is not None:
        keep &= aggregates.index < pd.Timestamp(max_date)
    return aggregates[keep].sort_index()


def law_by_object(sample: pd.DataFrame, objects=("W", "D", "T"), hac_lags: int = HAC_LAGS) -> dict[str, ArmsFit]:
    """The two-arm law on each round object of ``sample`` (from :func:`round_aggregates`)."""
    return {o: arms_fit(sample[o].to_numpy(), sample["gap"].to_numpy(), hac_lags=hac_lags) for o in objects}


def split_test(sample: pd.DataFrame, obj: str, split: pd.Timestamp | str, hac_lags: int = HAC_LAGS) -> dict:
    """Does one envelope hold on both sides of ``split``?

    Fits the law with a full set of interactions with an after-``split``
    indicator and returns the Wald statistic of the three interactions (with
    three degrees of freedom), the two sub-sample fits, their ratios with
    delta-method standard errors, and the ``z`` of the difference of ratios.
    """
    split = pd.Timestamp(split)
    pre = sample[sample.index < split]
    post = sample[sample.index >= split]
    f_pre = arms_fit(pre[obj].to_numpy(), pre["gap"].to_numpy(), hac_lags=hac_lags)
    f_post = arms_fit(post[obj].to_numpy(), post["gap"].to_numpy(), hac_lags=hac_lags)
    g = sample["gap"].to_numpy()
    d = np.asarray(sample.index >= split, dtype=float)
    X = arms_design(g)
    Xi = np.column_stack([X, d, d * X[:, 0], d * X[:, 1]])
    res = hac_ols(sample[obj].to_numpy(), Xi, lags=hac_lags)
    R = np.zeros((3, 6))
    R[0, 3] = R[1, 4] = R[2, 5] = 1.0
    stat = wald(res.params, res.cov, R)
    z = (f_post.r_plus - f_pre.r_plus) / np.sqrt(f_pre.r_plus_se**2 + f_post.r_plus_se**2)
    return {
        "pre": f_pre,
        "post": f_post,
        "interaction": res,
        "wald_joint": stat,
        "p_joint": chi2_p(stat, 3),
        "z_ratio_difference": float(z),
        "p_ratio_difference": chi2_p(float(z) ** 2, 1),
    }


def pooled_individual(
    panel: pd.DataFrame,
    value: str = "Variance_spd",
    mean: str = "Mean_spd",
    target: float = cv.TARGET,
    trim: tuple[float, float] = cv.INDIVIDUAL_MEAN_TRIM,
    max_date: pd.Timestamp | str | None = cv.FIT_MAX_PANEL_DATE,
) -> ArmsFit:
    """The law pooled over forecaster-rounds, the ``[-1, 5]`` rule applied to each density.

    White standard errors (``hac_lags = 0``), the papers' convention for the
    pooled individual fits.
    """
    p = panel.dropna(subset=[value, mean])
    p = p[p[value] > 0]
    lo, hi = trim
    keep = p[mean].between(lo, hi)
    if max_date is not None:
        keep &= p["Date"] < pd.Timestamp(max_date)
    p = p[keep]
    return arms_fit(p[value].to_numpy(), p[mean].to_numpy() - target, hac_lags=0)


# --------------------------------------------------------------------------
# Where the kink sits
# --------------------------------------------------------------------------


def _ssr(c: float, level: np.ndarray, y: np.ndarray):
    X = np.column_stack([np.ones(len(level)), np.maximum(c - level, 0.0), np.maximum(level - c, 0.0)])
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    u = y - X @ b
    return float(u @ u), b


def kink_profile(y, level, grid=None, target: float = cv.TARGET, step: float = 0.01) -> dict:
    """Profile the residual sum of squares of the law over candidate kink locations.

    ``level`` is the consensus forecast itself (not the gap): the candidate
    kink ``c`` runs over the central ninety per cent of its range in steps of
    ``step``. Returns the grid and its RSS, the profiled optimum, the
    profile-likelihood 95 per cent set (``RSS <= RSS_min * exp(3.841 / n)``),
    the RSS gain from freeing the kink relative to the announced target, and
    the likelihood ratio ``n log(RSS_target / RSS_min)``.
    """
    y = np.asarray(y, dtype=float)
    level = np.asarray(level, dtype=float)
    n = len(y)
    if grid is None:
        grid = np.arange(np.quantile(level, 0.05), np.quantile(level, 0.95) + 1e-9, step)
    grid = np.asarray(grid, dtype=float)
    S = np.array([_ssr(c, level, y)[0] for c in grid])
    chat = float(grid[S.argmin()])
    s_hat, b_hat = _ssr(chat, level, y)
    s_target, b_target = _ssr(target, level, y)
    thr = s_hat * np.exp(3.841 / n)
    inside = grid[S <= thr]
    return {
        "grid": grid,
        "rss": S,
        "c_hat": chat,
        "set95": (float(inside.min()), float(inside.max())),
        "rss_min": s_hat,
        "rss_target": s_target,
        "gain_pct": float(100.0 * (s_target - s_hat) / s_target),
        "lr": float(n * np.log(s_target / s_hat)),
        "b_at_c_hat": [float(v) for v in b_hat],
        "b_at_target": [float(v) for v in b_target],
        "n": int(n),
    }


def kink_bootstrap(y, level, grid, draws: int = 2000, seed: int = 20260728,
                   rng: np.random.Generator | None = None) -> dict:
    """Nonparametric bootstrap over rounds of the profiled kink location.

    Rounds are resampled with replacement; each draw's kink is the RSS
    minimiser over the same ``grid``. Returns the 90 per cent interval (the
    5th and 95th percentiles), the median and the draws. A generator passed
    as ``rng`` is drawn from in place (several bootstraps sharing one stream,
    as some scripts do); otherwise a fresh generator is seeded with ``seed``.
    """
    y = np.asarray(y, dtype=float)
    level = np.asarray(level, dtype=float)
    grid = np.asarray(grid, dtype=float)
    n = len(y)
    if rng is None:
        rng = np.random.default_rng(seed)
    bs = np.empty(draws)
    for k in range(draws):
        i = rng.integers(0, n, n)
        Sb = np.array([_ssr(c, level[i], y[i])[0] for c in grid])
        bs[k] = grid[Sb.argmin()]
    lo, hi = np.percentile(bs, [5, 95])
    return {"interval90": (float(lo), float(hi)), "median": float(np.median(bs)), "draws": bs}
