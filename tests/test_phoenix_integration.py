from pathlib import Path

import pytest

from github_triage.evaluation.comparison import load_predictions
from github_triage.evaluation.dataset import load_dataset
from github_triage.evaluation.metrics import compute_metrics
from github_triage.evaluation.types import PredictionRecord
from github_triage.models import (
    Annotation,
    DatasetRecord,
    IssueType,
    Priority,
    TriageDecision,
)
from github_triage.phoenix_integration import (
    critical_under_triage,
    default_phoenix_dataset_name,
    exact_match,
    high_priority_downgrade,
    human_review_false_negative,
    live_model_provider,
    phoenix_evaluators,
    phoenix_examples,
    phoenix_prompt_name,
    replay_task,
    validate_live_credentials,
    validate_replay_predictions,
)


def _record() -> DatasetRecord:
    return DatasetRecord(
        id="case-1",
        source="synthetic",
        title="Credential leak",
        body="A secret was committed.",
        gold=TriageDecision(
            issue_type=IssueType.BUG,
            priority=Priority.HIGH,
            needs_human_review=True,
        ),
        annotation=Annotation(reason="Security-sensitive incident."),
        slices=["security", "priority_high"],
        dataset_version="v1",
    )


def _prediction(decision: TriageDecision | None = None) -> PredictionRecord:
    record = _record()
    return PredictionRecord(
        id=record.id,
        gold=record.gold,
        prediction=decision or record.gold,
        slices=record.slices,
        latency_ms=1,
    )


def test_phoenix_examples_keep_gold_and_annotations_out_of_input() -> None:
    examples = phoenix_examples([_record()], "abc123")

    assert examples[0]["id"] == "case-1"
    assert examples[0]["input"] == {
        "title": "Credential leak",
        "body": "A secret was committed.",
    }
    assert examples[0]["output"]["priority"] == "high"
    assert "gold" not in examples[0]["input"]
    assert examples[0]["metadata"]["dataset_sha256"] == "abc123"
    assert default_phoenix_dataset_name([_record()], "abcdef0123456789") == (
        "github-triage-golden-v1-abcdef012345"
    )
    assert phoenix_prompt_name(
        Path("prompts/triage_v2.txt"), "groq/openai/gpt-oss-20b", "abcdef0123456789"
    ) == "github-triage-triage_v2-groq-openai-gpt-oss-20b-abcdef012345"


def test_replay_requires_identical_case_ids_and_gold() -> None:
    prediction = _prediction()
    indexed = validate_replay_predictions([_record()], [prediction])
    assert replay_task(indexed)({"case_id": "case-1"}) == prediction.gold.model_dump(mode="json")

    with pytest.raises(ValueError, match="prediction IDs do not match"):
        validate_replay_predictions([_record()], [])


def test_code_evaluators_match_existing_correctness_and_safety_semantics() -> None:
    expected = _record().gold.model_dump(mode="json")
    downgraded = TriageDecision(
        issue_type=IssueType.BUG,
        priority=Priority.LOW,
        needs_human_review=False,
    ).model_dump(mode="json")

    assert exact_match(expected, expected)["score"] == 1
    assert exact_match(downgraded, expected)["score"] == 0
    assert human_review_false_negative(downgraded, expected)["label"] == "violation"
    assert high_priority_downgrade(downgraded, expected)["score"] == 1
    assert critical_under_triage(downgraded, expected)["score"] == 1
    assert len(phoenix_evaluators()) == 8


def test_live_phoenix_accepts_gemini_and_verified_groq_models() -> None:
    assert live_model_provider("gemini-3.5-flash-lite") == "gemini"
    assert live_model_provider("gemini-flash-latest") == "gemini"
    assert live_model_provider("groq/openai/gpt-oss-20b") == "groq"

    with pytest.raises(ValueError, match="unsupported Groq model"):
        live_model_provider("groq/qwen/qwen3.6-27b")
    with pytest.raises(ValueError, match="support Gemini model IDs"):
        live_model_provider("openai/gpt-4.1")


def test_live_phoenix_requires_the_selected_provider_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for variable in ("GOOGLE_API_KEY", "GEMINI_API_KEY", "GROQ_API_KEY"):
        monkeypatch.delenv(variable, raising=False)

    with pytest.raises(ValueError, match="GOOGLE_API_KEY or GEMINI_API_KEY"):
        validate_live_credentials("gemini")
    with pytest.raises(ValueError, match="GROQ_API_KEY"):
        validate_live_credentials("groq")

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    validate_live_credentials("gemini")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    validate_live_credentials("groq")


def test_phoenix_scores_have_parity_with_saved_harness_metrics() -> None:
    records = load_dataset(Path("datasets/golden_test.jsonl"))
    predictions = load_predictions(
        Path("artifacts/golden-groq-gpt-oss-20b-v2/predictions.jsonl")
    )
    expected = {record.id: record.gold.model_dump(mode="json") for record in records}
    metrics = compute_metrics(predictions)

    assert sum(
        exact_match(item.prediction.model_dump(mode="json"), expected[item.id])["score"]
        for item in predictions
        if item.prediction is not None
    ) == metrics["exact_match_accuracy"] * len(predictions)
    assert sum(
        human_review_false_negative(
            item.prediction.model_dump(mode="json") if item.prediction else None,
            expected[item.id],
        )["score"]
        for item in predictions
    ) == metrics["human_review_false_negatives"]
    assert sum(
        high_priority_downgrade(
            item.prediction.model_dump(mode="json") if item.prediction else None,
            expected[item.id],
        )["score"]
        for item in predictions
    ) == metrics["high_priority_downgrades_count"]
    assert sum(
        critical_under_triage(
            item.prediction.model_dump(mode="json") if item.prediction else None,
            expected[item.id],
        )["score"]
        for item in predictions
    ) == metrics["critical_under_triage_count"]
