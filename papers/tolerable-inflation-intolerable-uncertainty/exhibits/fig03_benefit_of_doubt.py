#!/usr/bin/env python3
"""Figure 3 of *Tolerable Inflation, Intolerable Uncertainty*: the benefit of the doubt, read on the professionals.

Paper: Vansteenberghe, E. (2026), *Tolerable Inflation, Intolerable Uncertainty*,
working paper, Banque de France (``vansteenberghe2026tolerable``), Section 3,
Figure 3 (``fig:benefit``), and the numbers of Appendix A.4 (``app:clocks``:
the renewal calibration and the re-basing).

The share of ECB SPF respondents whose longer-term (four-to-five-years-ahead)
HICP point forecast is at or above 2.2 per cent -- two tenths above the
announced number, so that the many points that moved from 1.6--1.9 to exactly
2.0 with the July 2021 strategy review do not count -- read from the round
files, against inflation's distance above the target (headline HICP minus
two, the mean of the last three prints known at each round's base month).
Dashed: the renewal law of motion of the appendix, dA/dt = r (1 - A) - A eta d_+
for the anchored share, run quarterly on the observed overshoot with the
departure rate eta and the re-anchoring rate r fitted by least squares on
2021Q3--2026Q3, the resting level being the 2016Q1--2021Q2 mean share. The
results file carries every number the paper prints from this construction:
the fit on the realized overshoot and on the expected gap (the consensus
one-year-ahead mean minus two), the core panel of 26 forecasters as a check,
the two earlier overshoot episodes as an out-of-sample check, the flow
shortfall and the stationary anchored share in the law's units, and the
concavity wedge; and the re-basing jump of the same appendix -- the average
excess of a re-based longer-term point over the target, read three ways on
2021Q1--2026Q3 -- with the feedback quantities it implies at the fitted rates
(the feedback rate eta zeta, the stability margin, the multiplier, the decay
of the residual overshoot and its half-life, on both clocks). The swap-window
curvature numbers of the appendix rest on licensed daily data and are carried
as printed, not computed.

Inputs:  the ECB-SPF round files (through ``load_ecb_panel`` and ``load_longer_term_points``);
         the ECB macro block (unbalanced), for headline HICP inflation.
Outputs: ``figures/fig03_benefit_of_doubt.{pdf,png}``, ``results/fig03_benefit_of_doubt.{json,md}``.

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use
this code, cite the paper above.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from _common import style
from scipy.optimize import minimize

from nu_measures import conventions as cv
from nu_measures import law
from nu_measures.exhibit import Exhibit, load_ecb_panel, load_longer_term_points, load_macro_block

THRESHOLD = 2.2  # per cent: two tenths above the announced number
FIT_WINDOW = (pd.Period("2021Q3", "Q"), pd.Period("2026Q3", "Q"))
FLOOR_WINDOW = (pd.Period("2016Q1", "Q"), pd.Period("2021Q2", "Q"))
FIGURE_START, HISTORY_START, SERIES_START = pd.Period("2019Q1", "Q"), pd.Period("2005Q1", "Q"), pd.Period("2002Q1", "Q")
CORE_PRE, CORE_SURGE = (pd.Period("2015Q1", "Q"), pd.Period("2021Q2", "Q")), (pd.Period("2021Q3", "Q"), pd.Period("2024Q2", "Q"))
EPISODES = {"2007-09": ("2007Q3", "2009Q4"), "2011-13": ("2011Q1", "2013Q4"), "2021-26": ("2021Q3", "2026Q3")}
EPISODE_BASELINES = {"2007-09": ("2005Q1", "2007Q2"), "2011-13": ("2009Q3", "2010Q4"), "2021-26": ("2019Q1", "2021Q2")}
#: Who counts in the share's denominator: ``"reporting"`` -- the respondents who gave a longer-term point, the
#: paper's definition -- or ``"all_rows"`` -- every respondent present in the longer-term block, a density
#: without a point counted as an anchored point, which is what an earlier version of the figure computed.
DENOMINATOR = "reporting"
OLD_RATES = (0.424, 5.886)  # (eta, r) of the earlier calibration the appendix compares with
REBASING_WINDOW = (pd.Period("2021Q1", "Q"), pd.Period("2026Q3", "Q"))
PSI = 0.9  # the pass-through at conventional calibrations (eq:passthrough): zeta = psi * Jbar
#: Appendix A.4, the swap-window curvature check: licensed daily data, carried as printed.
SWAP_CURVATURE = {"computed": False, "n_daily": 5282, "n_nonoverlapping": 84, "s_best": 3.4, "r2_best": 0.520, "r2_linear": 0.508,
                  "r2_nonoverlapping_linear": 0.474, "r2_nonoverlapping_s3": 0.462}
RC = {"font.family": "serif", "font.size": 9}


def path(eta: float, r: float, d: np.ndarray, a0: float, floor: float = 0.0) -> np.ndarray:
    """The de-anchored share under the renewal law, Euler steps of a quarter, from ``a0``."""
    A = [a0]
    for t in range(len(d) - 1):
        A.append(A[-1] + 0.25 * (eta * max(d[t], 0) * (1 - A[-1]) - r * (A[-1] - floor)))
    return np.array(A)


def fit(obs: np.ndarray, d: np.ndarray) -> tuple[float, float, float]:
    """Least-squares (eta, r) of the law on ``obs``, Nelder--Mead from nine starts; returns eta, r, RMSE."""

    def loss(th):
        return float(np.sum((obs - path(np.exp(th[0]), np.exp(th[1]), d, obs[0])) ** 2))

    best = min((minimize(loss, [np.log(e0), np.log(r0)], method="Nelder-Mead", options={"maxiter": 6000, "xatol": 1e-9, "fatol": 1e-13})
                for e0 in (0.03, 0.1, 0.4) for r0 in (0.2, 0.8, 3.0)), key=lambda r: r.fun)
    return float(np.exp(best.x[0])), float(np.exp(best.x[1])), float(np.sqrt(best.fun / len(obs)))


def rebasing_feedback(lt: pd.DataFrame, pan: pd.DataFrame, rates: dict, share_peak: float) -> dict:
    """The re-basing jump Jbar, read three ways, and the depletion game's numbers at the fitted rates."""
    W = lt.merge(pan[["FCT_SOURCE", "q", "M"]], on=["FCT_SOURCE", "q"], how="left")
    W = W[(W["q"] >= REBASING_WINDOW[0]) & (W["q"] <= REBASING_WINDOW[1])].sort_values(["FCT_SOURCE", "q"])
    D = W[W["LT"] >= THRESHOLD]
    out = {"window": [str(REBASING_WINDOW[0]), str(REBASING_WINDOW[1])], "psi": PSI,
           "excess_over_target": {"mean": float((D["LT"] - cv.TARGET).mean()), "median": float((D["LT"] - cv.TARGET).median()),
                                  "respondent_rounds": int(len(D))}}
    jumps = []
    for _, g in W.groupby("FCT_SOURCE"):
        g = g.sort_values("q").reset_index(drop=True)
        for i in range(1, len(g)):
            if g["LT"][i - 1] < THRESHOLD and g["LT"][i] >= THRESHOLD:
                jumps.append((g["FCT_SOURCE"][i], g["LT"][i] - g["LT"][i - 1]))
    C = pd.DataFrame(jumps, columns=["FCT_SOURCE", "jump"])
    out["move_at_crossing"] = {"mean": float(C["jump"].mean()), "median": float(C["jump"].median()), "crossings": int(len(C)),
                               "respondents": int(C["FCT_SOURCE"].nunique())}
    rows = []
    for _, g in W.dropna(subset=["M"]).groupby("q"):
        a, b = g[g["LT"] < THRESHOLD], g[g["LT"] >= THRESHOLD]
        if len(b) >= 3 and len(a) >= 3:
            rows.append((len(b), b["M"].mean() - a["M"].mean()))
    X = pd.DataFrame(rows, columns=["n_rebased", "diff"])
    out["within_round_one_year_difference"] = {"weighted": float((X["diff"] * X["n_rebased"] / X["n_rebased"].sum()).sum()),
                                               "unweighted": float(X["diff"].mean()), "rounds": int(len(X))}

    def theory(jbar, eta, r):
        zeta = PSI * jbar
        ez = eta * zeta
        return {"zeta": zeta, "eta_zeta": ez, "margin": r / ez, "multiplier": r / (r - ez), "decay": r - ez,
                "half_life_years": float(np.log(2) / (r - ez)), "half_life_reanchoring_years": float(np.log(2) / r),
                "residual_at_peak_share": zeta * share_peak, "mean_threshold_point_years": 1 / eta}

    jbar = out["excess_over_target"]["mean"]
    readings = [out["move_at_crossing"]["mean"], out["within_round_one_year_difference"]["weighted"], jbar]
    for clock, (eta, r) in rates.items():
        out[clock] = theory(jbar, eta, r)
        out[clock]["over_the_three_readings"] = {k: [min(theory(j, eta, r)[k] for j in readings), max(theory(j, eta, r)[k] for j in readings)]
                                                for k in ("margin", "multiplier")}
    return out


