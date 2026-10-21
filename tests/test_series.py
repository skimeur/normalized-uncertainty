"""The horizons of the ECB-SPF reader and the round series, on synthetic round files."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from nu_measures import asymmetry, law, measures, series
from nu_measures import io_ecb_spf as io

HEADER = "TARGET_PERIOD,FCT_SOURCE,POINT,TN1_0,FN1_0TN0_6,FN0_5TN0_1,F0_0T0_4,F0_5T0_9,F1_0T1_4,F1_5T1_9,F2_0T2_4,F2_5T2_9,F3_0T3_4,F3_5T3_9,F4_0T4_4,F4_5T4_9,F5_0"
SYM = "0,0,0,0,0,0,25,50,25,0,0,0,0,0"     # [1.5, 3.0), mean 2.25, variance 0.125
UP = "0,0,0,0,0,0,0,10,20,30,30,10,0,0"     # mean 3.25
NONE = "," * 13


def _write(tmp_path, name, rows):
    lines = ["INFLATION EXPECTATIONS; YEAR-ON-YEAR CHANGE IN HICP" + "," * 16, HEADER, *rows, "," * 16,
             "CORE INFLATION" + "," * 16, HEADER, rows[0]]
    (tmp_path / name).write_text("\n".join(lines) + "\n")


@pytest.fixture
def rounds(tmp_path):
    _write(tmp_path, "2022Q4.csv", [
        f"2023Sep,1,3.0,{UP}", f"2023Sep,2,2.2,{SYM}",
        f"2024Sep,1,2.5,{SYM}", f"2024Sep,2,2.4,{SYM}", f"2024Sep,3,2.0,{NONE}",
        f"2027,1,2.0,{SYM}", f"2027,2,2.1,{SYM}", "2023,1,5.0," + UP,
    ])
    _write(tmp_path, "2023Q1.csv", [
        f"2023Dec,1,3.1,{UP}", f"2023Dec,2,2.3,{SYM}",
        f"2024Dec,1,2.6,{UP}", f"2024Dec,2,2.4,{SYM}",
    ])
    return tmp_path


def test_target_periods_of_the_three_horizons():
    assert io.target_period(2022, 4, "2Y") == ("2024Sep", pd.Timestamp("2024-09-01"))
    assert io.target_period(2023, 1, "2Y") == ("2024Dec", pd.Timestamp("2024-12-01"))
    assert io.target_period(2023, 2, "5Y")[0] == "2027"
    assert io.target_period(2023, 3, "5Y")[0] == "2028"
    with pytest.raises(ValueError):
        io.target_period(2023, 3, "10Y")


def test_every_horizon_shares_the_one_year_date(rounds):
    for h in ("1Y", "2Y", "5Y"):
        df = io.read_round(rounds / "2022Q4.csv", h)
        assert (df["Date"] == pd.Timestamp("2023-09-01")).all()
    assert set(io.read_round(rounds / "2022Q4.csv", "2Y")["TARGET_PERIOD"]) == {"2024Sep"}
    assert set(io.read_round(rounds / "2022Q4.csv", "5Y")["FCT_SOURCE"]) == {1, 2}
    assert io.read_round(rounds / "2023Q1.csv", "5Y").empty


def test_the_series_of_each_horizon(rounds):
    S = series.ecb_spf_series(rounds, ac_scales="own")
    assert list(S.columns) == list(series.SERIES_COLUMNS)
    r = S.loc[("2Y", pd.Period("2022Q4", freq="Q"))]
    assert r["n"] == 2 and r["n_point"] == 3
    assert np.isclose(r["level"], 2.25) and np.isclose(r["disagreement"], 0.0)
    assert np.isclose(r["raw_uncertainty"], np.sqrt(0.125))
    assert np.isclose(r["NU"], np.sqrt(0.125) / np.sqrt(1.25))
    assert np.isclose(r["level_point"], 2.3) and np.isclose(r["disagreement_point"], np.std([2.5, 2.4, 2.0]))
    assert np.isclose(r["aggregate_uncertainty"], r["W"] + r["D"])
    assert r["Date"] == pd.Timestamp("2022-09-01")
    # The longer-term question absent from a round: a gap, not a dropped row.
    g = S.loc[("5Y", pd.Period("2023Q1", freq="Q"))]
    assert g["n"] == 0 and np.isnan(g["level"])
    # T = W + D everywhere.
    ok = S.dropna(subset=["W"])
    assert np.allclose(ok["aggregate_uncertainty"], ok["W"] + ok["D"])


def test_the_one_year_series_are_the_libraries_own(rounds):
    S = series.ecb_spf_series(rounds).xs("1Y", level="horizon")
    panel = io.individual_panel(io.flat_panel(io.read_rounds(rounds)))
    nu = measures.nu_series(panel).set_index("Q")
    ac = asymmetry.ac_series(asymmetry.ac_panel(panel))
    A = law.round_aggregates(panel).set_index("Q")
    assert np.allclose(S["NU"], nu["NU_unit"])
    assert np.allclose(S["AC"], ac["AC"])
    assert np.allclose(S["level"], A["mu"])


def test_ac_scales_default_to_the_one_year_ones(rounds):
    S = series.ecb_spf_series(rounds)
    sc = S.attrs["ac_iqr_scales"]
    assert sc["2Y"]["median_gap"] == sc["1Y"]["median_gap"] == sc["5Y"]["median_gap"]
    own = series.ecb_spf_series(rounds, ac_scales="own").attrs["ac_iqr_scales"]
    assert own["1Y"]["median_gap"] == sc["1Y"]["median_gap"]


def test_long_and_wide_layouts(rounds):
    S = series.ecb_spf_series(rounds)
    long = series.to_long(S)
    assert list(long.columns) == ["round", "horizon", "series", "value"]
    assert len(long) == len(S) * (len(series.SERIES_COLUMNS) - 1)
    wide = series.to_wide(S)
    assert "NU_5Y" in wide.columns and wide.index.tolist() == ["2022Q4", "2023Q1"]
    assert wide.loc["2022Q4", "level_2Y"] == S.loc[("2Y", pd.Period("2022Q4", freq="Q")), "level"]
