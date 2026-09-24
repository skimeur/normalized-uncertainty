#!/usr/bin/env python3
"""Table 5 of *Uncertain and Asymmetric Forecasts*: the envelope in the US survey, by density question.

Paper: Vansteenberghe, E. (forthcoming), *Uncertain and Asymmetric Forecasts*,
working paper (``vansteenberghe2026uncertain``), Section 6, Table 5
(``tab:us_arms``).

Round-level two-arm fits of the total density variance on the signed distance
of the round's mean forecast from 2 per cent (Newey--West, four lags) for the
two grid-stable core questions of the Philadelphia Fed survey -- over 2007--2026,
before and after the FOMC's announcement of a numerical target in January
2012 -- and for the GDP price index question on each of its two grids; the
euro-area total law for comparison; the race between the 2012 announcement
and the 2014 change of grid at the individual level (|d| <= 2, White standard
errors); and the within-source ratio b_+/a at the individual level.

Sample conventions. The old-grid row of the GDP price index question is the
old grid *before the announcement*, 1992Q1--2011Q4 (81 rounds); the eight
old-grid rounds of 2012Q1--2013Q4 are written to the results file as
``GDP_old_2012_2013``. Every statistic is rounded once, from the computed value.

Inputs:  ``SPFmicrodata.xlsx`` (sheets PRCPCE, PRCCPI, PRPGDP); the ECB-SPF round files.
Outputs: ``tables/tab05_us_arms.tex``, ``results/tab05_us_arms.{json,md}``.

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use
this code, cite the paper above.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from nu_measures import conventions as cv
from nu_measures import econometrics as ec
from nu_measures import io_us_spf, law
from nu_measures.exhibit import Exhibit, load_ecb_panel, load_us_densities

ANNOUNCE = pd.Timestamp("2012-01-01")
GRID = pd.Timestamp("2014-01-01")

TEMPLATE = r"""\begin{table}[tbp]\centering
\caption{The envelope in the US survey, by density question}\label{tab:us_arms}
\begin{tabular}{lccccc}
\toprule
question / window & $n$ & $R^2$ sym. & $R^2$ arms & $b_-$ $(t)$ & $b_+$ $(t)$ \\
\midrule
core PCE, 2007--2026        & @PCE_all@ \\
\hspace{1em} before 2012    & @PCE_pre@ \\
\hspace{1em} after 2012     & @PCE_post@ \\
\addlinespace
core CPI, 2007--2026        & @CPI_all@ \\
\hspace{1em} before 2012    & @CPI_pre@ \\
\hspace{1em} after 2012     & @CPI_post@ \\
\addlinespace
GDP price index, old grid to 2011 & @GDP_old@ \\
\hspace{1em} new grid, 2014--  & @GDP_new@ \\
\addlinespace
euro area, for comparison   & @EA@ \\
\midrule
\multicolumn{6}{l}{\emph{the two events run against each other} (GDP price index, individual level, $|d|\leq 2$)}\\
\multicolumn{4}{l}{change of grid, 2014 $\times\,|d|$} & \multicolumn{2}{c}{$@race_grid@$ $(@race_grid_t@)$} \\
\multicolumn{4}{l}{announcement, 2012 $\times\,|d|$} & \multicolumn{2}{c}{$@race_ann@$ $(@race_ann_t@)$} \\
\midrule
\multicolumn{6}{l}{\emph{the within-source ratio} $b_+/a$, individual level}\\
\multicolumn{4}{l}{euro area} & \multicolumn{2}{c}{$@ratio_ea@$} \\
\multicolumn{4}{l}{US core CPI, after 2012} & \multicolumn{2}{c}{$@ratio_cpi@$} \\
\multicolumn{4}{l}{US core PCE, after 2012} & \multicolumn{2}{c}{$@ratio_pce@$} \\
\bottomrule
\end{tabular}
\vspace{0.3em}
\parbox{0.95\linewidth}{\footnotesize \textit{Notes:} round-level regressions of the total
density variance on the two arms of the signed distance from $2\,\%$, Newey--West standard
errors at four lags, except where stated. The core questions have used one grid since 2007;
the GDP price index question halved its bin widths in 2014Q1 and is therefore split by grid,
never across it; its old-grid row stops at the announcement, and the eight old-grid rounds of
2012--13 are in the script's results file. The race at the foot of the table is the specification in which the published
pre/post-2012 break was estimated: the interaction that carries the break is the change of
grid, not the announcement. Slopes are never compared across sources, only shapes and the
within-source ratio. Script: \texttt{tab05\_us\_arms.py}.}
\end{table}
"""


def fit_row(A: pd.DataFrame) -> dict:
    """The two-arm fit of the total variance and the symmetric fit's R2, on a round series."""
    arms = law.arms_fit(A["T"].to_numpy(), A["gap"].to_numpy())
    sym = ec.hac_ols(A["T"].to_numpy(), np.abs(A["gap"].to_numpy()), lags=4)
    return {"n": arms.n, "r2_sym": float(sym.r2), "r2_arms": arms.r2, "b_minus": arms.b_minus, "t_minus": arms.t_b_minus,
            "b_plus": arms.b_plus, "t_plus": arms.t_b_plus, "a": arms.a, "r_plus": arms.r_plus}


