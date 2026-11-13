"""Realized variance does not outlast the gap: the ARMA-GARCH footnote of Section 3, "The realized shadow".

Paper: Vansteenberghe, E. (2026), *Tolerable Inflation, Intolerable Uncertainty*,
working paper, Banque de France (``vansteenberghe2026tolerable``), Section 3,
paragraph "The realized shadow" (the persistence sentences and their footnote).

Not an exhibit: a register, as ``results_register.py``.

**Realized inflation.** The monthly euro-area headline gap (HICP year on year,
not seasonally adjusted, less 2; 1997-2026) follows an ARMA mean selected by
BIC, estimated jointly with a GARCH(1,1) variance by Student-t maximum
likelihood, with and without the two arms of the lagged gap in the variance:

    h_t = omega + alpha e_{t-1}^2 [+ gamma e_{t-1}^2 1(e_{t-1}<0)] + beta h_{t-1} + delta_+ (d_{t-1})_+ + delta_- (-d_{t-1})_+

A variance injection decays at alpha + beta + gamma/2 a month. Variants:
Gaussian errors, GJR asymmetry, the sample to 2019, month-on-month adjusted
inflation as the mean variable, and the quarterly gap. The likelihood ratio
of the GARCH terms (alpha = beta = 0) is the footnote's "constant variance
around the arms is not rejected".

**Forecasters.** The average individual variance W_t of the ECB-SPF (the
109-round sample) regressed on its own lag, the current and lagged arms of the
expected gap and the learned baseline (the mean squared AR(1) innovation of
the quarterly gap over the eight quarters known at the survey), HAC(4): the
loads on the current and the lagged overshoot.

Inputs:  ECB Data Portal ``ICP.M.U2.N.000000.4.INX`` (not adjusted, to December 2025) and
         ``ICP.M.U2.Y.000000.3.INX`` (adjusted), through ``load_ecb_series``; Eurostat
         ``prc_hicp_minr`` (EA, TOTAL, 2015 = 100) for the months of 2026, through
         ``load_eurostat_series``; the ECB-SPF round files.
Outputs: ``results/results_realized_persistence.{json,md}``.

Several minutes: the likelihood is evaluated in plain Python, from six starting points per model.

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use
this code, cite the paper above.
"""

from __future__ import annotations

import itertools
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy.optimize import minimize
from scipy.special import gammaln
from scipy.stats import chi2
from statsmodels.tsa.arima.model import ARIMA

from nu_measures import conventions as cv
from nu_measures.exhibit import Exhibit, load_ecb_panel, load_ecb_series, load_eurostat_series

NSA = "ICP.M.U2.N.000000.4.INX"
SA = "ICP.M.U2.Y.000000.3.INX"
SURVEY_BEFORE = "2026-04-01"


# --------------------------------------------------------------------------- data
def headline_index() -> pd.Series:
    """The not-adjusted index: the ECB's to December 2025, Eurostat's for the months after (both 2015 = 100)."""
    leg = load_ecb_series(NSA)
    new = load_eurostat_series("hicp_ea_total_minr", "prc_hicp_minr", {"geo": "EA", "coicop18": "TOTAL", "unit": "I15"},
                               since="2019-01")
    return pd.concat([leg, new[new.index > leg.index[-1]]]).sort_index()


def gaps(idx: pd.Series) -> tuple[pd.Series, pd.Series]:
    yoy = (100 * (idx / idx.shift(12) - 1)).dropna()
    gap_m = yoy - cv.TARGET
    gap_q = yoy.groupby(yoy.index.asfreq("Q")).mean() - cv.TARGET
    if idx.index[-1].month % 3 != 0:  # complete quarters only
        gap_q = gap_q.iloc[:-1]
    return gap_m, gap_q


# --------------------------------------------------------------------------- ARMA-GARCH-X likelihood
def unpack(x, p, q, ma12, arms, gjr):
    k = 0
    c = x[k]
    k += 1
    phi = x[k:k + p]
    k += p
    th = x[k:k + q]
    k += q
    t12 = x[k] if ma12 else 0.0
    k += ma12
    w, a, b = np.exp(x[k]), x[k + 1] ** 2, x[k + 2] ** 2
    k += 3
    g = x[k] ** 2 if gjr else 0.0
    k += gjr
    dp, dm = (x[k] ** 2, x[k + 1] ** 2) if arms else (0.0, 0.0)
    k += 2 * arms
    nu = 2.05 + np.exp(x[k])
    return c, phi, th, t12, w, a, b, g, dp, dm, nu


