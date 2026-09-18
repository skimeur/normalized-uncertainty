"""Moments of a binned density, against cases whose answer is known by hand."""

from __future__ import annotations

import math

import numpy as np
import pytest

from nu_measures import moments


def test_normalise_rescales_percentages():
    w = moments.normalise([50.0, 50.0])
    assert w.tolist() == [0.5, 0.5]


def test_normalise_treats_missing_as_zero():
    w = moments.normalise([np.nan, 25.0, 75.0])
    assert w[0] == 0.0
    assert math.isclose(w.sum(), 1.0)


def test_normalise_rejects_empty_density():
    with pytest.raises(ValueError):
        moments.normalise([0.0, 0.0])


def test_midpoints_of_a_half_point_grid():
    edges = [1.0, 1.5, 2.0, 2.5]
    assert moments.midpoints(edges).tolist() == [1.25, 1.75, 2.25]


def test_midpoints_reject_unsorted_edges():
    with pytest.raises(ValueError):
        moments.midpoints([2.0, 1.0, 3.0])


def test_mean_and_variance_of_a_two_point_density():
    # Half the mass at 1, half at 3: mean 2, variance 1.
    probs, support = [0.5, 0.5], [1.0, 3.0]
    assert math.isclose(moments.mean(probs, support), 2.0)
    assert math.isclose(moments.variance(probs, support), 1.0)
    assert math.isclose(moments.std(probs, support), 1.0)


def test_degenerate_density_has_zero_variance():
    assert moments.variance([0.0, 100.0, 0.0], [1.0, 2.0, 3.0]) == 0.0


def test_quantiles_interpolate_inside_the_containing_bin():
    # Uniform over [0, 2] reported as four half-point bins.
    edges = [0.0, 0.5, 1.0, 1.5, 2.0]
    probs = [25.0] * 4
    assert math.isclose(moments.median(probs, edges), 1.0)
    assert math.isclose(moments.quantile(probs, edges, 0.25), 0.5)
    assert math.isclose(moments.iqr(probs, edges), 1.0)


def test_quantile_rejects_endpoints():
    with pytest.raises(ValueError):
        moments.quantile([1.0, 1.0], [0.0, 1.0, 2.0], 0.0)


def test_bowley_is_zero_for_a_symmetric_density_and_signed_otherwise():
    edges = [0.0, 1.0, 2.0, 3.0]
    assert math.isclose(moments.bowley_skewness([25.0, 50.0, 25.0], edges), 0.0, abs_tol=1e-12)
    # Mass in the low bins leaves a long right tail: positive skewness.
    mass_low = moments.bowley_skewness([60.0, 30.0, 10.0], edges)
    mass_high = moments.bowley_skewness([10.0, 30.0, 60.0], edges)
    assert mass_high < 0 < mass_low
    # The two responses are mirror images, so the measure is exactly signed.
    assert math.isclose(mass_low, -mass_high, abs_tol=1e-12)


def test_bowley_is_bounded():
    edges = [0.0, 1.0, 2.0, 3.0]
    value = moments.bowley_skewness([90.0, 5.0, 5.0], edges)
    assert -1.0 <= value <= 1.0


def test_entropy_is_one_for_the_uniform_response_and_zero_for_a_point_mass():
    assert math.isclose(moments.entropy([25.0] * 4), 1.0)
    assert math.isclose(moments.entropy([0.0, 100.0, 0.0, 0.0]), 0.0)


def test_bins_filled_counts_used_bins():
    assert moments.bins_filled([0.0, 40.0, 60.0, 0.0]) == 2


def test_sheppard_correction_is_h_squared_over_twelve():
    assert math.isclose(moments.sheppard_correction(0.5), 0.25 / 12.0)
    # A grid change from one point to half a point changes the correction by
    # far less than it changes measured variance -- the reason it is reported
    # beside the raw number rather than applied to it.
    assert moments.sheppard_correction(1.0) - moments.sheppard_correction(0.5) < 0.07
