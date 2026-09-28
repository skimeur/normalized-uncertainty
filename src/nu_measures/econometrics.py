"""The estimators behind the printed numbers, with the papers' conventions kept explicit.

Everything here could be done with ``statsmodels``, and the tests check that
it agrees with ``statsmodels`` where the two coincide. It exists as its own
module because a published number is only reproducible when its convention is
named: the Newey--West estimator below carries the small-sample factor
``n / (n - k)`` on the whole sandwich, Bartlett weights ``1 - l / (L + 1)``
and ``L = 4`` lags, which is what every ``t``-statistic printed in the two
papers rests on. A reader who uses another package's default gets the same
coefficients and slightly different standard errors.

References: Vansteenberghe (2026), *Tolerable Inflation, Intolerable
Uncertainty* (``vansteenberghe2026tolerable``), Section 3; Vansteenberghe
(2026), *Uncertain and Asymmetric Forecasts*
(``vansteenberghe2026uncertain``), Section 3.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy import stats

__all__ = ["OLSResult", "hac_ols", "ols", "wald", "chi2_p", "cluster_ols", "wild_cluster_p", "add_constant"]

HAC_LAGS = 4


@dataclass
class OLSResult:
    """A fitted linear regression and the numbers the papers print."""

    params: np.ndarray
    se: np.ndarray
    cov: np.ndarray
    r2: float
    n: int
    k: int
    resid: np.ndarray = field(repr=False)
    fitted: np.ndarray = field(repr=False)
    names: tuple[str, ...] = ()

    @property
    def t(self) -> np.ndarray:
        return self.params / self.se

    def as_dict(self) -> dict[str, float]:
        names = self.names or tuple(f"b{i}" for i in range(len(self.params)))
        out: dict[str, float] = {}
        for name, b, s, t in zip(names, self.params, self.se, self.t, strict=True):
            out[name] = float(b)
            out[f"se_{name}"] = float(s)
            out[f"t_{name}"] = float(t)
        out["r2"] = float(self.r2)
        out["n"] = int(self.n)
        return out


def add_constant(X) -> np.ndarray:
    """A column of ones in front of ``X`` (one- or two-dimensional)."""
    X = np.asarray(X, dtype=float)
    if X.ndim == 1:
        X = X[:, None]
    return np.column_stack([np.ones(X.shape[0]), X])


def _clean(y, X):
    y = np.asarray(y, dtype=float)
    X = np.asarray(X, dtype=float)
    if X.ndim == 1:
        X = X[:, None]
    ok = np.isfinite(y) & np.isfinite(X).all(axis=1)
    return y[ok], X[ok]


def hac_ols(y, X, lags: int = HAC_LAGS, constant: bool = True, names: tuple[str, ...] = ()) -> OLSResult:
    """OLS with Newey--West (Bartlett) standard errors, the papers' convention.

    ``lags = 0`` gives heteroskedasticity-robust (White) standard errors with the
    same ``n / (n - k)`` factor -- the convention of the pooled individual-level
    fits. With ``constant`` a column of ones is prepended to ``X``.
    """
    y, X = _clean(y, X)
    Xf = add_constant(X) if constant else X
    n, k = Xf.shape
    if n <= k:
        raise ValueError("not enough observations")
    XtXi = np.linalg.inv(Xf.T @ Xf)
    b = XtXi @ (Xf.T @ y)
    u = y - Xf @ b
    Xu = Xf * u[:, None]
    S = Xu.T @ Xu
    for lag in range(1, lags + 1):
        G = Xu[lag:].T @ Xu[:-lag]
        S += (1.0 - lag / (lags + 1.0)) * (G + G.T)
    V = XtXi @ S @ XtXi * (n / (n - k))
    se = np.sqrt(np.diag(V))
    tss = float((y - y.mean()) @ (y - y.mean()))
    r2 = 1.0 - float(u @ u) / tss if tss > 0 else float("nan")
    if constant and names and len(names) == k - 1:
        names = ("const",) + tuple(names)
    return OLSResult(params=b, se=se, cov=V, r2=r2, n=n, k=k, resid=u, fitted=Xf @ b, names=tuple(names))


def ols(y, X, constant: bool = True, names: tuple[str, ...] = ()) -> OLSResult:
    """OLS with classical (homoskedastic) standard errors."""
    y, X = _clean(y, X)
    Xf = add_constant(X) if constant else X
    n, k = Xf.shape
    if n <= k:
        raise ValueError("not enough observations")
    XtXi = np.linalg.inv(Xf.T @ Xf)
    b = XtXi @ (Xf.T @ y)
    u = y - Xf @ b
    s2 = float(u @ u) / (n - k)
    V = s2 * XtXi
    se = np.sqrt(np.diag(V))
    tss = float((y - y.mean()) @ (y - y.mean()))
    r2 = 1.0 - float(u @ u) / tss if tss > 0 else float("nan")
    if constant and names and len(names) == k - 1:
        names = ("const",) + tuple(names)
    return OLSResult(params=b, se=se, cov=V, r2=r2, n=n, k=k, resid=u, fitted=Xf @ b, names=tuple(names))


def cluster_ols(y, X, groups, constant: bool = True, names: tuple[str, ...] = ()) -> OLSResult:
    """OLS with one-way cluster-robust standard errors (the usual finite-sample factors)."""
    y0 = np.asarray(y, dtype=float)
    X0 = np.asarray(X, dtype=float)
    if X0.ndim == 1:
        X0 = X0[:, None]
    g0 = np.asarray(groups)
    ok = np.isfinite(y0) & np.isfinite(X0).all(axis=1)
    y0, X0, g0 = y0[ok], X0[ok], g0[ok]
    Xf = add_constant(X0) if constant else X0
    n, k = Xf.shape
    XtXi = np.linalg.inv(Xf.T @ Xf)
    b = XtXi @ (Xf.T @ y0)
    u = y0 - Xf @ b
    S = np.zeros((k, k))
    labels = np.unique(g0)
    for lab in labels:
        m = g0 == lab
        s = Xf[m].T @ u[m]
        S += np.outer(s, s)
    G = len(labels)
    V = XtXi @ S @ XtXi * (G / (G - 1)) * ((n - 1) / (n - k))
    se = np.sqrt(np.diag(V))
    tss = float((y0 - y0.mean()) @ (y0 - y0.mean()))
    r2 = 1.0 - float(u @ u) / tss if tss > 0 else float("nan")
    if constant and names and len(names) == k - 1:
        names = ("const",) + tuple(names)
    return OLSResult(params=b, se=se, cov=V, r2=r2, n=n, k=k, resid=u, fitted=Xf @ b, names=tuple(names))


def wild_cluster_p(
    y, X, groups, coef: int, draws: int = 999, seed: int = 0, constant: bool = True, add_one: bool = True
) -> float:
    """Restricted wild-cluster (Rademacher) bootstrap ``p``-value for ``params[coef] = 0``.

    The restricted model (the coefficient set to zero) provides the residuals;
    each cluster's residuals are multiplied by a common ±1 draw; the statistic
    is the cluster-robust ``t`` of the coefficient under the null. The
    ``p``-value is ``(count + 1) / (draws + 1)`` by default; ``add_one=False``
    gives the plain share ``count / draws``.
    """
    y0 = np.asarray(y, dtype=float)
    X0 = np.asarray(X, dtype=float)
    if X0.ndim == 1:
        X0 = X0[:, None]
    g0 = np.asarray(groups)
    ok = np.isfinite(y0) & np.isfinite(X0).all(axis=1)
    y0, X0, g0 = y0[ok], X0[ok], g0[ok]
    Xf = add_constant(X0) if constant else X0
    j = coef + 1 if constant else coef
    full = cluster_ols(y0, X0, g0, constant=constant)
    t_obs = float(full.params[j] / full.se[j])
    Xr = np.delete(Xf, j, axis=1)
    br = np.linalg.lstsq(Xr, y0, rcond=None)[0]
    ur = y0 - Xr @ br
    yr = Xr @ br
    labels = np.unique(g0)
    idx = {lab: (g0 == lab) for lab in labels}
    rng = np.random.default_rng(seed)
    count = 0
    for _ in range(draws):
        w = rng.choice([-1.0, 1.0], size=len(labels))
        e = np.empty_like(ur)
        for wi, lab in zip(w, labels, strict=True):
            e[idx[lab]] = wi * ur[idx[lab]]
        yb = yr + e
        fb = cluster_ols(yb, X0, g0, constant=constant)
        tb = float(fb.params[j] / fb.se[j])
        if abs(tb) >= abs(t_obs):
            count += 1
    return (count + 1.0) / (draws + 1.0) if add_one else count / draws


def wald(params, cov, restrictions) -> float:
    """Wald statistic of the linear restrictions ``R b = 0``."""
    R = np.atleast_2d(np.asarray(restrictions, dtype=float))
    b = np.asarray(params, dtype=float)
    V = np.asarray(cov, dtype=float)
    m = R @ b
    return float(m.T @ np.linalg.inv(R @ V @ R.T) @ m)


def chi2_p(statistic: float, df: int = 1) -> float:
    """Upper-tail probability of a chi-square with ``df`` degrees of freedom."""
    return float(stats.chi2.sf(max(statistic, 0.0), df))
