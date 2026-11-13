#!/usr/bin/env python3
"""Report which of the third-party sources are present locally.

No data travels with this repository. Point ``NU_DATA_DIR`` at the folder that
holds the downloads described in ``data/README.md`` and run ``make data``: this
prints one line per source, whether it was found, and what reads it.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

from nu_measures import conventions as cv

#: (label, path pattern relative to NU_DATA_DIR, what needs it)
SOURCES: list[tuple[str, str, str]] = [
    (
        "ECB SPF individual density forecasts",
        "ecb_spf/rounds/*.csv",
        "every exhibit of both papers",
    ),
    (
        "ECB Data Portal macro block (HICP, policy rate, industrial production, unemployment, equity)",
        "ecb/macro_block.csv",
        "the industrial-production response, the overshoot clock",
    ),
    (
        "ECB Data Portal real GDP (for the potential-growth trend)",
        "ecb/real_gdp.csv",
        "Normalized Growth Uncertainty",
    ),
    (
        "Philadelphia Fed Survey of Professional Forecasters microdata",
        "us_spf/SPFmicrodata.xlsx",
        "the United States arms and the announcement comparison",
    ),
    (
        "FRED five-year breakeven inflation rate (T5YIE)",
        "fred/T5YIE.csv",
        "the daily market figure",
    ),
    (
        "FRED ten-year breakeven inflation rate (T10YIE)",
        "fred/T10YIE.csv",
        "the daily market figure's footnote check",
    ),
    (
        "FRED US core CPI index (CPILFESL)",
        "fred/CPILFESL.csv",
        "the euro area against the United States",
    ),
    (
        "Economic Policy Uncertainty, country workbook",
        "epu/All_Country_Data.xlsx",
        "the independent-proxy agreement checks",
    ),
    (
        "New York Fed Survey of Primary Dealers / Market Participants",
        "nyfed/*.xlsx",
        "the perceived-rule band",
    ),
    (
        "ECB Data Portal single series (HICP components, negotiated wages, the frozen ICP indices)",
        "ecb/series/*.csv",
        "the wages table, the energy split and the persistence footnote (fetched on first use)",
    ),
    (
        "Eurostat HICP index, euro area, 2026 months (prc_hicp_minr)",
        "eurostat/hicp_ea_total_minr.csv",
        "the persistence footnote (fetched on first use)",
    ),
    (
        "Barro-Lee data set, long form",
        "crosscountry/barlee_long.csv",
        "the cross-country growth regressions",
    ),
    (
        "Global Macro Database extract",
        "crosscountry/gmd*.parquet",
        "the cross-country growth regressions",
    ),
]


def main() -> int:
    raw = os.environ.get("NU_DATA_DIR")
    if not raw:
        print("NU_DATA_DIR is not set.\n")
        print("  export NU_DATA_DIR=/path/to/your/data\n")
        print("See data/README.md for what to download and where each source lives.")
        return 1

    root = Path(raw).expanduser()
    print(f"NU_DATA_DIR = {root}\n")
    missing = 0
    for label, pattern, used_by in SOURCES:
        found = sorted(root.glob(pattern))
        if found:
            detail = f"{len(found)} file(s)" if "*" in pattern else found[0].name
            print(f"  [ok]      {label}\n            {detail}")
        else:
            missing += 1
            print(f"  [missing] {label}\n            expected at {pattern} -- needed by {used_by}")
    print()
    if missing:
        print(f"{missing} source(s) missing; data/README.md says where each one comes from.")
    else:
        print("every source is present.")
    print()
    print("vintages (md5 against the files the published numbers were computed from):")
    same = differ = 0
    for rel, md5 in cv.PUBLISHED_INPUT_MD5.items():
        path = root / rel
        if not path.exists():
            continue
        if hashlib.md5(path.read_bytes()).hexdigest() == md5:
            same += 1
        else:
            differ += 1
            print(f"  [other vintage] {rel}")
    print(f"  {same} file(s) identical to the paper's, {differ} from another download"
          + (" -- see conventions.PUBLISHED_INPUT_MD5 for what moves" if differ else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
