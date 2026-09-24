#!/usr/bin/env python3
"""Figure 8 and Table 5 of *Tolerable Inflation, Intolerable Uncertainty*: Abel, Rich, Song and Tracy (2016) replicated and extended.

Paper: Vansteenberghe, E. (2026), *Tolerable Inflation, Intolerable Uncertainty*,
working paper, Banque de France (``vansteenberghe2026tolerable``), Appendix
(``app:abel_replication``): Figure 8 (``fig:abel_scatter``) and Table 5
(``tab:abel_replication``).

Section 3.2 / Table IV of Abel, Rich, Song and Tracy (Journal of Applied
Econometrics, 2016), one-year-ahead HICP inflation, re-estimated on this
paper's ECB-SPF panel: the round mean of the individual predictive variances
(square root) and the round median of the individual interquartile ranges,
regressed on the round mean or median of the point forecasts, Newey--West at
four lags. Their sample (1999Q1--2013Q4, 60 rounds), the extension to the
round conducted in 2026Q2 (110 rounds), and three departures: their closure
of the open-ended bins (twice the adjacent closed width) instead of the
realized range of inflation, the rounds before the 2024Q4 grid change only,
and their respondent selection (point and density both reported, the
density summing to 100, no renormalization). Their published estimates are
carried as printed.

Conventions of the moments here are theirs: each bin's mass is spread
uniformly over its closed interval (so the variance is the interval
distribution's), quartiles are interpolated inside the bin, and the outer
bins are closed on the realized range of inflation as the paper's panel
closes them (``HICP_MIN``, ``HICP_MAX``).

Inputs:  the ECB-SPF round files, through ``load_flat_panel``.
Outputs: ``figures/figA_abel2016_replication.{pdf,png}``, ``tables/figA_abel2016_replication.tex``,
         ``results/figA_abel2016_replication.{json,md}``.

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use
this code, cite the paper above.
"""

from __future__ import annotations

import re
from math import erf, sqrt

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from _common import style

from nu_measures import conventions as cv
from nu_measures import econometrics as ec
from nu_measures import law
from nu_measures.exhibit import Exhibit, load_flat_panel

ABEL_END = pd.Timestamp("2013-09-01")  # the 2013Q4 round, at formation time
GRID_BREAK = pd.Timestamp(cv.QUESTIONNAIRE_CHANGE_PANEL_DATE)  # the 2024Q4 round, first on the new grid
PAPER_END = pd.Timestamp("2026-03-01")  # the 2026Q2 round, the paper's cutoff
PRE, POST = list(cv.GRID_PRE_BINS), list(cv.GRID_POST_BINS)
PRE_INNER = [(-1, -0.5), (-0.5, 0), (0, 0.5), (0.5, 1), (1, 1.5), (1.5, 2), (2, 2.5), (2.5, 3), (3, 3.5), (3.5, 4), (4.0, 4.5), (4.5, 5)]
POST_INNER = [(-0.75, -0.25), (-0.25, 0.25), (0.25, 0.75), (0.75, 1.25), (1.25, 1.75), (1.75, 2.25), (2.25, 2.75), (2.75, 3.25),
              (3.25, 3.75), (3.75, 4.25), (4.25, 4.75)]
#: Abel, Rich, Song and Tracy (2016), Table IV, p. 547, HICP one year ahead: carried as printed.
PUBLISHED = {"computed": False, "T": 60, "var_b": -0.097, "var_se": 0.076, "var_r2": 0.048, "iqr_b": -0.071, "iqr_se": 0.081, "iqr_r2": 0.008}
RC = {"font.family": "serif", "font.serif": ["DejaVu Serif"], "mathtext.fontset": "cm", "font.size": 9.0, "axes.linewidth": 0.7,
      "xtick.major.width": 0.7, "ytick.major.width": 0.7}
BLUE, ORANGE, LINE = "#1f4e79", "#d1670a", "#222222"