def nll(x, y, z, p, q, ma12, arms, gjr, dist="t"):
    c, phi, th, t12, w, a, b, g, dp, dm, nu = unpack(x, p, q, ma12, arms, gjr)
    if a + b + g / 2 >= 0.9999:
        return 1e10
    n = len(y)
    e = np.zeros(n)
    h = np.zeros(n)
    m0 = max(p, 12 if ma12 else q, 1)
    h[:m0] = np.var(y)
    ll = 0.0
    for t in range(m0, n):
        mu = c + sum(phi[i] * y[t - 1 - i] for i in range(p)) + sum(th[j] * e[t - 1 - j] for j in range(q)) + (t12 * e[t - 12] if ma12 else 0.0)
        e[t] = y[t] - mu
        h[t] = w + a * e[t - 1] ** 2 + g * e[t - 1] ** 2 * (e[t - 1] < 0) + b * h[t - 1] + dp * max(z[t - 1], 0) + dm * max(-z[t - 1], 0)
        if h[t] <= 1e-10:
            return 1e10
        if dist == "t":
            ll += (gammaln((nu + 1) / 2) - gammaln(nu / 2) - 0.5 * np.log(np.pi * (nu - 2) * h[t])
                   - (nu + 1) / 2 * np.log(1 + e[t] ** 2 / ((nu - 2) * h[t])))
        else:
            ll += -0.5 * (np.log(2 * np.pi * h[t]) + e[t] ** 2 / h[t])
    return -ll


def fit(y, z, p, q, ma12=0, arms=1, gjr=0, dist="t", starts=6, seed=0):
    rng = np.random.default_rng(seed)
    best = None
    ols = sm.OLS(y[p:], sm.add_constant(np.column_stack([y[p - 1 - i:len(y) - 1 - i] for i in range(p)]))).fit() if p else None
    for _ in range(starts):
        x0 = [ols.params[0] if p else y.mean()] + (list(ols.params[1:]) if p else []) + [0.1] * q + [0.0] * ma12
        v = np.var(y) * 0.05
        x0 += [np.log(v * (1 + rng.random())), np.sqrt(0.05 + 0.15 * rng.random()), np.sqrt(0.5 + 0.4 * rng.random())]
        x0 += [0.1] * gjr + [0.1, 0.05] * arms + [np.log(6.0)]
        args = (y, z, p, q, ma12, arms, gjr, dist)
        r = minimize(nll, np.array(x0), args=args, method="Nelder-Mead", options=dict(maxiter=40000, maxfev=40000, xatol=1e-7, fatol=1e-8))
        r = minimize(nll, r.x, args=args, method="BFGS")
        if best is None or r.fun < best.fun:
            best = r
    return best


def num_hess(f, x, h=1e-4):
    k = len(x)
    H = np.zeros((k, k))
    for i in range(k):
        for j in range(i, k):
            ei, ej = np.eye(k)[i] * h, np.eye(k)[j] * h
            H[i, j] = H[j, i] = (f(x + ei + ej) - f(x + ei - ej) - f(x - ei + ej) + f(x - ei - ej)) / (4 * h * h)
    return H


