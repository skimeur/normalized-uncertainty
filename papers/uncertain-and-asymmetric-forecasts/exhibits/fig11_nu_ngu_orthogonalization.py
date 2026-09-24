#!/usr/bin/env python3
"""Figure 11 of *Uncertain and Asymmetric Forecasts*: inflation and growth uncertainty, before and after the purge.

Paper: Vansteenberghe, E. (forthcoming), *Uncertain and Asymmetric Forecasts*,
working paper (``vansteenberghe2026uncertain``), Section 5, Figure 11
(``fig:nu_ngu_orth``).

Panel (a): the round series of NU (fitted ratio) and the same series purged
of growth uncertainty. Panel (b): NGU and the same series purged of
inflation uncertainty. The purge is the forecaster-by-forecaster
orthogonalisation (``nu_measures.measures.orthogonalize``): each forecaster
with at least ten matched rounds carries their own slope, the others the
within-forecaster slope; residuals are averaged by round and standardised.
Each panel's title carries the correlation of the two lines it draws.

Inputs:  the ECB-SPF round files (inflation and growth blocks); real GDP.
Outputs: ``figures/fig11_nu_ngu_orthogonalization.{pdf,png}``, ``results/…{json,md}``.

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use
this code, cite the paper above.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
from _common import C, matched_panel, style, z

from nu_measures import measures
from nu_measures.exhibit import Exhibit


def main() -> None:
    ex = Exhibit(__file__)
    style()
    m = matched_panel()
    o_ngu, detail = measures.orthogonalize(m, "NGU", "NU_fitted", by="FCT", period="Q")
    o_nu, _ = measures.orthogonalize(m, "NU_fitted", "NGU", by="FCT", period="Q")
    qm = m.groupby("Q").agg(NU=("NU_fitted", "mean"), NGU=("NGU", "mean"))
    r_nu = float(z(qm["NU"]).corr(o_nu))
    r_ngu = float(z(qm["NGU"]).corr(o_ngu))
    ex.say(f"matched panel {len(m)} forecaster-rounds, {len(detail)} forecasters ({int(detail['own_slope'].sum())} own slope)")
    ex.say(f"corr(NU, NU perp NGU) = {r_nu:.3f}; corr(NGU, NGU perp NU) = {r_ngu:.3f}")

    fig, ax = plt.subplots(2, 1, figsize=(7.0, 4.6), sharex=True)
    t = qm.index.to_timestamp()
    ax[0].plot(t, z(qm["NU"]), color=C["fit"], lw=1.4, label="NU")
    ax[0].plot(o_nu.index.to_timestamp(), o_nu, color=C["fit"], lw=1.1, ls=(0, (4, 2)), label=r"NU $\perp$ NGU")
    ax[0].legend(ncol=2, loc="upper left", handlelength=2.0)
    ax[0].set_ylabel("standardized")
    ax[0].set_title("(a) inflation uncertainty, before and after the purge ($r=%.2f$)" % r_nu, loc="left", fontsize=9)
    ax[1].plot(t, z(qm["NGU"]), color=C["ngu"], lw=1.4, label="NGU")
    ax[1].plot(o_ngu.index.to_timestamp(), o_ngu, color=C["ngu"], lw=1.1, ls=(0, (4, 2)), label=r"NGU $\perp$ NU")
    ax[1].legend(ncol=2, loc="upper left", handlelength=2.0)
    ax[1].set_ylabel("standardized")
    ax[1].set_title("(b) growth uncertainty, before and after the purge ($r=%.2f$)" % r_ngu, loc="left", fontsize=9)
    fig.align_ylabels(ax)
    ex.save_figure(fig)
    ex.write_results({"matched_forecaster_rounds": len(m), "forecasters": len(detail),
                      "own_slope": int(detail["own_slope"].sum()), "within_slope": int((~detail["own_slope"]).sum()),
                      "corr_nu_purged": r_nu, "corr_ngu_purged": r_ngu},
                     "Figure 11 — inflation and growth uncertainty, before and after the purge")


if __name__ == "__main__":
    main()
