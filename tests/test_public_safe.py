"""The public-safety gate runs as part of the test suite, not only in CI."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _gate():
    spec = importlib.util.spec_from_file_location(
        "check_public_safe", ROOT / "scripts" / "check_public_safe.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_nothing_restricted_is_tracked():
    problems = _gate().check()
    assert problems == [], "public-safety gate found: " + "; ".join(problems)


def test_the_gate_without_git_skips_build_products(tmp_path):
    """A ZIP or Zenodo download has no .git: `pip install -e .` copies the README
    (which names the restricted sources) into *.egg-info, and the gate must not trip on it."""
    gate = _gate()
    gate.ROOT = tmp_path
    (tmp_path / "src" / "pkg.egg-info").mkdir(parents=True)
    (tmp_path / "src" / "pkg.egg-info" / "PKG-INFO").write_text("Loan-level AnaCredit data; licensed Bloomberg exports.\n")
    (tmp_path / "src" / "pkg").mkdir()
    (tmp_path / "src" / "pkg" / "ok.py").write_text("x = 1\n")
    assert gate.check() == []
    (tmp_path / "src" / "pkg" / "bad.py").write_text("import pyodbc  # AnaCredit\n")
    assert any("bad.py" in p for p in gate.check())
