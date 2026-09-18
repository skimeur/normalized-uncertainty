"""The sample constants are internally coherent."""

from __future__ import annotations

import math
from datetime import date

from nu_measures import calendar as cal


def test_the_top_bin_point_is_the_midpoint_of_its_interval():
    low, high = cal.TOP_BIN_INTERVAL
    assert math.isclose(cal.TOP_BIN_POINT, (low + high) / 2.0, abs_tol=5e-4)


def test_the_tails_are_closed_outside_the_reported_grid():
    assert cal.LEFT_TAIL_POINT < cal.TARGET < cal.TOP_BIN_INTERVAL[0]


def test_the_closure_bracket_names_the_builder_s_choice():
    assert cal.TOP_BIN_CLOSURES["midpoint"] == cal.TOP_BIN_POINT
    assert cal.TOP_BIN_CLOSURES["edge"] == cal.TOP_BIN_INTERVAL[0]


def test_the_trim_is_an_interval_around_the_target():
    low, high = cal.INDIVIDUAL_MEAN_TRIM
    assert low < cal.TARGET < high


def test_the_estimation_sample_ends_before_the_held_out_round():
    assert cal.FIT_MAX_PANEL_DATE <= date(2026, 4, 1)
    assert cal.HELD_OUT_SURVEY_ROUND == "2026Q3"
    assert cal.FIT_MAX_PANEL_DATE < cal.DATA_CUTOFF


def test_the_questionnaire_change_precedes_the_estimation_cutoff():
    assert cal.QUESTIONNAIRE_CHANGE_PANEL_DATE < cal.FIT_MAX_PANEL_DATE


def test_the_fitted_calibration_is_the_ratio_of_the_certified_law():
    ratio = cal.CERTIFIED["total_b_plus"] / cal.CERTIFIED["total_a"]
    assert math.isclose(ratio, cal.CERTIFIED["total_r_plus"], abs_tol=0.01)
    assert math.isclose(cal.NU_R_FITTED, cal.CERTIFIED["total_r_plus"])


def test_both_objects_are_flat_below_and_steep_above():
    for prefix in ("total", "W"):
        assert cal.CERTIFIED[f"{prefix}_b_minus"] < cal.CERTIFIED[f"{prefix}_b_plus"] / 10.0


def test_the_individual_object_sits_below_the_total_one():
    # Taking disagreement out lowers both the intercept and the arm: the two
    # laws are different objects and are never quoted interchangeably.
    assert cal.CERTIFIED["W_a"] < cal.CERTIFIED["total_a"]
    assert cal.CERTIFIED["W_b_plus"] < cal.CERTIFIED["total_b_plus"]
    assert math.isclose(cal.CERTIFIED["W_b_plus"], cal.CERTIFIED["within_b_plus"], abs_tol=1e-9)


def test_the_estimated_kink_sits_in_its_set_and_the_target_is_in_it():
    low, high = cal.CERTIFIED["W_kink_set_low"], cal.CERTIFIED["W_kink_set_high"]
    assert low <= cal.CERTIFIED["W_kink"] <= high
    assert low <= cal.TARGET <= high


def test_the_purge_raises_agreement_with_the_independent_proxy():
    # Both papers report this as the external check on the correction.
    assert cal.CERTIFIED["epu_corr_nu_unit"] > cal.CERTIFIED["epu_corr_raw"]
    assert cal.CERTIFIED["epu_corr_ngu_purged"] > cal.CERTIFIED["epu_corr_ngu_raw"]


def test_the_euro_area_basket_holds_only_member_states():
    assert "Sweden" not in cal.EPU_BASKET
    assert len(cal.EPU_BASKET) == 5
