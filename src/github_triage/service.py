"""Inference service around the Google ADK runtime."""

import json
import time
import uuid
from dataclasses import dataclass

from google.adk.runners import InMemoryRunner
from google.genai import types

from github_triage.agent import build_agent
from github_triage.config import AgentConfig
from github_triage.models import IssueInput, TriageDecision


@dataclass(frozen=True)
class TriageResult:
    decision: TriageDecision
    latency_ms: float
    input_tokens: int | None = None
    output_tokens: int | None = None


class TriageService:
    """Runs one isolated ADK session per issue to prevent cross-case leakage."""

    def __init__(self, config: AgentConfig) -> None:
        self.config = config
        agent = build_agent(model=config.model, prompt_path=config.prompt_path)
        self.runner = InMemoryRunner(agent=agent, app_name=config.app_name)

    async def triage(self, issue: IssueInput) -> TriageResult:
        session_id = uuid.uuid4().hex
        user_id = "evaluation-user"
        await self.runner.session_service.create_session(
            app_name=self.config.app_name,
            user_id=user_id,
            session_id=session_id,
        )

        message = types.Content(
            role="user",
            parts=[types.Part(text=issue.model_dump_json())],
        )
        started = time.perf_counter()
        final_text: str | None = None
        input_tokens: int | None = None
        output_tokens: int | None = None

        async for event in self.runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=message,
        ):
            usage = getattr(event, "usage_metadata", None)
            if usage is not None:
                input_tokens = getattr(usage, "prompt_token_count", input_tokens)
                output_tokens = getattr(usage, "candidates_token_count", output_tokens)
            if event.is_final_response() and event.content:
                final_text = "".join(
                    part.text or "" for part in event.content.parts if getattr(part, "text", None)
                )

        latency_ms = (time.perf_counter() - started) * 1000
        if not final_text:
            raise RuntimeError("ADK agent returned no final response")

        try:
            decision = TriageDecision.model_validate(json.loads(final_text))
        except (json.JSONDecodeError, ValueError) as exc:
            raise RuntimeError(f"agent returned invalid triage JSON: {final_text!r}") from exc

        return TriageResult(
            decision=decision,
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
