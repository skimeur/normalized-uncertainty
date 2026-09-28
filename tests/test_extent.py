"""The exhibit loaders stop every source at the extent the published papers use.

A reader who downloads the sources after publication gets more observations
than the papers used; the loaders of ``nu_measures.exhibit`` must ignore them
(``conventions.PUBLISHED_EXTENT``). Everything here runs on synthetic files.
"""

from __future__ import annotations

import contextlib

import numpy as np
import pandas as pd
import pytest

from nu_measures import conventions as cv
from nu_measures import exhibit, growth, io_ecb_spf

EXT = cv.PUBLISHED_EXTENT


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("NU_DATA_DIR", str(tmp_path))
    return tmp_path


def test_round_files_stop_at_the_published_round(tmp_path):
    for name in ("2026Q2.csv", "2026Q3.csv", "2026Q4.csv", "2027Q1.csv", "notes.txt"):
        (tmp_path / name).write_text("")
    assert [p.name for p in io_ecb_spf.round_files(tmp_path, EXT["ecb_spf"])] == ["2026Q2.csv", "2026Q3.csv"]
    assert len(io_ecb_spf.round_files(tmp_path)) == 4


def test_fred_stops_at_its_published_date(data_dir):
    (data_dir / "fred").mkdir()
    days = pd.bdate_range("2026-07-01", "2026-10-30")
    pd.DataFrame({"observation_date": days.strftime("%Y-%m-%d"), "T5YIE": 2.3}).to_csv(data_dir / "fred" / "T5YIE.csv", index=False)
    s = exhibit.load_fred("T5YIE")
    assert s.index.max() == pd.Timestamp(EXT["fred"]["T5YIE"])
    assert exhibit.load_fred("T5YIE", published=False).index.max() == days[-1]


def test_macro_block_stops_column_by_column(data_dir):
    (data_dir / "ecb").mkdir()
    months = pd.date_range("2025-01-31", "2026-12-31", freq="ME")
    df = pd.DataFrame({"TIME_PERIOD": months.strftime("%Y-%m-%d")} | {c: np.arange(len(months), dtype=float) for c in EXT["macro_block"]})
    df.to_csv(data_dir / "ecb" / "macro_block_unbalanced.csv", index=False)
    df.to_csv(data_dir / "ecb" / "macro_block.csv", index=False)
    ragged = exhibit.load_macro_block(balanced=False)
    for col, end in EXT["macro_block"].items():
        assert ragged[col].last_valid_index() == pd.Timestamp(end)
    balanced = exhibit.load_macro_block(balanced=True)
    assert balanced.index.max() == min(pd.Timestamp(d) for d in EXT["macro_block"].values())
    assert not balanced.isna().any().any()
    assert exhibit.load_macro_block(balanced=False, published=False).index.max() == months[-1]


def test_real_gdp_and_hicp_stop_at_their_published_dates(data_dir):
    (data_dir / "ecb").mkdir()
    quarters = pd.date_range("2020-03-31", "2026-09-30", freq="QE")
    pd.DataFrame({"DATE": quarters.strftime("%Y-%m-%d"), "GDP": np.linspace(100, 110, len(quarters))}).to_csv(data_dir / "ecb" / "real_gdp.csv", index=False)
    assert exhibit.load_real_gdp().index.max() == pd.Timestamp(EXT["real_gdp"])
    months = pd.date_range("2023-01-31", "2026-08-31", freq="ME")
    pd.DataFrame({"DATE": months.strftime("%Y-%m-%d"), "HICP": np.linspace(120, 130, len(months))}).to_csv(data_dir / "ecb" / "hicp_index.csv", index=False)
    assert exhibit.load_hicp_yoy().index.max().to_period("M") == pd.Period(EXT["hicp_index"], freq="M")
    assert exhibit.load_hicp_yoy(published=False).index.max().to_period("M") == pd.Period("2026-08", freq="M")


def test_epu_stops_at_its_published_month(data_dir):
    (data_dir / "epu").mkdir()
    months = pd.date_range("2025-01-01", "2026-09-01", freq="MS")
    df = pd.DataFrame({"Year": months.year, "Month": months.month} | {c: 100.0 for c in cv.EPU_BASKET})
    df.to_excel(data_dir / "epu" / "All_Country_Data.xlsx", sheet_name="EPU", index=False)
    assert exhibit.load_epu().index.max() == pd.Period(EXT["epu"], freq="M").asfreq("Q")
    assert exhibit.load_epu(published=False).index.max() == pd.Period("2026Q3", freq="Q")


def test_us_spf_stops_at_its_published_quarter(data_dir, monkeypatch):
    (data_dir / "us_spf").mkdir()
    (data_dir / "us_spf" / "SPFmicrodata.xlsx").write_bytes(b"")
    dates = pd.to_datetime(["2026-01-01", "2026-04-01", "2026-07-01"])
    fake = pd.DataFrame({"Date": dates, "ID": [1, 1, 1], "Mean": [2.0, 2.1, 2.2]})
    monkeypatch.setattr(exhibit.io_us_spf, "densities", lambda *a, **k: fake.copy())
    d = exhibit.load_us_densities("PRCCPI")
    assert d["Date"].max() == pd.Timestamp("2026-04-01") and list(d.index) == [0, 1]
    assert len(exhibit.load_us_densities("PRCCPI", published=False)) == 3


def _copy_on_write():
    if int(pd.__version__.split(".")[0]) >= 3:  # always on from pandas 3, where the option is deprecated
        return contextlib.nullcontext()
    return pd.option_context("mode.copy_on_write", True)


def test_growth_densities_survive_copy_on_write():
    """pandas 3 hands out read-only arrays; the density moments must not write into them."""
    flat = pd.DataFrame({"Date": ["2027-06-01"], "FCT_SOURCE": [1], "POINT": [1.3]} | {b: [np.nan] for b in growth._BINS})
    flat.loc[0, ["[0.5,0.9]", "[1.0,1.4]", "[1.5,1.9]"]] = [20.0, 50.0, 30.0]
    with _copy_on_write():
        out = growth.growth_densities(flat)
    assert out["Mean"].iloc[0] == pytest.approx(1.3)
    assert out["Variance"].iloc[0] == pytest.approx(0.1225)