TEMPLATE = r"""\begin{table}[tbp]
\centering
\small
\begin{tabular}{lccccc}
\toprule
 & & \multicolumn{2}{c}{Variance-based \eqref{eq:abel8}}
   & \multicolumn{2}{c}{IQR-based \eqref{eq:abel9}}\\
\cmidrule(lr){3-4}\cmidrule(lr){5-6}
Sample and specification & $T$ & $\hat\beta$ & $R^{2}$ & $\hat\beta$ & $R^{2}$\\
\midrule
\addlinespace[2pt]
\multicolumn{6}{l}{\textit{Panel A --- as published, and as replicated}}\\[2pt]
\quad\citet{abel2016measurement}, Table~IV & $60$ & $-0.097$ & $0.048$ & $-0.071$ & $0.008$\\
                                           &      & $(0.076)$ &        & $(0.081)$ & \\
\quad This paper, their sample             & @abel_window@\\
\quad This paper, extended to 2026Q2       & @full@\\
\addlinespace[4pt]
\multicolumn{6}{l}{\textit{Panel B --- the same slope under three departures}}\\[2pt]
\quad Their tail closure, their sample     & @abel_bins_window@\\
\quad Their tail closure, extended         & @abel_bins_full@\\
\quad Pre-2024Q4 histogram grid only       & @pre_grid@\\
\quad Their respondent filter, extended    & @abel_filter_full@\\
\bottomrule
\end{tabular}
\caption{Uncertainty and the aggregate point prediction: \citet{abel2016measurement} Table~IV
(one-year-ahead HICP inflation), replicated on their sample and extended. Dependent variables:
$\bar\sigma_{q,t}$, the square root of the cross-sectional mean of individual predictive
variances; $\tilde\phi^{\textsc{med}}_{q,t}$, the cross-sectional median of individual
interquartile ranges. The regressor is the cross-sectional mean (variance-based) or median
(IQR-based) of point forecasts. Newey--West standard errors with four lags in parentheses.
Their sample is 1999Q1--2013Q4; the extension runs to the round conducted in 2026Q2, this
paper's cutoff. Panel~B's first two rows close the open-ended bins as they do rather than on the
realised range of inflation; the third drops every round on the histogram grid the ECB-SPF
adopted in 2024Q4; the fourth imposes their respondent selection in place of renormalisation.
$^{***}p<0.01$, $^{**}p<0.05$, $^{*}p<0.10$.}
\label{tab:abel_replication}
\end{table}
"""


def edges(grid: str, convention: str) -> list[tuple[float, float]]:
    """The closed bins: outer bins on the realized range of inflation (``ours``) or twice the adjacent width (``abel``)."""
    lo_edge, hi_edge, inner = (-1.0, 5.0, PRE_INNER) if grid == "pre" else (-0.75, 4.75, POST_INNER)
    w = 2 * (inner[0][1] - inner[0][0])
    if convention == "abel":
        return [(lo_edge - w, lo_edge)] + inner + [(hi_edge, hi_edge + w)]
    return [(min(lo_edge, cv.HICP_MIN), lo_edge)] + inner + [(hi_edge, max(hi_edge, cv.HICP_MAX))]


def row_moments(p: np.ndarray, ed: list[tuple[float, float]], renormalise: bool) -> tuple[float, float]:
    """Variance of the interval distribution and the interquartile range of one density (per cent masses)."""
    tot = p.sum()
    if tot <= 0 or (not renormalise and not (99.0 <= tot <= 101.0)):
        return np.nan, np.nan
    e1 = sum(p[k] * (lo + hi) / 2.0 for k, (lo, hi) in enumerate(ed)) / tot
    e2 = sum(p[k] * (lo * lo + lo * hi + hi * hi) / 3.0 for k, (lo, hi) in enumerate(ed)) / tot
    var = max(e2 - e1 * e1, 0.0)
    cdf = np.cumsum(p) / tot * 100.0

    def q(pct):
        for i, c in enumerate(cdf):
            if c >= pct:
                lo, hi = ed[i]
                prev = 0.0 if i == 0 else cdf[i - 1]
                return None if c - prev <= 0 else lo + (pct - prev) / (c - prev) * (hi - lo)
        return None

    a, b = q(25.0), q(75.0)
    return var, (np.nan if a is None or b is None else b - a)


def prepared_panel() -> pd.DataFrame:
    df = load_flat_panel()
    df["Date"] = pd.to_datetime(df["Date"]) - pd.DateOffset(years=1)
    df = df.sort_values(["Date", "FCT_SOURCE"]).reset_index(drop=True)
    df["]-inf, - 1]"] = df.loc[:, list(cv.GRID_PRE_LEFT_SOURCES)].sum(axis=1, min_count=1)
    df["[5,+inf["] = df.loc[:, list(cv.GRID_PRE_RIGHT_SOURCES)].sum(axis=1, min_count=1)
    df = df.loc[:, ["Date", "FCT_SOURCE", "POINT"] + PRE + POST]
    return df.dropna(subset=PRE + POST, how="all").reset_index(drop=True)


