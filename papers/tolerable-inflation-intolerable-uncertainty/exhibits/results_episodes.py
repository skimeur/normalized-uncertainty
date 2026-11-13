"""The numbers of the appendix's four euro-area inflation hikes: the label, the gap, and the price per point.

Paper: Vansteenberghe, E. (2026), *Tolerable Inflation, Intolerable Uncertainty*,
working paper, Banque de France (``vansteenberghe2026tolerable``), Appendix
"The benefit of the doubt, read on the professionals", paragraph "When the
label is visible" (numbers printed in the text; no table or figure).

Not an exhibit: a register, as ``results_register.py``.

For each hike, how plainly the overshoot carried its supply label (the share of
the headline overshoot outside core inflation), how large an overshoot the
professionals expected one year ahead, and what each point of that expected
overshoot did to the average individual variance W_t (net of the learned
variance of the law's baseline) and to the share of longer-term points at or
above 2.2 per cent (Figure 3's share, in excess of its 2016Q1--2021Q2 mean).

Inputs:  the ECB-SPF round files (through ``load_ecb_panel`` and ``load_longer_term_points``);
         headline HICP inflation, the official annual rate (the macro block's ``HICP_YOY``,
         as core below; not the rate recomputed from the index); core HICP inflation (all items
         excluding energy and food), fetched from the ECB Data Portal on first use and
         cached under ``derived/``.
Outputs: ``results/results_episodes.{json,md}``.

Part of https://github.com/skimeur/normalized-uncertainty (MIT). If you use
this code, cite the paper above.
"""

from __future__ import annotations

import pandas as pd
import statsmodels.formula.api as smf

from nu_measures import conventions as cv
from nu_measures import io_ecb_data_portal, paths
from nu_measures.exhibit import Exhibit, load_ecb_panel, load_longer_term_points, load_macro_block

EPISODES = {"2000-01": ("2000Q2", "2001Q4"), "2007-08": ("2007Q4", "2008Q4"),
            "2011-12": ("2011Q1", "2012Q4"), "2021-23": ("2021Q3", "2023Q4")}
THRESHOLD = 2.2                                    # Figure 3's longer-term threshold
CALM = (pd.Period("2016Q1", "Q"), pd.Period("2021Q2", "Q"))
CORE_KEYS = ("HICP.M.U2.N.XEF000.4D0.ANR", "ICP.M.U2.N.XEF000.4.ANR")
PUBLISHED_THROUGH = pd.Period("2025-12", "M")
LABEL_MIN_OVERSHOOT = 0.2                          # quarters counted for the label: headline > target + 0.2


def load_core_yoy() -> pd.Series:
    """Core HICP (excluding energy and food), year on year, monthly; cached after the first fetch."""
    path = paths.derived_dir() / "hicp_core_yoy.csv"
    if not path.exists():
        _, s = io_ecb_data_portal.probe("HICP excluding energy and food", CORE_KEYS)
        s.rename("CORE_YOY").to_csv(path, index_label="TIME_PERIOD")
    s = pd.read_csv(path, index_col=0, parse_dates=True)["CORE_YOY"]
    s.index = s.index.to_period("M")
    return s[s.index <= PUBLISHED_THROUGH]


def learned_variance(hicp: pd.Series) -> pd.Series:
    """Assumption 7's learned variance: the decreasing-gain mean of past squared one-year surprises of the gap.

    Quarterly gap, AR(1) at the four-quarter lag, squared residual, expanding mean, lagged one quarter.
    """
    q = (hicp - cv.TARGET).resample("QS").mean().to_frame("d")
    q["dl"] = q["d"].shift(4)
    fit = smf.ols("d ~ dl", q.dropna()).fit()
    e2 = (q["d"] - fit.predict(q)) ** 2
    s = e2.dropna().expanding().mean().shift(1)
    s.index = s.index.to_period("Q")
    return s


