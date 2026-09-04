from collections import Counter
from pathlib import Path

from github_triage.evaluation.dataset import find_cross_split_leakage, load_dataset


def test_draft_dataset_has_planned_composition() -> None:
    calibration = load_dataset(Path("datasets/calibration.jsonl"))
    golden = load_dataset(Path("datasets/golden_test.jsonl"))
    records = calibration + golden

    assert len(calibration) == 15
    assert len(golden) == 35
    assert Counter(record.source for record in records) == {"github": 40, "synthetic": 10}
    assert not find_cross_split_leakage({"calibration": calibration, "golden": golden})


def test_draft_records_have_required_analysis_slices() -> None:
    records = load_dataset(Path("datasets/calibration.jsonl")) + load_dataset(
        Path("datasets/golden_test.jsonl")
    )

    for record in records:
        expected = {
            "real" if record.source == "github" else "synthetic",
            record.gold.issue_type.value,
            f"priority_{record.gold.priority.value}",
            "human_required" if record.gold.needs_human_review else "human_not_required",
        }
        assert expected <= set(record.slices), record.id
        assert record.dataset_version == "draft-v0"
        assert record.annotation.annotator == "codex-draft"
