"""Dependency-light, deterministic metrics for structured triage output."""

from __future__ import annotations

import math
import random
from collections import defaultdict
from collections.abc import Iterable, Sequence
from typing import Any

from github_triage.evaluation.types import PredictionRecord
from github_triage.models import IssueType, Priority


def _safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def _percentile(values: Sequence[float], probability: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = (len(ordered) - 1) * probability
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (rank - lower)


def macro_f1(gold: Sequence[str], predicted: Sequence[str], labels: Iterable[str]) -> float:
    scores: list[float] = []
    for label in labels:
        true_positive = sum(g == label and p == label for g, p in zip(gold, predicted, strict=True))
        false_positive = sum(
            g != label and p == label for g, p in zip(gold, predicted, strict=True)
        )
        false_negative = sum(
            g == label and p != label for g, p in zip(gold, predicted, strict=True)
        )
        precision = _safe_div(true_positive, true_positive + false_positive)
        recall = _safe_div(true_positive, true_positive + false_negative)
        scores.append(_safe_div(2 * precision * recall, precision + recall))
    return sum(scores) / len(scores) if scores else 0.0


def bootstrap_accuracy_interval(
    correct: Sequence[bool], *, samples: int = 5_000, seed: int = 42
) -> tuple[float, float]:
    if not correct:
        return (0.0, 0.0)
    generator = random.Random(seed)
    size = len(correct)
    distribution = [
        sum(correct[generator.randrange(size)] for _ in range(size)) / size for _ in range(samples)
    ]
    return (_percentile(distribution, 0.025), _percentile(distribution, 0.975))


def _confusion(gold: Sequence[str], predicted: Sequence[str]) -> dict[str, dict[str, int]]:
    matrix: defaultdict[str, defaultdict[str, int]] = defaultdict(lambda: defaultdict(int))
    for expected, actual in zip(gold, predicted, strict=True):
        matrix[expected][actual] += 1
    return {expected: dict(counts) for expected, counts in matrix.items()}


def compute_metrics(results: Sequence[PredictionRecord]) -> dict[str, Any]:
    """Compute metrics on successful predictions; failures remain in the denominator."""

    if not results:
        raise ValueError("cannot evaluate an empty result set")

    successful = [item for item in results if item.prediction is not None]
    exact = [
        item.prediction == item.gold if item.prediction is not None else False for item in results
    ]

    type_gold = [item.gold.issue_type.value for item in successful]
    type_pred = [item.prediction.issue_type.value for item in successful if item.prediction]
    priority_gold = [item.gold.priority.value for item in successful]
    priority_pred = [item.prediction.priority.value for item in successful if item.prediction]
    human_gold = [str(item.gold.needs_human_review) for item in successful]
    human_pred = [str(item.prediction.needs_human_review) for item in successful if item.prediction]

    human_required = sum(item.gold.needs_human_review for item in results)
    human_false_negatives = sum(
        item.gold.needs_human_review
        and (item.prediction is None or not item.prediction.needs_human_review)
        for item in results
    )
    critical_under_triage = sum(
        item.gold.priority is Priority.HIGH
        and item.prediction is not None
        and item.prediction.priority is Priority.LOW
        for item in results
    )
    ci_low, ci_high = bootstrap_accuracy_interval(exact)
    latencies = [item.latency_ms for item in results]
    known_costs = [
        item.estimated_cost_usd for item in results if item.estimated_cost_usd is not None
    ]
    known_input_tokens = [item.input_tokens for item in results if item.input_tokens is not None]
    known_output_tokens = [item.output_tokens for item in results if item.output_tokens is not None]

    return {
        "case_count": len(results),
        "successful_predictions": len(successful),
        "errors": len(results) - len(successful),
        "exact_match_accuracy": sum(exact) / len(results),
        "exact_match_bootstrap_95_ci": [ci_low, ci_high],
        "type_macro_f1": macro_f1(type_gold, type_pred, [item.value for item in IssueType]),
        "priority_macro_f1": macro_f1(
            priority_gold, priority_pred, [item.value for item in Priority]
        ),
        "human_review_macro_f1": macro_f1(human_gold, human_pred, ["True", "False"]),
        "human_review_false_negatives": human_false_negatives,
        "human_review_false_negative_rate": _safe_div(human_false_negatives, human_required),
        "critical_under_triage_count": critical_under_triage,
        "latency_ms": {
            "mean": sum(latencies) / len(latencies),
            "p95": _percentile(latencies, 0.95),
        },
        "usage": {
            "input_tokens": sum(known_input_tokens),
            "output_tokens": sum(known_output_tokens),
            "cases_with_usage": min(len(known_input_tokens), len(known_output_tokens)),
        },
        "estimated_cost_usd": {
            "total": sum(known_costs),
            "per_1000_issues": _safe_div(sum(known_costs), len(known_costs)) * 1000,
            "cases_with_cost": len(known_costs),
        },
        "confusion": {
            "issue_type": _confusion(type_gold, type_pred),
            "priority": _confusion(priority_gold, priority_pred),
            "human_review": _confusion(human_gold, human_pred),
        },
    }
