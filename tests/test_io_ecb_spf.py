"""The ECB-SPF reader on a synthetic round file laid out like the ECB's."""

from __future__ import annotations

import numpy as np
import pandas as pd

from nu_measures import conventions as cv
from nu_measures import io_ecb_spf as io

HEADER = "TARGET_PERIOD,FCT_SOURCE,POINT,TN1_0,FN1_0TN0_6,FN0_5TN0_1,F0_0T0_4,F0_5T0_9,F1_0T1_4,F1_5T1_9,F2_0T2_4,F2_5T2_9,F3_0T3_4,F3_5T3_9,F4_0T4_4,F4_5T4_9,F5_0"


def _write_round(tmp_path, name="2022Q4.csv"):
    lines = [
        "INFLATION EXPECTATIONS; YEAR-ON-YEAR CHANGE IN HICP" + "," * 16,
        HEADER,
        "2022,1,8.5,0,0,0,0,0,0,0,0,0,0,0,0,0,100",       # all mass in the open top bin
        "2023Sep,1,5.2,0,0,0,0,0,0,0,10,20,30,30,10,0,0",  # the one-year-ahead target
        "2023Sep,2,4.0,0,0,0,0,0,0,25,50,25,0,0,0,0,0",
        "2023Sep,3,3.0,0,0,0,0,0,0,0,0,0,0,0,0,0,0",       # no density at all
        "," * 16,
        "CORE INFLATION" + "," * 16,
        HEADER,
        "2023Sep,1,4.0,0,0,0,0,0,0,0,0,50,50,0,0,0,0",
    ]
    path = tmp_path / name
    path.write_text("\n".join(lines) + "\n")
    return path


def test_target_period_follows_the_survey_quarter():
    assert io.target_period(2022, 4) == ("2023Sep", pd.Timestamp("2023-09-01"))
    assert io.target_period(1999, 1) == ("1999Dec", pd.Timestamp("1999-12-01"))


def test_read_round_keeps_the_inflation_block_and_the_target_period(tmp_path):
    df = io.read_round(_write_round(tmp_path))
    assert set(df["TARGET_PERIOD"]) == {"2023Sep"}
    assert len(df) == 3
    assert (df["Date"] == pd.Timestamp("2023-09-01")).all()


def test_the_flat_panel_has_the_authoritative_layout(tmp_path):
    flat = io.flat_panel(io.read_rounds(tmp_path)) if (tmp_path / "2022Q4.csv").exists() else io.flat_panel(io.read_round(_write_round(tmp_path)))
    assert tuple(flat.columns) == cv.FLAT_PANEL_COLUMNS
    assert flat.loc[0, "[2.5,2.9]"] == 20.0


def test_the_individual_panel_moments_and_conventions(tmp_path):
    flat = io.flat_panel(io.read_round(_write_round(tmp_path)))
    panel = io.individual_panel(flat)
    assert tuple(panel.columns) == io.INDIVIDUAL_PANEL_COLUMNS
    # Formation time: the target period minus one year.
    assert (panel["Date"] == pd.Timestamp("2022-09-01")).all()
    # Forecaster 2: symmetric on [1.5, 3.0) with midpoints 1.75, 2.25, 2.75.
    row = panel[panel["FCT_SOURCE"] == 2].iloc[0]
    assert np.isclose(row["Mean_spd"], 2.25)
    assert np.isclose(row["Variance_spd"], 0.125)
    assert np.isclose(row["Bowley_Skewness"], 0.0)
    assert np.isclose(row["Q2_median_spd"], 2.25)
    assert row["bins_filled"] == 3
    # The symmetric unit correction the panel carries.
    assert np.isclose(row["NIU"], np.sqrt(0.125) / np.sqrt(1.25))
    # A response with no density at all is dropped by the builder.
    assert 3 not in set(panel["FCT_SOURCE"])
    assert len(panel) == 2
    assert set(panel.attrs["ac_iqr_scales"]) == {"median_gap", "skewness"}


def test_the_tail_closures_come_from_the_conventions():
    edges = cv.grid_edges()
    assert edges[0] == (cv.LEFT_TAIL_POINT, cv.LEFT_TAIL_POINT)
    assert edges[-1] == cv.TOP_BIN_INTERVAL
    assert np.isclose((edges[-1][0] + edges[-1][1]) / 2, cv.TOP_BIN_POINT)


def test_hicp_extremes_from_an_index():
    idx = pd.Series(100.0 * (1.02 ** (np.arange(36) / 12.0)), index=pd.date_range("2000-01-01", periods=36, freq="MS"))
    yoy = io.hicp_yoy_from_index(idx)
    lo, hi = io.hicp_extremes(yoy)
    assert np.isclose(lo, 2.0) and np.isclose(hi, 2.0)
