import pytest

from github_triage.evaluation.comparison import compare_experiments
from github_triage.evaluation.types import PredictionRecord
from github_triage.models import TriageDecision


def _decision(priority: str = "low", human: bool = False) -> TriageDecision:
    return TriageDecision(
        issue_type="bug",
        priority=priority,
        needs_human_review=human,
    )


def _result(case_id: str, gold: TriageDecision, prediction: TriageDecision) -> PredictionRecord:
    return PredictionRecord(
        id=case_id,
        gold=gold,
        prediction=prediction,
        slices=["synthetic"],
        latency_ms=1,
        estimated_cost_usd=0.001,
    )


def test_comparison_is_paired_and_detects_improvement() -> None:
    low = _decision()
    wrong = _decision(priority="medium")
    baseline = [_result(f"case-{index}", low, wrong) for index in range(10)]
    candidate = [_result(f"case-{index}", low, low) for index in range(10)]

    comparison = compare_experiments(baseline, candidate, samples=500, seed=7)

    assert comparison["exact_match_accuracy_delta"] == 1
    assert comparison["paired_bootstrap_delta_95_ci"] == [1, 1]
    assert comparison["prediction_agreement_rate"] == 0
    assert comparison["field_agreement"]["issue_type"] == 1
    assert comparison["promotion_recommended"] is True


def test_comparison_rejects_different_cases() -> None:
    low = _decision()

    with pytest.raises(ValueError, match="identical case IDs"):
        compare_experiments([_result("one", low, low)], [_result("two", low, low)])


def test_comparison_rejects_safety_regression() -> None:
    high_human = _decision(priority="high", human=True)
    low_no_human = _decision(priority="low", human=False)
    baseline = [_result("case", high_human, high_human)]
    candidate = [_result("case", high_human, low_no_human)]

    comparison = compare_experiments(baseline, candidate, samples=100, seed=7)

    assert comparison["safety_gates_pass"] is False
    assert comparison["promotion_recommended"] is False


def test_comparison_reports_repeat_agreement() -> None:
    high_human = _decision(priority="high", human=True)
    medium_human = _decision(priority="medium", human=True)
    first = [
        _result("same", high_human, high_human),
        _result("flip", high_human, medium_human),
    ]
    second = [
        _result("same", high_human, high_human),
        _result("flip", high_human, high_human),
    ]

    comparison = compare_experiments(first, second, samples=100, seed=7)

    assert comparison["prediction_agreement_rate"] == 0.5
    assert comparison["field_agreement"] == {
        "issue_type": 1,
        "priority": 0.5,
        "needs_human_review": 1,
    }
