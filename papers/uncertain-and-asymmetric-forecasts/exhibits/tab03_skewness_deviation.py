#!/usr/bin/env python3
"""Table 3 of *Uncertain and Asymmetric Forecasts*: asymmetry against the signed distance from target.

Paper: Vansteenberghe, E. (2026), *Uncertain and Asymmetric Forecasts*,
working paper (``vansteenberghe2026uncertain``), Section 4.1, Table 3
(``tab:skew_dev_regs``).

Ordinary least squares of the individual Bowley skewness on the signed
deviation of that forecaster's density mean from the 2 per cent target,
standard errors clustered by survey round; columns (2) and (4) add a full set
of survey-round dummies, columns (3) and (4) trim deviations beyond two
points. A positive slope says asymmetry is coherent on average.

Inputs:  the ECB-SPF round files, through ``nu_measures.exhibit.load_ecb_panel``.
Outputs: ``tables/tab03_skewness_deviation.tex``, ``results/tab03_skewness_deviation.{json,md}``.

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use
this code, cite the paper above.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from nu_measures import conventions as cv
from nu_measures import econometrics as ec
from nu_measures import measures
from nu_measures.exhibit import Exhibit, load_ecb_panel

TEMPLATE = r"""\begin{table}[tbp]\centering
\caption{Asymmetry against the signed distance from target}\label{tab:skew_dev_regs}
\begin{tabular}{lcccc}
\toprule
 & (1) & (2) & (3) & (4) \\
\midrule
$\mu_{i,t}-\mu^{*}$ & $@b1@$ & $@b2@$ & $@b3@$ & $@b4@$ \\
                    & $(@s1@)$ & $(@s2@)$ & $(@s3@)$ & $(@s4@)$ \\
$t$                 & $@t1@$ & $@t2@$ & $@t3@$ & $@t4@$ \\
\midrule
Observations        & $@n1@$ & $@n2@$ & $@n3@$ & $@n4@$ \\
$R^2$               & $@r1@$ & $@r2@$ & $@r3@$ & $@r4@$ \\
Survey-round effects & No & Yes & No & Yes \\
Trimmed $|d_{i,t}|\leq 2$ & No & No & Yes & Yes \\
\bottomrule
\end{tabular}
\vspace{0.3em}
\parbox{0.95\linewidth}{\footnotesize \textit{Notes:} ordinary least squares of individual
Bowley skewness on the signed deviation of that forecaster's density mean from the $2\,\%$
target, ECB-SPF one-year-ahead inflation densities, 1999Q1 to the latest round. Standard
errors clustered by survey round in parentheses. Columns (2) and (4) add a full set of
survey-round dummies, so the slope is identified from disagreement within a round. A positive
and significant coefficient says that asymmetry is coherent on average, $c>0$ in the notation
of Section~\ref{sec:distance_asymmetry}. The small $R^2$ is the noise the index of
Section~\ref{sec:AC_measure} is built to handle. Script: \texttt{tab03\_skewness\_deviation.py}.}
\end{table}
"""


def thousands(n: int) -> str:
    return f"{n:,}".replace(",", "{,}")


def main() -> None:
    ex = Exhibit(__file__)
    pan = measures.add_nu(load_ecb_panel()).dropna(subset=["Bowley_Skewness"]).copy()
    pan["d"] = pan["Mean_spd"] - cv.TARGET
    cols = {}
    for k, (trim, fe) in enumerate(((False, False), (False, True), (True, False), (True, True)), 1):
        d = pan[pan["d"].abs() <= 2] if trim else pan
        y, x, g = d["Bowley_Skewness"].to_numpy(), d["d"].to_numpy(), d["Date"].astype(str).to_numpy()
        if fe:
            D = pd.get_dummies(d["Date"].astype(str), drop_first=True).to_numpy(dtype=float)
            res = ec.cluster_ols(y, np.column_stack([x, D]), g)
        else:
            res = ec.cluster_ols(y, x, g)
        cols[k] = {"slope": float(res.params[1]), "se": float(res.se[1]), "t": float(res.t[1]), "r2": float(res.r2),
                   "n": int(res.n), "round_effects": fe, "trimmed": trim}
        ex.say(f"({k}) slope {res.params[1]:.4f} ({res.se[1]:.4f}) t {res.t[1]:.2f} R2 {res.r2:.4f} n {res.n}")
    text = TEMPLATE
    for k, c in cols.items():
        text = (text.replace(f"@b{k}@", "%.4f" % c["slope"]).replace(f"@s{k}@", "%.4f" % c["se"])
                .replace(f"@t{k}@", "%.2f" % c["t"]).replace(f"@n{k}@", thousands(c["n"])).replace(f"@r{k}@", "%.3f" % c["r2"]))
    ex.write_table(text)
    ex.write_results({"columns": cols, "sample": "forecaster-rounds with a mean, a positive variance and a skewness"},
                     "Table 3 — asymmetry against the signed distance from target")


if __name__ == "__main__":
    main()
