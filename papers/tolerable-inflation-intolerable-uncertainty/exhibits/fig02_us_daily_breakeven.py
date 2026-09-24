#!/usr/bin/env python3
"""Figure 2 of *Tolerable Inflation, Intolerable Uncertainty*: the announcement in the daily market.

Paper: Vansteenberghe, E. (2026), *Tolerable Inflation, Intolerable Uncertainty*,
working paper, Banque de France (``vansteenberghe2026tolerable``), Section 3,
Figure 2 (``fig:usdaily``) and the footnote of the same section.

The five-year TIPS breakeven (FRED ``T5YIE``) before and after the FOMC's
announcement of a numerical objective on 25 January 2012. Each point is one
non-overlapping sixty-three-day window: the breakeven at the window start
against the forward realized variance, the annualized mean squared daily
change over the sixty-three trading days ahead (the euro-area swap rung's
convention). Per era: the profiled free kink (grid from the 10th to the 90th
percentile of the breakeven, step 0.01) with a nonparametric bootstrap over
windows (1,000 draws, one stream seeded 20260819 across the bootstraps, in
the order the paper reports them); the two-arm fits at the imposed reference
2.4 (the CPI image of the 2 per cent PCE objective) and at 2.3 and 2.5, with
Newey--West standard errors at one lag; the 2008--09 TIPS liquidity
dislocation handled as a dummy or dropped; the pooled post-2012 interaction
test; the daily overlapping fits (Newey--West at sixty-three lags and at one),
reported as overlap-inflated and not used for inference; and the ten-year breakeven (``T10YIE``) as a check.
Every number of the figure and of the footnote is written to the results file.

Inputs:  FRED ``T5YIE`` and ``T10YIE`` (``$NU_DATA_DIR/fred/``; fetched when absent).
Outputs: ``figures/fig02_us_daily_breakeven.{pdf,png}``, ``results/fig02_us_daily_breakeven.{json,md}``.

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use
this code, cite the paper above.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from _common import style

from nu_measures import econometrics as ec
from nu_measures import law
from nu_measures.exhibit import Exhibit, load_fred

ANNOUNCE = pd.Timestamp("2012-01-25")
CRISIS = (pd.Timestamp("2008-07-01"), pd.Timestamp("2009-06-30"))
WINDOW = 63  # trading days
REFERENCE = 2.4  # the CPI image of the 2 per cent PCE objective
BAND = (2.3, 2.5)
SEED, DRAWS = 20260819, 1000
RC = {"font.family": "serif", "font.serif": ["DejaVu Serif"], "mathtext.fontset": "cm", "font.size": 9.0, "axes.linewidth": 0.6}
C_PRE, C_POST, C_CR = "#e08214", "#2166ac", "0.62"


def daily(series: pd.Series) -> pd.DataFrame:
    """The daily breakeven with its forward realized variance, and the era and crisis flags."""
    be = series.to_numpy(dtype=float)
    rv_back = 252.0 * pd.Series(np.diff(be, prepend=np.nan) ** 2).rolling(WINDOW).mean().to_numpy()
    rv_fwd = np.full(len(be), np.nan)
    rv_fwd[:-WINDOW] = rv_back[WINDOW:]
    out = pd.DataFrame({"date": series.index, "be": be, "rv": rv_fwd}).dropna()
    out["post"] = out["date"] >= ANNOUNCE
    # a window starting at t covers t+1..t+63: it is a crisis window if it starts inside [crisis start - 3 months, crisis end]
    out["crisis_win"] = (out["date"] >= CRISIS[0] - pd.DateOffset(months=3)) & (out["date"] <= CRISIS[1])
    return out


def nonoverlap(d: pd.DataFrame) -> pd.DataFrame:
    """Every sixty-third window of each era."""
    keep = [sub.reset_index(drop=True).iloc[::WINDOW] for _, sub in d.groupby("post")]
    return pd.concat(keep).sort_values("date").reset_index(drop=True)


def kink_grid(mu: np.ndarray) -> np.ndarray:
    """The candidate kinks: the 10th to the 90th percentile of the breakeven, step 0.01."""
    return np.arange(np.quantile(mu, 0.10), np.quantile(mu, 0.90) + 1e-9, 0.01)


def free_kink(S: pd.DataFrame, rng: np.random.Generator) -> dict:
    """The profiled kink of an era and its bootstrap; each draw profiles over its own resample's grid."""
    mu, y = S["be"].to_numpy(), S["rv"].to_numpy()
    prof = law.kink_profile(y, mu, grid=kink_grid(mu))
    draws = np.empty(DRAWS)
    for k in range(DRAWS):
        i = rng.integers(0, len(S), len(S))
        draws[k] = law.kink_profile(y[i], mu[i], grid=kink_grid(mu[i]))["c_hat"]
    lo, hi = np.percentile(draws, [5, 95])
    return {"n": int(len(S)), "c_hat": prof["c_hat"], "interval90": [float(lo), float(hi)],
            "grid": [float(prof["grid"].min()), float(prof["grid"].max())]}


