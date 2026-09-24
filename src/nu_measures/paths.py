"""Where the data lives: one environment variable, one layout.

No third-party file is redistributed with this repository. The reader points
``NU_DATA_DIR`` at a folder laid out as ``data/README.md`` describes, and every
exhibit script asks this module for the file it needs, so that a path is
written in one place. Derived files that the library builds (the panels, the
macro block) go under ``NU_DATA_DIR/derived/`` unless a script says otherwise.
"""

from __future__ import annotations

import os
from pathlib import Path

__all__ = ["data_dir", "derived_dir", "ecb_spf_rounds", "hicp_index_csv", "macro_block_csv", "real_gdp_csv",
           "us_spf_workbook", "fred_csv", "epu_workbook", "nyfed_dir", "crosscountry_dir", "require"]

ENV = "NU_DATA_DIR"


def data_dir() -> Path:
    """The folder ``NU_DATA_DIR`` points at (``./data`` of the working directory if unset)."""
    return Path(os.environ.get(ENV, "data")).expanduser().resolve()


def derived_dir() -> Path:
    d = data_dir() / "derived"
    d.mkdir(parents=True, exist_ok=True)
    return d


def ecb_spf_rounds() -> Path:
    """Folder of the ECB-SPF round files ``YYYYQn.csv``."""
    return data_dir() / "ecb_spf" / "rounds"


def hicp_index_csv() -> Path:
    """Monthly HICP index (a CSV with a date column and the index column), optional."""
    return data_dir() / "ecb" / "hicp_index.csv"


def macro_block_csv(balanced: bool = True) -> Path:
    name = "macro_block.csv" if balanced else "macro_block_unbalanced.csv"
    return data_dir() / "ecb" / name


def real_gdp_csv() -> Path:
    return data_dir() / "ecb" / "real_gdp.csv"


def us_spf_workbook() -> Path:
    return data_dir() / "us_spf" / "SPFmicrodata.xlsx"


def fred_csv(series: str = "T5YIE") -> Path:
    return data_dir() / "fred" / f"{series}.csv"


def epu_workbook() -> Path:
    return data_dir() / "epu" / "All_Country_Data.xlsx"


def nyfed_dir() -> Path:
    return data_dir() / "nyfed"


def crosscountry_dir() -> Path:
    return data_dir() / "crosscountry"


def require(path: Path, what: str) -> Path:
    """Raise a readable error when a source file is missing."""
    if not Path(path).exists():
        raise FileNotFoundError(
            f"{what} not found at {path}. Point {ENV} at a folder laid out as data/README.md "
            "describes, or download the source there."
        )
    return Path(path)
