#!/usr/bin/env python3
"""Table 2 of *Uncertain and Asymmetric Forecasts*: division or residual.

Paper: Vansteenberghe, E. (2026), *Uncertain and Asymmetric Forecasts*,
working paper (``vansteenberghe2026uncertain``), Section 3, Table 2
(``tab:residuals``) and the paragraph "Division or residual."

What it does: removes the level component of measured uncertainty by a
residual rather than by the division of Normalized Uncertainty, and sets the
two residuals beside NU. On the rounds of the fitted envelope (n = 109, through
2026Q2, consensus in [-1, 5]) the two-arm envelope of the average individual
variance W_t is fitted (Panel A)

* additively, by least squares -- the fit of Table 1 -- with residual
  W_t - W_hat_t;
* multiplicatively, as the mean of W_t = V_struct(d_t) exp(u_t), by Poisson
  pseudo-maximum likelihood with an identity link (Santos Silva and Tenreyro,
  2006, "The Log of Gravity", REStat 88(4)), with residual log(W_t / W_hat_t);

both with Newey--West t-statistics at four lags; and the fitted NU round series
(ratio 2.23) is regressed on each residual, with a constant (Panel B). On these
rounds the two routes are interchangeable; the paper's paragraph explains, on
the cross-country panel of Barro (1995) replicated in
``vansteenberghe2026tolerable``, why the measure is the ratio.

Inputs:  the ECB-SPF round files (``NU_DATA_DIR/ecb_spf/rounds``), through
         ``nu_measures.exhibit.load_ecb_panel``.
Outputs: ``tables/tab01b_residuals.tex``, ``results/tab01b_residuals.{json,md}``.
Sample:  rounds 1999Q1--2026Q2 inside the round rule (109).
Run time: seconds.

The file name keeps the ``tab01..tab06`` names of release 1.0.0 stable: this
table entered the manuscript after them, as its Table 2.

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use
this code, cite the paper above.
"""

from __future__ import annotations

import numpy as np

from nu_measures import conventions as cv
from nu_measures import econometrics as ec
from nu_measures import law, measures
from nu_measures.exhibit import Exhibit, load_ecb_panel

TEMPLATE = r"""\begin{table}[tbp]\centering
\caption{Division or residual: the envelope fitted additively and multiplicatively}\label{tab:residuals}
\begin{tabular}{lcc}
\toprule
 & Additive & Multiplicative \\
 & (least squares) & (Poisson pseudo-maximum likelihood) \\
\midrule
\multicolumn{3}{l}{\emph{Panel A. The residualising regression: $W_t$ on the two arms}}\\
$a$ & $@aO@$ $(@taO@)$ & $@aP@$ $(@taP@)$ \\
$b_-$ & $@bmO@$ $(@tbmO@)$ & $@bmP@$ $(@tbmP@)$ \\
$b_+$ & $@bpO@$ $(@tbpO@)$ & $@bpP@$ $(@tbpP@)$ \\
$r_+=b_+/a$ & $@rO@$ & $@rP@$ $[@srP@]$ \\
residual & $W_t-\widehat W_t$ & $\log(W_t/\widehat W_t)$ \\
\addlinespace
\multicolumn{3}{l}{\emph{Panel B. $\mathrm{NU}^{\mathrm{fit}}_t$ regressed on the residual}}\\
slope & $@sO@$ $(@tsO@)$ & $@sP@$ $(@tsP@)$ \\
$R^2$ & $@r2O@$ & $@r2P@$ \\
correlation & $@cO@$ & $@cP@$ \\
\bottomrule
\end{tabular}
\vspace{0.3em}
\parbox{0.95\linewidth}{\footnotesize \textit{Notes:} the rounds of the fitted envelope
($n=@n@$, through 2026Q2, consensus in $[-1,5]$). Panel~A fits the two-arm envelope
\eqref{eq:vstruct} to $W_t$ by least squares (the fit of Table~\ref{tab:arms}) and, as the
mean of a multiplicative model $W_t=V_{\mathrm{struct}}(d_t)\,e^{u_t}$, by Poisson
pseudo-maximum likelihood with an identity link \citep{santos2006log}; the residual of each
fit is taken with its coefficients frozen. Newey--West $t$-statistics at four lags in
parentheses; the delta-method standard error of the multiplicative ratio in brackets.
Panel~B regresses the fitted series~\eqref{eq:nu_fit}, round means, on each residual, with a
constant; $t$-statistics as in Panel~A. Script: \texttt{tab01b\_residuals.py}.}
\end{table}
"""


def signed(x: float, nd: int = 4) -> str:
    return f"{x:+.{nd}f}"


