#!/usr/bin/env python3
"""Table 4 of *Uncertain and Asymmetric Forecasts*: inflation and growth uncertainty.

Paper: Vansteenberghe, E. (2026), *Uncertain and Asymmetric Forecasts*,
working paper (``vansteenberghe2026uncertain``), Section 5, Table 4
(``tab:ngu_orth``).

The matched inflation--growth panel (forecaster-rounds reporting both
densities), the forecasters carrying their own slope in the purge, the
full-sample correlation of the two round series, the agreement of the raw
growth dispersion and of NGU with the EPU basket, and the correlation of the
purged growth series built on the two NU readings.

Inputs:  the ECB-SPF round files (both blocks); real GDP; the EPU workbook.
Outputs: ``tables/tab04_ngu_orthogonalization.tex``, ``results/…{json,md}``.

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use
this code, cite the paper above.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from _common import growth_quarterly, matched_panel, nu_quarterly

from nu_measures import conventions as cv
from nu_measures import measures
from nu_measures.exhibit import Exhibit

TEMPLATE = r"""\begin{table}[tbp]\centering
\caption{Inflation and growth uncertainty}\label{tab:ngu_orth}
\begin{tabular}{lc}
\toprule
\multicolumn{2}{l}{\emph{the matched panel}}\\
forecaster-rounds with both densities, through 2026Q2 & $@n_fit@$ \\
\hspace{1em} through the latest round & $@n_all@$ \\
forecasters carrying their own slope ($\geq 10$ matched rounds) & $@own@$ \\
forecasters taking the within-forecaster slope & $@within@$ \\
\addlinespace
\multicolumn{2}{l}{\emph{correlation between the two round series}}\\
full sample, @span@ & $@corr@$ \\
\addlinespace
\multicolumn{2}{l}{\emph{agreement with the text-based uncertainty index}}\\
raw growth standard deviation & $@e_raw@$ \\
$\mathrm{NGU}$ & $@e_ngu@$ \\
\addlinespace
\multicolumn{2}{l}{\emph{the orthogonalized components}}\\
correlation of $\mathrm{NGU}\perp\mathrm{NU}$ built on the two NU series & $@c_orth@$ \\
\bottomrule
\end{tabular}
\vspace{0.3em}
\parbox{0.95\linewidth}{\footnotesize \textit{Notes:} the matched panel is the set of
forecaster-rounds reporting both an inflation and a GDP-growth density. The purge is
\eqref{eq:orth}, run forecaster by forecaster. Script: \texttt{tab04\_ngu\_orthogonalization.py}.}
\end{table}
"""


def thousands(n: int) -> str:
    return f"{n:,}".replace(",", "{,}")


def main() -> None:
    ex = Exhibit(__file__)
    m = matched_panel()
    cutoff_q = pd.Period(cv.FIT_MAX_PANEL_DATE, freq="Q")  # the survey quarter of the last round in the fit, 2026Q2
    n_all, n_fit = len(m), int((m["Q"] <= cutoff_q).sum())
    o_fit, detail = measures.orthogonalize(m, "NGU", "NU_fitted", by="FCT", period="Q")
    o_cal, _ = measures.orthogonalize(m, "NGU", "NU_unit", by="FCT", period="Q")
    c_orth = float(o_fit.corr(o_cal))
    own, within = int(detail["own_slope"].sum()), int((~detail["own_slope"]).sum())
    q = nu_quarterly()
    g = growth_quarterly()
    K = q[["NU_fitted", "NU_unit"]].join(g[["NGU"]], how="inner").dropna()
    corr_full = float(K["NU_fitted"].corr(K["NGU"]))
    corr_unit = float(K["NU_unit"].corr(K["NGU"]))
    g2 = g.dropna(subset=["EPU"])
    e_raw = float(np.corrcoef(g2["raw_sd"], g2["EPU"])[0, 1])
    e_ngu = float(np.corrcoef(g2["NGU"], g2["EPU"])[0, 1])
    span = f"{K.index.min()}--{K.index.max()}"
    ex.say(f"matched {n_all} (through 2026Q2 {n_fit}); forecasters {len(detail)}: own slope {own}, within slope {within}")
    ex.say(f"corr(NU fitted, NGU) full sample {span}: {corr_full:+.4f} (NU a=b=1: {corr_unit:+.4f}); EPU raw {e_raw:.3f} NGU {e_ngu:.3f}; corr of the two purged series {c_orth:.3f}")
    rep = {"@n_fit@": thousands(n_fit), "@n_all@": thousands(n_all), "@own@": str(own), "@within@": str(within),
           "@span@": span, "@corr@": "%+.2f" % corr_full, "@e_raw@": "%.2f" % e_raw, "@e_ngu@": "%.2f" % e_ngu,
           "@c_orth@": "%.2f" % c_orth}
    text = TEMPLATE
    for k, v in rep.items():
        text = text.replace(k, v)
    ex.write_table(text)
    ex.write_results({"matched_forecaster_rounds": n_all, "matched_through_2026Q2": n_fit, "forecasters": len(detail),
                      "own_slope": own, "within_slope": within, "corr_nu_fitted_ngu_full_sample": corr_full,
                      "corr_nu_unit_ngu_full_sample": corr_unit, "span": span, "epu_correlation_raw_growth_sd": e_raw,
                      "epu_correlation_ngu": e_ngu, "corr_purged_series_two_nu_readings": c_orth},
                     "Table 4 — inflation and growth uncertainty")


if __name__ == "__main__":
    main()