def main() -> None:
    ex = Exhibit(__file__)
    pan = load_ecb_panel().rename(columns={"Mean_spd": "M", "Variance_spd": "V"}).dropna(subset=["M", "V"])
    pan = pan[pan["V"] > 0].copy()
    pan["q"] = (pan["Date"] + pd.DateOffset(months=1)).dt.to_period("Q")       # the round, as in Figure 3
    R = pan.groupby("q").agg(W=("V", "mean"), mu=("M", "mean"))
    R["dep"] = (R["mu"] - cv.TARGET).clip(lower=0)
    # Headline is the official annual rate, like core: the published numbers are on it. (``load_hicp_yoy``
    # recomputes the rate from the index when ``ecb/hicp_index.csv`` is present, which moves the slopes.)
    hicp = load_macro_block(balanced=False)["HICP_YOY"].dropna()
    R["sig"] = learned_variance(hicp).reindex(R.index - 1).to_numpy()            # known before the round
    R = R.dropna(subset=["sig"])

    lt = load_longer_term_points().rename(columns={"round": "q", "POINT": "LT"})
    lt["q"] = pd.PeriodIndex(lt["q"], freq="Q")
    share = lt.groupby("q")["LT"].apply(lambda v: float((v >= THRESHOLD).mean()))
    calm = float(share[(share.index >= CALM[0]) & (share.index <= CALM[1])].mean())

    head = hicp.copy()
    head.index = head.index.to_period("M")
    head_q = head.groupby(head.index.asfreq("Q")).mean()
    core = load_core_yoy()
    core_q = core.groupby(core.index.asfreq("Q")).mean()

    terms = []
    for k, (a, b) in EPISODES.items():
        col = "dep_" + k.replace("-", "_")
        R[col] = R["dep"] * R.index.to_series().between(pd.Period(a, "Q"), pd.Period(b, "Q")).astype(float)
        terms.append(col)
    in_any = R[terms].sum(axis=1) > 0
    R["dep_other"] = R["dep"].where(~in_any, 0.0)
    fit = smf.ols("W ~ sig + " + " + ".join(terms + ["dep_other"]), R).fit(cov_type="HAC", cov_kwds={"maxlags": 4})
    base = smf.ols("W ~ sig", R[R["dep"] == 0]).fit()                         # the law's baseline, fitted where no overshoot is expected
    R["W_excess"] = R["W"] - base.predict(R)
    p_equal = float(fit.f_test("dep_2007_08 = dep_2021_23").pvalue)

    rows, out = [], {}
    for k, (a, b) in EPISODES.items():
        qq = pd.period_range(a, b, freq="Q")
        h, c = head_q.reindex(qq), core_q.reindex(qq)
        over = h - cv.TARGET
        label = (1 - ((c - cv.TARGET).clip(lower=0) / over.clip(lower=1e-9)).clip(upper=1))[over > LABEL_MIN_OVERSHOOT]
        r = R[R.index.isin(qq)]
        col = "dep_" + k.replace("-", "_")
        has_gap = bool((r["dep"] > 0).any())
        s = share.reindex(qq)
        dep_q = R["dep"].reindex(qq)
        ok = s.notna() & dep_q.notna()
        lt_slope = float(((s[ok] - calm) * dep_q[ok]).sum() / (dep_q[ok] ** 2).sum()) if has_gap else None
        out[k] = {"window": [a, b], "peak_headline": round(float(h.max()), 1), "peak_core": round(float(c.max()), 1),
                  "label_outside_core": round(float(label.mean()), 2), "mean_expected_overshoot": round(float(r["dep"].mean()), 2),
                  "max_expected_overshoot": round(float(r["dep"].max()), 2),
                  "mean_W_excess": round(float(r["W_excess"].mean()), 2), "max_W_excess": round(float(r["W_excess"].max()), 2),
                  "longer_term_share_peak": round(float(s.max()), 2), "longer_term_share_peak_round": str(s.idxmax()),
                  "rounds": int(len(r)), "rounds_with_expected_overshoot": int((r["dep"] > 0).sum()),
                  "W_slope": round(float(fit.params[col]), 2) if has_gap else None,
                  "W_slope_se": round(float(fit.bse[col]), 2) if has_gap else None,
                  "longer_term_share_slope": round(lt_slope, 2) if lt_slope is not None else None}
        e = out[k]
        ex.say(f"{k}: peak {e['peak_headline']}/{e['peak_core']}, label {e['label_outside_core']}, mean (de)+ {e['mean_expected_overshoot']}, "
               f"max (de)+ {e['max_expected_overshoot']}, W excess mean {e['mean_W_excess']} max {e['max_W_excess']}, "
               f"LT share peak {e['longer_term_share_peak']} ({e['longer_term_share_peak_round']}), "
               f"W slope {e['W_slope']} ({e['W_slope_se']}), LT share slope {e['longer_term_share_slope']}, "
               f"rounds {e['rounds']} ({e['rounds_with_expected_overshoot']} with an expected overshoot)")
        rows.append(e)
    ex.say(f"equality of the 2007-08 and 2021-23 slopes: p = {p_equal:.2f}; learned-variance coefficient {fit.params['sig']:.3f}")
    ex.write_results({"episodes": out, "p_equal_2007_08_vs_2021_23": round(p_equal, 2),
                      "learned_variance_coefficient": round(float(fit.params["sig"]), 3),
                      "calm_longer_term_share": round(calm, 3), "threshold": THRESHOLD,
                      "baseline": {"a": round(float(base.params["Intercept"]), 3), "gamma": round(float(base.params["sig"]), 3)}},
                     title="Four euro-area inflation hikes: the numbers of the appendix text")


if __name__ == "__main__":
    main()
