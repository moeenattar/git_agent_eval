"""Evaluation result contracts."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from github_triage.models import TriageDecision


class PredictionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    gold: TriageDecision
    prediction: TriageDecision | None
    slices: list[str]
    latency_ms: float
    input_tokens: int | None = None
    output_tokens: int | None = None
    estimated_cost_usd: float | None = None
    error: str | None = None
