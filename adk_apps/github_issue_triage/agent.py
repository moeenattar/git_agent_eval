"""Expose the existing classifier in the layout expected by ADK Web."""

from pathlib import Path

from dotenv import load_dotenv

from github_triage.agent import build_agent
from github_triage.config import AgentConfig
from github_triage.instrumentation import configure_phoenix_from_env

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# ADK Web may load the app from a directory other than the repository root.
load_dotenv(PROJECT_ROOT / ".env")

config = AgentConfig.from_env()
prompt_path = config.prompt_path
if not prompt_path.is_absolute():
    prompt_path = PROJECT_ROOT / prompt_path

configure_phoenix_from_env()
root_agent = build_agent(model=config.model, prompt_path=prompt_path)
