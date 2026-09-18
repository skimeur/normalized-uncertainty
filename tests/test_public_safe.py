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
