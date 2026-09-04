import pytest

from github_triage.evaluation.metrics import bootstrap_accuracy_interval, compute_metrics
from github_triage.evaluation.types import PredictionRecord
from github_triage.models import TriageDecision


def _decision(issue_type: str, priority: str, human: bool) -> TriageDecision:
    return TriageDecision(
        issue_type=issue_type,
        priority=priority,
        needs_human_review=human,
    )


def test_metrics_count_failures_and_safety_errors() -> None:
    results = [
        PredictionRecord(
            id="correct",
            gold=_decision("documentation", "low", False),
            prediction=_decision("documentation", "low", False),
            slices=["clear"],
            latency_ms=10,
            input_tokens=100,
            output_tokens=20,
            estimated_cost_usd=0.001,
        ),
        PredictionRecord(
            id="under-triage",
            gold=_decision("bug", "high", True),
            prediction=_decision("bug", "low", False),
            slices=["security"],
            latency_ms=20,
            input_tokens=200,
            output_tokens=30,
            estimated_cost_usd=0.002,
        ),
        PredictionRecord(
            id="failed",
            gold=_decision("maintenance", "low", False),
            prediction=None,
            slices=["clear"],
            latency_ms=0,
            error="RuntimeError: unavailable",
        ),
    ]

    metrics = compute_metrics(results)

    assert metrics["exact_match_accuracy"] == pytest.approx(1 / 3)
    assert metrics["errors"] == 1
    assert metrics["critical_under_triage_count"] == 1
    assert metrics["human_review_false_negatives"] == 1
    assert metrics["human_review_false_negative_rate"] == 1
    assert metrics["estimated_cost_usd"]["total"] == pytest.approx(0.003)
    assert metrics["estimated_cost_usd"]["per_1000_issues"] == pytest.approx(1.5)


def test_bootstrap_interval_is_reproducible_and_bounded() -> None:
    first = bootstrap_accuracy_interval([True, True, False, True], samples=500, seed=7)
    second = bootstrap_accuracy_interval([True, True, False, True], samples=500, seed=7)

    assert first == second
    assert 0 <= first[0] <= first[1] <= 1
