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
    assert X[:, 0].tolist() == [1.0, 1.0, 1.0]
    assert X[:, 1].tolist() == [1.0, 0.0, 0.0]
    assert X[:, 2].tolist() == [0.0, 0.0, 2.0]


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
    d = rng.uniform(-1.5, 2.0, 600)
    true_kink = 0.5
    y = 0.4 + 1.9 * np.clip(d - true_kink, 0, None) + rng.normal(0, 0.05, 600)
    profile = law.kink_profile(y, d, grid=np.arange(-0.5, 1.51, 0.1))
    best = profile.loc[profile["rss"].idxmin(), "kink"]
    assert abs(best - true_kink) <= 0.15


def test_within_and_between_split_the_individual_law():
    rng = np.random.default_rng(11)
    rows = []
    for i in range(30):
        level = rng.normal(0.0, 0.25)
        for _ in range(25):
            d = rng.uniform(-1.0, 1.5)
            rows.append(
                {
                    "forecaster": f"f{i:02d}",
                    "gap": d,
                    "variance": 0.4 + level + 0.9 * max(d, 0.0) + rng.normal(0, 0.05),
                }
            )
    panel = pd.DataFrame(rows)
    parts = law.within_between(panel, value="variance", gap="gap")
    assert set(parts) == {"pooled", "within", "between"}
    # The mechanism is within: the same forecaster widens as the overshoot grows.
    assert math.isclose(parts["within"].b_plus, 0.9, abs_tol=0.06)
    assert math.isclose(parts["within"].b_minus, 0.0, abs_tol=0.06)
    # Forecaster averages carry the level differences, not the slope.
    assert parts["between"].n == 30
