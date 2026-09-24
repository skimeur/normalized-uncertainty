#!/usr/bin/env python3
"""Figure 5 of *Tolerable Inflation, Intolerable Uncertainty*: the purge in the euro-area series.

Paper: Vansteenberghe, E. (2026), *Tolerable Inflation, Intolerable Uncertainty*,
working paper, Banque de France (``vansteenberghe2026tolerable``), Section 3,
Figure 5 (``fig:nu``).

This is the figure of NU at a = b = 1. Panel (a): raw survey uncertainty --
the round mean of the individual one-year predictive standard deviations --
and its purged counterpart, each forecaster's standard deviation divided by
sqrt(1 + (mu_i - 2)_+), quarterly from 1999Q1; nothing drawn depends on a
fitted coefficient. The last round postdates the sample the paper's fitted
results use and is drawn dashed. Panel (b): the purged series against the
euro-area Economic Policy Uncertainty basket, both standardised over their
overlap, with the two correlations printed.

Inputs:  the ECB-SPF round files (through ``load_ecb_panel``); the EPU workbook.
Outputs: ``figures/fig05_nu_purge.{pdf,png}``, ``results/fig05_nu_purge.{json,md}``.
Sample:  every round, 1999Q1--2026Q3; the correlations on the overlap with the index, 1999Q1--2026Q2.

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use
this code, cite the paper above.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from _common import style

from nu_measures import measures
from nu_measures.exhibit import Exhibit, load_ecb_panel, load_epu

RC = {"font.family": "serif", "font.serif": ["DejaVu Serif"], "mathtext.fontset": "cm", "font.size": 9.0, "axes.linewidth": 0.6}
C_RAW, C_NU = "#b2182b", "#2166ac"
#: The shaded episodes: the 2021--23 surge, and the rounds after the fitted sample.
EPISODES = [("2021-07-01", "2023-06-30"), ("2026-01-01", "2026-09-30")]
LAST_FITTED_QUARTER = "2026Q2"


def main() -> None:
    ex = Exhibit(__file__)
    style(RC)
    q = measures.quarterly(measures.nu_series(load_ecb_panel()))
    m = q.join(load_epu(), how="left")
    m.index = m.index.astype(str)
    ov = m[m.index <= LAST_FITTED_QUARTER].dropna(subset=["EPU"])
    c_nu = float(np.corrcoef(ov["NU_unit"], ov["EPU"])[0, 1])
    c_raw = float(np.corrcoef(ov["raw_sd"], ov["EPU"])[0, 1])
    c_fit = float(np.corrcoef(ov["NU_fitted"], ov["EPU"])[0, 1])
    ex.say(f"{len(m)} quarters {m.index[0]}..{m.index[-1]}; overlap with the index {len(ov)} quarters through {ov.index[-1]}")
    ex.say(f"corr with EPU: purged (a = b = 1) {c_nu:.3f}, raw {c_raw:.3f}, purged at the fitted ratio {c_fit:.3f}")

    t = pd.PeriodIndex(m.index, freq="Q").to_timestamp()
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(6.35, 4.6), sharex=True)
    for lo, hi in EPISODES:
        ax.axvspan(pd.Timestamp(lo), pd.Timestamp(hi), color="0.93", zorder=0)
        ax2.axvspan(pd.Timestamp(lo), pd.Timestamp(hi), color="0.93", zorder=0)
    n = len(m)
    raw, nu = m["raw_sd"].to_numpy(), m["NU_unit"].to_numpy()
    ax.plot(t[: n - 1], raw[: n - 1], color=C_RAW, lw=1.5, zorder=3, label="raw uncertainty")
    ax.plot(t[n - 2 :], raw[n - 2 :], color=C_RAW, lw=1.5, ls=(0, (3, 2)), zorder=3)
    ax.plot(t[: n - 1], nu[: n - 1], color=C_NU, lw=1.5, zorder=4, label=r"purged: $\mathrm{NU}$, calibrated $\sqrt{1+(d^{e})_{+}}$")
    ax.plot(t[n - 2 :], nu[n - 2 :], color=C_NU, lw=1.5, ls=(0, (3, 2)), zorder=4)
    ax.fill_between(t, nu, raw, where=raw >= nu, color=C_RAW, alpha=0.12, lw=0, zorder=1)
    ax.set_ylabel("predictive s.d. (pp)")
    ax.legend(loc="upper left", frameon=False, fontsize=8.2)
    ax.text(0.985, 0.92, "(a)", transform=ax.transAxes, ha="right", va="top")

    def zs(x):
        return (x - x.mean()) / x.std()

    tb = pd.PeriodIndex(ov.index, freq="Q").to_timestamp()
    ax2.plot(tb, zs(ov["EPU"]), color="0.45", lw=1.2, zorder=2, label="EPU, euro-area basket")
    ax2.plot(tb, zs(ov["NU_unit"]), color=C_NU, lw=1.5, zorder=3, label=r"purged: $\mathrm{NU}$, calibrated")
    ax2.set_ylabel("standardised")
    ax2.legend(loc="upper left", frameon=False, fontsize=8.2)
    ax2.text(0.985, 0.92, "(b)", transform=ax2.transAxes, ha="right", va="top")
    ax2.text(0.985, 0.06, rf"corr with EPU: purged ${c_nu:.2f}$, raw ${c_raw:.2f}$", transform=ax2.transAxes,
             ha="right", va="bottom", fontsize=8.0)
    for a in (ax, ax2):
        a.spines[["top", "right"]].set_visible(False)
        a.margins(x=0.01)
    fig.align_ylabels()
    fig.tight_layout(h_pad=0.7)
    ex.save_figure(fig)
    ex.write_results({"quarters": int(n), "first": m.index[0], "last": m.index[-1], "overlap_quarters": int(len(ov)),
                      "overlap_last": ov.index[-1], "corr_epu": {"raw": c_raw, "NU_unit": c_nu, "NU_fitted": c_fit},
                      "epu_countries": getattr(load_epu(), "attrs", {}).get("countries"),
                      "series": {k: {"raw_sd": float(r["raw_sd"]), "NU_unit": float(r["NU_unit"]), "NU_fitted": float(r["NU_fitted"]),
                                     "EPU": (None if pd.isna(r["EPU"]) else float(r["EPU"]))} for k, r in m.iterrows()}},
                     "Figure 5 — the purge in the euro-area series")


if __name__ == "__main__":
    main()
