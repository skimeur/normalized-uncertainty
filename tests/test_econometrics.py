"""The estimators agree with statsmodels where the conventions coincide."""

from __future__ import annotations

import numpy as np
import pytest

from nu_measures import econometrics as ec

sm = pytest.importorskip("statsmodels.api")


def _data(n=120, seed=3):
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(n, 2))
    e = rng.normal(size=n)
    e = e + 0.5 * np.r_[0.0, e[:-1]]  # some serial correlation
    y = 1.0 + 0.5 * x[:, 0] - 0.25 * x[:, 1] + e
    return y, x


def test_hac_coefficients_and_standard_errors_match_statsmodels():
    y, x = _data()
    ours = ec.hac_ols(y, x, lags=4)
    theirs = sm.OLS(y, sm.add_constant(x)).fit(
        cov_type="HAC", cov_kwds={"maxlags": 4, "use_correction": True}
    )
    assert np.allclose(ours.params, theirs.params)
    assert np.allclose(ours.se, theirs.bse)
    assert np.isclose(ours.r2, theirs.rsquared)


def test_white_errors_match_statsmodels_hc1():
    y, x = _data()
    ours = ec.hac_ols(y, x, lags=0)
    theirs = sm.OLS(y, sm.add_constant(x)).fit(cov_type="HC1")
    assert np.allclose(ours.se, theirs.bse)


def test_classical_ols_matches_statsmodels():
    y, x = _data()
    ours = ec.ols(y, x)
    theirs = sm.OLS(y, sm.add_constant(x)).fit()
    assert np.allclose(ours.params, theirs.params)
    assert np.allclose(ours.se, theirs.bse)


def test_cluster_errors_match_statsmodels():
    y, x = _data(n=200)
    groups = np.repeat(np.arange(20), 10)
    ours = ec.cluster_ols(y, x, groups)
    theirs = sm.OLS(y, sm.add_constant(x)).fit(cov_type="cluster", cov_kwds={"groups": groups})
    assert np.allclose(ours.params, theirs.params)
    assert np.allclose(ours.se, theirs.bse)


def test_wald_and_its_p_value():
    y, x = _data()
    res = ec.hac_ols(y, x, lags=4)
    stat = ec.wald(res.params, res.cov, [[0.0, 1.0, 0.0]])
    assert np.isclose(stat, (res.params[1] / res.se[1]) ** 2)
    assert 0.0 <= ec.chi2_p(stat) <= 1.0
    assert ec.chi2_p(0.0) == 1.0


def test_wild_cluster_p_is_a_probability_and_rejects_a_strong_effect():
    y, x = _data(n=200)
    groups = np.repeat(np.arange(20), 10)
    p = ec.wild_cluster_p(y, x, groups, coef=0, draws=99, seed=1)
    assert 0.0 < p <= 1.0
    assert p < 0.1


def test_named_results_serialise():
    y, x = _data()
    res = ec.hac_ols(y, x, names=("x1", "x2"))
    d = res.as_dict()
    assert set(d) >= {"const", "x1", "x2", "se_x1", "t_x2", "r2", "n"}
