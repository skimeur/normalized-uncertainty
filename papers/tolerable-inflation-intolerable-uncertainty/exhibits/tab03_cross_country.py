#!/usr/bin/env python3
"""Table 3 of *Tolerable Inflation, Intolerable Uncertainty*: cross-country growth regressions, raw and purged inflation volatility.

Paper: Vansteenberghe, E. (2026), *Tolerable Inflation, Intolerable Uncertainty*,
working paper, Banque de France (``vansteenberghe2026tolerable``), Section 3,
Table 3 (``tab:crosscountry``).

Barro (1995), Table 2, rebuilt from the Barro--Lee source over his own
periods (1965--75, 1975--85, 1985--90) with his full control set, period
fixed effects and standard errors clustered by country, and the inflation
experience entered five ways: mean inflation alone, the raw within-period
standard deviation alone, the purged measure sigma / sqrt(1 + |pi_bar|) alone
(pi_bar in percentage points; no target, nothing estimated), and mean
inflation together with each of the two. Inflation moments are period means
and standard deviations of the annual log change in the consumer price index
of the Global Macro Database, untrimmed. The wild-cluster row is a restricted
Rademacher bootstrap (999 draws, clustered by country) for the volatility
term of the last two columns.

The build follows the paper's faithful reconstruction: Barro--Lee's five-year
blocks aligned to his periods (verified against the year values of the
World-Bank series), log income from the Summers--Heston series in 1985
international prices, government consumption net of defence and education,
the political-rights index rescaled to [0, 1], life expectancy from the
lagged block, the interaction of demeaned log income with the fitted
human-capital index iterated to a fixed point, and growth as the log change
of Summers--Heston real per capita GDP between the period's endpoints. The
rule-of-law index is not in the Barro--Lee distribution and is not included.

Inputs:  ``$NU_DATA_DIR/crosscountry/barlee_long.csv`` (the Barro--Lee data set in long form, one
         row per country and year, with the SHCODE country code and, in the same file or in
         ``barlee_selected_x_gmd_1960_1990.csv`` beside it, the ISO3 crosswalk);
         ``$NU_DATA_DIR/crosscountry/gmd*.parquet`` or ``gmd*.csv`` (the Global Macro Database,
         columns ``ISO3``, ``year``, ``infl``). The built panel is written to
         ``$NU_DATA_DIR/derived/crosscountry_panel.csv`` and read back from there when the
         Barro--Lee source is absent.
Outputs: ``tables/tab03_cross_country.tex``, ``results/tab03_cross_country.{json,md}``.

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use
this code, cite the paper above.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from nu_measures import conventions as cv
from nu_measures import econometrics as ec
from nu_measures import paths
from nu_measures.exhibit import Exhibit

PERIODS = [1965, 1975, 1985]
BLOCKS = {1965: [2, 3], 1975: [4, 5], 1985: [6]}  # Barro--Lee five-year blocks making up each period (flows)
STATE_YEAR = {1965: 1965, 1975: 1975, 1985: 1985}  # start-of-period states
LIFE_BLOCK = {1965: 1, 1975: 3, 1985: 5}  # 1960--64, 1970--74, 1980--84
INFLATION_YEARS = {1965: (1965, 1974), 1975: (1975, 1984), 1985: (1985, 1990)}
CONTROLS = ["lgdp", "sm", "sf", "llife", "lfert", "gcons", "geduc", "bmp", "tot", "dem", "dem2", "inv"]
BOOTSTRAP = {"draws": 999, "seed": 20260818}
SPECS = [("1", None, True), ("2", "raw", False), ("3", "purged", False), ("4", "raw", True), ("5", "purged", True)]
ROWS = [("pi_bar", r"Mean inflation $\bar\pi$"), ("raw", r"Raw $\sigma_\pi$"), ("purged", r"Purged $\sigma_\pi/\sqrt{1+|\bar\pi|}$")]

NOTES = r"""\vspace{0.2em}
\begin{minipage}{0.90\linewidth}\footnotesize
\textit{Notes:} Each column is one growth regression on \citeauthor{barro1995inflation}'s panel
over his own periods---1965--75, 1975--85 and 1985--90; the dependent variable is the country's
average annual growth of real GDP per capita over the period, in 1985 international prices. Every
column includes his full control set, period fixed effects, and standard errors clustered by
country; $t$-statistics are in parentheses. The columns differ only in which summary of the
inflation experience enters: \textbf{(1)} mean inflation $\bar\pi$ alone; \textbf{(2)} the raw
within-period standard deviation $\sigma_\pi$ alone; \textbf{(3)} the purged measure alone;
\textbf{(4)} mean inflation together with the raw standard deviation; \textbf{(5)} mean inflation
together with the purged measure. Comparing~(4) with~(5) is the point of the exercise: the raw
standard deviation is virtually zero conditional on the level, as \citeauthor{barro1995inflation}
reports, and masks it; the purged measure is significant at five percent and the level's own
coefficient sharpens beside it.
\emph{Raw} is $\sigma_\pi$; \emph{purged} divides it by $\sqrt{1+|\bar\pi|}$. That deflator uses no
inflation target---no country in these periods had announced one---and contains nothing estimated:
it is $\sqrt{1+|\bar\pi|}$ exactly, with $\bar\pi$ in percentage points, the units in which
the envelope of \eqref{eq:var_decomp} is fitted. The dependent variable is a fraction: in column~(5) a
one-standard-deviation rise in the purged measure is worth $@osd_purged@$ percentage points of
annual growth, against $@osd_raw@$ for the raw measure in column~(4). The wild-cluster row
reports restricted Rademacher bootstrap $p$-values ($999$ draws, clustered by country)
for the volatility term of columns~(4) and~(5).
The controls are \citeauthor{barro1995inflation}'s own: initial income, male and female school
attainment at the secondary and higher levels, the interaction of initial income with human
capital as he defines it, life expectancy, fertility, government consumption net of education and
defence, public education spending, the black-market premium, the terms-of-trade change, the
investment ratio, and the political-rights index with its square. The one control of his we cannot
match is the rule-of-law index, which is not in the \citeauthor{barro1995inflation}--Lee
distribution and which he himself uses among his instruments. Inflation moments are period means
and standard deviations of the annual log change in the consumer price index
\citep{muller2025global}, untrimmed, as in his own exercise. Script: \texttt{tab03\_cross\_country.py}.
$^{***}p<0.01$, $^{**}p<0.05$, $^{*}p<0.1$.
\end{minipage}
\end{table}
"""


# ------------------------------------------------------------------ the build, from the Barro--Lee source
def barro_lee_sources(long_csv: Path):
    """Country constants (the block variables), the year-by-year series, and the ISO3 crosswalk."""
    L = pd.read_csv(long_csv, low_memory=False)
    L["SHCODE"] = pd.to_numeric(L["SHCODE"], errors="coerce")
    L["year"] = pd.to_numeric(L["year"], errors="coerce")
    W = L.groupby("SHCODE").agg({c: "first" for c in L.columns if c not in ("SHCODE", "year")})
    W = W.apply(pd.to_numeric, errors="coerce")
    byyr = {}
    for v in ["gdpsh5", "gdpwb", "syrm", "hyrm", "syrf", "hyrf", "fert"]:
        t = L.assign(**{v: pd.to_numeric(L[v], errors="coerce")}).pivot_table(index="SHCODE", columns="year", values=v, aggfunc="first")
        byyr[v] = t.apply(pd.to_numeric, errors="coerce").astype(float)
    if "ISO3" in L.columns:
        iso = L[["SHCODE", "ISO3"]].dropna().drop_duplicates("SHCODE").set_index("SHCODE")["ISO3"]
    else:
        S = pd.read_csv(long_csv.parent / "barlee_selected_x_gmd_1960_1990.csv", usecols=["SHCODE", "ISO3"], low_memory=False)
        S["SHCODE"] = pd.to_numeric(S["SHCODE"], errors="coerce")
        iso = S.dropna().drop_duplicates("SHCODE").set_index("SHCODE")["ISO3"]
    return W, byyr, iso


def block_alignment(W, byyr) -> list[str]:
    """Verify that block x of the growth series covers 1955 + 5x .. 1960 + 5x."""
    g = byyr["gdpwb"]
    out = []
    for k in range(1, 7):
        y0 = 1955 + 5 * k
        gr = (np.log(g[y0 + 5]) - np.log(g[y0])) / 5.0
        r = pd.concat([gr.rename("a"), W[f"grwb{k}"].rename("b")], axis=1).dropna()
        out.append(f"grwb{k} vs {y0}-{y0 + 5}: corr {r['a'].corr(r['b']):+.3f} (n={len(r)})")
    return out


def block_mean(W, stem, blocks, carry=None):
    cols = [f"{stem}{b}" for b in blocks if f"{stem}{b}" in W.columns]
    s = W[cols].mean(axis=1, skipna=True) if cols else pd.Series(np.nan, index=W.index, dtype=float)
    used_carry = False
    if carry is not None and f"{stem}{carry}" in W.columns:
        fill = W[f"{stem}{carry}"].astype(float)
        used_carry = bool(s.isna().any())
        s = s.where(s.notna(), fill)
    return s, used_carry


def inflation_moments(gmd_path: Path) -> pd.DataFrame:
    """Period mean and standard deviation of annual inflation, the log change of the CPI, in per cent."""
    g = pd.read_parquet(gmd_path) if gmd_path.suffix == ".parquet" else pd.read_csv(gmd_path, low_memory=False)
    g = g[["ISO3", "year", "infl"]].copy()
    g["ISO3"] = g["ISO3"].astype(str).str.strip()
    for c in ("year", "infl"):
        g[c] = pd.to_numeric(g[c], errors="coerce")
    g = g.dropna(subset=["ISO3", "year", "infl"])
    g = g[g["infl"] > -99.0].copy()
    g["infl"] = 100.0 * np.log1p(g["infl"] / 100.0)
    rows = []
    for p, (a, b) in INFLATION_YEARS.items():
        s = g[(g["year"] >= a) & (g["year"] <= b)].groupby("ISO3")["infl"].agg(["mean", "std", "count"]).reset_index()
        s["per"] = p
        rows.append(s)
    return pd.concat(rows, ignore_index=True).rename(columns={"mean": "pi_bar", "std": "sig", "count": "n_yr"})


def build_panel(long_csv: Path, gmd_path: Path) -> tuple[pd.DataFrame, list[str]]:
    """Barro's country-period panel with the raw and the purged inflation volatility."""
    W, byyr, iso = barro_lee_sources(long_csv)
    notes = block_alignment(W, byyr)
    recs = []
    for p in PERIODS:
        blk, sy = BLOCKS[p], STATE_YEAR[p]
        r = pd.DataFrame(index=W.index)
        s5 = byyr["gdpsh5"]
        y0, y1 = (1965, 1975) if p == 1965 else (1975, 1985) if p == 1975 else (1985, 1990)
        r["grw"] = (np.log(s5[y1].where(s5[y1] > 0)) - np.log(s5[y0].where(s5[y0] > 0))) / float(y1 - y0)
        r["lgdp"] = np.log(s5[sy].where(s5[sy] > 0))
        r["sm"] = byyr["syrm"][sy] + byyr["hyrm"][sy]
        r["sf"] = byyr["syrf"][sy] + byyr["hyrf"][sy]
        r["llife"] = np.log(W[f"lifee0{LIFE_BLOCK[p]}"].where(lambda s: s > 0))
        fe, _ = block_mean(W, "fert", blk, carry=5)
        fe = fe.where(fe.notna(), byyr["fert"][1985] if p == 1985 else np.nan)
        r["lfert"] = np.log(fe.where(lambda s: s > 0))
        r["gcons"], c1 = block_mean(W, "gvxdxe4", blk, carry=5)
        r["geduc"], c2 = block_mean(W, "geetot", blk, carry=5)
        r["bmp"], _ = block_mean(W, "bmp", blk)
        r["tot"], c3 = block_mean(W, "tot", blk, carry=5)
        if p == 1985:
            r["inv"] = W["invsh56"]
            if c1 or c2 or c3:
                notes.append("1985-90: gvxdxe / geetot / tot carried forward from 1980-85; investment ratio from the Summers-Heston v5 block invsh56")
        else:
            r["inv"], _ = block_mean(W, "invsh4", blk)
        pr = (W[["prightsb", "prights3"]].mean(axis=1) if p == 1965 else W[["prights4", "prights5"]].mean(axis=1) if p == 1975 else W["prights6"])
        r["dem"] = (7.0 - pr) / 6.0
        r["dem2"] = r["dem"] ** 2
        r["per"] = p
        r["SHCODE"] = r.index
        recs.append(r.reset_index(drop=True))
    d = pd.concat(recs, ignore_index=True)
    d["ISO3"] = d["SHCODE"].map(iso)
    d = d.merge(inflation_moments(gmd_path), on=["ISO3", "per"], how="inner")
    d = d[d["n_yr"] >= 4].copy()
    d["pi_bar"], d["sig"] = d["pi_bar"] / 100.0, d["sig"] / 100.0
    d["raw"] = d["sig"]
    d["purged"] = d["sig"] / np.sqrt(1.0 + 100.0 * d["pi_bar"].abs())  # pi_bar in percentage points
    return d, notes