def arms_at(S: pd.DataFrame, c: float, crisis_dummy: bool = False, lags: int = 1) -> dict:
    g = S["be"].to_numpy() - c
    cols = [np.maximum(-g, 0), np.maximum(g, 0)]
    names = ["b_minus", "b_plus"]
    if crisis_dummy and S["crisis_win"].any():  # the post-2012 era has no crisis window: the dummy would be a zero column
        cols.append(S["crisis_win"].to_numpy(dtype=float))
        names.append("crisis")
    r = ec.hac_ols(S["rv"].to_numpy(), np.column_stack(cols), lags=lags, names=("a", *names))
    out = {"n": r.n, "c": c, "r2": float(r.r2)}
    for i, k in enumerate(("a", *names)):
        out[k] = float(r.params[i])
        out[f"t_{k}"] = float(r.t[i]) if np.isfinite(r.t[i]) else None
    return out


def main() -> None:
    ex = Exhibit(__file__)
    style(RC)
    rng = np.random.default_rng(SEED)
    d5 = daily(load_fred("T5YIE"))
    w5 = nonoverlap(d5)
    pre, post = w5[~w5["post"]], w5[w5["post"]]
    prex, precr = pre[~pre["crisis_win"]], pre[pre["crisis_win"]]
    pre_days = d5[~d5["post"]]
    ex.say(f"T5YIE: {len(d5)} days {d5['date'].min().date()}..{d5['date'].max().date()}; windows pre {len(pre)} post {len(post)}; "
           f"pre-announcement days {len(pre_days)}, share above {REFERENCE}: {(pre_days['be'] > REFERENCE).mean():.2f}")
    kinks = {"pre_all": free_kink(pre, rng), "post_all": free_kink(post, rng), "pre_crisis_dropped": free_kink(prex, rng)}
    for k, v in kinks.items():
        ex.say(f"  free kink {k:<20} n {v['n']:>3}  c_hat {v['c_hat']:.2f}  90% [{v['interval90'][0]:.2f}, {v['interval90'][1]:.2f}]")
    fits = {"pre_baseline": arms_at(pre, REFERENCE), "pre_crisis_dummy": arms_at(pre, REFERENCE, True),
            "pre_crisis_dropped": arms_at(prex, REFERENCE), "post_baseline": arms_at(post, REFERENCE),
            "post_crisis_dummy": arms_at(post, REFERENCE, True)}
    for c in BAND:
        fits[f"post_c{c}"] = arms_at(post, c)
        fits[f"pre_crisis_dropped_c{c}"] = arms_at(prex, c)
    for k, v in fits.items():
        ex.say(f"  {k:<26} n {v['n']:>4}  b- {v['b_minus']:+.3f} (t {v['t_b_minus']:+.1f})  b+ {v['b_plus']:+.3f} (t {v['t_b_plus']:+.1f})  R2 {v['r2']:.2f}")
    g = w5["be"].to_numpy() - REFERENCE
    P = w5["post"].to_numpy(dtype=float)
    X = np.column_stack([np.maximum(-g, 0), np.maximum(g, 0), P, P * np.maximum(-g, 0), P * np.maximum(g, 0), w5["crisis_win"].to_numpy(dtype=float)])
    inter = ec.hac_ols(w5["rv"].to_numpy(), X, lags=1, names=("a", "b_minus", "b_plus", "post", "post_x_below", "post_x_above", "crisis"))
    # the daily overlapping fits: with Newey--West at 63 lags, and at one lag (what the paper's footnote quotes)
    daily_fits = {}
    for lags in (WINDOW, 1):
        for k, S in (("pre_crisis_dropped", d5[(~d5["post"]) & (~d5["crisis_win"])]), ("post", d5[d5["post"]])):
            v = daily_fits[f"{k}_hac{lags}"] = arms_at(S, REFERENCE, lags=lags)
            ex.say(f"  daily overlapping {k:<20} HAC({lags:>2}) n {v['n']:>5}  b+ {v['b_plus']:+.3f} (t {v['t_b_plus']:+.1f}), overlap-inflated")
    d10 = daily(load_fred("T10YIE"))
    w10 = nonoverlap(d10)
    pre10, post10 = w10[~w10["post"]], w10[w10["post"]]
    ten = {"pre_crisis_dropped_kink": free_kink(pre10[~pre10["crisis_win"]], rng), "post_kink": free_kink(post10, rng),
           "post_baseline": arms_at(post10, REFERENCE), "pre_crisis_dropped": arms_at(pre10[~pre10["crisis_win"]], REFERENCE)}
    ex.say(f"  T10YIE: post kink {ten['post_kink']['c_hat']:.2f} [{ten['post_kink']['interval90'][0]:.2f}, {ten['post_kink']['interval90'][1]:.2f}]")

    # the figure: each era's arms hinged at its own profiled kink (OLS), the intervals from the bootstrap;
    # the kinks and intervals are drawn at the two decimals the paper reports them with
    k_pre = {"c_hat": round(kinks["pre_crisis_dropped"]["c_hat"], 2), "interval90": [round(v, 2) for v in kinks["pre_crisis_dropped"]["interval90"]]}
    k_post = {"c_hat": round(kinks["post_all"]["c_hat"], 2), "interval90": [round(v, 2) for v in kinks["post_all"]["interval90"]]}

    def hinged(S, c):
        g = S["be"].to_numpy() - c
        X = np.column_stack([np.ones(len(S)), np.maximum(-g, 0), np.maximum(g, 0)])
        return np.linalg.lstsq(X, S["rv"].to_numpy(), rcond=None)[0]

    b_pre, b_post = hinged(prex, k_pre["c_hat"]), hinged(post, k_post["c_hat"])
    fig, axes = plt.subplots(1, 2, figsize=(6.35, 2.75), sharey=True, sharex=True)
    for a in axes:
        a.axvspan(BAND[0], BAND[1], color="0.90", zorder=0)
        a.axvline(2.0, color="0.75", lw=0.7, zorder=1)
        a.set_xlim(0.55, 3.25)
        a.set_ylim(0, 2.45)
        a.set_xlabel("5-year breakeven at the window start ($\\%$)", fontsize=8.3)
        a.tick_params(labelsize=8.0)
    ax = axes[0]
    ax.scatter(precr["be"], precr["rv"].clip(upper=2.38), s=22, marker="x", color=C_CR, linewidths=1.0, zorder=3)
    ax.scatter(prex["be"], prex["rv"], s=16, marker="^", facecolors="none", edgecolors=C_PRE, linewidths=0.9, zorder=4)
    xs = np.linspace(prex["be"].min(), prex["be"].max(), 120)
    ax.plot(xs, b_pre[0] + b_pre[1] * np.maximum(k_pre["c_hat"] - xs, 0) + b_pre[2] * np.maximum(xs - k_pre["c_hat"], 0),
            color=C_PRE, lw=1.6, ls=(0, (4, 2)), zorder=5)
    ax.axvline(k_pre["c_hat"], color=C_PRE, lw=0.9, ls=":", zorder=2)
    ax.set_title("(a) before the announcement (2003--2011)", fontsize=8.6)
    ax.set_ylabel("realized variance, 63 days ahead", fontsize=8.3)
    ax.text(0.66, 2.36, f"free kink ${k_pre['c_hat']:.2f}$ $[{k_pre['interval90'][0]:.2f},\\,{k_pre['interval90'][1]:.2f}]$: wanders",
            color=C_PRE, fontsize=7.6, va="top")
    ax.text(0.66, 2.16, "2008--09 windows ($\\times$) excluded;", color="0.45", fontsize=7.0, va="top")
    ax.text(0.66, 2.00, f"one at ${precr['rv'].max():.1f}$ above the frame", color="0.45", fontsize=7.0, va="top")
    ax.text(2.40, 0.88, "CPI image band ($2.3$--$2.5$)", rotation=90, fontsize=6.6, color="0.42", ha="center", va="bottom")
    ax = axes[1]
    ax.scatter(post["be"], post["rv"], s=13, marker="o", facecolors="none", edgecolors=C_POST, linewidths=0.9, zorder=4)
    xs = np.linspace(post["be"].min(), post["be"].max(), 120)
    ax.plot(xs, b_post[0] + b_post[1] * np.maximum(k_post["c_hat"] - xs, 0) + b_post[2] * np.maximum(xs - k_post["c_hat"], 0),
            color=C_POST, lw=1.7, zorder=5)
    ax.axvspan(k_post["interval90"][0], k_post["interval90"][1], color=C_POST, alpha=0.10, zorder=1)
    ax.axvline(k_post["c_hat"], color=C_POST, lw=0.9, ls=":", zorder=2)
    ax.set_title("(b) after the announcement (2012--2026)", fontsize=8.6)
    ax.text(0.66, 2.36, f"free kink ${k_post['c_hat']:.2f}$ $[{k_post['interval90'][0]:.2f},\\,{k_post['interval90'][1]:.2f}]$:",
            color=C_POST, fontsize=7.6, va="top")
    ax.text(0.66, 2.18, "the CPI image of $2\\%$ PCE,", color=C_POST, fontsize=7.6, va="top")
    ax.text(0.66, 2.00, "excluding $2$ itself", color=C_POST, fontsize=7.6, va="top")
    fig.tight_layout(w_pad=1.2)
    ex.save_figure(fig)
    ex.write_results({
        "T5YIE": {"days": int(len(d5)), "first": str(d5["date"].min().date()), "last": str(d5["date"].max().date()),
                  "windows_pre": int(len(pre)), "windows_post": int(len(post)), "windows_pre_crisis": int(len(precr)),
                  "pre_announcement_days": int(len(pre_days)), "share_pre_days_above_reference": float((pre_days["be"] > REFERENCE).mean()),
                  "share_post_days_above_reference": float((d5[d5["post"]]["be"] > REFERENCE).mean()),
                  "crisis_window_max_rv": float(precr["rv"].max())},
        "free_kinks": kinks, "arms_nonoverlapping_hac1": fits, "post2012_interactions_pooled": inter.as_dict(),
        "daily_overlapping_overlap_inflated": daily_fits, "T10YIE": ten,
        "figure": {"pre_arms_at_kink": [float(x) for x in b_pre], "post_arms_at_kink": [float(x) for x in b_post]},
        "conventions": {"announcement": str(ANNOUNCE.date()), "window_days": WINDOW, "reference": REFERENCE, "band": list(BAND),
                        "crisis": [str(c.date()) for c in CRISIS], "bootstrap": {"draws": DRAWS, "seed": SEED}},
    }, "Figure 2 — the announcement in the daily market")


if __name__ == "__main__":
    main()
