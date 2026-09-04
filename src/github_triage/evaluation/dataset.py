"""JSONL loading and cross-split validation."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from github_triage.models import DatasetRecord


class DatasetError(ValueError):
    pass


def load_dataset(path: Path) -> list[DatasetRecord]:
    records: list[DatasetRecord] = []
    seen_ids: set[str] = set()
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                record = DatasetRecord.model_validate(json.loads(line))
            except (json.JSONDecodeError, ValidationError) as exc:
                raise DatasetError(f"{path}:{line_number}: {exc}") from exc
            if record.id in seen_ids:
                raise DatasetError(f"{path}:{line_number}: duplicate id {record.id!r}")
            seen_ids.add(record.id)
            records.append(record)
    if not records:
        raise DatasetError(f"dataset is empty: {path}")
    return records


def find_cross_split_leakage(datasets: dict[str, list[DatasetRecord]]) -> list[str]:
    """Return examples that overlap by ID or normalized title/body fingerprint."""

    owners_by_id: dict[str, str] = {}
    owners_by_content: dict[tuple[str, str], str] = {}
    errors: list[str] = []
    for split_name, records in datasets.items():
        for record in records:
            previous = owners_by_id.setdefault(record.id, split_name)
            if previous != split_name:
                errors.append(f"id {record.id!r} appears in {previous} and {split_name}")
            fingerprint = (record.title.strip().casefold(), record.body.strip().casefold())
            previous = owners_by_content.setdefault(fingerprint, split_name)
            if previous != split_name:
                errors.append(
                    f"content for {record.id!r} appears in both {previous} and {split_name}"
                )
    return errors
