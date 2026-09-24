#!/usr/bin/env python3
"""Figure 5 of *Uncertain and Asymmetric Forecasts*: the correction in the euro-area series.

Paper: Vansteenberghe, E. (forthcoming), *Uncertain and Asymmetric Forecasts*,
working paper (``vansteenberghe2026uncertain``), Section 3, Figure 5
(``fig:nu_series``); the agreement numbers of Section 3.4.

Panel (a): raw survey uncertainty (the round mean of the individual standard
deviations) and its two corrected counterparts, NU at the fitted ratio and NU
at a = b = 1, quarterly. Panel (b): the corrected series against the
euro-area Economic Policy Uncertainty basket, both standardised over their
overlap, the correlations in the legend.

Inputs:  the ECB-SPF round files; the EPU country workbook.
Outputs: ``figures/fig05_nu_series.{pdf,png}``, ``results/fig05_nu_series.{json,md}``.
Sample:  rounds 1999Q1--2026Q3; the EPU overlap.

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use
this code, cite the paper above.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from _common import C, nu_quarterly, style, z

from nu_measures.exhibit import Exhibit


def main() -> None:
    ex = Exhibit(__file__)
    style()
    M = nu_quarterly()
    M["t"] = M.index.to_timestamp()
    ov = M.dropna(subset=["EPU"])
    corr = {k: float(np.corrcoef(ov[k], ov["EPU"])[0, 1]) for k in ("raw_sd", "NU_unit", "NU_fitted")}
    c_uf = float(M["NU_unit"].corr(M["NU_fitted"]))
    ex.say(f"{len(M)} quarters; EPU overlap {len(ov)} ({ov.index.min()}..{ov.index.max()})")
    ex.say(f"agreement with the index: raw {corr['raw_sd']:.3f} | NU a=b=1 {corr['NU_unit']:.3f} | NU fitted {corr['NU_fitted']:.3f}; corr(NU unit, NU fitted) {c_uf:.3f}")

    fig, ax = plt.subplots(2, 1, figsize=(7.0, 4.6), sharex=True)
    ax[0].plot(M["t"], M["raw_sd"], color=C["raw"], lw=1.4, label="raw")
    ax[0].plot(M["t"], M["NU_unit"], color=C["cal"], lw=1.4, label=r"$\mathrm{NU}^{\mathrm{cal}}$")
    ax[0].plot(M["t"], M["NU_fitted"], color=C["fit"], lw=1.4, label=r"$\mathrm{NU}^{\mathrm{fit}}$")
    ax[0].legend(ncol=3, loc="upper left")
    ax[0].set_ylabel("standard deviation")
    ax[0].set_title("(a) the raw series and its two corrections", loc="left", fontsize=9)
    ax[1].plot(ov["t"], z(ov["EPU"]), color="k", lw=1.2, label="EPU index")
    ax[1].plot(ov["t"], z(ov["NU_unit"]), color=C["cal"], lw=1.4, label=r"$\mathrm{NU}^{\mathrm{cal}}$ ($r=%.2f$)" % corr["NU_unit"])
    ax[1].plot(ov["t"], z(ov["NU_fitted"]), color=C["fit"], lw=1.4, label=r"$\mathrm{NU}^{\mathrm{fit}}$ ($r=%.2f$)" % corr["NU_fitted"])
    ax[1].legend(ncol=3, loc="upper left")
    ax[1].set_ylabel("standardized")
    ax[1].set_title("(b) against a text-based index (raw: $r=%.2f$)" % corr["raw_sd"], loc="left", fontsize=9)
    ex.save_figure(fig)
    ex.write_results({"quarters": len(M), "epu_overlap": [len(ov), str(ov.index.min()), str(ov.index.max())],
                      "epu_correlation": corr, "corr_nu_unit_fitted": c_uf,
                      "series": M[["raw_sd", "NU_unit", "NU_fitted", "EPU"]].reset_index().assign(Q=lambda d: d["Q"].astype(str)).to_dict("records")},
                     "Figure 5 — the correction in the euro-area series")


if __name__ == "__main__":
    main()
