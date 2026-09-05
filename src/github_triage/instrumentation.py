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

    endpoint = os.getenv(
        "TRIAGE_PHOENIX_COLLECTOR_ENDPOINT",
        os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006/v1/traces"),
    )
    return register(
        endpoint=endpoint,
        project_name=os.getenv("PHOENIX_PROJECT_NAME", "github-triage"),
        protocol="http/protobuf",
        auto_instrument=True,
    )
