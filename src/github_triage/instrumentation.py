"""Optional Phoenix setup kept outside the evaluation source of truth."""

import os
from typing import Any


def configure_phoenix_from_env() -> Any | None:
    if os.getenv("TRIAGE_ENABLE_PHOENIX", "false").lower() not in {"1", "true", "yes"}:
        return None

    try:
        from phoenix.otel import register
    except ImportError as exc:
        raise RuntimeError(
            "Phoenix tracing was enabled but optional dependencies are missing; "
            "install with: pip install -e '.[observability]'"
        ) from exc

    return register(
        project_name=os.getenv("PHOENIX_PROJECT_NAME", "github-triage"),
        auto_instrument=True,
    )
