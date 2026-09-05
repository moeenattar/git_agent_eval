"""Google ADK agent definition."""

from pathlib import Path

from google.adk.agents import LlmAgent
from google.genai import types

from github_triage.models import AgentTriageDecision, IssueInput


def load_prompt(path: Path) -> str:
    prompt = path.read_text(encoding="utf-8").strip()
    if not prompt:
        raise ValueError(f"prompt file is empty: {path}")
    return prompt


def resolve_model(model: str):
    """Return an ADK model connector while keeping Groq support optional."""

    if not model.startswith("groq/"):
        return model
    try:
        from google.adk.models.lite_llm import LiteLlm
    except ImportError as exc:
        raise RuntimeError(
            "Groq models require the optional dependency: pip install -e '.[groq]'"
        ) from exc
    # GPT-OSS exposes reasoning separately; excluding it keeps ADK's final text
    # aligned with the strict JSON response schema.
    return LiteLlm(model=model, include_reasoning=False)


def build_agent(*, model: str, prompt_path: Path) -> LlmAgent:
    """Build one deliberately tool-free classifier agent."""

    return LlmAgent(
        name="github_issue_triage_agent",
        description="Classifies a GitHub issue by type, urgency, and review requirement.",
        model=resolve_model(model),
        instruction=load_prompt(prompt_path),
        input_schema=IssueInput,
        output_schema=AgentTriageDecision,
        output_key="triage_decision",
        generate_content_config=types.GenerateContentConfig(temperature=0),
    )