def report(y, z, p, q, ma12=0, arms=1, gjr=0, dist="t", per_q=1, label=""):
    r = fit(y, z, p, q, ma12, arms, gjr, dist)
    c, phi, th, t12, w, a, b, g, dp, dm, nu = unpack(r.x, p, q, ma12, arms, gjr)
    pers = a + b + g / 2
    f = lambda x: nll(x, y, z, p, q, ma12, arms, gjr, dist)  # noqa: E731
    try:
        V = np.linalg.inv(num_hess(f, r.x))

        def grad(fn):
            return np.array([(fn(r.x + np.eye(len(r.x))[i] * 1e-6) - fn(r.x - np.eye(len(r.x))[i] * 1e-6)) / 2e-6 for i in range(len(r.x))])

        def pf(x):
            u = unpack(x, p, q, ma12, arms, gjr)
            return u[5] + u[6] + u[7] / 2

        def dpf(x):
            return unpack(x, p, q, ma12, arms, gjr)[8]

        gp = grad(pf)
        se_p = float(np.sqrt(max(gp @ V @ gp, 0)))
        se_dp = float(np.sqrt(max(grad(dpf) @ V @ grad(dpf), 0))) if arms else None
    except np.linalg.LinAlgError:
        se_p = se_dp = None
    pq = pers ** per_q
    se_pq = se_p * per_q * pers ** (per_q - 1) if se_p else None
    rq = np.sqrt(pq)
    se_r = se_pq / (2 * rq) if se_pq else None
    out = dict(label=label, p=p, q=q, ma12=ma12, gjr=gjr, arms=arms, dist=dist, n=len(y), llf=round(-r.fun, 2),
               phi=np.round(phi, 3).tolist(), alpha=round(a, 3), beta=round(b, 3), gamma=round(g, 3), omega=round(w, 4),
               delta_plus=round(dp, 3), delta_plus_se=round(se_dp, 3) if se_dp else None, delta_minus=round(dm, 3),
               pers=round(pers, 4), pers_se=round(se_p, 4) if se_p else None, pers_quarterly=round(pq, 3),
               r=round(rq, 3), r_se=round(se_r, 3) if se_r else None,
               r_ci=[round(float(np.sqrt(max(pq - 1.96 * se_pq, 0))), 3), round(float(np.sqrt(min(pq + 1.96 * se_pq, 1))), 3)] if se_pq else None)
    return out, r


def select_mean(y, grid_p, grid_q, ma12_opts):
    warnings.filterwarnings("ignore", module="statsmodels")  # starting values and convergence notes of the BIC grid
    best = None
    for p, q, m12 in itertools.product(grid_p, grid_q, ma12_opts):
        try:
            mod = ARIMA(y, order=(p, 0, list(range(1, q + 1)) + [12])).fit() if m12 else ARIMA(y, order=(p, 0, q)).fit()
            if best is None or mod.bic < best[0]:
                best = (mod.bic, p, q, m12)
        except Exception:  # noqa: BLE001, S112 - a grid point that does not estimate is skipped, as in the paper's run
            continue
    return dict(bic=round(best[0], 1), p=best[1], q=best[2], ma12=best[3])


def garch_block(ex: Exhibit) -> dict:
    gap_m, gap_q = gaps(headline_index())
    sa = load_ecb_series(SA)
    mom = (1200 * np.log(sa).diff()).dropna()
    ym, yq = gap_m.to_numpy(), gap_q.to_numpy()
    res = {"sample_monthly": [str(gap_m.index[0]), str(gap_m.index[-1])], "sample_quarterly": [str(gap_q.index[0]), str(gap_q.index[-1])]}
    sm_ = select_mean(ym, [1, 2, 3], [0, 1, 2], [0, 1])
    sq_ = select_mean(yq, [1, 2], [0, 1, 2], [0])
    res["mean_selected_monthly"], res["mean_selected_quarterly"] = sm_, sq_
    P, Q, M12 = sm_["p"], sm_["q"], sm_["ma12"]
    runs = {}
    runs["monthly_arms"], rH = report(ym, ym, P, Q, M12, arms=1, per_q=3, label="monthly ARMA-GARCH-X (arms), t")
    runs["monthly_plain"], _ = report(ym, ym, P, Q, M12, arms=0, per_q=3, label="monthly plain GARCH(1,1), t")
    runs["monthly_gjr"], _ = report(ym, ym, P, Q, M12, arms=1, gjr=1, per_q=3, label="monthly GJR-GARCH-X, t")
    runs["monthly_gaussian"], _ = report(ym, ym, P, Q, M12, arms=1, dist="n", per_q=3, label="monthly GARCH-X, Gaussian")
    pre = gap_m[gap_m.index <= pd.Period("2019-12", "M")].to_numpy()
    runs["monthly_to_2019"], _ = report(pre, pre, P, Q, M12, arms=1, per_q=3, label="monthly GARCH-X, to 2019")
    al = pd.concat([mom, gap_m], axis=1, keys=["mom", "gap"]).dropna()
    runs["monthly_mom"], _ = report(al["mom"].to_numpy(), al["gap"].to_numpy(), 2, 0, 0, arms=1, per_q=3, label="monthly m/m adjusted, arms on the y/y gap")
    runs["quarterly_arms"], _ = report(yq, yq, sq_["p"], sq_["q"], 0, arms=1, per_q=1, label="quarterly ARMA-GARCH-X (arms), t")
    runs["quarterly_plain"], _ = report(yq, yq, sq_["p"], sq_["q"], 0, arms=0, per_q=1, label="quarterly plain GARCH, t")

    k0 = 1 + P + Q + M12

    def nll_const(x):  # alpha = beta = 0 (held at 1e-4 on the transformed scale)
        return nll(np.r_[x[:k0], x[k0], 1e-4, 1e-4, x[k0 + 1:]], ym, ym, P, Q, M12, 1, 0)

    rc = minimize(nll_const, np.r_[rH.x[:k0], rH.x[k0], rH.x[k0 + 3:]], method="Nelder-Mead", options=dict(maxiter=40000, maxfev=40000))
    rc = minimize(nll_const, rc.x, method="BFGS")
    lr = float(2 * (rc.fun - rH.fun))
    res["LR_garch_terms"] = {"LR": round(lr, 2), "p": round(float(chi2.sf(lr, 2)), 3)}
    res["runs"] = runs
    for v in runs.values():
        ex.say(f"{v['label']:<46} n {v['n']}  alpha+beta(+gamma/2) {v['pers']:.3f}/month  quarterly {v['pers_quarterly']:.3f}"
               f"  delta+ {v['delta_plus']} ({v['delta_plus_se']})  delta- {v['delta_minus']}  r {v['r']}")
    ex.say(f"GARCH terms vs constant variance around the arms: LR {res['LR_garch_terms']['LR']}, p {res['LR_garch_terms']['p']}")
    return res


