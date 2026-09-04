import pytest

from github_triage.config import ModelPricing
from github_triage.evaluation.runner import evaluate_records
from github_triage.models import DatasetRecord, TriageDecision
from github_triage.service import TriageResult


def _record(case_id: str) -> DatasetRecord:
    return DatasetRecord.model_validate(
        {
            "id": case_id,
            "source": "synthetic",
            "title": "Broken search",
            "body": "Search always fails.",
            "gold": {
                "issue_type": "bug",
                "priority": "medium",
                "needs_human_review": False,
            },
            "annotation": {"reason": "A clear functional failure."},
            "slices": ["synthetic"],
        }
    )


@pytest.mark.asyncio
async def test_runner_records_usage_and_normalized_cost() -> None:
    async def predictor(_issue):
        return TriageResult(
            decision=TriageDecision(issue_type="bug", priority="medium", needs_human_review=False),
            latency_ms=12.5,
            input_tokens=1_000,
            output_tokens=100,
        )

    results = await evaluate_records(
        [_record("one")],
        predictor,
        ModelPricing(input_per_million=1.0, output_per_million=5.0),
    )

    assert results[0].prediction == results[0].gold
    assert results[0].estimated_cost_usd == pytest.approx(0.0015)


@pytest.mark.asyncio
async def test_runner_preserves_failed_case() -> None:
    async def predictor(_issue):
        raise TimeoutError("model timed out")

    results = await evaluate_records(
        [_record("one")], predictor, ModelPricing(input_per_million=0, output_per_million=0)
    )

    assert results[0].prediction is None
    assert results[0].error == "TimeoutError: model timed out"


@pytest.mark.asyncio
async def test_runner_retries_quota_error() -> None:
    attempts = 0

    async def predictor(_issue):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("429 RESOURCE_EXHAUSTED")
        return TriageResult(
            decision=TriageDecision(issue_type="bug", priority="medium", needs_human_review=False),
            latency_ms=10,
        )

    results = await evaluate_records(
        [_record("one")],
        predictor,
        ModelPricing(input_per_million=0, output_per_million=0),
        max_attempts=2,
        retry_delay_seconds=0,
    )

    assert attempts == 2
    assert results[0].prediction == results[0].gold
