"""What every exhibit script shares: where it writes, how it records its numbers, what it loads.

An exhibit script is thin: it loads the panels through the functions here,
computes with the library, and writes its figure or table **and** a results
file recording every number it prints (``results/<name>.json``, with a
Markdown rendering beside it). The paper pages' key-numbers tables are
generated from those files, so the published package and the paper cannot
disagree without it showing.

Determinism is part of the contract: inputs are sorted, seeds fixed, and no
timestamp enters a results file, so that a rebuild reproduces it byte for byte.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

from . import growth, io_ecb_data_portal, io_ecb_spf, io_other, io_us_spf, paths, plotting

__all__ = ["Exhibit", "load_ecb_panel", "load_flat_panel", "load_longer_term_points", "load_growth_panel", "load_epu", "load_macro_block",
           "load_us_densities", "load_us_quartiles", "load_real_gdp", "load_fred", "load_hicp_yoy"]


class Exhibit:
    """The output folders of the paper an exhibit script belongs to, and its results writer."""

    def __init__(self, script_file: str | Path, paper_dir: str | Path | None = None):
        script = Path(script_file).resolve()
        self.name = script.stem
        self.paper = Path(paper_dir).resolve() if paper_dir else script.parents[1]
        self.figures = self.paper / "figures"
        self.tables = self.paper / "tables"
        self.results = self.paper / "results"
        for d in (self.figures, self.tables, self.results):
            d.mkdir(parents=True, exist_ok=True)
        self._log: list[str] = []
        plotting.style()

    # -- recording ---------------------------------------------------------
    def say(self, line: str = "") -> None:
        """Print a line and keep it for the Markdown rendering of the results."""
        print(line)
        self._log.append(line)

    def write_results(self, data: dict, title: str | None = None) -> Path:
        """Write ``results/<name>.json`` (sorted keys) and ``results/<name>.md`` (the printed lines)."""
        path = self.results / f"{self.name}.json"
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(_jsonable(data), fh, indent=1, sort_keys=True, ensure_ascii=False)
            fh.write("\n")
        md = self.results / f"{self.name}.md"
        lines = [f"# {title or self.name}", ""] + self._log + [""]
        md.write_text("\n".join(lines), encoding="utf-8")
        return path

    def write_table(self, text: str, name: str | None = None) -> Path:
        path = self.tables / f"{name or self.name}.tex"
        path.write_text(text, encoding="utf-8")
        self.say(f"written {path.relative_to(self.paper)}")
        return path

    def save_figure(self, fig, name: str | None = None) -> list[Path]:
        out = plotting.save(fig, name or self.name, self.figures)
        self.say("written " + ", ".join(str(p.relative_to(self.paper)) for p in out))
        return out


def _jsonable(obj):
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if hasattr(obj, "item") and not isinstance(obj, (str, bytes)):
        try:
            return obj.item()
        except (TypeError, ValueError):
            pass
    if hasattr(obj, "tolist"):
        return obj.tolist()
    if isinstance(obj, (pd.Timestamp, pd.Period)):
        return str(obj)
    return obj


# -- loaders -----------------------------------------------------------------


def load_ecb_panel(rebuild: bool = False) -> pd.DataFrame:
    """The ECB-SPF individual panel: built from the round files once, then read from ``derived/``."""
    derived = paths.derived_dir()
    cached = derived / "individual_panel.csv"
    if cached.exists() and not rebuild:
        panel = pd.read_csv(cached)
    else:
        rounds = paths.require(paths.ecb_spf_rounds(), "the ECB-SPF round files")
        print(f"building the individual panel from {rounds} ...", file=sys.stderr)
        _, panel = io_ecb_spf.build_panels(rounds, derived)
    panel["Date"] = pd.to_datetime(panel["Date"])
    return panel


def load_real_gdp() -> pd.Series:
    """Quarterly real GDP levels from ``ecb/real_gdp.csv`` (written by the fetcher, or a manual download)."""
    path = paths.require(paths.real_gdp_csv(), "the real GDP series")
    df = pd.read_csv(path)
    date_col = "TIME_PERIOD" if "TIME_PERIOD" in df.columns else df.columns[0]
    value_col = [c for c in df.columns if c not in (date_col, "TIME PERIOD")][-1]
    s = pd.Series(pd.to_numeric(df[value_col], errors="coerce").to_numpy(), index=pd.to_datetime(df[date_col]))
    return s.dropna().sort_index()


def load_growth_panel(rebuild: bool = False) -> pd.DataFrame:
    """The growth densities with potential growth and NGU (``derived/growth_panel.csv``)."""
    derived = paths.derived_dir()
    cached = derived / "growth_panel.csv"
    if cached.exists() and not rebuild:
        panel = pd.read_csv(cached)
        panel["Date"] = pd.to_datetime(panel["Date"])
        return panel
    rounds = paths.require(paths.ecb_spf_rounds(), "the ECB-SPF round files")
    print(f"building the growth panel from {rounds} ...", file=sys.stderr)
    flat = growth.flat_panel_growth(growth.read_rounds_growth(rounds))
    flat_path = derived / "growth_flat_panel.csv"
    flat.to_csv(flat_path, index=False)
    flat = pd.read_csv(flat_path)
    dens = growth.growth_densities(flat)
    pot = growth.potential_growth(load_real_gdp())
    panel = growth.ngu_panel(dens, pot)
    panel.to_csv(cached, index=False)
    return panel


def load_epu() -> pd.Series:
    return io_other.epu_basket(paths.require(paths.epu_workbook(), "the EPU workbook"))


def load_macro_block(balanced: bool = True) -> pd.DataFrame:
    path = paths.macro_block_csv(balanced)
    if not path.exists():
        print("fetching the ECB macro block ...", file=sys.stderr)
        io_ecb_data_portal.macro_block(out_dir=path.parent)
    df = pd.read_csv(path)
    df["TIME_PERIOD"] = pd.to_datetime(df["TIME_PERIOD"])
    return df.set_index("TIME_PERIOD").sort_index()


def load_us_densities(sheet: str, **kwargs) -> pd.DataFrame:
    return io_us_spf.densities(paths.require(paths.us_spf_workbook(), "the Philadelphia Fed workbook"), sheet, **kwargs)


def load_us_quartiles(sheet: str, **kwargs) -> pd.DataFrame:
    """The densities of a grid-stable US core question with their quartiles and Bowley skewness."""
    return io_us_spf.quartiles(paths.require(paths.us_spf_workbook(), "the Philadelphia Fed workbook"), sheet, **kwargs)


def load_fred(series: str = "T5YIE") -> pd.Series:
    path = paths.fred_csv(series)
    if not path.exists():
        print(f"fetching FRED {series} ...", file=sys.stderr)
        s = io_other.fred_fetch(series)
        path.parent.mkdir(parents=True, exist_ok=True)
        s.rename_axis("observation_date").to_csv(path)
        return s
    return io_other.fred_csv(path, series)


def load_longer_term_points(keep_missing: bool = False) -> pd.DataFrame:
    """The longer-term HICP point forecasts of every ECB-SPF round file (``io_ecb_spf.longer_term_panel``)."""
    return io_ecb_spf.longer_term_panel(paths.require(paths.ecb_spf_rounds(), "the ECB-SPF round files"), keep_missing=keep_missing)


def load_flat_panel(rebuild: bool = False) -> pd.DataFrame:
    """The ECB-SPF flat panel (probabilities in per cent, ``Date`` = target period), from ``derived/``."""
    derived = paths.derived_dir()
    cached = derived / "flat_panel.csv"
    if not cached.exists() or rebuild:
        load_ecb_panel(rebuild=True)
    flat = pd.read_csv(cached)
    flat["Date"] = pd.to_datetime(flat["Date"])
    return flat


def load_hicp_yoy() -> pd.Series:
    """Realized euro-area HICP inflation, year on year, monthly (per cent), indexed by month start.

    From ``ecb/hicp_index.csv`` (the index, as the panel builder reads it) when
    present, else from the macro block's ``HICP_YOY`` column.
    """
    idx_path = paths.hicp_index_csv()
    if idx_path.exists():
        df = pd.read_csv(idx_path)
        date_col = "DATE" if "DATE" in df.columns else df.columns[0]
        value_col = [c for c in df.columns if c not in (date_col, "TIME PERIOD", "TIME_PERIOD")][-1]
        s = pd.Series(pd.to_numeric(df[value_col], errors="coerce").to_numpy(),
                      index=pd.to_datetime(df[date_col]).dt.to_period("M").dt.to_timestamp())
        return io_ecb_spf.hicp_yoy_from_index(s.sort_index()).dropna().rename("HICP_YOY")
    block = load_macro_block(balanced=False)
    return block["HICP_YOY"].dropna()
