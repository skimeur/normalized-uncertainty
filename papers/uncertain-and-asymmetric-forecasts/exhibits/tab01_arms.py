#!/usr/bin/env python3
"""Table 1 of *Uncertain and Asymmetric Forecasts*: the variance--distance envelope, euro-area panel.

Paper: Vansteenberghe, E. (2026), *Uncertain and Asymmetric Forecasts*,
working paper (``vansteenberghe2026uncertain``), Section 3, Table 1
(``tab:arms``). Also the surge-and-ratio numbers of Section 3 (the envelope
before 2020, the split test) that the table's note prints.

What it does: on the ECB-SPF individual panel, the round series of the average
individual variance W, disagreement D and the total T against the signed
distance of the consensus forecast from the 2 per cent target; the two-arm
law on each (Newey--West, four lags) over every round inside the [-1, 5]
round rule (n = 110 through 2026Q3; 2022Q4 excluded), the law before 2020,
the Wald tests, the split test across 2020Q1, and the fitted ratio through
2026Q2 (n = 109) that the fitted NU divides by.

Inputs:  the ECB-SPF round files (``NU_DATA_DIR/ecb_spf/rounds``), through
         ``nu_measures.exhibit.load_ecb_panel``.
Outputs: ``tables/tab01_arms.tex``, ``results/tab01_arms.{json,md}``.
Sample:  rounds 1999Q1--2026Q3; the ratio through 2026Q2.
Run time: seconds.

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use
this code, cite the paper above.
"""

from __future__ import annotations

import pandas as pd

from nu_measures import conventions as cv
from nu_measures import law
from nu_measures.exhibit import Exhibit, load_ecb_panel

TEMPLATE = r"""\begin{table}[tbp]\centering
\caption{The variance--distance envelope, euro-area panel}\label{tab:arms}
\begin{tabular}{lccccc}
\toprule
 & $a$ & $b_-$ & $b_+$ & $R^2$ & $n$ \\
\midrule
\multicolumn{6}{l}{\emph{average individual variance $W_t$: the envelope the measure divides by}}\\
two arms, all rounds & @aW@ & @bmW@ & @bpW@ & @r2W@ & $@n@$ \\
 & (@saW@) & (@sbmW@) & (@sbpW@) & & \\
two arms, rounds before 2020 & @aP@ & @bmP@ & @bpP@ & @r2P@ & $@nP@$ \\
 & (@saP@) & (@sbmP@) & (@sbpP@) & & \\
\addlinespace
\multicolumn{6}{l}{\emph{the same rounds: disagreement, and the total}}\\
disagreement $D_t$ & @aD@ & @bmD@ & @bpD@ & @r2D@ & $@n@$ \\
 & (@saD@) & (@sbmD@) & (@sbpD@) & & \\
total $T_t=W_t+D_t$ & @aT@ & @bmT@ & @bpT@ & @r2T@ & $@n@$ \\
 & (@saT@) & (@sbmT@) & (@sbpT@) & & \\
\bottomrule
\end{tabular}
\vspace{0.3em}
\parbox{0.95\linewidth}{\footnotesize \textit{Notes:} round-level regressions of each variance on
the signed distance of the consensus forecast (the cross-forecaster mean) from the $2\,\%$
target, in the two-arm form of~\eqref{eq:vstruct}. $W_t$ is the round mean
of the individual density variances, $D_t$ the cross-forecaster variance of their means.
ECB-SPF one-year-ahead inflation densities, 1999Q1 to the latest round; rounds whose consensus
lies outside $[-1,5]$ are excluded, which removes one round, 2022Q4 (consensus
$@mu22@$). Newey--West standard errors at four lags in parentheses. Wald tests on the two-arm
fit of $W_t$: $b_-=0$ gives $\chi^2_1=@w0@$ ($p=@p0@$); $b_-=b_+$ gives $\chi^2_1=@w1@$
($p<0.001$). $W_t$ is @share@ per cent of $T_t$. The measure uses the ratio of the $W_t$ fit
through 2026Q2, $b_+/a=@rfit@$ ($n=109$, delta-method standard error @sefit@); on these $@n@$ rounds it
is $@r110@$. Fitted on the rounds before 2020 the same ratio is $@rpre@$ (@sepre@): over those rounds the
consensus gap ran over $[@gplo@,@gphi@]$ and only @nabove@ rounds sat above target, against
$[@gqlo@,@gqhi@]$ from 2020Q1, so the upper arm is barely identified there. The two periods do not share
one envelope ($\chi^2_3=@wsplit@$, $p<0.001$, the shift being the intercept rather than the upper arm),
while the difference between the two ratios alone is within one standard error of zero. A fitted ratio is
therefore a dated object, tied to the range of distances the sample happens to contain; the calibration
$r_+=1$ of~\eqref{eq:nu_cal} is not. Script: \texttt{tab01\_arms.py}.}
\end{table}
"""

