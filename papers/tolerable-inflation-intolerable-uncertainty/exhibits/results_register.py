#!/usr/bin/env python3
"""The numbers of Section 3 of *Tolerable Inflation, Intolerable Uncertainty*, on one sample.

Paper: Vansteenberghe, E. (2026), *Tolerable Inflation, Intolerable Uncertainty*,
working paper, Banque de France (``vansteenberghe2026tolerable``): the survey
law of Section 3 (``eq:lawsurvey``), the three-object decomposition, the
tests on the arms, the kink, the realized-inflation shadow
(``eq:lawrealized``), and the numbers of the introduction that come from them.

Not an exhibit: a register. Every number printed in the text from the ECB-SPF
law is computed here on the paper's one sample -- the rounds through 2026Q2
with the consensus inside [-1, 5] per cent (109 rounds) -- and written to the
results file, from which the paper page's key-numbers table is generated.

* The two-arm law on the average individual predictive variance W_t, on
  disagreement D_t and on the total mixture variance T_t: coefficients,
  Newey--West (four lags) standard errors, R2 against the symmetric form,
  the share of the total that is individual, the ratio b_+ / a that
  calibrates the fitted purge.
* Wald tests on the total, by subsample: b_- = 0 (the below-target side is
  flat) and b_- = b_+ (the symmetric form is adequate); the range of the
  overshoot by subsample; the split test on W at 2020Q1.
* The kink profile on W and its bootstrap (as in Figure 1), and on T.
* The realized shadow: an AR(1) on the quarterly euro-area HICP gap, the
  squared innovation on the two arms of the lagged gap, and the absolute
  innovation on the symmetric specification.
* The purge's own test: the round means of the purged series (symmetric,
  unit, fitted) regressed on the overshoot.

Inputs:  the ECB-SPF round files (through ``load_ecb_panel``); the ECB macro block (unbalanced) for HICP.
Outputs: ``results/results_register.{json,md}``.

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use
this code, cite the paper above.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from nu_measures import conventions as cv
from nu_measures import econometrics as ec
from nu_measures import law, measures
from nu_measures.exhibit import Exhibit, load_ecb_panel, load_macro_block

STAMPED_CUTOFF = pd.Timestamp("2026-07-01")  # the paper's cutoff for realized data: months before it
SUBSAMPLES = {"full": (None, None), "pre_2021": (None, "2021-01-01"), "from_2021": ("2021-01-01", None)}


def realized_shadow() -> dict:
    pi = load_macro_block(balanced=False)["HICP_YOY"].dropna()
    pi = pi[pi.index < STAMPED_CUTOFF]
    q = pi.resample("QE").mean()
    d = (q - cv.TARGET).dropna()
    y, x = d.iloc[1:].to_numpy(), d.iloc[:-1].to_numpy()
    rho = np.polyfit(x, y, 1)
    eps = y - (rho[0] * x + rho[1])
    sym = ec.hac_ols(eps**2, np.abs(x), lags=4)
    arms = law.arms_fit(eps**2, x, hac_lags=4)
    absolute = ec.hac_ols(np.abs(eps), np.abs(x), lags=4)
    return {"quarters": int(len(y)), "last_quarter": str(d.index[-1].to_period("Q")), "ar1_rho": float(rho[0]),
            "arms_on_squared_innovation": arms.summary_row(),
            "symmetric_on_squared_innovation": {"g": float(sym.params[1]), "se": float(sym.se[1]), "t": float(sym.t[1]), "r2": float(sym.r2)},
            "symmetric_on_absolute_innovation": {"g": float(absolute.params[1]), "se": float(absolute.se[1]), "t": float(absolute.t[1]), "r2": float(absolute.r2)}}


def main() -> None:
    ex = Exhibit(__file__)
    panel = load_ecb_panel()
    A = law.round_aggregates(panel)
    S = law.estimation_sample(A)
    R: dict = {"sample": {"rounds": int(len(S)), "first": str(S.index.min().date()), "last": str(S.index.max().date()),
                          "consensus_rule": list(cv.INDIVIDUAL_MEAN_TRIM), "last_round_included": "2026Q2"}}
    ex.say(f"estimation sample: {len(S)} rounds, {S.index.min():%Y-%m} to {S.index.max():%Y-%m}")
    fits = law.law_by_object(S)
    R["law"] = {}
    for k, label in (("W", "average individual variance"), ("D", "disagreement"), ("T", "total mixture variance")):
        f = fits[k]
        sym = ec.hac_ols(S[k].to_numpy(), np.abs(S["gap"].to_numpy()), lags=4)
        R["law"][k] = {**f.summary_row(), "r2_symmetric": float(sym.r2), "wald": law.wald_tests(f)}
        ex.say(f"{k} ({label}): a {f.a:.3f} ({f.se_a:.3f}) b- {f.b_minus:+.3f} ({f.se_b_minus:.3f}, t {f.t_b_minus:.2f}) "
               f"b+ {f.b_plus:+.3f} ({f.se_b_plus:.3f}, t {f.t_b_plus:.2f}) R2 {f.r2:.3f} (symmetric {sym.r2:.3f})")
    W = fits["W"]
    R["ratio_b_plus_over_a"] = {"W": W.r_plus, "W_se": W.r_plus_se, "T": fits["T"].r_plus}
    R["share_individual_of_total"] = float(S["W"].mean() / S["T"].mean())
    R["variation_explained_by_distance_pct"] = 100.0 * W.r2
    ex.say(f"ratio b+/a on W {W.r_plus:.3f} ({W.r_plus_se:.2f}); on T {fits['T'].r_plus:.2f}; individual share of the total {100 * R['share_individual_of_total']:.0f}%; "
           f"the distance explains {100 * W.r2:.0f}% of the variation in W")

    R["wald_by_subsample"] = {}
    for name, (lo, hi) in SUBSAMPLES.items():
        keep = np.ones(len(S), dtype=bool)
        if lo:
            keep &= np.asarray(S.index >= pd.Timestamp(lo))
        if hi:
            keep &= np.asarray(S.index < pd.Timestamp(hi))
        Ssub = S[keep]
        f = law.arms_fit(Ssub["T"].to_numpy(), Ssub["gap"].to_numpy())
        g = Ssub["gap"]
        R["wald_by_subsample"][name] = {"n": f.n, "b_minus": f.b_minus, "b_plus": f.b_plus, "r2": f.r2, "wald": law.wald_tests(f),
                                        "max_overshoot": float(max(g.max(), 0)), "max_undershoot": float(max((-g).max(), 0)),
                                        "rounds_above_target": int((g > 0).sum())}
        w = law.wald_tests(f)
        ex.say(f"  T, {name:<10} n {f.n:>3}: b- {f.b_minus:+.3f} b+ {f.b_plus:+.3f}; b-=0 p {w['b_minus_zero']['p_value']:.3f}; b-=b+ p {w['arms_equal']['p_value']:.2e}")
    st = law.split_test(S, "W", "2020-01-01")
    R["split_test_W_2020Q1"] = {"pre": st["pre"].summary_row(), "post": st["post"].summary_row(), "interaction": st["interaction"].as_dict(),
                                "wald_joint": st["wald_joint"], "p_joint": st["p_joint"], "z_ratio_difference": st["z_ratio_difference"],
                                "p_ratio_difference": st["p_ratio_difference"]}

    prof = law.kink_profile(S["W"].to_numpy(), S["mu"].to_numpy())
    boot = law.kink_bootstrap(S["W"].to_numpy(), S["mu"].to_numpy(), prof["grid"])
    prof_T = law.kink_profile(S["T"].to_numpy(), S["mu"].to_numpy())
    R["kink"] = {"W": {"c_hat": prof["c_hat"], "set95": list(prof["set95"]), "bootstrap90": list(boot["interval90"]), "gain_pct": prof["gain_pct"], "lr": prof["lr"]},
                 "T": {"c_hat": prof_T["c_hat"], "set95": list(prof_T["set95"])}}
    ex.say(f"kink on W {prof['c_hat']:.2f} [{prof['set95'][0]:.2f}, {prof['set95'][1]:.2f}], bootstrap [{boot['interval90'][0]:.2f}, {boot['interval90'][1]:.2f}]; on T {prof_T['c_hat']:.3f}")

    R["realized"] = realized_shadow()
    r = R["realized"]
    ex.say(f"realized shadow: rho {r['ar1_rho']:.3f}; arms b- {r['arms_on_squared_innovation']['b_minus']:+.3f} ({r['arms_on_squared_innovation']['se_b_minus']:.3f}) "
           f"b+ {r['arms_on_squared_innovation']['b_plus']:+.3f} ({r['arms_on_squared_innovation']['se_b_plus']:.3f}) R2 {r['arms_on_squared_innovation']['r2']:.3f} n {r['quarters']}; "
           f"|innovation| g {r['symmetric_on_absolute_innovation']['g']:.3f} (t {r['symmetric_on_absolute_innovation']['t']:.1f})")

    # the purge's own test: the round means of the purged series on the overshoot
    p = measures.add_nu(panel[panel["Date"] < pd.Timestamp(cv.FIT_MAX_PANEL_DATE)])
    p["NU_symmetric"] = p["sigma_spd"] / np.sqrt(1.0 + (p["Mean_spd"] - cv.TARGET).abs())
    q = p.groupby("Date")[["NU_symmetric", "NU_unit", "NU_fitted"]].mean().join(S[["gap"]], how="inner")
    dplus = np.maximum(q["gap"].to_numpy(), 0)
    R["purged_series_on_overshoot"] = {}
    for c in ("NU_symmetric", "NU_unit", "NU_fitted"):
        o = ec.hac_ols(q[c].to_numpy(), dplus, lags=4)
        R["purged_series_on_overshoot"][c] = {"slope": float(o.params[1]), "t": float(o.t[1]), "r2": float(o.r2)}
        ex.say(f"  {c:<13} on (d)+: slope {o.params[1]:+.4f} (t {o.t[1]:+.2f}) R2 {o.r2:.3f}")
    ex.write_results(R, "The numbers of Section 3, on one sample")


if __name__ == "__main__":
    main()
