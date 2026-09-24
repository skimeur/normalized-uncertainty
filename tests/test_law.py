"""The two-arm law, recovered from data built to satisfy it."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from nu_measures import law


def _draw(n=400, a=0.42, b_minus=0.0, b_plus=1.88, sd=0.10, seed=20260918):
    rng = np.random.default_rng(seed)
    d = rng.uniform(-1.2, 1.8, size=n)
    y = a + b_minus * np.clip(-d, 0, None) + b_plus * np.clip(d, 0, None) + rng.normal(0, sd, n)
    return y, d


def test_design_is_flat_below_and_rising_above_the_kink():
    X = law.arms_design([-1.0, 0.0, 2.0])
    assert X[:, 0].tolist() == [1.0, 0.0, 0.0]
    assert X[:, 1].tolist() == [0.0, 0.0, 2.0]


def test_the_arms_are_recovered():
    y, d = _draw()
    fit = law.arms_fit(y, d)
    assert fit.n == 400
    assert math.isclose(fit.a, 0.42, abs_tol=0.05)
    assert math.isclose(fit.b_minus, 0.0, abs_tol=0.05)
    assert math.isclose(fit.b_plus, 1.88, abs_tol=0.05)
    assert fit.r2 > 0.9


def test_the_ratio_is_the_calibration():
    y, d = _draw()
    fit = law.arms_fit(y, d)
    assert math.isclose(fit.r_plus, fit.b_plus / fit.a)
    assert 3.5 < fit.r_plus < 5.5


def test_the_flat_arm_is_not_rejected_and_the_symmetric_law_is():
    y, d = _draw()
    tests = law.wald_tests(law.arms_fit(y, d))
    assert tests["b_minus_zero"]["p_value"] > 0.10
    assert tests["arms_equal"]["p_value"] < 0.01


def test_a_symmetric_world_rejects_neither():
    y, d = _draw(b_minus=1.88, b_plus=1.88)
    tests = law.wald_tests(law.arms_fit(y, d))
    assert tests["arms_equal"]["p_value"] > 0.10


def test_too_few_observations_is_an_error():
    with pytest.raises(ValueError):
        law.arms_fit([1.0, 2.0], [0.0, 1.0])


def test_the_kink_profile_finds_the_break():
    rng = np.random.default_rng(7)
    level = rng.uniform(0.5, 4.0, 600)
    true_kink = 2.5
    y = 0.4 + 1.9 * np.clip(level - true_kink, 0, None) + rng.normal(0, 0.05, 600)
    profile = law.kink_profile(y, level, grid=np.arange(1.5, 3.51, 0.1))
    assert abs(profile["c_hat"] - true_kink) <= 0.15
    lo, hi = profile["set95"]
    assert lo <= profile["c_hat"] <= hi
    assert profile["rss_min"] <= profile["rss_target"]


def test_the_kink_bootstrap_brackets_the_estimate():
    rng = np.random.default_rng(8)
    level = rng.uniform(0.5, 4.0, 200)
    y = 0.4 + 1.9 * np.clip(level - 2.5, 0, None) + rng.normal(0, 0.05, 200)
    grid = np.arange(1.5, 3.51, 0.1)
    boot = law.kink_bootstrap(y, level, grid, draws=50, seed=1)
    lo, hi = boot["interval90"]
    assert lo <= boot["median"] <= hi
    assert boot["draws"].shape == (50,)


def _panel(seed=11):
    rng = np.random.default_rng(seed)
    rows = []
    dates = pd.date_range("2000-03-01", periods=40, freq="QS")
    for date in dates:
        mu = 2.0 + rng.normal(0.0, 0.6)
        for i in range(30):
            m = mu + rng.normal(0.0, 0.15)
            v = 0.4 + 0.9 * max(m - 2.0, 0.0) + abs(rng.normal(0, 0.03))
            rows.append({"Date": date, "FCT_SOURCE": i, "Mean_spd": m, "Variance_spd": v})
    return pd.DataFrame(rows)


def test_round_aggregates_carry_the_three_objects():
    A = law.round_aggregates(_panel())
    assert list(A.index) == sorted(A.index)
    assert np.allclose(A["T"], A["W"] + A["D"])
    assert (A["n"] == 30).all()
    assert A["Q"].iloc[0] == pd.Period("2000Q2")


def test_the_estimation_sample_applies_the_round_rule_and_the_cutoff():
    A = law.round_aggregates(_panel())
    A.loc[A.index[3], "mu"] = 6.0
    S = law.estimation_sample(A, max_date=None)
    assert len(S) == len(A) - 1
    S2 = law.estimation_sample(A, max_date=A.index[10])
    assert len(S2) == 9


def test_the_law_by_object_recovers_the_arms():
    A = law.round_aggregates(_panel())
    fits = law.law_by_object(law.estimation_sample(A, max_date=None))
    assert set(fits) == {"W", "D", "T"}
    assert math.isclose(fits["W"].b_plus, 0.9, abs_tol=0.1)
    assert math.isclose(fits["W"].b_minus, 0.0, abs_tol=0.1)


def test_the_pooled_individual_fit_uses_white_errors():
    fit = law.pooled_individual(_panel(), max_date=None)
    assert fit.hac_lags == 0
    assert math.isclose(fit.b_plus, 0.9, abs_tol=0.05)


def test_the_split_test_reports_both_sides():
    A = law.round_aggregates(_panel())
    S = law.estimation_sample(A, max_date=None)
    out = law.split_test(S, "W", S.index[20])
    assert out["pre"].n + out["post"].n == len(S)
    assert 0.0 <= out["p_joint"] <= 1.0
