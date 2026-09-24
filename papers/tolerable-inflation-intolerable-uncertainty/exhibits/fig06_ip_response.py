#!/usr/bin/env python3
"""Figure 6 of *Tolerable Inflation, Intolerable Uncertainty*: industrial production after an uncertainty shock.

Paper: Vansteenberghe, E. (2026), *Tolerable Inflation, Intolerable Uncertainty*,
working paper, Banque de France (``vansteenberghe2026tolerable``), Section 3,
Figure 6 (``fig:rawnu``) and the vector-autoregression paragraph with its
footnote.

A quarterly euro-area system -- the policy-uncertainty index, an uncertainty
measure, HICP inflation, the deposit facility rate, unemployment and log
industrial production -- identified recursively, lag order by the Akaike
criterion over one to three lags, horizon eight quarters, ninety-percent
asymptotic bands. The shock is either the raw survey dispersion (the round
mean of the individual one-year predictive standard deviations, the numerator
of NU) or Normalized Uncertainty at the fitted ratio. The figure contrasts, on
the sample ending in 2019Q4, the baseline ordering (shock variable second)
with the above-anchor distance (pi - 2)_+ ordered ahead of the shock -- the
recursive control for the distance. The results file carries every variant
the paragraph and its footnote quote: the linear level ordered first, the
distance at the estimated anchor 1.96, the series partialled on the arms, the
measure ordered last, the lag order forced to 1, 2 and 3, the system without
the policy-uncertainty index, the seven-variable system with growth
uncertainty, the variance- and median-based raw alternates, and the full
sample. No causal reading is claimed: these are conditional covariances.

Inputs:  the ECB-SPF round files (through ``load_ecb_panel`` and ``load_growth_panel``);
         the EPU workbook; the ECB macro block (balanced, complete quarters).
Outputs: ``figures/fig06_ip_response.{pdf,png}``, ``results/fig06_ip_response.{json,md}``.
Sample:  quarters 2000Q1--2019Q4 for the figure (80); the full joined sample for the full-sample runs.

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use
this code, cite the paper above.
"""

from __future__ import annotations

import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from _common import style
from statsmodels.tsa.api import VAR

from nu_measures import conventions as cv
from nu_measures import measures
from nu_measures.exhibit import (
    Exhibit,
    load_ecb_panel,
    load_epu,
    load_growth_panel,
    load_macro_block,
)

H, Z90 = 8, 1.645
PRE_END = pd.Timestamp("2020-01-01")
ANCHOR, ANCHOR_ESTIMATED = cv.TARGET, 1.96
MEASURES = ["EPU", "NGU", "NU", "RAWSD_R", "RAWVAR", "RAWVAR_MED"]
PRINTED_FULL_SAMPLE_END = "2025Q4"  # the manuscript's full sample stopped where its micro-moment file did
RC = {"font.family": "serif", "font.serif": ["DejaVu Serif"], "mathtext.fontset": "cm", "font.size": 9.0, "axes.linewidth": 0.6}
C_DIST, C_BASE = "#2166ac", "#e08214"


def assemble() -> pd.DataFrame:
    """The quarterly system: macro block plus the uncertainty measures, z-scored on the joined sample."""
    panel = load_ecb_panel()
    nu = measures.quarterly(measures.nu_series(panel)).rename(columns={"raw_sd": "RAWSD_R", "NU_fitted": "NU"})
    p = panel.dropna(subset=["Mean_spd", "Variance_spd"])
    p = p[p["Variance_spd"] > 0].copy()
    p["Q"] = (p["Date"] + pd.DateOffset(months=1)).dt.to_period("Q")
    raw = p.groupby("Q").agg(RAWVAR=("Variance_spd", "mean"), RAWVAR_MED=("Variance_spd", "median"))
    g = load_growth_panel()
    g["Q"] = pd.to_datetime(g["Date"]).dt.to_period("Q")
    ngu = g.groupby("Q")["NGU"].mean().rename("NGU")
    unc = nu[["RAWSD_R", "NU"]].join(load_epu(), how="inner").join(raw, how="inner").join(ngu, how="inner")
    unc.index = unc.index.astype(str)

    m = load_macro_block(balanced=True)
    full_q = m.groupby(m.index.to_period("Q")).size()
    keep = full_q[full_q == 3].index  # complete quarters only
    q = pd.DataFrame({"DFR": m["DFR"].resample("QE").last(), "UNEMP": m["UNRATE"].resample("QE").mean(),
                      "logIP": m["logIP"].resample("QE").mean(), "INFL": m["HICP_YOY"].resample("QE").mean()}).dropna()
    q = q[q.index.to_period("Q").isin(keep)]
    q["Q"] = q.index.to_period("Q").astype(str)
    df = q.reset_index().merge(unc, left_on="Q", right_index=True, how="inner").set_index("TIME_PERIOD").sort_index()
    for c in MEASURES:
        df[c] = (df[c] - df[c].mean()) / df[c].std()
    return df.dropna(subset=["DFR", "UNEMP", "logIP", "INFL"] + MEASURES)


