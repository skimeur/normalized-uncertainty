#!/usr/bin/env python3
"""Figure 10 of *Uncertain and Asymmetric Forecasts*: Normalized Growth Uncertainty.

Paper: Vansteenberghe, E. (2026), *Uncertain and Asymmetric Forecasts*,
working paper (``vansteenberghe2026uncertain``), Section 5, Figure 10
(``fig:ngu_series``).

Panel (a): the round mean of the individual one-year-ahead growth density
standard deviations and its corrected counterpart, NGU. Panel (b): NGU and
the raw series against the euro-area EPU basket, standardised, the
correlations in the legend.

Inputs:  the ECB-SPF round files (growth block); real GDP (ECB Data Portal)
         for the Hodrick--Prescott trend; the EPU workbook.
Outputs: ``figures/fig10_ngu_series.{pdf,png}``, ``results/fig10_ngu_series.{json,md}``.

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use
this code, cite the paper above.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from _common import C, growth_quarterly, style, z

from nu_measures.exhibit import Exhibit


def main() -> None:
    ex = Exhibit(__file__)
    style()
    G = growth_quarterly()
    G["t"] = G.index.to_timestamp()
    g2 = G.dropna(subset=["EPU"])
    e_raw = float(np.corrcoef(g2["raw_sd"], g2["EPU"])[0, 1])
    e_ngu = float(np.corrcoef(g2["NGU"], g2["EPU"])[0, 1])
    ex.say(f"{len(G)} quarters; EPU agreement raw {e_raw:.3f}, NGU {e_ngu:.3f} ({len(g2)} quarters)")
    fig, ax = plt.subplots(2, 1, figsize=(7.0, 4.6), sharex=True)
    ax[0].plot(G["t"], G["raw_sd"], color=C["raw"], lw=1.4, label="raw growth s.d.")
    ax[0].plot(G["t"], G["NGU"], color=C["ngu"], lw=1.4, label="NGU")
    ax[0].legend(ncol=2, loc="upper left")
    ax[0].set_ylabel("standard deviation")
    ax[0].set_title("(a) growth densities, raw and corrected", loc="left", fontsize=9)
    ax[1].plot(g2["t"], z(g2["EPU"]), color="k", lw=1.2, label="EPU index")
    ax[1].plot(g2["t"], z(g2["NGU"]), color=C["ngu"], lw=1.4, label="NGU ($r=%.2f$)" % e_ngu)
    ax[1].plot(g2["t"], z(g2["raw_sd"]), color=C["raw"], lw=1.2, label="raw ($r=%.2f$)" % e_raw)
    ax[1].legend(ncol=3, loc="upper left")
    ax[1].set_ylabel("standardized")
    ax[1].set_title("(b) against the same text-based index", loc="left", fontsize=9)
    ex.save_figure(fig)
    ex.write_results({"quarters": len(G), "epu_overlap": len(g2), "epu_correlation_raw": e_raw, "epu_correlation_ngu": e_ngu},
                     "Figure 10 — Normalized Growth Uncertainty")


if __name__ == "__main__":
    main()
