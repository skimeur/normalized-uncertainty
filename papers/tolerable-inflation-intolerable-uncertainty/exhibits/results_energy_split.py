"""How much of the realized upper arm is energy: the footnote of Section 3, "The realized shadow".

Paper: Vansteenberghe, E. (2026), *Tolerable Inflation, Intolerable Uncertainty*,
working paper, Banque de France (``vansteenberghe2026tolerable``), Section 3,
paragraph "The realized shadow" (footnote on the energy share).

Not an exhibit: a register, as ``results_register.py``.

Monthly surprises of headline, energy and ex-energy HICP are the residuals of
autoregressions in the month-on-month log change with month dummies, the lag
order chosen by BIC up to twelve. The headline surprise is projected on the
two component surprises (no constant), which splits its square into an energy
part, an ex-energy part, their covariance and a remainder. Each part is
regressed on the two arms of the lagged year-on-year gap (HAC, twelve lags);
the energy part's and the ex-energy part's upper arms, as shares of the
headline's, are the footnote's 66 and 8 per cent.

Inputs:  ECB Data Portal ``HICP.M.U2.Y.000000.4F0.INX``, ``HICP.M.U2.Y.NRGY00.4F0.INX``
         and ``HICP.M.U2.Y.XE0000.4F0.INX`` (seasonally adjusted indices), through
         ``load_ecb_series``.
Outputs: ``results/results_energy_split.{json,md}``.

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use
this code, cite the paper above.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from nu_measures import conventions as cv
from nu_measures.exhibit import Exhibit, load_ecb_series

KEYS = {"headline": "HICP.M.U2.Y.000000.4F0.INX", "energy": "HICP.M.U2.Y.NRGY00.4F0.INX",
        "ex-energy": "HICP.M.U2.Y.XE0000.4F0.INX"}
START = pd.Period("1999-01", "M")
EPISODE = (pd.Period("2021-07", "M"), pd.Period("2023-12", "M"))
P_MAX, HAC_LAGS = 12, 12


def surprises(P: pd.Series, pmax: int = P_MAX) -> pd.Series:
    """Residuals of the BIC-best AR(p), p <= pmax, in 100 x log change with month dummies, on a common sample."""
    pi = 100 * np.log(P).diff().dropna()
    best = None
    for p in range(1, pmax + 1):
        X = pd.concat([pi.shift(k).rename(f"l{k}") for k in range(1, p + 1)], axis=1)
        M = pd.get_dummies(pi.index.month, drop_first=True).astype(float)
        M.index = pi.index
        M.columns = [f"m{c}" for c in M.columns]
        Z = pd.concat([pi.rename("y"), X, M], axis=1).dropna().iloc[pmax - p:]
        m = sm.OLS(Z["y"], sm.add_constant(Z.drop(columns="y"))).fit()
        if best is None or m.bic < best[0]:
            best = (m.bic, m.resid, p)
    return best[1]


def arms_fit(v: pd.Series, arms: pd.DataFrame, mask: pd.Series | None = None) -> dict:
    Z = pd.concat([v.rename("y"), arms], axis=1).dropna()
    if mask is not None:
        Z = Z[mask.reindex(Z.index).fillna(False).astype(bool)]
    m = sm.OLS(Z["y"], sm.add_constant(Z[["up", "dn"]])).fit(cov_type="HAC", cov_kwds={"maxlags": HAC_LAGS})
    return {k: [float(m.params[k]), float(m.bse[k]), float(m.tvalues[k])] for k in ("const", "up", "dn")} | {"n": int(m.nobs)}


def main() -> None:
    ex = Exhibit(__file__)
    P = {k: load_ecb_series(key) for k, key in KEYS.items()}
    P["energy"] = P["energy"][P["energy"].index >= pd.Period("1997-01", "M")]
    gap = 100 * (P["headline"] / P["headline"].shift(12) - 1) - cv.TARGET
    e = {k: surprises(v) for k, v in P.items()}
    Z = pd.concat([e["headline"].rename("H"), e["energy"].rename("E"), e["ex-energy"].rename("X")], axis=1).dropna()
    Z = Z[Z.index >= START]
    w = sm.OLS(Z["H"], Z[["E", "X"]]).fit()
    wE, wX = float(w.params["E"]), float(w.params["X"])
    parts = {"headline": Z["H"] ** 2, "energy part": (wE * Z["E"]) ** 2, "ex-energy part": (wX * Z["X"]) ** 2,
             "covariance part": 2 * wE * wX * Z["E"] * Z["X"]}
    parts["remainder"] = parts["headline"] - parts["energy part"] - parts["ex-energy part"] - parts["covariance part"]
    arms = pd.DataFrame({"up": gap.shift(1).clip(lower=0), "dn": (-gap.shift(1)).clip(lower=0)})
    outside = pd.Series(~((Z.index >= EPISODE[0]) & (Z.index <= EPISODE[1])), index=Z.index)

    full = {k: arms_fit(v, arms) for k, v in parts.items()}
    excl = {k: arms_fit(v, arms, outside) for k, v in parts.items()}
    share = {k: full[k]["up"][0] / full["headline"]["up"][0] for k in parts}
    share_excl = {k: excl[k]["up"][0] / excl["headline"]["up"][0] for k in parts}

    ex.say(f"surprises {Z.index.min()}-{Z.index.max()}, n {len(Z)}; weights energy {wE:.3f}, ex-energy {wX:.3f}, R2 {w.rsquared:.3f}")
    for k in parts:
        ex.say(f"{k:<16} upper arm {full[k]['up'][0]:+.4f} ({full[k]['up'][2]:.1f})  share of headline's {share[k]:.2f}"
               f"   without 2021-07..2023-12: {share_excl[k]:.2f}")
    ex.say(f"the footnote: energy part {100 * share['energy part']:.0f} per cent, ex-energy part {100 * share['ex-energy part']:.0f} per cent")
    ex.write_results({"weights": {"energy": wE, "ex-energy": wX, "R2": float(w.rsquared)}, "arms": full,
                      "arms_without_2021_23": excl, "share_of_headline_upper_arm": share,
                      "share_of_headline_upper_arm_without_2021_23": share_excl, "n": int(len(Z)),
                      "sources": KEYS}, title="The energy share of the realized upper arm (Section 3)")


if __name__ == "__main__":
    main()
