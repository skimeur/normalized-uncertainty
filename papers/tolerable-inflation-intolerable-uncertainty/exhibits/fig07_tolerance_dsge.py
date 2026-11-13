"""Figure 5 (rework 2026-11-12; panel (b) dropped 2026-11-13, review_dsge_panelb_20261113.md):
is there a divine coincidence? Tolerance with unobserved slope and shocks.
Uses nk_tolerance_dsge.py (Gali 2015 calibration, high-gain limit of the paper's rule).
The comparison of a bank that sees the composition, one that knows share and slope, and one that observes
neither is reported in Table tab:dsge only (Eric 2026-11-13: panel (b) dropped); the json keeps it, with the
range of the full-information optimum over the published ranges."""

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.environ.get("NK_DIR", os.path.dirname(os.path.abspath(__file__))))
import matplotlib
import nk_tolerance_dsge as M

matplotlib.use("Agg")
import matplotlib.pyplot as plt

beta, eps, HG = 0.99, 9.0, 1e4
K = np.linspace(*M.K_RANGE, 11)
S = np.linspace(*M.S_RANGE, 11)
LAM = np.linspace(-1, 2, 601)
R = [0.0, 0.25, 0.5, 0.8]
res = {}
for rho in R:
    Lc = np.array([[[M.L_at(k, s, lm, rho, HG) for lm in LAM] for s in S] for k in K])
    EL = Lc.mean(axis=(0, 1))
    ib = EL.argmin()
    reg = (Lc - Lc.min(axis=2)[..., None]).max(axis=(0, 1))
    c = 1 - beta * rho
    lu = c / (eps * K[:, None] + c**2)
    opt = LAM[Lc.argmin(axis=2)]
    seen = S[None, :] * lu
    res[rho] = dict(
        known=float(opt.mean()),
        known_min=float(opt.min()),
        known_max=float(opt.max()),
        unknown=float(LAM[ib]),
        mmr=float(LAM[reg.argmin()]),
        seen=float(seen.mean()),
        seen_min=float(seen.min()),
        seen_max=float(seen.max()),
        EL=EL,
        ib=ib,
    )
fig, ax = plt.subplots(1, 2, figsize=(9.6, 3.8))
Sx = np.linspace(0.02, 0.98, 49)
for k, ls in ((M.K_RANGE[0], "--"), (np.mean(M.K_RANGE), "-"), (M.K_RANGE[1], ":")):
    ax[0].plot(
        Sx,
        [LAM[np.argmin([M.L_at(k, s, lm, 0.5, HG) for lm in LAM])] for s in Sx],
        color="#2a6f97",
        ls=ls,
        lw=1.6,
        label=f"s, κ known (κ = {k:.3f})",
    )
ax[0].axvspan(*M.S_RANGE, color="0.88", zorder=0)
ax[0].axhline(
    res[0.5]["unknown"], color="#c9852b", lw=1.8, label=f"s, κ unknown: {res[0.5]['unknown']:.2f}"
)
ax[0].set_xlabel("supply share s")
ax[0].set_ylabel("optimal tolerance")
ax[0].set_title("(a) known against unknown, ρ = 0.5")
ax[0].legend(frameon=False, fontsize=8)
x = np.linspace(0, 1, 101)
for rho, ls in ((0.0, "-"), (0.5, "--"), (0.8, ":")):
    lb = LAM[res[rho]["ib"]]

    def E(lm, rho=rho):
        return np.mean([[M.L_at(k, s, lm, rho, HG) for s in S] for k in K])

    Eb = E(lb)
    y = [100 * (E(f * lb) / Eb - 1) for f in x[::4]]
    ax[1].plot(x[::4], y, color="#c9852b", ls=ls, lw=1.7, label=f"ρ = {rho}")
ax[1].set_xlabel("tolerance, as a share of the optimum with s, κ unknown")
ax[1].set_ylabel("excess expected loss (%)")
ax[1].set_title("(b) the price of tolerating less")
ax[1].legend(frameon=False, fontsize=8)
for a in ax:
    a.grid(alpha=0.3, lw=0.5)
out = os.environ.get("FIG_OUT", os.path.dirname(os.path.abspath(__file__)))
fig.tight_layout()
fig.savefig(os.path.join(out, "fig07_tolerance_dsge.pdf"))
fig.savefig(os.path.join(out, "fig07_tolerance_dsge.png"), dpi=130)
json.dump(
    {str(r): {k: v for k, v in res[r].items() if k not in ("EL", "ib")} for r in R},
    open(os.path.join(out, "fig07_tolerance_dsge.json"), "w"),
    indent=1,
)