def load_panel(ex: Exhibit) -> pd.DataFrame:
    folder = paths.crosscountry_dir()
    long_csv = folder / "barlee_long.csv"
    gmd = sorted(list(folder.glob("gmd*.parquet")) + list(folder.glob("gmd*.csv")))
    # the published table uses the 2025_12 release of the Global Macro Database; prefer it when several are present
    gmd = sorted(gmd, key=lambda f: cv.PUBLISHED_EXTENT["gmd"] not in f.name)
    derived = paths.derived_dir() / "crosscountry_panel.csv"
    if long_csv.exists() and gmd:
        if cv.PUBLISHED_EXTENT["gmd"] not in gmd[0].name:
            ex.say(f"note: the published table uses the {cv.PUBLISHED_EXTENT['gmd']} release of the Global Macro Database; reading {gmd[0].name}")
        d, notes = build_panel(long_csv, gmd[0])
        for n in notes:
            ex.say("  " + n)
        derived.parent.mkdir(parents=True, exist_ok=True)
        d.to_csv(derived, index=False)
        ex.say(f"panel built from {long_csv.name} and {gmd[0].name}: {len(d)} country-periods; written to {derived.relative_to(paths.data_dir())}")
        return d
    if derived.exists():
        ex.say(f"Barro--Lee source absent; reading the previously built panel {derived.relative_to(paths.data_dir())}")
        return pd.read_csv(derived)
    raise SystemExit(f"the Barro--Lee source ({long_csv}) and the Global Macro Database extract are needed; see data/README.md")


