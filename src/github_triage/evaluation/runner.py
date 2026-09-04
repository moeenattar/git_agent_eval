"""Model-agnostic evaluation loop."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence

from github_triage.config import ModelPricing
from github_triage.evaluation.types import PredictionRecord
from github_triage.models import DatasetRecord, IssueInput
from github_triage.service import TriageResult

Predictor = Callable[[IssueInput], Awaitable[TriageResult]]


async def evaluate_records(
    records: Sequence[DatasetRecord],
    predictor: Predictor,
    pricing: ModelPricing,
) -> list[PredictionRecord]:
    results: list[PredictionRecord] = []
    for record in records:
        try:
            response = await predictor(record.inference_input())
            cost = None
            if response.input_tokens is not None and response.output_tokens is not None:
                cost = pricing.estimate(response.input_tokens, response.output_tokens)
            results.append(
                PredictionRecord(
                    id=record.id,
                    gold=record.gold,
                    prediction=response.decision,
                    slices=record.slices,
                    latency_ms=response.latency_ms,
                    input_tokens=response.input_tokens,
                    output_tokens=response.output_tokens,
                    estimated_cost_usd=cost,
                )
            )
        except Exception as exc:  # Each dataset case must be represented in aggregate metrics.
            results.append(
                PredictionRecord(
                    id=record.id,
                    gold=record.gold,
                    prediction=None,
                    slices=record.slices,
                    latency_ms=0,
                    error=f"{type(exc).__name__}: {exc}",
                )
            )
    return results
