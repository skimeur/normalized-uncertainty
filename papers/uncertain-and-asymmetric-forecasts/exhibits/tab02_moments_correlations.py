#!/usr/bin/env python3
"""Table 2 of *Uncertain and Asymmetric Forecasts*: moments of the reported densities, correlations.

Paper: Vansteenberghe, E. (forthcoming), *Uncertain and Asymmetric Forecasts*,
working paper (``vansteenberghe2026uncertain``), Section 4, Table 2
(``tab:momentscorr``).

Correlations of the mean, the coefficient of variation (standard deviation
over mean) and Bowley's skewness, across survey rounds (each moment averaged
within a round first) and across the individual forecaster-rounds.

Inputs:  the ECB-SPF round files, through ``nu_measures.exhibit.load_ecb_panel``.
Outputs: ``tables/tab02_moments_correlations.tex``, ``results/tab02_moments_correlations.{json,md}``.

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use
this code, cite the paper above.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from nu_measures import measures
from nu_measures.exhibit import Exhibit, load_ecb_panel

HEAD = r"""\begin{table}[tbp]\centering
\caption{Moments of the reported densities: correlations}\label{tab:momentscorr}
\begin{tabular}{lccc}
\toprule
\multicolumn{4}{l}{\emph{across survey rounds} ($n=@nr@$)}\\
 & Mean & CV & Bowley \\
\midrule
"""
MID = r"""
\addlinespace
\multicolumn{4}{l}{\emph{across individual forecaster-rounds} ($n=@ni@$)}\\
 & Mean & CV & Bowley \\
\midrule
"""
TAIL = r"""
\bottomrule
\end{tabular}
\vspace{0.3em}
\parbox{0.95\linewidth}{\footnotesize \textit{Notes:} Bowley's skewness as defined in
Section~\ref{sec:moments}; CV is a density's standard deviation over its mean. The upper panel
averages each moment within a survey round before correlating; the lower panel correlates the
forecaster-round observations themselves. The mean--asymmetry relation is positive at both
levels and an order of magnitude weaker at the level where the third moment is measured. Script: \texttt{tab02\_moments\_correlations.py}.}
\end{table}
"""


def mat(m: pd.DataFrame) -> str:
    return "\n".join(n + " & " + " & ".join("$" + ("%.2f" % m.loc[n, c]) + "$" for c in m.columns) + r" \\" for n in m.index)


def main() -> None:
    ex = Exhibit(__file__)
    pan = measures.add_nu(load_ecb_panel())
    sub = pan.dropna(subset=["Bowley_Skewness"]).copy()
    sub["sigma"] = np.sqrt(sub["Variance_spd"])
    rnd = sub.groupby("Date").agg(Mean=("Mean_spd", "mean"), SD=("sigma", "mean"), Skew=("Bowley_Skewness", "mean"))
    rnd["CV"] = rnd["SD"] / rnd["Mean"]
    ri = rnd[["Mean", "CV", "Skew"]].corr()
    ii = pd.DataFrame({"Mean": sub["Mean_spd"], "CV": sub["sigma"] / sub["Mean_spd"], "Skew": sub["Bowley_Skewness"]})
    ii = ii.replace([np.inf, -np.inf], np.nan).dropna()
    ic = ii.corr()
    ex.say(f"rounds {len(rnd)}; forecaster-rounds {len(sub)} ({len(ii)} with a finite CV)")
    ex.say(f"mean-skewness correlation: across rounds {ri.loc['Mean', 'Skew']:.3f}; across forecaster-rounds {ic.loc['Mean', 'Skew']:.3f}")
    text = HEAD.replace("@nr@", str(len(rnd))) + mat(ri) + MID.replace("@ni@", str(len(sub))) + mat(ic) + TAIL
    ex.write_table(text)
    ex.write_results({"rounds": len(rnd), "forecaster_rounds": len(sub), "across_rounds": ri.round(6).to_dict(),
                      "across_forecaster_rounds": ic.round(6).to_dict()}, "Table 2 — moments of the reported densities: correlations")


if __name__ == "__main__":
    main()