def with_distance(d: pd.DataFrame, anchor: float) -> pd.DataFrame:
    d = d.copy()
    gap = d["INFL"] - anchor
    d["DPLUS"], d["DABS"] = np.maximum(gap, 0.0), gap.abs()
    return d


def partialled(d: pd.DataFrame, x: str, anchor: float) -> tuple[np.ndarray, float]:
    """The measure's residual on the law's two arms, OLS on this sample, standardised."""
    gap = d["INFL"] - anchor
    Xm = np.column_stack([np.ones(len(d)), np.maximum(gap, 0), np.maximum(-gap, 0)])
    y = d[x].to_numpy()
    beta = np.linalg.lstsq(Xm, y, rcond=None)[0]
    resid = y - Xm @ beta
    return (resid - resid.mean()) / resid.std(), float(1 - resid.var() / y.var())


def run(d: pd.DataFrame, order: tuple[str, ...], shock: str, p_force: int | None = None, responses=("logIP", "UNEMP")) -> dict:
    """One system: the orthogonalised responses to a one-s.d. shock, cumulated over quarters 1..8, in per cent."""
    X = d[list(order)].dropna()
    if p_force is None:
        sel = VAR(X).select_order(maxlags=3).selected_orders
        p = int(max(1, sel.get("aic", 3) or 3))
    else:
        p = p_force
    res = VAR(X).fit(p)
    irf = res.irf(H)
    se = irf.stderr(orth=True)
    si = list(order).index(shock)
    out = {"order": list(order), "shock": shock, "p": p, "nobs": int(res.nobs)}
    for r in responses:
        ri = list(order).index(r)
        path, s = irf.orth_irfs[:, ri, si] * 100.0, se[:, ri, si] * 100.0
        out[r] = {"cum_pct": float(path[1:].sum()), "away": [k for k in range(1, H + 1) if abs(path[k]) > Z90 * s[k]],
                  "path_pct": [float(v) for v in path], "se_pct": [float(v) for v in s]}
    return out


def say_run(ex: Exhibit, tag: str, o: dict) -> None:
    ip = o["logIP"]
    ex.say(f"  {tag:<44} p={o['p']} n={o['nobs']:<3} cum(logIP) {ip['cum_pct']:+.2f}% away@{ip['away'] or '-'}")


