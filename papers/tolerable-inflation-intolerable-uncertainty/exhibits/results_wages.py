"""The table of Section 3, "Wages, and the flat lower arm": the arms of the gap on squared wage surprises.

Paper: Vansteenberghe, E. (2026), *Tolerable Inflation, Intolerable Uncertainty*,
working paper, Banque de France (``vansteenberghe2026tolerable``), Section 3,
paragraph "Wages, and the flat lower arm" (an in-text table and its footnote).

Not an exhibit: a register, as ``results_register.py``.

Negotiated wage growth (the ECB indicator, annual rate, quarterly) is projected
on its own two lags and on the two arms of the gap; the squared residuals are
then regressed on the same arms. Two rows: the realized gap of the previous
quarter (HICP headline, year on year, quarterly average, less 2) and the
expected gap of the previous survey round (ECB-SPF consensus less 2). HAC
standard errors with four lags. The printed columns are the upper arm, the
lower arm and their difference, with t-statistics.

Inputs:  ECB Data Portal ``STS.Q.I9.N.INWR.000000.3.ANR`` (negotiated wages) and
         ``HICP.M.U2.Y.000000.4F0.INX`` (headline index), through ``load_ecb_series``;
         the ECB-SPF round files (through ``load_ecb_panel``).
Outputs: ``results/results_wages.{json,md}``.

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use
this code, cite the paper above.
"""

from __future__ import annotations

import pandas as pd
import statsmodels.api as sm

from nu_measures import conventions as cv
from nu_measures.exhibit import Exhibit, load_ecb_panel, load_ecb_series

WAGES = "STS.Q.I9.N.INWR.000000.3.ANR"
HEADLINE = "HICP.M.U2.Y.000000.4F0.INX"
SURVEY_BEFORE = "2026-04-01"  # rounds through 2026Q2 (panel Date before April 2026): the 109-round sample
AR_LAGS, HAC_LAGS = 2, 4


def survey_quarterly() -> pd.DataFrame:
    """The survey's expected gap by round, dated at the quarter in which the round is conducted."""
    d = load_ecb_panel().rename(columns={"Mean_spd": "M", "Variance_spd": "V"}).dropna(subset=["M", "V"])
    d = d[(d["V"] > 0) & (d["Date"] < SURVEY_BEFORE)]
    S = d.groupby("Date").agg(mu=("M", "mean"))
    lo, hi = cv.INDIVIDUAL_MEAN_TRIM  # the [-1, 5] round rule on the consensus
    S = S[(S["mu"] >= lo) & (S["mu"] <= hi)]
    S.index = pd.PeriodIndex(S.index, freq="M")
    S["up"] = (S["mu"] - cv.TARGET).clip(lower=0)
    S["dn"] = (cv.TARGET - S["mu"]).clip(lower=0)
    S.index = (S.index + 1).asfreq("Q")  # Date is the last observed month; the round is held the month after
    return S


def hac_ols(y: pd.Series, X: pd.DataFrame):
    Z = pd.concat([y.rename("y"), X], axis=1).dropna()
    return sm.OLS(Z["y"], sm.add_constant(Z.drop(columns="y"))).fit(cov_type="HAC", cov_kwds={"maxlags": HAC_LAGS})


def main() -> None:
    ex = Exhibit(__file__)
    w = load_ecb_series(WAGES)
    w = w[w.index >= pd.Period("1998Q1", "Q")]
    P = load_ecb_series(HEADLINE)
    gap_q = (100 * (P / P.shift(12) - 1) - cv.TARGET).resample("Q").mean()
    S = survey_quarterly()

    base = pd.concat([w.shift(k).rename(f"w_l{k}") for k in range(1, AR_LAGS + 1)], axis=1)
    rows = {
        "realized gap, previous quarter": pd.DataFrame({"up": gap_q.shift(1).clip(lower=0), "dn": (-gap_q.shift(1)).clip(lower=0)}),
        "expected gap (survey), previous round": pd.DataFrame({"up": S["up"].shift(1), "dn": S["dn"].shift(1)}),
    }
    out = {}
    ex.say("negotiated wages: squared AR(2) surprises on the arms of the gap, HAC(4); coefficient (t)")
    for name, X in rows.items():
        mean = hac_ols(w, pd.concat([base, X], axis=1))
        e2 = (mean.resid ** 2).rename("e2")
        var = hac_ols(e2, X)
        diff = var.t_test("up - dn = 0")
        rec = {
            "upper_arm": [float(var.params["up"]), float(var.bse["up"]), float(var.tvalues["up"])],
            "lower_arm": [float(var.params["dn"]), float(var.bse["dn"]), float(var.tvalues["dn"])],
            "upper_minus_lower": [float(diff.effect.squeeze()), float(diff.sd.squeeze()), float(diff.tvalue.squeeze())],
            "n": int(var.nobs),
            "sample": f"{e2.index.min()}-{e2.index.max()}",
        }
        out[name] = rec
        u, lo, df = rec["upper_arm"], rec["lower_arm"], rec["upper_minus_lower"]
        ex.say(f"{name}: upper {u[0]:+.3f} ({u[2]:.1f}), lower {lo[0]:+.3f} ({lo[2]:.1f}), "
               f"upper - lower {df[0]:.3f} ({df[2]:.1f}), n {rec['n']}")
    out["source"] = {"wages": WAGES, "headline": HEADLINE, "survey": "ECB-SPF rounds through 2026Q2"}
    ex.write_results(out, title="Wages: the arms of the gap on squared wage surprises (Section 3)")


if __name__ == "__main__":
    main()