# --------------------------------------------------------------------------- the survey: habituation, not memory
def survey_block(ex: Exhibit) -> dict:
    pan = load_ecb_panel().rename(columns={"Mean_spd": "M", "Variance_spd": "V"}).dropna(subset=["M", "V"])
    pan = pan[pan["V"] > 0].copy()
    pan["q"] = (pan["Date"] + pd.DateOffset(months=1)).dt.to_period("Q")
    lo, hi = cv.INDIVIDUAL_MEAN_TRIM
    RD = pan.groupby("Date").agg(mu=("M", "mean"))
    keep = RD[(RD["mu"] >= lo) & (RD["mu"] <= hi) & (RD.index < SURVEY_BEFORE)].index
    paper_q = set((pd.DatetimeIndex(keep) + pd.DateOffset(months=1)).to_period("Q"))

    h = load_ecb_series(SA)
    yoy = (100 * (h / h.shift(12) - 1)).dropna()
    gap = yoy.groupby(yoy.index.asfreq("Q")).mean() - cv.TARGET
    ar = sm.OLS(gap.to_numpy()[1:], sm.add_constant(gap.to_numpy()[:-1])).fit()
    innov = pd.Series(np.r_[np.nan, ar.resid], index=gap.index)
    s8 = (innov ** 2).rolling(8, min_periods=8).mean().shift(1)  # the survey in quarter q knows through q - 1

    cons = pan.groupby("q")["M"].mean()
    A = pan[pan["q"].isin(paper_q)].groupby("q")["V"].mean().rename("W").to_frame()
    A["de"] = cons - cv.TARGET
    A = A.sort_index()
    A = A.reindex(pd.period_range(A.index.min(), A.index.max(), freq="Q"))
    A["dp"], A["dm"] = A["de"].clip(lower=0), (-A["de"]).clip(lower=0)
    for c in ("W", "dp", "dm"):
        A[c + "1"] = A[c].shift(1)
    A["s8"] = s8.reindex(A.index)
    A = A.dropna(subset=["W", "W1", "dp", "dp1"])
    m = smf.ols("W ~ W1 + dp + dp1 + dm + dm1 + s8", A).fit(cov_type="HAC", cov_kwds={"maxlags": 4})
    coefs = {k: [round(float(v), 3), round(float(m.bse[k]), 3)] for k, v in m.params.items()}
    ex.say(f"ECB-SPF, W on its lag, the arms and their lags, the learned baseline (HAC 4), n {int(m.nobs)}: "
           f"current overshoot {coefs['dp'][0]:+.3f} ({coefs['dp'][1]}), lagged overshoot {coefs['dp1'][0]:+.3f} ({coefs['dp1'][1]}), "
           f"own lag {coefs['W1'][0]:.2f}")
    return {"coefficients": coefs, "n": int(m.nobs), "R2": round(float(m.rsquared), 3)}


def main() -> None:
    ex = Exhibit(__file__)
    out = {"realized": garch_block(ex), "survey": survey_block(ex)}
    ex.write_results(out, title="Realized variance does not outlast the gap (Section 3)")


if __name__ == "__main__":
    main()