def main() -> None:
    warnings.filterwarnings("ignore")
    ex = Exhibit(__file__)
    style(RC)
    df = assemble()
    pre = with_distance(df[df.index < PRE_END], ANCHOR)
    ex.say(f"joined sample {df.index.min():%Y-%m}..{df.index.max():%Y-%m} n={len(df)}; before 2020 n={len(pre)}")
    if len(pre) != 80:
        raise SystemExit(f"the pre-2020 sample has {len(pre)} quarters, not 80")

    def base(x):
        return ("EPU", x, "INFL", "DFR", "UNEMP", "logIP")

    R: dict = {"figure": {}, "pre2020": {}, "full": {}}
    ex.say("baseline [EPU, X, INFL, DFR, UNEMP, logIP] and distance-first [EPU, D+, X, ...], before 2020:")
    for x in ("RAWSD_R", "NU"):
        R["figure"][f"{x}_baseline"] = run(pre, base(x), x)
        R["figure"][f"{x}_distance_first"] = run(pre, ("EPU", "DPLUS", x, "DFR", "UNEMP", "logIP"), x)
        say_run(ex, f"{x} baseline", R["figure"][f"{x}_baseline"])
        say_run(ex, f"{x} distance first", R["figure"][f"{x}_distance_first"])
    ex.say("the checks, before 2020:")
    for x in ("RAWSD_R", "NU", "RAWVAR", "RAWVAR_MED"):
        R["pre2020"][f"{x}_level_first"] = run(pre, ("EPU", "INFL", x, "DFR", "UNEMP", "logIP"), x)
        R["pre2020"][f"{x}_abs_distance_first"] = run(pre, ("EPU", "DABS", x, "DFR", "UNEMP", "logIP"), x)
        pre[f"{x}_T"], r2 = partialled(pre, x, ANCHOR)
        R["pre2020"][f"{x}_partialled_on_arms"] = {**run(pre, ("EPU", f"{x}_T", "INFL", "DFR", "UNEMP", "logIP"), f"{x}_T"), "r2_on_arms": r2}
        R["pre2020"][f"{x}_ordered_last"] = run(pre, ("EPU", "INFL", "DFR", "UNEMP", "logIP", x), x)
        R["pre2020"][f"{x}_without_epu"] = run(pre, (x, "INFL", "DFR", "UNEMP", "logIP"), x)
        R["pre2020"][f"{x}_with_ngu_7var"] = run(pre, ("EPU", "NGU", x, "INFL", "DFR", "UNEMP", "logIP"), x)
        for p in (1, 2, 3):
            R["pre2020"][f"{x}_p{p}"] = run(pre, base(x), x, p_force=p)
        if x in ("RAWVAR", "RAWVAR_MED"):
            R["pre2020"][f"{x}_baseline"] = run(pre, base(x), x)
            R["pre2020"][f"{x}_distance_first"] = run(pre, ("EPU", "DPLUS", x, "DFR", "UNEMP", "logIP"), x)
        for k in (f"{x}_level_first", f"{x}_abs_distance_first", f"{x}_partialled_on_arms", f"{x}_ordered_last", f"{x}_without_epu",
                  f"{x}_with_ngu_7var", f"{x}_p1", f"{x}_p2", f"{x}_p3"):
            say_run(ex, k, R["pre2020"][k])
    pre196 = with_distance(df[df.index < PRE_END], ANCHOR_ESTIMATED)
    R["pre2020"]["RAWSD_R_distance_first_anchor_1.96"] = run(pre196, ("EPU", "DPLUS", "RAWSD_R", "DFR", "UNEMP", "logIP"), "RAWSD_R")
    pre196["RS_T"], r2 = partialled(pre196, "RAWSD_R", ANCHOR_ESTIMATED)
    R["pre2020"]["RAWSD_R_partialled_on_arms_anchor_1.96"] = {**run(pre196, ("EPU", "RS_T", "INFL", "DFR", "UNEMP", "logIP"), "RS_T"), "r2_on_arms": r2}
    say_run(ex, "RAWSD_R distance first, anchor 1.96", R["pre2020"]["RAWSD_R_distance_first_anchor_1.96"])
    ex.say("the full sample:")
    full_printed = df[df.index.to_period("Q").astype(str) <= PRINTED_FULL_SAMPLE_END]
    for label, d in (("through_last_quarter", df), (f"through_{PRINTED_FULL_SAMPLE_END}", full_printed)):
        R["full"][label] = {"quarters": int(len(d)), "last": str(d.index.max().to_period("Q"))}
        for x in ("RAWSD_R", "NU", "RAWVAR"):
            R["full"][label][f"{x}_baseline"] = run(d, base(x), x)
            R["full"][label][f"{x}_ordered_last"] = run(d, ("EPU", "INFL", "DFR", "UNEMP", "logIP", x), x)
            R["full"][label][f"{x}_distance_first"] = run(with_distance(d, ANCHOR), ("EPU", "DPLUS", x, "DFR", "UNEMP", "logIP"), x)
            for k in (f"{x}_baseline", f"{x}_ordered_last", f"{x}_distance_first"):
                say_run(ex, f"full ({label}) {k}", R["full"][label][k])
        cums = [v["logIP"]["cum_pct"] for k, v in R["full"][label].items() if isinstance(v, dict) and "logIP" in v]
        R["full"][label]["cum_range_pct"] = [float(min(cums)), float(max(cums))]

    fb, fd = R["figure"], R["figure"]
    hs = np.arange(H + 1)
    fig, axes = plt.subplots(1, 2, figsize=(6.35, 2.6), sharey=True)
    for a, x, ttl in ((axes[0], "RAWSD_R", "(a) shock to the raw dispersion (the numerator)"),
                      (axes[1], "NU", "(b) shock to Normalized Uncertainty")):
        pb = np.array(fb[f"{x}_baseline"]["logIP"]["path_pct"])
        pd_, sd_ = np.array(fd[f"{x}_distance_first"]["logIP"]["path_pct"]), np.array(fd[f"{x}_distance_first"]["logIP"]["se_pct"])
        a.axhline(0.0, color="0.78", lw=0.6, zorder=1)
        a.fill_between(hs, pd_ - Z90 * sd_, pd_ + Z90 * sd_, color=C_DIST, alpha=0.15, lw=0, zorder=2)
        a.plot(hs, pb, color=C_BASE, lw=1.3, ls=(0, (4, 2)), zorder=3)
        a.plot(hs, pd_, color=C_DIST, lw=1.7, zorder=4)
        a.plot(hs, pd_, color=C_DIST, marker="o", ms=2.5, lw=0, zorder=5)
        a.set_title(ttl, fontsize=8.6)
        a.set_xlabel("quarters after the shock", fontsize=8.4)
        a.set_xticks(range(0, H + 1, 2))
        a.tick_params(labelsize=8.0)
    axes[0].set_ylim(-1.55, 0.85)
    axes[0].text(3.95, 0.36, "distance ordered first", color=C_DIST, fontsize=7.8)
    axes[0].text(4.30, -1.34, "baseline ordering", color=C_BASE, fontsize=7.8)
    axes[1].text(3.95, 0.36, "distance ordered first", color=C_DIST, fontsize=7.8)
    axes[1].text(3.20, -1.34, "baseline ordering", color=C_BASE, fontsize=7.8)
    axes[0].set_ylabel("log industrial production ($\\%$)", fontsize=8.4)
    fig.tight_layout(w_pad=1.4)
    ex.save_figure(fig)
    R["conventions"] = {"horizon": H, "band": "asymptotic, 90 per cent", "lag_order": "AIC over 1..3 unless forced", "anchor": ANCHOR,
                        "measures_zscored_on": "the joined sample", "NU": "at the fitted ratio NU_R_FITTED", "pre_sample_end": "2019Q4"}
    ex.write_results(R, "Figure 6 — industrial production after an uncertainty shock")


if __name__ == "__main__":
    main()