# ------------------------------------------------------------------ the estimation
def design(d: pd.DataFrame, cols: list[str], unc: str | None, with_level: bool):
    tail = (["pi_bar", unc] if with_level else [unc]) if unc else (["pi_bar"] if with_level else [])
    keep = list(dict.fromkeys(cols + tail))
    X = pd.concat([d[keep].astype(float), pd.get_dummies(d["per"].astype(int), prefix="p", drop_first=True).astype(float)], axis=1)
    reg = pd.concat([d["grw"].astype(float).rename("Y"), X], axis=1).dropna()
    return reg, d.loc[reg.index, "ISO3"].to_numpy()


def ols(d: pd.DataFrame, cols: list[str], unc: str | None, with_level: bool = True):
    reg, grp = design(d, cols, unc, with_level)
    names = list(reg.columns[1:])
    r = ec.cluster_ols(reg["Y"].to_numpy(), reg[names].to_numpy(), grp, names=tuple(names))
    c = {n: {"b": float(r.params[i]), "se": float(r.se[i]), "t": float(r.t[i]), "p": float(ec.chi2_p(r.t[i] ** 2))}
         for i, n in enumerate(["const"] + names)}
    return c, {"n": r.n, "countries": int(pd.Series(grp).nunique()), "r2": float(r.r2), "names": names, "reg": reg, "grp": grp}


