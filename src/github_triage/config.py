"""Runtime configuration loaded from flags or environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AgentConfig:
    model: str = "gemini-2.5-flash"
    prompt_path: Path = Path("prompts/triage_v1.txt")
    app_name: str = "github_triage"

    @classmethod
    def from_env(cls) -> AgentConfig:
        return cls(
            model=os.getenv("TRIAGE_MODEL", cls.model),
            prompt_path=Path(os.getenv("TRIAGE_PROMPT_PATH", str(cls.prompt_path))),
        )


@dataclass(frozen=True)
class ModelPricing:
    """Normalized USD list prices, supplied per experiment."""

    input_per_million: float
    output_per_million: float

    def __post_init__(self) -> None:
        if self.input_per_million < 0 or self.output_per_million < 0:
            raise ValueError("prices cannot be negative")

    def estimate(self, input_tokens: int, output_tokens: int) -> float:
        if input_tokens < 0 or output_tokens < 0:
            raise ValueError("token counts cannot be negative")
        return (
            input_tokens * self.input_per_million + output_tokens * self.output_per_million
        ) / 1_000_000
