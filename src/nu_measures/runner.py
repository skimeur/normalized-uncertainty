"""Run the exhibit scripts of a paper folder, in order, and report.

Each paper folder holds ``exhibits/``: one script per figure or table, named so
that sorting them gives the order of the manuscript. Each script is run in its
own process, so one failure neither stops the others nor leaves state behind.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

__all__ = ["discover", "run_exhibits", "main"]


def discover(folder: Path) -> list[Path]:
    """The exhibit scripts of ``folder``, in manuscript order."""
    exhibits = folder / "exhibits"
    if not exhibits.is_dir():
        return []
    return sorted(p for p in exhibits.glob("*.py") if not p.name.startswith("_"))


def run_exhibits(folder: Path, only: str | None = None) -> int:
    scripts = discover(folder)
    if only:
        scripts = [p for p in scripts if only in p.stem]
        if not scripts:
            print(f"no exhibit matches {only!r}", file=sys.stderr)
            return 1
    if not scripts:
        print(
            f"no exhibit scripts in {folder.name}/exhibits yet.\n"
            "The exhibits are written phase by phase; see CHANGELOG.md."
        )
        return 0

    failures = []
    for script in scripts:
        print(f"--- {script.stem}", flush=True)
        started = time.monotonic()
        result = subprocess.run([sys.executable, str(script)], cwd=folder)
        elapsed = time.monotonic() - started
        if result.returncode == 0:
            print(f"    ok ({elapsed:.1f}s)")
        else:
            failures.append(script.stem)
            print(f"    FAILED ({elapsed:.1f}s)", file=sys.stderr)

    print()
    print(f"{len(scripts) - len(failures)}/{len(scripts)} exhibits rebuilt")
    if failures:
        print("failed: " + ", ".join(failures), file=sys.stderr)
        return 1
    return 0


def main(folder: str | Path) -> int:
    folder = Path(folder).resolve()
    parser = argparse.ArgumentParser(description=f"Rebuild the exhibits of {folder.name}.")
    parser.add_argument("--only", help="run only exhibits whose name contains this")
    parser.add_argument("--list", action="store_true", help="list the exhibits and exit")
    args = parser.parse_args()

    if args.list:
        for script in discover(folder):
            print(script.stem)
        return 0
    return run_exhibits(folder, only=args.only)