def fit(d: pd.DataFrame, unc: str | None, with_level: bool = True, iters: int = 60):
    """Barro's specification, the human-capital interaction iterated to a fixed point."""
    d = d.copy()
    for c in ("sm", "sf", "llife", "lgdp"):
        d["_" + c] = d[c] - d[c].mean()
    c, meta = ols(d, CONTROLS, unc, with_level)
    for _ in range(iters):
        h = c["sm"]["b"] * d["_sm"] + c["sf"]["b"] * d["_sf"] + c["llife"]["b"] * d["_llife"]
        d["xint"] = d["_lgdp"] * h
        c2, meta = ols(d, CONTROLS + ["xint"], unc, with_level)
        if all(abs(c2[k]["b"] - c.get(k, {"b": 0})["b"]) < 1e-10 for k in ("sm", "sf", "llife")):
            return c2, meta
        c = c2
    return c, meta


def star(p: float) -> str:
    return "^{***}" if p < 0.01 else "^{**}" if p < 0.05 else "^{*}" if p < 0.10 else ""


def main() -> None:
    ex = Exhibit(__file__)
    d = load_panel(ex)
    cols, results = [], {"panel": {"country_periods": int(len(d)), "countries": int(d["ISO3"].nunique())}, "columns": {}}
    for tag, unc, wl in SPECS:
        c, m = fit(d, unc, wl)
        col = {"tag": tag, "coefs": c, "n": m["n"], "countries": m["countries"], "r2": m["r2"], "meta": m}
        if unc and wl:
            j = m["names"].index(unc)
            col["wild_p"] = ec.wild_cluster_p(m["reg"]["Y"].to_numpy(), m["reg"][m["names"]].to_numpy(), m["grp"], j,
                                              draws=BOOTSTRAP["draws"], seed=BOOTSTRAP["seed"], add_one=False)
        cols.append(col)
        bits = [f"{k} {c[k]['b']:+.4f} (t {c[k]['t']:+.2f})" for k in ("pi_bar", "raw", "purged") if k in c]
        ex.say(f"column ({tag}): " + " | ".join(bits) + f" || n {m['n']} countries {m['countries']} R2 {m['r2']:.3f}"
               + (f" | wild-cluster p {col['wild_p']:.3f}" if "wild_p" in col else ""))
        results["columns"][tag] = {"coefficients": {k: v for k, v in c.items() if k in ("pi_bar", "raw", "purged")},
                                   "n": m["n"], "countries": m["countries"], "r2": m["r2"], **({"wild_cluster_p": col["wild_p"]} if "wild_p" in col else {})}
    est = cols[4]["meta"]["reg"]
    idx = est.index
    sd = {k: float(d.loc[idx, k].std()) for k in ("raw", "purged")}
    osd_raw = abs(cols[3]["coefs"]["raw"]["b"]) * sd["raw"] * 100.0
    osd_pur = abs(cols[4]["coefs"]["purged"]["b"]) * sd["purged"] * 100.0
    results["one_sd_effect_pp"] = {"raw_col4": osd_raw, "purged_col5": osd_pur}
    results["bootstrap"] = BOOTSTRAP

    body = []
    for key, label in ROWS:
        top, bot = [label], [""]
        for col in cols:
            if key in col["coefs"]:
                o = col["coefs"][key]
                top.append(f"${o['b']:.4f}{star(o['p'])}$")
                bot.append(f"$({o['t']:.2f})$")
            else:
                top.append("")
                bot.append("")
        body.append(" & ".join(top) + r" \\")
        body.append(" & ".join(bot) + r" \\")
    wild = " & ".join((f"${col['wild_p']:.2f}$" if col["wild_p"] >= 0.1 else f"${col['wild_p']:.3f}$") if "wild_p" in col else "" for col in cols)
    lines = [r"\begin{table}[tp]", r"\centering", r"\caption{Cross-country growth regressions, raw and purged inflation volatility}",
             r"\label{tab:crosscountry}", r"\begin{tabular}{lccccc}", r"\toprule", r" & (1) & (2) & (3) & (4) & (5) \\", r"\midrule",
             *body, r"\midrule",
             "Observations & " + " & ".join(str(c["n"]) for c in cols) + r" \\",
             "Countries & " + " & ".join(str(c["countries"]) for c in cols) + r" \\",
             "$R^2$ & " + " & ".join(f"{c['r2']:.3f}" for c in cols) + r" \\",
             r"Period fixed effects & Yes & Yes & Yes & Yes & Yes \\", r"Country-clustered SE & Yes & Yes & Yes & Yes & Yes \\",
             "Wild-cluster bootstrap $p$ & " + wild + r" \\", r"\bottomrule", r"\end{tabular}"]
    text = "\n".join(lines) + "\n" + NOTES.replace("@osd_purged@", f"{osd_pur:.2f}").replace("@osd_raw@", f"{osd_raw:.2f}")
    if re.search(r"@[a-z_]+@", text):
        raise SystemExit("unfilled placeholder in the table")
    ex.write_table(text)
    ex.write_results(results, "Table 3 — cross-country growth regressions, raw and purged inflation volatility")


if __name__ == "__main__":
    main()