def compute(denominator: str, ex: Exhibit) -> dict:
    """The series, the fits and every derived number, under one denominator convention."""
    pan = load_ecb_panel().rename(columns={"Mean_spd": "M", "Variance_spd": "V"}).dropna(subset=["M", "V"])
    pan = pan[pan["V"] > 0].copy()
    pan["q"] = (pan["Date"] + pd.DateOffset(months=1)).dt.to_period("Q")
    qdate = pan.groupby("q")["Date"].first()
    de = (pan.groupby("q")["M"].mean() - cv.TARGET)
    lt = load_longer_term_points(keep_missing=(denominator == "all_rows")).rename(columns={"round": "q", "POINT": "LT"})
    npre = pan[(pan["q"] >= CORE_PRE[0]) & (pan["q"] <= CORE_PRE[1])].groupby("FCT_SOURCE").size()
    nsur = pan[(pan["q"] >= CORE_SURGE[0]) & (pan["q"] <= CORE_SURGE[1])].groupby("FCT_SOURCE").size()
    core = sorted(f for f in nsur.index if nsur[f] >= 8 and npre.get(f, 0) >= 12)
    hicp = load_macro_block(balanced=False)["HICP_YOY"].dropna()
    hicp.index = hicp.index.to_period("M")

    def realized_gap(q) -> float:
        m0 = pd.Timestamp(qdate[q]).to_period("M")
        last3 = [m for m in hicp.index if m0 - 2 <= m <= m0]
        return float(np.mean([hicp[m] for m in last3]) - cv.TARGET) if last3 else np.nan

    rows = []
    for q in sorted(pan["q"].unique()):
        s_ = lt[lt["q"] == q]
        if len(s_) == 0 or q < SERIES_START:
            continue
        c_ = s_[s_["FCT_SOURCE"].isin(core)]
        rows.append(dict(q=str(q), n_all=int(len(s_)), share_all=float((s_["LT"] >= THRESHOLD).mean()), n_core=int(len(c_)),
                         share_core=float((c_["LT"] >= THRESHOLD).mean()) if len(c_) else np.nan, dR=realized_gap(q), de=float(de[q])))
    S = pd.DataFrame(rows)
    S["qp"] = pd.PeriodIndex(S["q"], freq="Q")
    ex.say(f"{len(S)} rounds {S['q'].iloc[0]}..{S['q'].iloc[-1]}; respondents per round {S['n_all'].min()}-{S['n_all'].max()}; core panel {len(core)} forecasters")

    W = S[(S["qp"] >= FIT_WINDOW[0]) & (S["qp"] <= FIT_WINDOW[1])].reset_index(drop=True)
    obs = W["share_all"].to_numpy()
    eta_R, r_R, rmse_R = fit(obs, W["dR"].to_numpy())
    A_R = path(eta_R, r_R, W["dR"].to_numpy(), obs[0])
    eta_e, r_e, rmse_e = fit(obs, W["de"].to_numpy())
    eta_c, r_c, rmse_c = fit(W["share_core"].to_numpy(), W["dR"].to_numpy())
    floor = float(S[(S["qp"] >= FLOOR_WINDOW[0]) & (S["qp"] <= FLOOR_WINDOW[1])]["share_all"].mean())
    ex.say(f"realized clock: eta {eta_R:.3f} per point-year, r {r_R:.3f} per year (half-life {np.log(2) / r_R:.2f} y), RMSE {rmse_R:.3f}; "
           f"expected-gap clock: eta {eta_e:.3f}, r {r_e:.3f}, scale r/eta {r_e / eta_e:.2f}, RMSE {rmse_e:.3f}; core: eta {eta_c:.3f}, r {r_c:.3f}")
    H = S[S["qp"] >= HISTORY_START].reset_index(drop=True)
    A_hist = path(eta_R, r_R, H["dR"].to_numpy(), float(H["share_all"][0]), floor)
    M = S[S["qp"] >= FIGURE_START].reset_index(drop=True)
    A_main = path(eta_R, r_R, M["dR"].to_numpy(), float(M["share_all"][0]), floor)

    def peak(df, A, a, b):
        sel = (df["qp"] >= pd.Period(a, "Q")) & (df["qp"] <= pd.Period(b, "Q"))
        return float(df["share_all"][sel].max()), float(pd.Series(A)[sel].max())

    episodes = {}
    for k, (a, b) in EPISODES.items():
        o, f_ = peak(H, A_hist, a, b)
        ba, bb = EPISODE_BASELINES[k]
        base = float(H["share_all"][(H["qp"] >= pd.Period(ba, "Q")) & (H["qp"] <= pd.Period(bb, "Q"))].mean())
        episodes[k] = {"observed_peak": o, "fitted_peak": f_, "baseline": base}
    # consequences in the law's units: the expected gaps of the estimation sample
    sample = law.estimation_sample(law.round_aggregates(load_ecb_panel()))
    gpos = sample["gap"][sample["gap"] > 0]
    dmean, dmax = float(gpos.mean()), float(gpos.max())

    def shortfall(d, eta, r):
        return eta * d / (r + eta * d)

    def a_star(d, eta, r):
        return r / (r + eta * d)

    # the concavity wedge: the affine arm fitted on the survey's own gaps as a projection of the exact law
    dp = np.maximum(sample["gap"].to_numpy(), 0)
    Xa = np.column_stack([np.ones(len(dp)), np.maximum(-sample["gap"].to_numpy(), 0), dp])
    bx = np.linalg.lstsq(Xa, r_e * eta_e * dp / (r_e + eta_e * dp), rcond=None)[0]
    wedge = float(bx[2] / eta_e)

    feedback = rebasing_feedback(lt, pan, {"expected_gap_clock": (eta_e, r_e), "realized_clock": (eta_R, r_R)}, float(obs.max()))
    fb = feedback["expected_gap_clock"]
    ex.say(f"re-basing jump: Jbar {feedback['excess_over_target']['mean']:.3f} ({feedback['excess_over_target']['respondent_rounds']} respondent-rounds), "
           f"crossing {feedback['move_at_crossing']['mean']:.3f} ({feedback['move_at_crossing']['crossings']} by {feedback['move_at_crossing']['respondents']}), "
           f"within-round {feedback['within_round_one_year_difference']['weighted']:.3f} ({feedback['within_round_one_year_difference']['rounds']} rounds); "
           f"expected-gap clock: eta zeta {fb['eta_zeta']:.3f}, margin {fb['margin']:.2f}, multiplier {fb['multiplier']:.3f}, decay {fb['decay']:.3f} "
           f"(half-life {fb['half_life_years']:.2f} vs {fb['half_life_reanchoring_years']:.2f} y)")
    numbers = {
        "denominator": denominator,
        "rebasing_feedback": feedback,
        "threshold": THRESHOLD, "respondents_per_round": [int(S["n_all"].min()), int(S["n_all"].max())],
        "respondents_per_round_fit_window": [int(W["n_all"].min()), int(W["n_all"].max())],
        "share": {"2021Q3": float(obs[0]), "peak": float(obs.max()), "peak_round": W["q"][int(np.argmax(obs))],
                  "2024Q3": float(W["share_all"][W["q"] == "2024Q3"].iloc[0]), "last": float(obs[-1]), "last_round": W["q"].iloc[-1]},
        "core_panel": {"forecasters": len(core), "peak": float(np.nanmax(W["share_core"])), "peak_round": W["q"][int(np.nanargmax(W["share_core"]))],
                       "eta": eta_c, "r": r_c, "rmse": rmse_c},
        "realized_clock": {"eta": eta_R, "r": r_R, "rmse": rmse_R, "half_life_years": float(np.log(2) / r_R),
                           "fitted_peak": float(A_R.max()), "fitted_peak_round": W["q"][int(np.argmax(A_R))], "fitted_end": float(A_R[-1])},
        "expected_gap_clock": {"eta": eta_e, "r": r_e, "rmse": rmse_e, "scale_r_over_eta": r_e / eta_e},
        "floor_2016Q1_2021Q2": floor, "episodes": episodes,
        "expected_gaps": {"mean_positive": dmean, "max_positive": dmax, "rounds": int(len(sample))},
        "shortfall": {"at_mean": shortfall(dmean, eta_e, r_e), "at_1": shortfall(1.0, eta_e, r_e), "at_max": shortfall(dmax, eta_e, r_e),
                      "at_2.3": shortfall(2.3, eta_e, r_e), "old_rates_at_1.76": shortfall(1.76, *OLD_RATES)},
        "stationary_anchored_share": {"0.5": a_star(0.5, eta_e, r_e), "1": a_star(1.0, eta_e, r_e), "2": a_star(2.0, eta_e, r_e)},
        "concavity_wedge": {"value": wedge, "rounds": int(len(dp))},
    }
    return {"numbers": numbers, "S": S, "M": M, "A_main": A_main}


