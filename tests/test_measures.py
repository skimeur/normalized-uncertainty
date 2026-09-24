"""NU, NGU and the orthogonalisation, on constructed cases."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from nu_measures import measures
from nu_measures.conventions import NU_R_FITTED, NU_R_UNIT, TARGET


def test_below_target_the_correction_does_nothing():
    # The target is announced: there is nothing to purge on the flat arm.
    sigma = np.array([1.0, 1.0, 1.0])
    means = np.array([0.5, 1.5, TARGET])
    assert np.allclose(measures.nu(sigma, means), sigma)


def test_above_target_the_correction_divides():
    value = measures.nu(1.0, TARGET + 1.0, r=NU_R_FITTED)
    assert math.isclose(float(value), 1.0 / math.sqrt(1.0 + NU_R_FITTED))
    assert float(value) < 1.0


def test_the_correction_is_monotone_in_the_overshoot():
    gaps = np.array([0.0, 0.5, 1.0, 2.0])
    values = measures.nu(np.ones_like(gaps), TARGET + gaps)
    assert np.all(np.diff(values) < 0)


def test_the_unit_calibration_purges_less_than_the_fitted_one():
    unit = measures.nu_unit(1.0, TARGET + 1.0)
    fitted = measures.nu(1.0, TARGET + 1.0, r=NU_R_FITTED)
    assert float(fitted) < float(unit) < 1.0
    assert math.isclose(float(unit), 1.0 / math.sqrt(1.0 + NU_R_UNIT))


def test_a_negative_calibration_is_refused():
    with pytest.raises(ValueError):
        measures.normalizer([1.0], r=-1.0)


def test_growth_is_normalised_symmetrically():
    # Potential growth is an estimate, not an announced number: a shortfall and
    # an overshoot of the same size are treated alike.
    below = measures.ngu(1.0, 0.0, 1.0)
    above = measures.ngu(1.0, 2.0, 1.0)
    assert math.isclose(float(below), float(above))
    assert float(below) < 1.0


def _panel(n_forecasters: int, n_periods: int, slope: float, seed: int = 20260918) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n_forecasters):
        level = rng.normal(0.0, 1.0)
        for t in range(n_periods):
            x = rng.normal(1.0, 0.4)
            rows.append(
                {
                    "forecaster": f"f{i:02d}",
                    "period": t,
                    "nu": x,
                    "ngu": level + slope * x + rng.normal(0.0, 0.05),
                }
            )
    return pd.DataFrame(rows)


def test_orthogonalisation_removes_the_common_component():
    panel = _panel(n_forecasters=12, n_periods=20, slope=2.0)
    series, detail = measures.orthogonalize(panel, y="ngu", x="nu", min_obs=10)
    # Every forecaster has enough rounds to carry their own slope, and each
    # slope recovers the one used to build the panel.
    assert detail["own_slope"].all()
    assert np.allclose(detail["slope"], 2.0, atol=0.15)
    assert math.isclose(float(detail["slope"].mean()), 2.0, abs_tol=0.03)
    # What is left is noise: it cannot still be explained by the regressor.
    merged = panel.groupby("period")["nu"].mean().to_frame().join(series.rename("resid"))
    assert abs(merged["nu"].corr(merged["resid"])) < 0.5


def test_short_forecasters_borrow_the_pooled_slope():
    panel = _panel(n_forecasters=6, n_periods=20, slope=1.5)
    short = panel[panel["forecaster"] == "f00"].head(4)
    panel = pd.concat([panel[panel["forecaster"] != "f00"], short])
    _, detail = measures.orthogonalize(panel, y="ngu", x="nu", min_obs=10)
    row = detail[detail["forecaster"] == "f00"].iloc[0]
    assert not row["own_slope"]
    assert math.isclose(row["slope"], detail[detail["own_slope"]]["slope"].iloc[0], abs_tol=0.2)


def test_the_returned_series_is_standardised_by_default():
    panel = _panel(n_forecasters=8, n_periods=15, slope=1.0)
    series, _ = measures.orthogonalize(panel, y="ngu", x="nu")
    assert math.isclose(float(series.mean()), 0.0, abs_tol=1e-9)
    assert math.isclose(float(series.std(ddof=1)), 1.0, abs_tol=1e-9)


def test_a_missing_column_is_an_error_not_a_silent_drop():
    panel = _panel(2, 12, 1.0).drop(columns=["ngu"])
    with pytest.raises(KeyError):
        measures.orthogonalize(panel, y="ngu", x="nu")
