#!/usr/bin/env python3
"""Table 1 of *Tolerable Inflation, Intolerable Uncertainty*: the arms specification, source by source.

Paper: Vansteenberghe, E. (2026), *Tolerable Inflation, Intolerable Uncertainty*,
working paper, Banque de France (``vansteenberghe2026tolerable``), Section 3,
Table 1 (``tab:armsbysource``).

The two-arm law V = a + b_-(-d)_+ + b_+(d)_+ fitted on each source's own
distance measure. Estimated here: the three ECB SPF rows (average individual
variance, disagreement, total mixture variance; Newey--West at four lags on
the 109 rounds through 2026Q2) and the US SPF row (individual core-CPI
densities after January 2012). Carried as printed, not computed: the
inflation-swap rows and the inflation-option row, which rest on licensed
daily data (see ``../restricted/README.md``).

Inference on the US row: standard errors clustered by survey round (58
rounds), as the table's note says; the Newey--West t-statistics of the
stacked individual observations, which an earlier version of the table
printed, are kept in the results file (``us_row_hac4_stacked``).

Inputs:  the ECB-SPF round files; ``SPFmicrodata.xlsx`` (sheet PRCCPI).
Outputs: ``tables/tab01_arms_by_source.tex``, ``results/tab01_arms_by_source.{json,md}``.

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use
this code, cite the paper above.
"""

from __future__ import annotations

import re

import pandas as pd

from nu_measures import conventions as cv
from nu_measures import econometrics as ec
from nu_measures import law
from nu_measures.exhibit import Exhibit, load_ecb_panel, load_us_densities

ANNOUNCE = pd.Timestamp("2012-01-01")
US_MEAN_TRIM = (-1.0, 6.0)

#: The market rows, as printed in the paper (Table 1); they rest on licensed data and are not computed here.
CARRIED = {
    "swaps": {"computed": False, "label": "Inflation swaps, 2y, 63d RV", "n": "5{,}421", "a": "0.451", "b_minus": "-0.078",
              "b_plus": "+1.606", "r2": "0.496", "t_minus": "---", "t_plus": "---"},
    "swaps_nonoverlapping": {"computed": False, "label": "\\quad non-overlapping windows", "n": "87", "a": "0.395",
                             "b_minus": "-0.015", "b_plus": "+1.664", "r2": "0.461", "t_minus": "(-0.1)", "t_plus": "(6.4)"},
    "options": {"computed": False, "label": "Inflation options, adjusted", "n": "3{,}941", "a": "0.380", "b_minus": "-0.089",
                "b_plus": "+0.680", "r2": "0.359", "t_minus": "(-0.78)", "t_plus": "(7.85)"},
}

TEMPLATE = r"""\begin{table}[!htbp]\centering
\caption{The arms specification, source by source}
\label{tab:armsbysource}
\begin{tabular}{lrrrrr}
\toprule
 & $n$ & $a$ & $b_-$ & $b_+$ & $R^2$ \\
\midrule
ECB SPF, average individual variance $W_t$ & @W_n@ & @W_a@ & @W_bm@ & @W_bp@ & @W_r2@ \\
                              &         &         & @W_tm@ & @W_tp@ &        \\
ECB SPF, disagreement $D_t$   & @D_n@   & @D_a@ & @D_bm@ & @D_bp@ & @D_r2@ \\
                              &         &         & @D_tm@ & @D_tp@ &        \\
ECB SPF, total mixture variance $T_t$ & @T_n@ & @T_a@ & @T_bm@ & @T_bp@ & @T_r2@ \\
                              &         &         & @T_tm@ & @T_tp@ &        \\
Inflation swaps, 2y, 63d RV   & $5{,}421$ & $0.451$ & $-0.078$ & $+1.606$ & $0.496$ \\
                              &         &         & --- & --- &        \\
\quad non-overlapping windows & $87$ & $0.395$ & $-0.015$ & $+1.664$ & $0.461$ \\
                              &         &         & $(-0.1)$ & $(6.4)$ &        \\
Inflation options, adjusted   & $3{,}941$ & $0.380$ & $-0.089$ & $+0.680$ & $0.359$ \\
                              &         &         & $(-0.78)$ & $(7.85)$ &         \\
US SPF, core CPI, individual  & @US_n@ & @US_a@ & @US_bm@ & @US_bp@ & @US_r2@ \\
                              &         &         & @US_tm@ & @US_tp@ &          \\
\bottomrule
\end{tabular}
\vspace{0.3em}
\parbox{\linewidth}{\footnotesize \textit{Notes:} $t$-statistics in parentheses.
Each row fits $V=a+b_-(-d)_++b_+(d)_+$ on that source's own distance measure; the survey
rows use the forecast gap, the market rows the level gap. Inference is each source's own:
the survey rows HAC(4); the daily swap row reports no $t$-statistics: because its sixty-three-day windows
overlap, daily HAC inference overstates precision (it returns $t\approx25$); the honest
inference uses the $87$ non-overlapping windows of the row beneath it, where the same arms
are $+1.664$ with $t=6.4$ (block-bootstrap $95\%$ interval $[1.24,\,2.26]$) and $-0.015$
with $t=-0.1$; the options row on the premium-adjusted daily series; the US row clustered by round. \emph{Slopes are
not comparable across rows}---the variances are in different units; only the shape is. The
three ECB rows are the objects of Section~\ref{sec:fitlaw}: the law is estimated on the average
individual variance; the total is what aggregate data deliver and is the object of the US
announcement regressions, the market rows and every macro application; disagreement is the
complement. The ratio $b_+/a$ that normalizes the corrected series where it is estimated is that of the average individual variance, $@W_ratio_text@=@W_ratio@$. The level of the survey arms depends on where the mass in the open top bin is
placed; the bracket is in \citet{vansteenberghe2026uncertain}. The
US SPF row is the individual-level fit after January 2012; the aggregate US fit is
symmetric because disagreement, which is symmetric there, dominates it
(Section~\ref{sec:law}). The options row is the premium-adjusted series; the same days
fitted on raw implied variance return inverted arms, the case for the adjustment
(Section~\ref{sec:law}). Script: \texttt{tab01\_arms\_by\_source.py}, which estimates the
survey rows; the swap and option rows rest on licensed data and are carried as printed.}
\end{table}
"""


