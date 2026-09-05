from pathlib import Path

import pytest

from github_triage.agent import build_agent, load_prompt, resolve_model
from github_triage.models import AgentTriageDecision


def test_agent_uses_structured_output_and_zero_temperature() -> None:
    prompt = Path("prompts/triage_v1.txt")
    agent = build_agent(model="gemini-3.5-flash-lite", prompt_path=prompt)

    assert agent.output_schema is AgentTriageDecision
    assert agent.generate_content_config.temperature == 0
    assert agent.tools == []
    assert "Security and privacy concerns" in load_prompt(prompt)


def test_agent_response_schema_avoids_unsupported_additional_properties() -> None:
    assert "additionalProperties" not in AgentTriageDecision.model_json_schema()


def test_non_groq_model_does_not_require_optional_connector() -> None:
    assert resolve_model("gemini-3.5-flash-lite") == "gemini-3.5-flash-lite"


def test_groq_model_excludes_reasoning_from_structured_response() -> None:
    model = resolve_model("groq/openai/gpt-oss-20b")

    assert model.model == "groq/openai/gpt-oss-20b"
    assert model._additional_args["include_reasoning"] is False


def test_unverified_groq_model_is_rejected_before_api_call() -> None:
    with pytest.raises(ValueError, match="unsupported Groq model"):
        resolve_model("groq/qwen/qwen3.6-27b")
