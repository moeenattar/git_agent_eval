import pytest
from pydantic import ValidationError

from github_triage.models import DatasetRecord, IssueInput, TriageDecision


def test_issue_input_rejects_unexpected_metadata() -> None:
    with pytest.raises(ValidationError):
        IssueInput(title="Broken", body="Details", labels=["bug"])


def test_triage_decision_rejects_unknown_label() -> None:
    with pytest.raises(ValidationError):
        TriageDecision(
            issue_type="incident",
            priority="high",
            needs_human_review=True,
        )


def test_dataset_inference_input_drops_annotation_fields() -> None:
    record = DatasetRecord.model_validate(
        {
            "id": "case-1",
            "source": "synthetic",
            "title": "A title",
            "body": "A body",
            "gold": {
                "issue_type": "bug",
                "priority": "medium",
                "needs_human_review": False,
            },
            "annotation": {"reason": "Clear functional defect."},
            "slices": ["synthetic"],
        }
    )

    assert record.inference_input().model_dump() == {"title": "A title", "body": "A body"}