def us_individual_post2012() -> pd.DataFrame:
    """The individual core-CPI densities after the announcement, mean inside [-1, 6], positive variance."""
    d = load_us_densities("PRCCPI")
    lo, hi = US_MEAN_TRIM
    return d[(d["Date"] >= ANNOUNCE) & (d["Mean"] >= lo) & (d["Mean"] <= hi) & (d["Variance"] > 0)].copy()


def cells(key: str, fit: law.ArmsFit) -> dict[str, str]:
    n = f"{fit.n:,}".replace(",", "{,}")
    return {f"{key}_n": f"${n}$", f"{key}_a": f"${fit.a:.3f}$", f"{key}_bm": f"${fit.b_minus:+.3f}$",
            f"{key}_bp": f"${fit.b_plus:+.3f}$", f"{key}_r2": f"${fit.r2:.3f}$",
            f"{key}_tm": f"$({fit.t_b_minus:.2f})$", f"{key}_tp": f"$({fit.t_b_plus:.2f})$"}


def main() -> None:
    ex = Exhibit(__file__)
    S = law.estimation_sample(law.round_aggregates(load_ecb_panel()))
    fits = law.law_by_object(S)
    values: dict[str, str] = {}
    results: dict = {"sample_ecb": {"rounds": int(len(S)), "first": str(S.index.min().date()), "last": str(S.index.max().date())}}
    for k in ("W", "D", "T"):
        f = fits[k]
        values.update(cells(k, f))
        results[f"ECB_{k}"] = f.summary_row()
        ex.say(f"ECB {k}: n {f.n} a {f.a:.3f} b- {f.b_minus:+.3f} ({f.t_b_minus:.2f}) b+ {f.b_plus:+.3f} ({f.t_b_plus:.2f}) R2 {f.r2:.3f}")
    u = us_individual_post2012()
    us = law.arms_fit(u["Variance"].to_numpy(), u["Mean"].to_numpy() - cv.TARGET, hac_lags=4)
    values.update(cells("US", us))
    results["US_core_cpi_individual_post2012"] = us.summary_row()
    ex.say(f"US SPF: n {us.n} a {us.a:.3f} b- {us.b_minus:+.3f} ({us.t_b_minus:.2f}) b+ {us.b_plus:+.3f} ({us.t_b_plus:.2f}) R2 {us.r2:.3f}")
    clus = ec.cluster_ols(u["Variance"].to_numpy(), law.arms_design(u["Mean"].to_numpy() - cv.TARGET),
                          u["Date"].to_numpy(), names=("a", "b_minus", "b_plus"))
    values["US_tm"], values["US_tp"] = f"$({clus.t[1]:.2f})$", f"$({clus.t[2]:.2f})$"
    results["us_row_clustered_by_round"] = {**clus.as_dict(), "rounds": int(u["Date"].nunique())}
    results["us_row_hac4_stacked"] = {"t_b_minus": us.t_b_minus, "t_b_plus": us.t_b_plus}
    ex.say(f"US SPF, clustered by round ({u['Date'].nunique()} rounds): t(b-) {clus.t[1]:.2f}, t(b+) {clus.t[2]:.2f} (the table's inference)")
    ratio = fits["W"].r_plus
    values["W_ratio_text"] = f"{fits['W'].b_plus:.3f}/{fits['W'].a:.3f}"
    values["W_ratio"] = f"{ratio:.2f}"
    results["ratio_b_plus_over_a_W"] = ratio
    results["carried_as_printed"] = CARRIED

    text = TEMPLATE
    for k, v in values.items():
        text = text.replace(f"@{k}@", v)
    if re.search(r"@[A-Za-z_0-9]+@", text):
        raise SystemExit("unfilled placeholder in the table")
    ex.write_table(text)
    ex.write_results(results, "Table 1 — the arms specification, source by source")


if __name__ == "__main__":
    main()
