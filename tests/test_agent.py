from pathlib import Path

from github_triage.agent import build_agent, load_prompt
from github_triage.models import TriageDecision


def test_agent_uses_structured_output_and_zero_temperature() -> None:
    prompt = Path("prompts/triage_v1.txt")
    agent = build_agent(model="gemini-2.5-flash", prompt_path=prompt)

    assert agent.output_schema is TriageDecision
    assert agent.generate_content_config.temperature == 0
    assert agent.tools == []
    assert "Security and privacy concerns" in load_prompt(prompt)
