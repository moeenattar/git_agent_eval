#!/usr/bin/env python3
"""Validate annotated datasets and detect calibration/test leakage."""

from __future__ import annotations

import argparse
from pathlib import Path

from github_triage.evaluation.dataset import (
    find_cross_split_leakage,
    find_manifest_errors,
    find_review_coverage_errors,
    load_dataset,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("datasets", nargs="+", type=Path)
    args = parser.parse_args()

    loaded = {path.stem: load_dataset(path) for path in args.datasets}
    errors = find_cross_split_leakage(loaded)
    errors.extend(
        find_review_coverage_errors([record for records in loaded.values() for record in records])
    )
    parents = {path.parent.resolve() for path in args.datasets}
    if len(parents) == 1:
        manifest_path = parents.pop() / "manifest.json"
        if manifest_path.exists():
            errors.extend(find_manifest_errors(manifest_path))
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
