"""Paired comparison for experiments run on an identical frozen dataset."""

from __future__ import annotations

import random
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from github_triage.evaluation.metrics import _percentile, compute_metrics
from github_triage.evaluation.types import PredictionRecord


def _by_id(results: Sequence[PredictionRecord]) -> dict[str, PredictionRecord]:
    indexed = {item.id: item for item in results}
    if len(indexed) != len(results):
        raise ValueError("prediction records contain duplicate IDs")
    return indexed


def compare_experiments(
    baseline: Sequence[PredictionRecord],
    candidate: Sequence[PredictionRecord],
    *,
    samples: int = 5_000,
    seed: int = 42,
) -> dict[str, Any]:
    """Compare paired correctness and enforce safety-sensitive promotion gates."""

    baseline_by_id = _by_id(baseline)
    candidate_by_id = _by_id(candidate)
    if baseline_by_id.keys() != candidate_by_id.keys():
        missing = sorted(baseline_by_id.keys() - candidate_by_id.keys())
        extra = sorted(candidate_by_id.keys() - baseline_by_id.keys())
        raise ValueError(
            f"experiments must contain identical case IDs; missing={missing}, extra={extra}"
        )
    if not baseline:
        raise ValueError("cannot compare empty experiments")

    case_ids = sorted(baseline_by_id)
    paired_deltas: list[int] = []
    for case_id in case_ids:
        base = baseline_by_id[case_id]
        cand = candidate_by_id[case_id]
        if base.gold != cand.gold:
            raise ValueError(f"gold label changed between experiments for {case_id!r}")
        base_correct = base.prediction is not None and base.prediction == base.gold
        cand_correct = cand.prediction is not None and cand.prediction == cand.gold
        paired_deltas.append(int(cand_correct) - int(base_correct))

    generator = random.Random(seed)
    size = len(paired_deltas)
    bootstrap_deltas = [
        sum(paired_deltas[generator.randrange(size)] for _ in range(size)) / size
        for _ in range(samples)
    ]
    delta_ci = [_percentile(bootstrap_deltas, 0.025), _percentile(bootstrap_deltas, 0.975)]

    base_metrics = compute_metrics(baseline)
    candidate_metrics = compute_metrics(candidate)
    base_cost = base_metrics["estimated_cost_usd"]["per_1000_issues"]
    candidate_cost = candidate_metrics["estimated_cost_usd"]["per_1000_issues"]
    cost_multiplier = candidate_cost / base_cost if base_cost else None
    safety_pass = (
        candidate_metrics["critical_under_triage_count"]
        <= base_metrics["critical_under_triage_count"]
        and candidate_metrics["human_review_false_negatives"]
        <= base_metrics["human_review_false_negatives"]
    )
    accuracy_delta = sum(paired_deltas) / size

    return {
        "case_count": size,
        "baseline_exact_match_accuracy": base_metrics["exact_match_accuracy"],
        "candidate_exact_match_accuracy": candidate_metrics["exact_match_accuracy"],
        "exact_match_accuracy_delta": accuracy_delta,
        "paired_bootstrap_delta_95_ci": delta_ci,
        "baseline_critical_under_triage": base_metrics["critical_under_triage_count"],
        "candidate_critical_under_triage": candidate_metrics["critical_under_triage_count"],
        "baseline_human_review_false_negatives": base_metrics["human_review_false_negatives"],
        "candidate_human_review_false_negatives": candidate_metrics["human_review_false_negatives"],
        "baseline_cost_per_1000_usd": base_cost,
        "candidate_cost_per_1000_usd": candidate_cost,
        "cost_multiplier": cost_multiplier,
        "safety_gates_pass": safety_pass,
        "statistically_clear_improvement": delta_ci[0] > 0,
        "promotion_recommended": safety_pass and delta_ci[0] > 0,
    }


def load_predictions(path: Path) -> list[PredictionRecord]:
    records: list[PredictionRecord] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(PredictionRecord.model_validate_json(line))
    return records
