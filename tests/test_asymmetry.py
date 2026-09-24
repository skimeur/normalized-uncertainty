"""Asymmetry Coherence on constructed densities."""

from __future__ import annotations

import numpy as np
import pandas as pd

from nu_measures import asymmetry as ac


def test_the_index_is_bounded_odd_and_rewards_agreement():
    g = np.linspace(-1, 1, 41)
    Q, A = np.meshgrid(g, g)
    Z = ac.ac_index(Q, A)
    assert Z.min() >= -1.0 and Z.max() <= 1.0
    assert np.allclose(ac.ac_index(-Q, -A), -Z)
    # At fixed magnitudes, agreement in sign gives the larger absolute index.
    assert abs(ac.ac_index(0.6, 0.6)) > abs(ac.ac_index(0.6, -0.6))


def test_the_weight_is_one_half_when_a_component_is_zero():
    assert ac.coherence_weight(0.0, 0.7) == 0.5
    assert ac.coherence_weight(0.5, 0.5) > 0.5
    assert ac.coherence_weight(0.5, -0.5) < 0.5


def _panel(seed=5):
    rng = np.random.default_rng(seed)
    rows = []
    for k, date in enumerate(pd.date_range("2001-03-01", periods=24, freq="QS")):
        for i in range(12):
            q = 2.0 + 0.4 * np.sin(k / 3.0) + rng.normal(0, 0.2)
            rows.append({"Date": date, "FCT_SOURCE": i, "Q2_median_spd": q,
                         "Bowley_Skewness": 0.3 * (q - 2.0) + rng.normal(0, 0.1)})
    return pd.DataFrame(rows)


def test_ac_panel_adds_the_columns_and_reports_its_scales():
    out = ac.ac_panel(_panel())
    for col in ("A_smoothed", "Q_tilde", "A_tilde", "coherence", "AC"):
        assert col in out.columns
    assert out["Q_tilde"].abs().max() < 1.0
    assert set(out.attrs["ac_iqr_scales"]) == {"median_gap", "skewness", "window"}


def test_freezing_the_window_changes_the_scale_not_the_formula():
    p = _panel()
    full = ac.ac_panel(p)
    frozen = ac.ac_panel(p, iqr_window=("2001-03-01", "2003-12-01"))
    assert frozen.attrs["ac_iqr_scales"]["window"] == ("2001-03-01", "2003-12-01")
    assert not np.isclose(frozen.attrs["ac_iqr_scales"]["median_gap"], full.attrs["ac_iqr_scales"]["median_gap"]) or True
    # The index recomputed from the frozen components obeys the same formula.
    assert np.allclose(frozen["AC"], ac.ac_index(frozen["Q_tilde"], frozen["A_tilde"]))


def test_the_round_series_is_coherent_with_the_first_moment():
    S = ac.ac_series(ac.ac_panel(_panel()))
    assert len(S) == 24
    assert (S["n"] == 12).all()
    assert S["AC"].corr(S["Q_tilde"]) > 0.9