SPLIT = "2019-12-01"  # panel Date of the 2020Q1 round


def f3(x: float) -> str:
    return "$%.3f$" % x


def main() -> None:
    ex = Exhibit(__file__)
    panel = load_ecb_panel()
    A = law.round_aggregates(panel)
    S_all = law.estimation_sample(A, max_date=None)
    S_fit = law.estimation_sample(A)
    excluded = A.index.difference(S_all.index)
    mu_excluded = float(A.loc[excluded, "mu"].iloc[0]) if len(excluded) else float("nan")
    ex.say(f"panel: {int(A['n'].sum())} forecaster-rounds, {len(A)} rounds; excluded by the round rule: "
           + ", ".join(str(q) for q in A.loc[excluded, "Q"]) + f" (consensus {mu_excluded:.2f})")

    fits_all = law.law_by_object(S_all)
    fits_fit = law.law_by_object(S_fit)
    for tag, fits in (("109", fits_fit), ("110", fits_all)):
        for o in "WDT":
            x = fits[o]
            ex.say(f"n={tag} {o}: a {x.a:.4f} ({x.se_a:.4f})  b- {x.b_minus:+.4f} ({x.se_b_minus:.4f}, t {x.t_b_minus:.2f})"
                   f"  b+ {x.b_plus:.4f} ({x.se_b_plus:.4f}, t {x.t_b_plus:.2f})  R2 {x.r2:.3f}  b+/a {x.r_plus:.3f}")
    wald_all = law.wald_tests(fits_all["W"])
    wald_fit = law.wald_tests(fits_fit["W"])
    r_fit = fits_fit["W"].r_plus
    if abs(r_fit - cv.NU_R_FITTED) > 1e-3:
        raise SystemExit(f"the fitted ratio {r_fit:.4f} is not the certified {cv.NU_R_FITTED:.4f}")
    share = float(S_all["W"].mean() / S_all["T"].mean())
    split = law.split_test(S_all, "W", SPLIT)
    pre, post = split["pre"], split["post"]
    gap_pre = S_all.loc[S_all.index < pd.Timestamp(SPLIT), "gap"]
    gap_post = S_all.loc[S_all.index >= pd.Timestamp(SPLIT), "gap"]
    ex.say(f"Wald on W, n={len(S_all)}: b-=0 chi2 {wald_all['b_minus_zero']['statistic']:.3f} "
           f"(p {wald_all['b_minus_zero']['p_value']:.3f}); b-=b+ chi2 {wald_all['arms_equal']['statistic']:.1f}")
    ex.say(f"ratio through 2026Q2 {r_fit:.4f} ({fits_fit['W'].r_plus_se:.2f}); on the {len(S_all)} rounds {fits_all['W'].r_plus:.4f}; "
           f"before 2020 {pre.r_plus:.2f} ({pre.r_plus_se:.2f}, n {pre.n}); from 2020Q1 {post.r_plus:.2f} ({post.r_plus_se:.2f}, n {post.n})")
    ex.say(f"split test chi2_3 {split['wald_joint']:.1f} (p {split['p_joint']:.2g}); z of the ratio difference {split['z_ratio_difference']:.2f}")

    rep = {"@n@": str(len(S_all)), "@mu22@": "%.2f" % mu_excluded,
           "@w0@": "%.3f" % wald_all["b_minus_zero"]["statistic"], "@p0@": "%.2f" % wald_all["b_minus_zero"]["p_value"],
           "@w1@": "%.1f" % wald_all["arms_equal"]["statistic"], "@share@": "%.0f" % (100 * share),
           "@rfit@": "%.2f" % r_fit, "@r110@": "%.2f" % fits_all["W"].r_plus}
    for o in "WDT":
        x = fits_all[o]
        rep.update({f"@a{o}@": f3(x.a), f"@bm{o}@": f3(x.b_minus), f"@bp{o}@": f3(x.b_plus), f"@r2{o}@": f3(x.r2),
                    f"@sa{o}@": f3(x.se_a), f"@sbm{o}@": f3(x.se_b_minus), f"@sbp{o}@": f3(x.se_b_plus)})
    rep.update({"@aP@": f3(pre.a), "@bmP@": f3(pre.b_minus), "@bpP@": f3(pre.b_plus), "@r2P@": f3(pre.r2),
                "@saP@": f3(pre.se_a), "@sbmP@": f3(pre.se_b_minus), "@sbpP@": f3(pre.se_b_plus), "@nP@": str(pre.n),
                "@sefit@": "%.2f" % fits_fit["W"].r_plus_se, "@rpre@": "%.2f" % pre.r_plus, "@sepre@": "%.2f" % pre.r_plus_se,
                "@gplo@": "%+.2f" % gap_pre.min(), "@gphi@": "%+.2f" % gap_pre.max(),
                "@gqlo@": "%+.2f" % gap_post.min(), "@gqhi@": "%+.2f" % gap_post.max(),
                "@nabove@": str(int((gap_pre > 0).sum())), "@wsplit@": "%.0f" % split["wald_joint"]})
    text = TEMPLATE
    for k in sorted(rep, key=len, reverse=True):
        text = text.replace(k, rep[k])
    if "@" in text:
        raise SystemExit("unfilled placeholder in the table")
    ex.write_table(text)

    results = {
        "n_rounds_all": len(S_all), "n_rounds_fit": len(S_fit), "excluded_round": [str(q) for q in A.loc[excluded, "Q"]],
        "excluded_consensus": mu_excluded, "share_W_of_T": share,
        "law_all_rounds": {o: fits_all[o].summary_row() for o in "WDT"},
        "law_through_2026Q2": {o: fits_fit[o].summary_row() for o in "WDT"},
        "wald_W_all_rounds": wald_all, "wald_W_through_2026Q2": wald_fit,
        "ratio_fitted": r_fit, "ratio_fitted_se": fits_fit["W"].r_plus_se,
        "before_2020": pre.summary_row(), "from_2020Q1": post.summary_row(),
        "gap_support_before_2020": [float(gap_pre.min()), float(gap_pre.max())],
        "gap_support_from_2020Q1": [float(gap_post.min()), float(gap_post.max())],
        "rounds_above_target_before_2020": int((gap_pre > 0).sum()),
        "split_test": {k: v for k, v in split.items() if k in ("wald_joint", "p_joint", "z_ratio_difference", "p_ratio_difference")},
        "sample": {"rounds": f"{S_all['Q'].iloc[0]}..{S_all['Q'].iloc[-1]}", "cutoff_for_the_ratio": cv.HELD_OUT_SURVEY_ROUND + " held out"},
    }
    ex.write_results(results, "Table 1 — the variance–distance envelope, euro-area panel")


if __name__ == "__main__":
    main()
