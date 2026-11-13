"""The numbers of the appendix "Where the observational-equivalence effect could be seen: the United States".

Paper: Vansteenberghe, E. (2026), *Tolerable Inflation, Intolerable Uncertainty*,
working paper, Banque de France (``vansteenberghe2026tolerable``), Appendix A,
subsection "Where the observational-equivalence effect could be seen: the
United States" (numbers printed in the text; no table or figure).

Not an exhibit: a register, as ``results_register.py``.

**The survey.** The Philadelphia Fed SPF core-CPI densities (one year ahead,
an unchanged grid since 2007): the round's total variance of the consensus
density (average individual variance plus disagreement) on the two arms of
the expected gap, era by era -- before 2012, 2012-2020, 2021-2026 -- with HAC
standard errors (four lags, small-sample correction). The announcement
regression (both arms and their post-2012 shifts) at 2012 and at placebo dates
2014, 2016, 2018 and 2021, and the breakpoint profiled on the post-2012 sample
(grid over the central eighty per cent of the consensus).

**The market.** The five-year breakeven, in non-overlapping sixty-three-day
windows: the annualised realized variance of daily changes on the two arms of
the window's starting level around the announced number's CPI image (2.3 and
2.5 per cent), HC1 standard errors, by era.

Inputs:  ``us_spf/SPFmicrodata.xlsx`` (sheet ``PRCCPI``), FRED ``T5YIE``.
Outputs: ``results/results_us_appendix.{json,md}``.

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use
this code, cite the paper above.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from nu_measures import conventions as cv
from nu_measures import io_us_spf, law
from nu_measures.exhibit import Exhibit, load_fred, load_us_densities

ANNOUNCEMENT = "2012-01-01"
PLACEBOS = ("2014-01-01", "2016-01-01", "2018-01-01", "2021-01-01")
ERAS = {"before 2012": (None, "2011-12-31"), "2012-2020": ("2012-01-01", "2020-12-31"), "2021-2026": ("2021-01-01", None)}
CPI_IMAGES = (2.3, 2.5)
WINDOW = 63
HAC = {"cov_type": "HAC", "cov_kwds": {"maxlags": 4, "use_correction": True}}


def triple(m, k):
    return [float(m.params[k]), float(m.bse[k]), float(m.tvalues[k])]


def era(A: pd.DataFrame, start, end) -> pd.DataFrame:
    if start:
        A = A[A.index >= start]
    if end:
        A = A[A.index <= end]
    return A


def arms(A: pd.DataFrame) -> dict:
    g = A["mu"] - cv.TARGET
    X = pd.DataFrame({"dn": (-g).clip(lower=0), "up": g.clip(lower=0)}, index=A.index)
    m = sm.OLS(A["T"], sm.add_constant(X)).fit(**HAC)
    return {"up": triple(m, "up"), "dn": triple(m, "dn"), "n": int(m.nobs), "n_above": int((g > 0).sum()), "max_gap": float(g.max())}


def announcement(A: pd.DataFrame, brk: str) -> dict:
    g = A["mu"] - cv.TARGET
    post = (A.index >= brk).astype(float)
    X = pd.DataFrame({"dn": (-g).clip(lower=0), "up": g.clip(lower=0), "post": post,
                      "post_dn": post * (-g).clip(lower=0), "post_up": post * g.clip(lower=0)}, index=A.index)
    m = sm.OLS(A["T"], sm.add_constant(X)).fit(**HAC)
    t = m.t_test("post_up - post_dn = 0")
    return {"c0": triple(m, "post"), "c_plus": triple(m, "post_up"), "c_minus": triple(m, "post_dn"),
            "p_c_plus_eq_c_minus": float(np.squeeze(t.pvalue)), "R2": float(m.rsquared), "n": int(m.nobs)}


def breakeven_windows() -> pd.DataFrame:
    b = load_fred("T5YIE").dropna()
    dx = b.diff()
    rows = [(b.index[i], b.iloc[i], float(252 * (dx.iloc[i + 1:i + 1 + WINDOW] ** 2).mean())) for i in range(1, len(b) - WINDOW, WINDOW)]
    return pd.DataFrame(rows, columns=["d", "lvl", "rv"]).set_index("d")


def breakeven_arms(W: pd.DataFrame, ref: float, start=None, end=None) -> dict:
    z = W
    if start:
        z = z[z.index >= start]
    if end:
        z = z[z.index <= end]
    g = z["lvl"] - ref
    out = {"n": int(len(z)), "n_above": int((g > 0).sum())}
    if out["n_above"] == 0:
        return out | {"up": None}
    X = pd.DataFrame({"dn": (-g).clip(lower=0), "up": g.clip(lower=0)}, index=z.index)
    m = sm.OLS(z["rv"], sm.add_constant(X)).fit(cov_type="HC1")
    return out | {"up": triple(m, "up"), "dn": triple(m, "dn")}


def main() -> None:
    ex = Exhibit(__file__)
    A = io_us_spf.round_aggregates(load_us_densities("PRCCPI"))
    out = {"sample": [str(A.index[0].date()), str(A.index[-1].date())], "n_rounds": int(len(A))}

    out["arms_by_era"] = {k: arms(era(A, *v)) for k, v in ERAS.items()}
    for k, v in out["arms_by_era"].items():
        ex.say(f"core CPI, {k:<12} upper arm {v['up'][0]:+.2f} (t {v['up'][2]:.1f}), {v['n_above']} of {v['n']} rounds above 2, "
               f"largest expected gap {v['max_gap']:.2f}")

    out["announcement"] = {brk[:4]: announcement(A, brk) for brk in (ANNOUNCEMENT,) + PLACEBOS}
    for k, v in out["announcement"].items():
        ex.say(f"break at {k}: c+ {v['c_plus'][0]:+.3f} (t {v['c_plus'][2]:.1f}), c- {v['c_minus'][0]:+.3f}, "
               f"p(c+ = c-) {v['p_c_plus_eq_c_minus']:.3f}, R2 {v['R2']:.3f}")

    S = A[A.index >= ANNOUNCEMENT]
    mu = S["mu"].to_numpy()
    grid = np.arange(np.quantile(mu, 0.10), np.quantile(mu, 0.90) + 1e-9, 0.01)
    k = law.kink_profile(S["T"].to_numpy(), mu, grid=grid)
    out["kink_post_2012"] = {"c_hat": k["c_hat"], "rss_gain_pct": k["gain_pct"], "n": k["n"]}
    ex.say(f"kink profiled on the post-2012 sample: {k['c_hat']:.3f}; freeing it gains {k['gain_pct']:.2f} per cent of the RSS")

    W = breakeven_windows()
    be = {}
    for ref in CPI_IMAGES:
        be[f"ref {ref}"] = {
            "2012-2020": breakeven_arms(W, ref, "2012-01-25", "2020-12-31"),
            "2021-2026": breakeven_arms(W, ref, "2021-01-01"),
            "2012-2026": breakeven_arms(W, ref, "2012-01-25"),
        }
        r = be[f"ref {ref}"]
        ex.say(f"5y breakeven, CPI image {ref}: windows starting above it 2012-2020 {r['2012-2020']['n_above']} of {r['2012-2020']['n']}; "
               f"upper arm 2021-2026 {r['2021-2026']['up'][0]:+.3f} (t {r['2021-2026']['up'][2]:.1f}), "
               f"2012-2026 {r['2012-2026']['up'][0]:+.3f} (t {r['2012-2026']['up'][2]:.1f})")
    out["breakeven_5y"] = be
    ex.write_results(out, title="The United States: where the observational-equivalence effect could be seen (Appendix A)")


if __name__ == "__main__":
    main()
