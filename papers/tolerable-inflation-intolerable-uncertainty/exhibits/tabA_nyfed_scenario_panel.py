#!/usr/bin/env python3
"""Table 6 of *Tolerable Inflation, Intolerable Uncertainty*: the perceived-rule band from the NY Fed scenario matrices.

Paper: Vansteenberghe, E. (2026), *Tolerable Inflation, Intolerable Uncertainty*,
working paper, Banque de France (``vansteenberghe2026tolerable``), Appendix,
Table 6 (``tab:spd_panel``).

The Federal Reserve Bank of New York's Survey of Primary Dealers and Survey
of Market Participants ask, in some rounds, for the year-end target rate
under nine hypothetical states (inflation and unemployment each at the
SEP median, 50 basis points above, 50 below); the published files give the
25th, 50th and 75th percentiles of the answers in each cell. For each
instance: the cross-dealer interquartile range of the state-pinned answers
(its mean over the nine cells, and the centre cell), the IQR of the
unconditional modal-path question at the same horizon, their ratio, and the
perceived responses -- the median cell differences per point of the
conditioning variable, the high-inflation row minus the low-inflation row
averaged over the unemployment columns and the transpose. The table prints
the dealer panel; the buy-side and combined panels are in the results file.

Inputs:  the survey workbooks ``$NU_DATA_DIR/nyfed/{sep-2023,apr-may-2024,sep-2024,jul-2025,apr-2026}-data.xlsx``
         (newyorkfed.org, Markets, surveys); and, beside this script,
         ``../inputs/nyfed_scenario_matrices_pdf_read.csv`` -- the matrices of the March 2023 round
         (before the workbook format) and of the two 2024 rounds (whose workbook scenario cells
         are zeroed at source), read from the published results PDFs, each row carrying its source,
         plus an independent PDF reading of the April 2026 combined matrix used as a check.
Outputs: ``tables/tabA_nyfed_scenario_panel.tex``, ``results/tabA_nyfed_scenario_panel.{json,md}``.

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use
this code, cite the paper above.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from nu_measures import paths
from nu_measures.exhibit import Exhibit

WORKBOOKS = {"Sep 2023": ("sep-2023-data.xlsx", 2024), "Apr/May 2024": ("apr-may-2024-data.xlsx", 2024),
             "Sep 2024": ("sep-2024-data.xlsx", 2024), "Jul 2025": ("jul-2025-data.xlsx", 2025), "Apr 2026": ("apr-2026-data.xlsx", 2026)}
HORIZON = {"Mar 2023": 9, "Sep 2023": 15, "Apr/May 2024": 8, "Sep 2024": 3, "Jul 2025": 5, "Apr 2026": 8}
DATE = {"Mar 2023": "2023-03", "Sep 2023": "2023-09", "Apr/May 2024": "2024-04", "Sep 2024": "2024-09", "Jul 2025": "2025-07", "Apr 2026": "2026-04"}
LABEL = {"Mar 2023": "Mar.\\ 2023", "Sep 2023": "Sep.\\ 2023", "Apr/May 2024": "Apr./May 2024", "Sep 2024": "Sep.\\ 2024",
         "Jul 2025": "Jul.\\ 2025", "Apr 2026": "Apr.\\ 2026"}
DEALER = {"SPD", "Dealer"}
SCENARIOS = ("SEP-50bp", "SEP median", "SEP+50bp")
PDF_READ = Path(__file__).resolve().parent.parent / "inputs" / "nyfed_scenario_matrices_pdf_read.csv"


def level_key(s) -> int:
    s = str(s)
    return 0 if "-50" in s else 2 if "+50" in s else 1


def parse_workbook(path: Path, scenario_year: int) -> dict:
    """The scenario matrices (per cent) and the matched-horizon unconditional percentiles, by panel type."""
    df = pd.read_excel(path, sheet_name=0, header=0)
    out = {}
    for ptype, sub in df.groupby("panel_type"):
        m = sub[sub["question_text"].astype(str).str.contains("hypothetical scenarios", case=False, na=False)]
        if m.empty:
            continue
        mats = {k: np.full((3, 3), np.nan) for k in ("p25", "med", "p75")}
        key = {"pctl25": "p25", "pctl50": "med", "pctl75": "p75"}
        counts = []
        for _, r in m.iterrows():
            agg = str(r["aggregation"])
            if agg in key:
                mats[key[agg]][level_key(r["left_header_value"]), level_key(r["top_header_value"])] = float(r["aggregation_value"]) * 100
            elif agg == "count":
                counts.append(float(r["aggregation_value"]))
        u = sub[(sub["theme"] == "rate_policy_expectations")
                & sub["question_text"].astype(str).str.contains("most likely outcome", case=False, na=False)
                & ~sub["question_text"].astype(str).str.contains("hypothetical", case=False, na=False)]
        horizons = u["horizon"].astype(str).unique().tolist()
        best = next((h for h in horizons if str(scenario_year) in h and "dec" in h.lower()), None)
        if best is None:
            best = next((h for h in horizons if h.strip() == f"{scenario_year} Q4"), None)
        um = u[u["horizon"].astype(str) == best] if best else u.iloc[0:0]
        uncond = {key[str(r["aggregation"])]: float(r["aggregation_value"]) * 100 for _, r in um.iterrows() if str(r["aggregation"]) in key}
        out[ptype] = {"n": int(max(counts)) if counts else None, **{k: np.round(v, 4) for k, v in mats.items()},
                      "uncond": uncond, "uncond_horizon": best}
    return out


def pdf_read_entries() -> dict:
    """The PDF-read instances, keyed by (instance, panel)."""
    df = pd.read_csv(PDF_READ)
    out = {}
    for (inst, panel), g in df.groupby(["instance", "panel"], sort=False):
        e = {"n": int(g["n"].iloc[0]), "n_note": g["n_note"].iloc[0], "source": g["source"].iloc[0], "uncond": {}}
        for stat in ("p25", "med", "p75"):
            m = np.full((3, 3), np.nan)
            for _, r in g[g["statistic"] == stat].iterrows():
                m[SCENARIOS.index(r["inflation_scenario"]), SCENARIOS.index(r["unemployment_scenario"])] = r["value_pct"]
            e[stat] = m
        for _, r in g[g["statistic"].str.startswith("uncond_")].iterrows():
            e["uncond"][r["statistic"].replace("uncond_", "").replace("p50", "med")] = float(r["value_pct"])
            e["uncond_horizon"] = r["source"].split("; ")[-1]
        out[(inst, panel)] = e
    return out


def statistics(e: dict) -> dict:
    p25, med, p75 = (np.asarray(e[k], dtype=float) for k in ("p25", "med", "p75"))
    iqr = (p75 - p25) * 100
    u = e.get("uncond") or {}
    u_iqr = (u["p75"] - u["p25"]) * 100 if {"p25", "p75"} <= set(u) else np.nan
    return {"mean_cond_iqr_bp": float(iqr.mean()), "center_iqr_bp": float(iqr[1, 1]), "uncond_iqr_bp": float(u_iqr),
            "ratio": float(iqr.mean() / u_iqr) if np.isfinite(u_iqr) and u_iqr > 0 else None,
            "di_dpi": float((med[2] - med[0]).mean()), "di_du": float((med[:, 2] - med[:, 0]).mean()),
            "iqr_matrix_bp": iqr.round(0).astype(int).tolist(), "median_matrix": med.tolist()}


def main() -> None:
    ex = Exhibit(__file__)
    folder = paths.nyfed_dir()
    parsed = {label: parse_workbook(paths.require(folder / fn, f"the NY Fed workbook {fn}"), yr) for label, (fn, yr) in WORKBOOKS.items()}
    pdf = pdf_read_entries()
    # the check: the April 2026 combined matrix read from the PDF against the workbook, all 27 cells
    chk = pdf[("Apr 2026", "Combined")]
    wb = parsed["Apr 2026"]["Combined"]
    cells = sum(int(np.allclose(chk[k], wb[k], atol=1e-6)) * 9 for k in ("p25", "med", "p75"))
    ex.say(f"April 2026 combined matrix: {cells} of 27 cells agree between the PDF reading and the workbook")
    if cells != 27:
        raise SystemExit("the workbook and the PDF reading of the April 2026 matrix disagree")

    panel = []
    for (inst, ptype), e in pdf.items():
        if inst == "Apr 2026":
            continue
        uncond, uh = e["uncond"], e.get("uncond_horizon", "")
        if not uncond:  # the 2024 rounds: the unconditional percentiles come from the workbook, where they are valid
            w = parsed[inst][ptype]
            uncond, uh = w["uncond"], f"{w['uncond_horizon']} (workbook)"
        panel.append({"instance": inst, "date": DATE[inst], "panel": ptype, "source": "PDF", "n": e["n"], "n_note": e["n_note"],
                      "horizon_months": HORIZON[inst], "uncond_horizon": uh, **statistics({**e, "uncond": uncond})})
    for inst, blob in parsed.items():
        for ptype, e in blob.items():
            if np.nanmax(e["med"]) == 0:  # the 2024 workbooks: scenario cells zeroed at source
                continue
            panel.append({"instance": inst, "date": DATE[inst], "panel": ptype, "source": "workbook", "n": e["n"], "n_note": "",
                          "horizon_months": HORIZON[inst], "uncond_horizon": str(e["uncond_horizon"]), **statistics(e)})
    panel.sort(key=lambda r: (r["date"], r["panel"]))
    for r in panel:
        ex.say(f"  {r['instance']:<13} {r['panel']:<12} n {r['n']:>3} h {r['horizon_months']:>2}  IQR mean {r['mean_cond_iqr_bp']:5.1f} centre {r['center_iqr_bp']:3.0f} "
               f"uncond {r['uncond_iqr_bp']:5.1f}  ratio {r['ratio'] if r['ratio'] is None else round(r['ratio'], 2)}  di/dpi {r['di_dpi']:+.2f} di/du {r['di_du']:+.2f}")

    dealer = [r for r in panel if r["panel"] in DEALER]
    lines = [r"\begin{tabular}{lcccccccc}", r"\toprule",
             r"Survey & $n$ & Horizon & \multicolumn{3}{c}{Cross-dealer IQR (bp)} & Ratio & \multicolumn{2}{c}{Perceived response}\\",
             r"\cmidrule(lr){4-6}\cmidrule(lr){8-9}",
             r" & & (months) & 9-cell mean & center cell & uncond.\ path & cond./uncond. & $\partial i/\partial\pi$ & $\partial i/\partial u$\\",
             r"\midrule"]
    for r in dealer:
        ratio = "---" if r["ratio"] is None else f"{r['ratio']:.2f}"
        centre, uncond = f"{r['center_iqr_bp']:.0f}", f"{r['uncond_iqr_bp']:.1f}"
        lines.append(f"{LABEL[r['instance']]:<14} & {r['n']} & {r['horizon_months']:<2} & {r['mean_cond_iqr_bp']:.1f} & {centre:<2} "
                     f"& {uncond:<4} & {ratio:<4} & ${r['di_dpi']:+.2f}$ & ${r['di_du']:+.2f}$\\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    ex.write_table("\n".join(lines) + "\n")
    ex.write_results({"dealer_rows": dealer, "panel": panel, "april_2026_cross_validation_cells": cells,
                      "pdf_read_inputs": str(PDF_READ.relative_to(PDF_READ.parents[2]))},
                     "Table 6 — the perceived-rule band from the NY Fed scenario matrices")


if __name__ == "__main__":
    main()