def main() -> None:
    ex = Exhibit(__file__)
    panel = load_ecb_panel()
    A = law.round_aggregates(panel)
    S = law.estimation_sample(A)
    X = law.arms_design(S["gap"].to_numpy())
    W = S["W"].to_numpy()

    add = ec.hac_ols(W, X, names=("b_minus", "b_plus"))
    mul = ec.poisson_pml_identity(W, X, names=("b_minus", "b_plus"))
    r_add, r_mul = add.params[2] / add.params[0], mul.params[2] / mul.params[0]
    se_r_mul = law.ratio_se(mul.params, mul.cov)
    if abs(r_add - cv.NU_R_FITTED) > 1e-3:
        raise SystemExit(f"the least-squares ratio {r_add:.4f} is not the certified {cv.NU_R_FITTED:.4f}")

    res_add = W - add.fitted
    res_mul = np.log(W / mul.fitted)
    nu = measures.nu_series(panel).loc[S.index, "NU_fitted"].to_numpy()
    on_add = ec.hac_ols(nu, res_add)
    on_mul = ec.hac_ols(nu, res_mul)
    c_add, c_mul = float(np.corrcoef(nu, res_add)[0, 1]), float(np.corrcoef(nu, res_mul)[0, 1])
    for tag, fit, r in (("least squares", add, r_add), ("Poisson PML", mul, r_mul)):
        ex.say(f"{tag}: a {fit.params[0]:.4f} (t {fit.t[0]:.2f})  b- {fit.params[1]:+.4f} (t {fit.t[1]:.2f})  "
               f"b+ {fit.params[2]:.4f} (t {fit.t[2]:.2f})  r+ {r:.3f}")
    ex.say(f"Poisson PML ratio s.e. {se_r_mul:.3f}; corr(W, fitted)^2 {mul.r2:.3f}")
    ex.say(f"NU on the additive residual: slope {on_add.params[1]:.3f} (t {on_add.t[1]:.2f}), R2 {on_add.r2:.3f}, corr {c_add:.3f}")
    ex.say(f"NU on the multiplicative residual: slope {on_mul.params[1]:.3f} (t {on_mul.t[1]:.2f}), R2 {on_mul.r2:.3f}, corr {c_mul:.3f}")

    rep = {"@n@": str(len(S)),
           "@aO@": f"{add.params[0]:.4f}", "@taO@": f"{add.t[0]:.2f}", "@bmO@": signed(add.params[1]), "@tbmO@": f"{add.t[1]:.2f}",
           "@bpO@": f"{add.params[2]:.4f}", "@tbpO@": f"{add.t[2]:.2f}", "@rO@": f"{r_add:.3f}",
           "@aP@": f"{mul.params[0]:.4f}", "@taP@": f"{mul.t[0]:.2f}", "@bmP@": signed(mul.params[1]), "@tbmP@": f"{mul.t[1]:.2f}",
           "@bpP@": f"{mul.params[2]:.4f}", "@tbpP@": f"{mul.t[2]:.2f}", "@rP@": f"{r_mul:.3f}", "@srP@": f"{se_r_mul:.3f}",
           "@sO@": f"{on_add.params[1]:.3f}", "@tsO@": f"{on_add.t[1]:.2f}", "@r2O@": f"{on_add.r2:.3f}", "@cO@": f"{c_add:.3f}",
           "@sP@": f"{on_mul.params[1]:.3f}", "@tsP@": f"{on_mul.t[1]:.2f}", "@r2P@": f"{on_mul.r2:.3f}", "@cP@": f"{c_mul:.3f}"}
    text = TEMPLATE
    for k in sorted(rep, key=len, reverse=True):
        text = text.replace(k, rep[k])
    if "@" in text:
        raise SystemExit("unfilled placeholder in the table")
    ex.write_table(text)
    ex.write_results({
        "n_rounds": len(S), "sample": f"{S['Q'].iloc[0]}..{S['Q'].iloc[-1]}",
        "additive_least_squares": {**add.as_dict(), "r_plus": float(r_add)},
        "multiplicative_poisson_pml": {**mul.as_dict(), "r_plus": float(r_mul), "r_plus_se": float(se_r_mul),
                                       "r2_is": "squared correlation of W with the fitted mean"},
        "nu_on_additive_residual": {"slope": float(on_add.params[1]), "t": float(on_add.t[1]), "r2": float(on_add.r2), "corr": c_add},
        "nu_on_multiplicative_residual": {"slope": float(on_mul.params[1]), "t": float(on_mul.t[1]), "r2": float(on_mul.r2), "corr": c_mul},
        "conventions": {"hac_lags": 4, "nu_ratio": cv.NU_R_FITTED, "residuals": "coefficients frozen at the fit"},
    }, "Table 2 — division or residual: the envelope fitted additively and multiplicatively")


if __name__ == "__main__":
    main()
