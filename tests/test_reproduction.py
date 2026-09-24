"""The certified numbers, reproduced from the raw sources.

These tests run only when ``NU_DATA_DIR`` holds the sources described in
``data/README.md``; without it every test here is skipped, so that the suite
stays green on a machine with no data. With the data present they are the
gate of the library: the individual panel rebuilt from the round files must
be identical to the authoritative one, and the law must print the papers'
numbers.
"""

from __future__ import annotations

import hashlib
import math
import os

import numpy as np
import pytest

from nu_measures import asymmetry, io_ecb_spf, io_us_spf, law, measures, paths
from nu_measures import conventions as cv

pytestmark = pytest.mark.skipif(
    os.environ.get(paths.ENV) is None or not paths.ecb_spf_rounds().is_dir(),
    reason="NU_DATA_DIR with the ECB-SPF round files is needed",
)

#: md5 of the authoritative individual panel (4,638 forecaster-rounds, 111 rounds, 1999Q1-2026Q3).
CERTIFIED_PANEL_MD5 = "b3b30bbba09b63de398021ce1385f29f"


@pytest.fixture(scope="module")
def panel(tmp_path_factory):
    _, panel = io_ecb_spf.build_panels(paths.ecb_spf_rounds(), tmp_path_factory.mktemp("panels"))
    return panel


def test_the_rebuilt_panel_is_the_certified_one_when_it_is_available(panel, tmp_path):
    certified = paths.data_dir() / "ecb_spf" / "ECB_SPF_individual_NIU_ACI_1Y.csv"
    if not certified.exists():
        pytest.skip("the certified panel is not in NU_DATA_DIR/ecb_spf")
    text = certified.read_text()
    assert hashlib.md5(text.encode()).hexdigest() == CERTIFIED_PANEL_MD5
    out = tmp_path / "rebuilt.csv"
    panel.to_csv(out, index=False)
    mine = out.read_text()

    def strip(t):  # sigma_resid (a LOESS residual, unused by the exhibits) is version-dependent
        return "\n".join(",".join(line.split(",")[:-1]) for line in t.strip().split("\n"))

    assert strip(mine) == strip(text)


def test_the_law_prints_the_papers_numbers(panel):
    A = law.round_aggregates(panel)
    S = law.estimation_sample(A)
    assert len(S) == cv.N_FIT_ROUNDS
    fits = law.law_by_object(S)
    W, T = fits["W"], fits["T"]
    assert math.isclose(W.a, cv.CERTIFIED["W_a"], abs_tol=5e-4)
    assert math.isclose(W.b_minus, cv.CERTIFIED["W_b_minus"], abs_tol=5e-4)
    assert math.isclose(W.b_plus, cv.CERTIFIED["W_b_plus"], abs_tol=5e-4)
    assert math.isclose(W.r_plus, cv.CERTIFIED["W_r_plus_exact"], abs_tol=1e-6)
    assert math.isclose(W.t_b_plus, 12.22, abs_tol=0.01)
    assert math.isclose(T.a, cv.CERTIFIED["total_a"], abs_tol=5e-5)
    assert math.isclose(T.b_minus, cv.CERTIFIED["total_b_minus"], abs_tol=5e-5)
    assert math.isclose(T.b_plus, cv.CERTIFIED["total_b_plus"], abs_tol=5e-5)
    assert math.isclose(T.r2, cv.CERTIFIED["total_r2"], abs_tol=5e-4)
    pooled = law.pooled_individual(panel)
    assert math.isclose(pooled.b_plus, cv.CERTIFIED["pooled_individual_b_plus"], abs_tol=5e-4)


def test_the_kink_sits_where_the_paper_says(panel):
    S = law.estimation_sample(law.round_aggregates(panel))
    kp = law.kink_profile(S["W"].to_numpy(), S["mu"].to_numpy())
    assert math.isclose(kp["c_hat"], cv.CERTIFIED["W_kink"], abs_tol=0.006)
    assert math.isclose(kp["set95"][0], cv.CERTIFIED["W_kink_set_low"], abs_tol=0.006)
    assert math.isclose(kp["set95"][1], cv.CERTIFIED["W_kink_set_high"], abs_tol=0.006)


def test_ac_reproduces_the_certified_individual_index(panel):
    out = asymmetry.ac_panel(panel)
    ok = out.dropna(subset=["ACI"])
    assert np.abs(ok["AC"] - ok["ACI"]).max() < 1e-12


def test_the_unit_nu_series_agrees_with_the_independent_proxy(panel):
    epu_file = paths.epu_workbook()
    if not epu_file.exists():
        pytest.skip("the EPU workbook is not in NU_DATA_DIR/epu")
    from nu_measures import io_other

    q = measures.quarterly(measures.nu_series(panel))
    epu = io_other.epu_basket(epu_file)
    J = q.join(epu, how="inner").dropna(subset=["EPU"])
    J = J[J.index <= "2026Q2"]
    assert math.isclose(np.corrcoef(J["NU_unit"], J["EPU"])[0, 1], cv.CERTIFIED["epu_corr_nu_unit"], abs_tol=5e-4)
    assert math.isclose(np.corrcoef(J["raw_sd"], J["EPU"])[0, 1], cv.CERTIFIED["epu_corr_raw"], abs_tol=5e-4)


def test_the_us_panel_rebuilds_the_archive_when_present():
    wb = paths.us_spf_workbook()
    if not wb.exists():
        pytest.skip("SPFmicrodata.xlsx is not in NU_DATA_DIR/us_spf")
    p = io_us_spf.panel(wb)
    assert p["Date"].min() == np.datetime64("1992-01-01")
    assert (p["grid"] == "post2014").sum() > 0
    core = io_us_spf.densities(wb, "PRCCPI")
    assert core["Date"].min() == np.datetime64("2007-01-01")