def cell(r: dict) -> str:
    return "$%d$ & $%.3f$ & $%.3f$ & $%+.3f$ $(%.1f)$ & $%+.3f$ $(%.1f)$" % (
        r["n"], r["r2_sym"], r["r2_arms"], r["b_minus"], r["t_minus"], r["b_plus"], r["t_plus"])


def main() -> None:
    ex = Exhibit(__file__)
    rows, results = {}, {}
    for sheet, key in (("PRCPCE", "PCE"), ("PRCCPI", "CPI")):
        d = load_us_densities(sheet)
        A = io_us_spf.round_aggregates(d)
        for tag, S in (("all", A), ("pre", A[A.index < ANNOUNCE]), ("post", A[A.index >= ANNOUNCE])):
            r = fit_row(S)
            rows[f"{key}_{tag}"] = cell(r)
            results[f"{key}_{tag}"] = r
            ex.say(f"{sheet} {tag}: n {r['n']} R2 sym {r['r2_sym']:.3f} arms {r['r2_arms']:.3f} b- {r['b_minus']:+.3f} ({r['t_minus']:.1f}) b+ {r['b_plus']:+.3f} ({r['t_plus']:.1f})")
        if key in ("CPI", "PCE"):
            post = d[d["Date"] >= ANNOUNCE]
            ind = law.arms_fit(post["Variance"].to_numpy(), post["Mean"].to_numpy() - cv.TARGET, hac_lags=0)
            results[f"ratio_{key.lower()}_individual_post2012"] = ind.summary_row()
            rows[f"ratio_{key.lower()}"] = "%.2f" % ind.r_plus
            ex.say(f"{sheet} individual level after 2012: n {ind.n} a {ind.a:.3f} b+ {ind.b_plus:+.3f} ratio {ind.r_plus:.2f}")
    dg = load_us_densities("PRPGDP")
    Ag = io_us_spf.round_aggregates(dg)
    # the table's "old grid" row is the old grid before the announcement (1992Q1--2011Q4);
    # the eight old-grid rounds of 2012--2013 are reported in the results file only
    for tag, S in (("old", Ag[Ag.index < ANNOUNCE]), ("old_2012_2013", Ag[(Ag.index >= ANNOUNCE) & (Ag.index < GRID)]),
                   ("new", Ag[Ag.index >= GRID])):
        r = fit_row(S)
        results[f"GDP_{tag}"] = r
        if tag != "old_2012_2013":
            rows[f"GDP_{tag}"] = cell(r)
        ex.say(f"PRPGDP {tag} grid: n {r['n']} R2 sym {r['r2_sym']:.3f} arms {r['r2_arms']:.3f} b- {r['b_minus']:+.3f} ({r['t_minus']:.1f}) b+ {r['b_plus']:+.3f} ({r['t_plus']:.1f})")
    # the race: individual level, |d| <= 2, White standard errors
    dd = dg.copy()
    dd["d"] = (dd["Mean"] - cv.TARGET).abs()
    dd = dd[dd["d"] <= 2]
    post12 = (dd["Date"] >= ANNOUNCE).to_numpy(dtype=float)
    new14 = (dd["YEAR"] >= 2014).to_numpy(dtype=float)
    X = np.column_stack([dd["d"].to_numpy(), post12, post12 * dd["d"].to_numpy(), new14, new14 * dd["d"].to_numpy()])
    race = ec.hac_ols(dd["Variance"].to_numpy(), X, lags=0, names=("abs_d", "post2012", "post2012_x_abs_d", "newgrid2014", "newgrid2014_x_abs_d"))
    results["race"] = race.as_dict()
    ex.say(f"race (n {race.n}): grid x |d| {race.params[5]:+.3f} (t {race.t[5]:+.1f}); announcement x |d| {race.params[3]:+.3f} (t {race.t[3]:+.1f})")
    # the euro area: the total law through 2026Q2 and the pooled individual ratio
    panel = load_ecb_panel()
    S = law.estimation_sample(law.round_aggregates(panel))
    ea = fit_row(S)
    rows["EA"] = cell(ea)
    results["EA"] = ea
    pooled = law.pooled_individual(panel)
    results["ratio_ea_individual"] = pooled.summary_row()
    rows["ratio_ea"] = "%.2f" % pooled.r_plus
    ex.say(f"euro area: n {ea['n']} R2 sym {ea['r2_sym']:.3f} arms {ea['r2_arms']:.3f}; individual ratio {pooled.r_plus:.2f}")

    text = TEMPLATE
    for k, v in rows.items():
        text = text.replace(f"@{k}@", v)
    text = (text.replace("@race_grid@", "%+.3f" % race.params[5]).replace("@race_grid_t@", "%+.1f" % race.t[5])
            .replace("@race_ann@", "%+.3f" % race.params[3]).replace("@race_ann_t@", "%+.1f" % race.t[3]))
    if "@" in text:
        raise SystemExit("unfilled placeholder in the table")
    ex.write_table(text)
    ex.write_results(results, "Table 5 — the envelope in the US survey, by density question")


if __name__ == "__main__":
    main()
