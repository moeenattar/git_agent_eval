"""Model-agnostic evaluation loop."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable, Sequence

from github_triage.config import ModelPricing
from github_triage.evaluation.types import PredictionRecord
from github_triage.models import DatasetRecord, IssueInput
from github_triage.service import TriageResult

Predictor = Callable[[IssueInput], Awaitable[TriageResult]]


def _is_retryable_model_error(exc: Exception) -> bool:
    message = f"{type(exc).__name__}: {exc}".lower()
    return any(
        marker in message
        for marker in ("resource_exhausted", "429", "unavailable", "503")
    )


async def evaluate_records(
    records: Sequence[DatasetRecord],
    predictor: Predictor,
    pricing: ModelPricing,
    *,
    requests_per_minute: float | None = None,
    max_attempts: int = 1,
    retry_delay_seconds: float = 30,
) -> list[PredictionRecord]:
    if requests_per_minute is not None and requests_per_minute <= 0:
        raise ValueError("requests_per_minute must be positive")
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    if retry_delay_seconds < 0:
        raise ValueError("retry_delay_seconds cannot be negative")

    results: list[PredictionRecord] = []
    minimum_interval = 60 / requests_per_minute if requests_per_minute else 0
    last_request_started: float | None = None

    for record in records:
        for attempt in range(max_attempts):
            if last_request_started is not None:
                elapsed = time.monotonic() - last_request_started
                await asyncio.sleep(max(0, minimum_interval - elapsed))
            last_request_started = time.monotonic()

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
                break
            except Exception as exc:
                if attempt + 1 < max_attempts and _is_retryable_model_error(exc):
                    await asyncio.sleep(retry_delay_seconds)
                    continue
                # Every dataset case must be represented in aggregate metrics.
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
                break
    return results
