#!/usr/bin/env python3
"""Validate annotated datasets and detect calibration/test leakage."""

from __future__ import annotations

import argparse
from pathlib import Path

from github_triage.evaluation.dataset import find_cross_split_leakage, load_dataset


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("datasets", nargs="+", type=Path)
    args = parser.parse_args()

    loaded = {path.stem: load_dataset(path) for path in args.datasets}
    errors = find_cross_split_leakage(loaded)
    for name, records in loaded.items():
        print(f"{name}: {len(records)} valid records")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("No cross-split leakage detected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