def aggregate(df: pd.DataFrame, convention: str = "ours", abel_filter: bool = False) -> pd.DataFrame:
    d = df[df["POINT"].notna()].copy() if abel_filter else df.copy()
    Ppre = d[PRE].apply(pd.to_numeric, errors="coerce").fillna(0.0).to_numpy(dtype=float)
    Ppost = d[POST].apply(pd.to_numeric, errors="coerce").fillna(0.0).to_numpy(dtype=float)
    is_post = (d["Date"] >= GRID_BREAK).to_numpy()
    ed = {"pre": edges("pre", convention), "post": edges("post", convention)}
    V, Q = np.empty(len(d)), np.empty(len(d))
    for i in range(len(d)):
        V[i], Q[i] = row_moments(Ppost[i] if is_post[i] else Ppre[i], ed["post" if is_post[i] else "pre"], renormalise=not abel_filter)
    d = d.assign(V=V, IQR=Q).dropna(subset=["V"])
    g = d.groupby("Date")
    A = pd.DataFrame({"sigma_bar": np.sqrt(g["V"].mean()), "iqr_med": g["IQR"].median(), "point_mean": g["POINT"].mean(),
                      "point_med": g["POINT"].median(), "dis_sd": g["POINT"].std(),
                      "dis_iqr": g["POINT"].apply(lambda x: x.quantile(0.75) - x.quantile(0.25)), "n_resp": g["POINT"].count()})
    return A[A.index <= PAPER_END].sort_index()


