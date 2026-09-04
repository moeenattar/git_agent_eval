"""JSONL loading and cross-split validation."""

from __future__ import annotations

import hashlib
import json
import math
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


def find_review_coverage_errors(records: list[DatasetRecord]) -> list[str]:
    """Validate the human-review evidence required for a frozen dataset."""

    errors: list[str] = []
    frozen = [record for record in records if record.dataset_version == "v1"]
    if not frozen:
        return errors

    reviewed = [record for record in frozen if record.annotation.review_status is not None]
    minimum = math.ceil(len(frozen) * 0.20)
    if len(reviewed) < minimum:
        errors.append(f"v1 requires at least {minimum} reviewed cases; found {len(reviewed)}")

    for record in reviewed:
        if record.annotation.reviewed_by is None or record.annotation.reviewed_on is None:
            errors.append(f"review metadata is incomplete for {record.id!r}")

    for record in frozen:
        is_high_risk = record.gold.priority.value == "high" or "security" in record.slices
        if is_high_risk and record.annotation.review_status is None:
            errors.append(f"high/security case {record.id!r} has no independent review")
    return errors


def find_manifest_errors(manifest_path: Path) -> list[str]:
    """Verify frozen dataset files against their recorded SHA-256 hashes and counts."""

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    for filename, expected in manifest["files"].items():
        path = manifest_path.parent / filename
        if not path.exists():
            errors.append(f"manifest file is missing: {path}")
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != expected["sha256"]:
            errors.append(f"SHA-256 mismatch for {path}")
        record_count = sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line)
        if record_count != expected["records"]:
            errors.append(
                f"record count mismatch for {path}: expected {expected['records']}, "
                f"found {record_count}"
            )
    return errors