def main() -> None:
    ex = Exhibit(__file__)
    style(RC)
    main_run = compute(DENOMINATOR, ex)
    other = "reporting" if DENOMINATOR == "all_rows" else "all_rows"
    ex.say(f"--- the same construction with the {other} denominator:")
    other_run = compute(other, ex)
    M, A_main = main_run["M"], main_run["A_main"]

    t = M["qp"].dt.to_timestamp()
    fig, ax = plt.subplots(figsize=(7.2, 3.3))
    ax2 = ax.twinx()
    ax2.fill_between(t, 0, np.maximum(M["dR"], 0), color="0.88", zorder=0, label="inflation above the target, HICP minus 2 (right scale)")
    ax2.set_ylim(0, 16)
    ax2.set_yticks([0, 4, 8])
    ax2.set_ylabel("percentage points", fontsize=8)
    ax2.tick_params(labelsize=8)
    ax.set_zorder(ax2.get_zorder() + 1)
    ax.patch.set_visible(False)
    ax.plot(t, M["share_all"], "-", color="#1b7837", lw=1.9, marker="o", ms=3, label="share of forecasters whose longer-term point is at or above 2.2%")
    ax.plot(t, A_main, "--", color="#b2182b", lw=1.6, label="the renewal law of motion, fitted on 2021--26")
    ax.set_ylim(0, 0.5)
    ax.set_yticks([0, 0.1, 0.2, 0.3, 0.4, 0.5])
    ax.set_ylabel("share", fontsize=8)
    ax.tick_params(labelsize=8)
    ax.set_xlim(pd.Timestamp("2019-01-01"), pd.Timestamp("2026-10-01"))
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, frameon=False, fontsize=7.5, loc="upper left")
    ax.spines[["top"]].set_visible(False)
    ax2.spines[["top"]].set_visible(False)
    fig.tight_layout()
    ex.save_figure(fig)
    ex.write_results({**main_run["numbers"], "swap_curvature_carried_as_printed": SWAP_CURVATURE,
                      "series": main_run["S"].drop(columns="qp").to_dict(orient="records"),
                      f"with_the_{other}_denominator": other_run["numbers"]},
                     "Figure 3 — the benefit of the doubt, read on the professionals")


if __name__ == "__main__":
    main()