def stars(t: float) -> tuple[str, float]:
    p = 2 * (1 - 0.5 * (1 + erf(abs(t) / sqrt(2))))
    return ("***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.10 else ""), p


def leg(A: pd.DataFrame) -> dict:
    """The bivariate and the joint regressions of both measures on one round sample."""
    out = {"T": int(len(A)), "first": str(A.index.min().date()), "last": str(A.index.max().date()),
           "point_mean_range": [float(A["point_mean"].min()), float(A["point_mean"].max())]}
    for tag, ylab, xlab, dlab in (("var", "sigma_bar", "point_mean", "dis_sd"), ("iqr", "iqr_med", "point_med", "dis_iqr")):
        s = A.dropna(subset=[ylab, xlab])
        r = ec.hac_ols(s[ylab].to_numpy(), s[xlab].to_numpy(), lags=4)
        st, p = stars(r.t[1])
        out[tag] = {"b": float(r.params[1]), "se": float(r.se[1]), "t": float(r.t[1]), "p": p, "stars": st, "r2": float(r.r2), "n": r.n}
        sj = A.dropna(subset=[ylab, xlab, dlab])
        rj = ec.hac_ols(sj[ylab].to_numpy(), np.column_stack([sj[dlab].to_numpy(), sj[xlab].to_numpy()]), lags=4)
        out[f"{tag}_joint"] = {"b_dispersion": float(rj.params[1]), "se_dispersion": float(rj.se[1]), "b_point": float(rj.params[2]),
                               "se_point": float(rj.se[2]), "r2": float(rj.r2), "n": rj.n}
    return out


def cells(o: dict) -> str:
    v, i = o["var"], o["iqr"]
    return (f"${o['T']}$ & ${v['b']:+.3f}{('^{' + v['stars'] + '}') if v['stars'] else ''}$ & ${v['r2']:.3f}$ & "
            f"${i['b']:+.3f}{('^{' + i['stars'] + '}') if i['stars'] else ''}$ & ${i['r2']:.3f}$\\\\\n"
            f"                                           &      & $({v['se']:.3f})$ &        & $({i['se']:.3f})$ & ")


def main() -> None:
    ex = Exhibit(__file__)
    style(RC)
    df = prepared_panel()
    A, Aa, Af = aggregate(df, "ours"), aggregate(df, "abel"), aggregate(df, "ours", abel_filter=True)
    legs = {"abel_window": leg(A[A.index <= ABEL_END]), "full": leg(A), "pre_grid": leg(A[A.index < GRID_BREAK]),
            "abel_bins_window": leg(Aa[Aa.index <= ABEL_END]), "abel_bins_full": leg(Aa), "abel_filter_window": leg(Af[Af.index <= ABEL_END]),
            "abel_filter_full": leg(Af)}
    for k, o in legs.items():
        ex.say(f"{k:<20} T={o['T']:>3}  var b {o['var']['b']:+.3f} ({o['var']['se']:.3f}){o['var']['stars']:<3} R2 {o['var']['r2']:.3f} | "
               f"iqr b {o['iqr']['b']:+.3f} ({o['iqr']['se']:.3f}){o['iqr']['stars']:<3} R2 {o['iqr']['r2']:.3f}")
    early = A[A.index <= ABEL_END]
    above = early["point_mean"] - cv.TARGET
    ex.say(f"their sample: the consensus left the target upward in {(above > 0).sum()} of {len(early)} rounds, never by more than {above.max():.2f}")
    # The appendix's reading of their null through the law: the arms form on their window and on the full sample,
    # fitted on their variance-based measure squared (the mean individual variance) against the mean point forecast
    # minus the target; the above-target regressor's spread and its sum, the "gap they could have priced".
    arms_text = {}
    for k, S in (("their_window", early), ("full", A)):
        y, d = S["sigma_bar"].to_numpy() ** 2, S["point_mean"].to_numpy() - cv.TARGET
        f = law.arms_fit(y, d, hac_lags=4)
        arms_text[k] = {**f.summary_row(), "sd_of_positive_gap": float(np.maximum(d, 0).std()),
                        "sum_of_positive_gap": float(np.maximum(d, 0).sum())}
    ex.say(f"arms on their window: b+ {arms_text['their_window']['b_plus']:+.2f}; sd of (d)+ {arms_text['their_window']['sd_of_positive_gap']:.3f} "
           f"against {arms_text['full']['sd_of_positive_gap']:.3f} on the full sample; sum of (d)+ {arms_text['their_window']['sum_of_positive_gap']:.1f} against "
           f"{arms_text['full']['sum_of_positive_gap']:.1f}")
    text = TEMPLATE
    for k in ("abel_window", "full", "abel_bins_window", "abel_bins_full", "pre_grid", "abel_filter_full"):
        text = text.replace(f"@{k}@", cells(legs[k]))
    if re.search(r"@[a-z_]+@", text):
        raise SystemExit("unfilled placeholder in the table")
    ex.write_table(text)

    fig, axes = plt.subplots(1, 2, figsize=(6.5, 3.15))
    panels = [(axes[0], "point_mean", "sigma_bar", r"mean point forecast $\bar f_{q,t}$ (%)", r"$\bar\sigma_{q,t}$  (variance-based)", "(a)  variance-based"),
              (axes[1], "point_med", "iqr_med", r"median point forecast $\tilde f^{\rm MED}_{q,t}$ (%)", r"$\tilde\phi^{\rm MED}_{q,t}$  (IQR-based)", "(b)  IQR-based")]
    for ax, xc, yc, xlab, ylab, tag in panels:
        S = A.dropna(subset=[xc, yc])
        early, late = S[S.index <= ABEL_END], S[S.index > ABEL_END]
        ax.axvline(cv.TARGET, color="0.75", lw=0.7, ls=":", zorder=0)
        ax.scatter(early[xc], early[yc], s=17, facecolor="none", edgecolor=BLUE, lw=0.9, label="1999Q1–2013Q4 (Abel sample)", zorder=3)
        ax.scatter(late[xc], late[yc], s=17, facecolor="none", edgecolor=ORANGE, lw=0.9, label="2014Q1–2026Q2 (extension)", zorder=3)
        bf = ec.hac_ols(S[yc].to_numpy(), S[xc].to_numpy(), lags=4).params
        be = ec.hac_ols(early[yc].to_numpy(), early[xc].to_numpy(), lags=4).params
        gx = np.linspace(S[xc].min() - 0.08, S[xc].max() + 0.08, 50)
        ax.plot(gx, bf[0] + bf[1] * gx, color=LINE, lw=1.3, zorder=2, label=f"full sample: $\\hat\\beta={bf[1]:+.3f}$")
        gxe = np.linspace(early[xc].min() - 0.08, early[xc].max() + 0.08, 50)
        ax.plot(gxe, be[0] + be[1] * gxe, color=BLUE, lw=1.1, ls="--", zorder=2, label=f"Abel sample: $\\hat\\beta={be[1]:+.3f}$")
        ax.set_xlabel(xlab)
        ax.set_ylabel(ylab)
        ax.set_title(tag, fontsize=9, loc="left", pad=4)
        ax.legend(fontsize=6.4, loc="upper left", handlelength=1.5, borderpad=0.25, labelspacing=0.28, frameon=True, facecolor="white",
                  edgecolor="none", framealpha=0.88)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
    fig.tight_layout(pad=0.6)
    plt.rcParams.update({"savefig.dpi": 220, "savefig.bbox": "tight"})
    ex.save_figure(fig)
    ex.write_results({"published_table_iv": PUBLISHED, "legs": legs, "tail_closure": {"hicp_min": cv.HICP_MIN, "hicp_max": cv.HICP_MAX},
                      "their_sample_above_target": {"rounds": int((above > 0).sum()), "of": int(len(early)), "max_gap": float(above.max())},
                      "arms_form_on_their_measure": arms_text},
                     "Figure 8 and Table 5 — Abel, Rich, Song and Tracy (2016) replicated and extended")


if __name__ == "__main__":
    main()
