#!/usr/bin/env python3
"""Refuse anything that must not be published from this repository.

The repository was private until the second paper was posted (arXiv:2609.31512,
September 2026) and is public since; git keeps its history across that switch,
so the rule has held from the first commit rather than being applied at the end. This gate runs in continuous
integration and as a test, and fails on:

1. **Restricted-data code.** The loan-level credit application rests on
   supervisory data held at the Banque de France, and the swap and option
   evidence on licensed market exports. Their code is not published; only the
   prose description in the restricted route is, and prose is allowed only in
   the documentation files listed in ``PROSE_EXEMPT``.
2. **Redistributed data.** No third-party file travels with this repository.
3. **Local paths and working files.** Absolute paths from the author's machine,
   and the internal records of the writing workflow, do not belong in a code
   repository.
4. **Credentials.** Anything shaped like a token or a private key.

This file names the patterns it forbids, so it exempts itself and its test.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SELF_EXEMPT = {"scripts/check_public_safe.py", "tests/test_public_safe.py"}

#: Files where the restricted sources may be *named*, because describing the
#: route a reader with access would take is the point of them.
PROSE_EXEMPT = {
    "README.md",
    "CHANGELOG.md",
    "data/README.md",
    "docs/METHODS.md",
    "papers/tolerable-inflation-intolerable-uncertainty/README.md",
    "papers/tolerable-inflation-intolerable-uncertainty/restricted/README.md",
    "papers/uncertain-and-asymmetric-forecasts/README.md",
}

CODE_SUFFIXES = {".py", ".r", ".sh", ".ipynb", ".yml", ".yaml", ".toml", ".cfg", ".do"}

DATA_SUFFIXES = {".csv", ".xlsx", ".xls", ".parquet", ".dta", ".pkl", ".feather", ".sav", ".rds"}

BINARY_SUFFIXES = DATA_SUFFIXES | {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".zip", ".gz", ".ico"}

#: Forbidden everywhere.
ALWAYS = {
    "local path": re.compile(r"/Users/[A-Za-z0-9._-]+|/sessions/|/mnt/user-data"),
    "credential": re.compile(
        r"ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|BEGIN (?:RSA |OPENSSH )?PRIVATE KEY"
    ),
    "internal working file": re.compile(
        r"PAPER_CONTEXT_AND_TASKS|MODEL_PROVENANCE_LEDGER|lambda_research_record"
        r"|empirical_research_record|appendix_proof_additional_old_elements"
        r"|answers_referee|670fc6c095a99d8c9f24db38",
        re.IGNORECASE,
    ),
}

#: Forbidden in code, allowed as prose in the documentation files above.
RESTRICTED = {
    "supervisory credit data": re.compile(r"anacredit|pyodbc|\bhive\b", re.IGNORECASE),
    "licensed market data": re.compile(
        r"bloomberg|\bxbbg\b|\bblp\b|ils_daily_panel|option_hybrid|swaps_floors_caps|ILS_ESTR",
        re.IGNORECASE,
    ),
}


def tracked_files() -> list[Path]:
    try:
        # Tracked files and untracked ones alike (ignored files excluded): the
        # gate must catch a violation before it is ever committed.
        out = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.split()
        return [ROOT / p for p in out]
    except (subprocess.CalledProcessError, FileNotFoundError):
        # No git (a ZIP or Zenodo download): skip what .gitignore skips -- build
        # products, virtual environments and caches -- so that `pip install -e .`
        # (which copies the README into *.egg-info) does not trip the gate.
        return [
            p
            for p in ROOT.rglob("*")
            if p.is_file() and not any(_ignored(part) for part in p.relative_to(ROOT).parts)
        ]


def _ignored(part: str) -> bool:
    return part in _IGNORED_PARTS or part.endswith(".egg-info")


_IGNORED_PARTS = {".git", "__pycache__", ".pytest_cache", ".ruff_cache", ".venv", "venv", "build", "dist", ".tox", "htmlcov"}


def check() -> list[str]:
    problems: list[str] = []
    for path in tracked_files():
        rel = path.relative_to(ROOT).as_posix()
        if rel in SELF_EXEMPT:
            continue
        suffix = path.suffix.lower()

        if suffix in DATA_SUFFIXES and not rel.startswith("papers/"):
            problems.append(f"{rel}: data file tracked; this repository distributes no data")
            continue
        if rel.startswith(("data/raw/", "data/derived/")):
            problems.append(f"{rel}: tracked under a data directory that must stay local")
            continue
        if suffix in BINARY_SUFFIXES:
            continue

        try:
            text = path.read_text(encoding="utf-8", errors="strict")
        except (UnicodeDecodeError, OSError):
            continue

        for label, pattern in ALWAYS.items():
            hit = pattern.search(text)
            if hit:
                problems.append(f"{rel}: {label} ({hit.group(0)[:40]!r})")

        if rel in PROSE_EXEMPT and suffix not in CODE_SUFFIXES:
            continue
        for label, pattern in RESTRICTED.items():
            hit = pattern.search(text)
            if hit:
                problems.append(f"{rel}: {label} named outside the documented route ({hit.group(0)!r})")
    return problems


def main() -> int:
    problems = check()
    if problems:
        print("public-safety gate FAILED:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print("public-safety gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
