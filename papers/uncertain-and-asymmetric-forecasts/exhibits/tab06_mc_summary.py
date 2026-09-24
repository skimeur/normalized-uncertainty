#!/usr/bin/env python3
"""Table 6 of *Uncertain and Asymmetric Forecasts*: the Monte Carlo summary, raw against corrected moments.

Paper: Vansteenberghe, E. (forthcoming), *Uncertain and Asymmetric Forecasts*,
working paper (``vansteenberghe2026uncertain``), Section 7, Table 6
(``tab:mc_simulation_summary``).

Strategies A and B of the simulation in ``_simulation.py`` (500 replications,
T = 200, N = 30, seed 42): the oracle R2 of raw individual uncertainty and of
NU against genuine uncertainty and against the distance of the latent target
from the anchor; the rejection rates of the slope of growth on the measure
(Newey--West standard errors), with and without the distance as a control;
and the R2 of raw asymmetry and of AC against the noise-free coherent signal.

Inputs:  none (simulated).
Outputs: ``tables/tab06_mc_summary.tex``, ``results/tab06_mc_summary.{json,md}``.

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use
this code, cite the paper above.
"""

from __future__ import annotations

import re

import numpy as np
from _simulation import PARAMS, SEED, rejection_rate, strategy_A, strategy_B

from nu_measures.exhibit import Exhibit

TEMPLATE = r"""\begin{table}[tbp]
\centering
\small
\caption{Monte Carlo simulation: raw versus corrected moments}\label{tab:mc_simulation_summary}
\begin{tabular}{@{}llcc@{}}
\toprule
\textbf{Strategy} & \textbf{Metric} & \textbf{Raw} & \textbf{Corrected} \\
\midrule
\multicolumn{4}{@{}l}{\emph{Panel A: Normalized Uncertainty}} \\[2pt]
A.\ Oracle $R^2$: tracking $u_t$ & $R^2(\cdot,\, u_t)$ & @r2_raw_u@ & \textbf{@r2_nu_u@} \\
A.\ Artifact exposure: tracking $d_t$ & $R^2(\cdot,\, d_t)$ & @r2_raw_d@ & \textbf{@r2_nu_d@} \\
B.\ Spurious rejection (HAC, outcome $\sim$ measure) & \% reject at 5\% & @rej_raw@\% & @rej_nu@\% \\
B.\ Controlled (HAC, outcome $\sim$ measure $+$ $d$) & \% reject at 5\% & @rej_raw_ctrl@\% & \textbf{@rej_nu_ctrl@\%} \\
\addlinespace[4pt]
\multicolumn{4}{@{}l}{\emph{Panel B: Asymmetry Coherence}} \\[2pt]
A.\ Coherent signal recovery & $R^2(\cdot,\, \mathrm{AC}^{nf})$ & @r2_raw_nf@ & \textbf{@r2_ac_nf@} \\
\bottomrule
\end{tabular}
\vspace{0.2em}
\begin{minipage}{0.97\linewidth}\footnotesize
\textit{Notes:} Monte Carlo simulation with @M@ replications, $T=$@T@ periods, $N=$@N@ forecasters. The DGP is an extended UCSV model with a latent inflation target (mean-reverting with state-dependent drift, $\kappa_\theta=$@kappa_theta@), AR(1) genuine uncertainty $u_t$, and AR(1) directional risk $\delta_t$. Raw: cross-sectional mean of individual variances (IU) or raw asymmetry (Bowley's formula). Corrected: NU $= \sqrt{\mathrm{Var}}/\sqrt{a + b\,|{\mu-\mu^*}|}$ or AC $= [(\tilde{Q}+\tilde{A})/2]\cdot[(1+\tilde{Q}\tilde{A})/2]$. $\mathrm{AC}^{nf}$: noise-free AC computed from structural and genuine Bowley components (without incoherent noise). Strategy~B uses Newey--West (HAC) standard errors; Strategy~D uses expanding-window (real-time) AC normalisation with no look-ahead. Bold: the measure with better performance. Full results in Section~\ref{sec:simulation}. Script: \texttt{tab06\_mc\_summary.py}.
\end{minipage}
\end{table}
"""


def main() -> None:
    ex = Exhibit(__file__)
    p = PARAMS
    ex.say(f"strategy A, {p['M']} replications, T {p['T']}, N {p['N']}, seed {SEED} ...")
    A = strategy_A(p, p["M"])
    ex.say(f"strategy B, {p['M']} replications ...")
    B = strategy_B(p, p["M"])
    values = {
        "r2_raw_u": A["r2_rawIU_u"].mean(), "r2_nu_u": A["r2_NU_u"].mean(),
        "r2_raw_d": A["r2_rawIU_d"].mean(), "r2_nu_d": A["r2_NU_d"].mean(),
        "rej_raw": rejection_rate(B["raw_hac"]), "rej_nu": rejection_rate(B["nu_hac"]),
        "rej_raw_ctrl": rejection_rate(B["raw_ctrl_hac"]), "rej_nu_ctrl": rejection_rate(B["nu_ctrl_hac"]),
        "r2_raw_nf": A["r2_rawS_nfAC"].mean(), "r2_ac_nf": A["r2_AC_nfAC"].mean(),
    }
    for k, v in values.items():
        ex.say(f"  {k:<14} {v:.4f}")
    text = TEMPLATE
    for k, v in values.items():
        text = text.replace(f"@{k}@", ("%.1f" if k.startswith("rej") else "%.3f") % v)
    text = text.replace("@M@", str(p["M"])).replace("@T@", str(p["T"])).replace("@N@", str(p["N"])).replace("@kappa_theta@", str(p["kappa_theta"]))
    if re.search(r"@[a-z_0-9]+@", text):
        raise SystemExit("unfilled placeholder in the table")
    ex.write_table(text)
    results = {"parameters": p, "seed": SEED, "table": values,
               "strategy_A_means": {k: float(v.mean()) for k, v in A.items()},
               "strategy_A_medians": {k: float(np.median(v)) for k, v in A.items()},
               "strategy_B_rejection_rates_pct": {k: rejection_rate(v) for k, v in B.items()}}
    ex.write_results(results, "Table 6 — Monte Carlo summary, raw against corrected moments")


if __name__ == "__main__":
    main()
