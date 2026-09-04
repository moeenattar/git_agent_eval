import json
from pathlib import Path

import pytest

from github_triage.evaluation.dataset import (
    DatasetError,
    find_cross_split_leakage,
    find_review_coverage_errors,
    load_dataset,
)
from github_triage.models import DatasetRecord


def _record(case_id: str, title: str = "Broken search") -> dict:
    return {
        "id": case_id,
        "source": "synthetic",
        "title": title,
        "body": "Search always fails.",
        "gold": {
            "issue_type": "bug",
            "priority": "medium",
            "needs_human_review": False,
        },
        "annotation": {"reason": "A clear functional failure."},
        "slices": ["synthetic", "bug"],
        "dataset_version": "draft-v0",
    }


def test_load_dataset_rejects_duplicate_ids(tmp_path: Path) -> None:
    path = tmp_path / "data.jsonl"
    item = json.dumps(_record("duplicate"))
    path.write_text(f"{item}\n{item}\n", encoding="utf-8")

    with pytest.raises(DatasetError, match="duplicate id"):
        load_dataset(path)


def test_cross_split_leakage_detects_same_content(tmp_path: Path) -> None:
    first = tmp_path / "cal.jsonl"
    second = tmp_path / "test.jsonl"
    first.write_text(json.dumps(_record("cal-1")) + "\n", encoding="utf-8")
    second.write_text(json.dumps(_record("test-1")) + "\n", encoding="utf-8")

    errors = find_cross_split_leakage(
        {"calibration": load_dataset(first), "test": load_dataset(second)}
    )

    assert errors == ["content for 'test-1' appears in both calibration and test"]


def test_frozen_high_priority_case_requires_review() -> None:
    value = _record("high-risk")
    value["dataset_version"] = "v1"
    value["gold"]["priority"] = "high"
    record = DatasetRecord.model_validate(value)

    errors = find_review_coverage_errors([record])

    assert "high/security case 'high-risk' has no independent review" in errors
