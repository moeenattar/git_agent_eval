"""Google ADK agent definition."""

from pathlib import Path

from google.adk.agents import LlmAgent
from google.genai import types

from github_triage.models import IssueInput, TriageDecision


def load_prompt(path: Path) -> str:
    prompt = path.read_text(encoding="utf-8").strip()
    if not prompt:
        raise ValueError(f"prompt file is empty: {path}")
    return prompt


def build_agent(*, model: str, prompt_path: Path) -> LlmAgent:
    """Build one deliberately tool-free classifier agent."""

    return LlmAgent(
        name="github_issue_triage_agent",
        description="Classifies a GitHub issue by type, urgency, and review requirement.",
        model=model,
        instruction=load_prompt(prompt_path),
        input_schema=IssueInput,
        output_schema=TriageDecision,
        output_key="triage_decision",
        generate_content_config=types.GenerateContentConfig(temperature=0),
    )
