#!/usr/bin/env python3
"""Rebuild every exhibit of this paper. See the paper's README for the map."""

from pathlib import Path

from nu_measures.runner import main

if __name__ == "__main__":
    raise SystemExit(main(Path(__file__).resolve().parent))
