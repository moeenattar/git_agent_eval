"""Phoenix dataset and experiment integration for the frozen triage harness.

The Phoenix SDK is imported lazily so the core CLI and unit tests keep working
without the optional observability dependencies.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import time
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from github_triage.config import SUPPORTED_GROQ_MODELS, AgentConfig
from github_triage.evaluation.comparison import load_predictions
from github_triage.evaluation.dataset import load_dataset
from github_triage.evaluation.types import PredictionRecord
from github_triage.instrumentation import configure_phoenix_from_env
from github_triage.models import DatasetRecord, IssueInput, Priority, TriageDecision
from github_triage.service import TriageService

DEFAULT_PHOENIX_URL = "http://localhost:6006"
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def default_phoenix_dataset_name(records: Sequence[DatasetRecord], digest: str) -> str:
    versions = sorted({record.dataset_version for record in records})
    version = versions[0] if len(versions) == 1 else "mixed"
    return f"github-triage-golden-{version}-{digest[:12]}"


def _project_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def phoenix_prompt_name(prompt_path: Path, model: str, digest: str) -> str:
    model_slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", model).strip("-")
    return f"github-triage-{prompt_path.stem}-{model_slug}-{digest[:12]}"


def ensure_phoenix_prompt(
    client: Any,
    *,
    prompt_path: Path,
    model: str,
    prompt_sha256: str,
) -> tuple[Any, bool, str]:
    """Register a fingerprinted frozen prompt once and return its Phoenix version."""

    resolved_path = _project_path(prompt_path)
    if not resolved_path.exists():
        raise ValueError(f"prompt file does not exist: {resolved_path}")
    actual_digest = file_sha256(resolved_path)
    if prompt_sha256 != actual_digest:
        raise ValueError(
            f"prompt SHA-256 does not match {resolved_path}: "
            f"expected {prompt_sha256}, found {actual_digest}"
        )
    name = phoenix_prompt_name(prompt_path, model, prompt_sha256)
    try:
        return client.prompts.get(prompt_identifier=name), False, name
    except ValueError:
        pass

    try:
        from phoenix.client.types.prompts import PromptVersion
    except ImportError as exc:
        raise RuntimeError(
            "Phoenix prompts require: pip install -e '.[observability]'"
        ) from exc

    if model.startswith("groq/"):
        provider = "GROQ"
        model_name = model.removeprefix("groq/")
    elif model.startswith("gemini-"):
        provider = "GOOGLE"
        model_name = model
    else:
        raise ValueError(f"cannot map model to a Phoenix prompt provider: {model!r}")
    version = PromptVersion(
        [
            {"role": "system", "content": resolved_path.read_text(encoding="utf-8").strip()},
            {
                "role": "user",
                "content": '{"title":"{{title}}","body":"{{body}}"}',
            },
        ],
        model_name=model_name,
        model_provider=provider,
        template_format="MUSTACHE",
        description="Frozen GitHub issue triage instruction and title/body input template.",
    )
    created = client.prompts.create(
        name=name,
        version=version,
        prompt_description="Versioned prompt used by the GitHub triage evaluation harness.",
        prompt_metadata={
            "prompt_path": str(prompt_path),
            "prompt_sha256": prompt_sha256,
            "model": model,
        },
    )
    return created, True, name


def phoenix_examples(
    records: Sequence[DatasetRecord], dataset_sha256: str
) -> list[dict[str, Any]]:
    """Map frozen records to Phoenix without leaking annotation data into inputs."""

    return [
        {
            "id": record.id,
            "input": record.inference_input().model_dump(mode="json"),
            "output": record.gold.model_dump(mode="json"),
            "metadata": {
                "case_id": record.id,
                "source": record.source,
                "source_url": record.source_url,
                "slices": record.slices,
                "dataset_version": record.dataset_version,
                "dataset_sha256": dataset_sha256,
                "annotation_reason": record.annotation.reason,
                "review_status": record.annotation.review_status,
            },
        }
        for record in records
    ]


def validate_replay_predictions(
    records: Sequence[DatasetRecord], predictions: Sequence[PredictionRecord]
) -> dict[str, PredictionRecord]:
    records_by_id = {record.id: record for record in records}
    predictions_by_id = {prediction.id: prediction for prediction in predictions}
    if len(predictions_by_id) != len(predictions):
        raise ValueError("prediction artifact contains duplicate case IDs")
    if records_by_id.keys() != predictions_by_id.keys():
        missing = sorted(records_by_id.keys() - predictions_by_id.keys())
        extra = sorted(predictions_by_id.keys() - records_by_id.keys())
        raise ValueError(f"prediction IDs do not match dataset; missing={missing}, extra={extra}")
    for case_id, record in records_by_id.items():
        if predictions_by_id[case_id].gold != record.gold:
            raise ValueError(f"gold label differs in prediction artifact for {case_id!r}")
    return predictions_by_id


def replay_task(
    predictions_by_id: Mapping[str, PredictionRecord],
) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Build a Phoenix task that imports saved outputs without an LLM call."""

    def task(metadata: dict[str, Any]) -> dict[str, Any]:
        case_id = str(metadata["case_id"])
        record = predictions_by_id[case_id]
        if record.prediction is None:
            return {"error": record.error or "prediction missing"}
        return record.prediction.model_dump(mode="json")

    task.__name__ = "replay_saved_triage_prediction"
    return task


def _decision(value: Any) -> TriageDecision | None:
    try:
        return TriageDecision.model_validate(value)
    except ValueError:
        return None


def _correct_result(correct: bool, field: str) -> dict[str, Any]:
    return {
        "score": float(correct),
        "label": "correct" if correct else "incorrect",
        "explanation": f"Predicted {field} matches the frozen reference label."
        if correct
        else f"Predicted {field} does not match the frozen reference label.",
    }


def valid_output(output: Any) -> dict[str, Any]:
    valid = _decision(output) is not None
    return {
        "score": float(valid),
        "label": "valid" if valid else "invalid",
        "explanation": "Output satisfies the three-field triage schema."
        if valid
        else "Output is missing or does not satisfy the three-field triage schema.",
    }


def issue_type_correct(output: Any, expected: Any) -> dict[str, Any]:
    actual, reference = _decision(output), _decision(expected)
    return _correct_result(
        actual is not None and reference is not None and actual.issue_type == reference.issue_type,
        "issue type",
    )


def priority_correct(output: Any, expected: Any) -> dict[str, Any]:
    actual, reference = _decision(output), _decision(expected)
    return _correct_result(
        actual is not None and reference is not None and actual.priority == reference.priority,
        "priority",
    )


def human_review_correct(output: Any, expected: Any) -> dict[str, Any]:
    actual, reference = _decision(output), _decision(expected)
    return _correct_result(
        actual is not None
        and reference is not None
        and actual.needs_human_review == reference.needs_human_review,
        "human-review decision",
    )


def exact_match(output: Any, expected: Any) -> dict[str, Any]:
    actual, reference = _decision(output), _decision(expected)
    return _correct_result(actual is not None and actual == reference, "three-field output")


def _violation_result(violation: bool, explanation: str) -> dict[str, Any]:
    return {
        # Safety evaluators intentionally score 1 for a violation so the Phoenix
        # aggregate is the violation rate and can be compared with harness rates.
        "score": float(violation),
        "label": "violation" if violation else "clear",
        "explanation": explanation,
        "metadata": {"score_semantics": "1=violation, 0=clear"},
    }


def human_review_false_negative(output: Any, expected: Any) -> dict[str, Any]:
    actual, reference = _decision(output), _decision(expected)
    violation = bool(
        reference
        and reference.needs_human_review
        and (actual is None or not actual.needs_human_review)
    )
    return _violation_result(
        violation,
        "Human review was required but the prediction omitted it."
        if violation
        else "No human-review false negative.",
    )


def high_priority_downgrade(output: Any, expected: Any) -> dict[str, Any]:
    actual, reference = _decision(output), _decision(expected)
    violation = bool(
        reference
        and reference.priority is Priority.HIGH
        and (actual is None or actual.priority is not Priority.HIGH)
    )
    return _violation_result(
        violation,
        "A high-priority reference was downgraded or missing."
        if violation
        else "No high-priority downgrade.",
    )


def critical_under_triage(output: Any, expected: Any) -> dict[str, Any]:
    actual, reference = _decision(output), _decision(expected)
    violation = bool(
        reference
        and reference.priority is Priority.HIGH
        and actual is not None
        and actual.priority is Priority.LOW
    )
    return _violation_result(
        violation,
        "A high-priority reference was predicted as low priority."
        if violation
        else "No high-to-low critical under-triage.",
    )


def phoenix_evaluators() -> dict[str, Callable[..., dict[str, Any]]]:
    """Code evaluators whose definitions match the local harness metrics."""

    return {
        "valid_output": valid_output,
        "issue_type_correct": issue_type_correct,
        "priority_correct": priority_correct,
        "human_review_correct": human_review_correct,
        "exact_match": exact_match,
        "human_review_false_negative": human_review_false_negative,
        "high_priority_downgrade": high_priority_downgrade,
        "critical_under_triage": critical_under_triage,
    }


def _value(item: Any, key: str) -> Any:
    if isinstance(item, Mapping):
        return item.get(key)
    return getattr(item, key, None)


def _validate_remote_dataset(dataset: Any, expected_examples: Sequence[dict[str, Any]]) -> None:
    expected = {str(example["id"]): example for example in expected_examples}
    actual = {str(example["id"]): example for example in dataset.examples}
    if expected.keys() != actual.keys():
        raise RuntimeError("existing Phoenix dataset case IDs do not match the frozen dataset")
    for case_id, expected_example in expected.items():
        actual_example = actual[case_id]
        if actual_example["input"] != expected_example["input"]:
            raise RuntimeError(f"Phoenix dataset input differs for {case_id!r}")
        if actual_example["output"] != expected_example["output"]:
            raise RuntimeError(f"Phoenix dataset reference output differs for {case_id!r}")
        if actual_example["metadata"].get("dataset_sha256") != expected_example["metadata"].get(
            "dataset_sha256"
        ):
            raise RuntimeError(f"Phoenix dataset fingerprint differs for {case_id!r}")


def ensure_phoenix_dataset(
    client: Any,
    *,
    records: Sequence[DatasetRecord],
    dataset_sha256: str,
    dataset_name: str | None = None,
) -> tuple[Any, bool]:
    """Create the fingerprinted dataset once, then strictly verify and reuse it."""

    name = dataset_name or default_phoenix_dataset_name(records, dataset_sha256)
    examples = phoenix_examples(records, dataset_sha256)
    existing = next((item for item in client.datasets.list() if _value(item, "name") == name), None)
    if existing is not None:
        dataset = client.datasets.get_dataset(dataset=_value(existing, "id") or name)
        _validate_remote_dataset(dataset, examples)
        return dataset, False

    dataset = client.datasets.create_dataset(
        name=name,
        examples=examples,
        dataset_description=(
            "Frozen GitHub issue triage golden split. Inputs contain only title/body; "
            f"reference outputs contain the three approved labels. SHA-256: {dataset_sha256}"
        ),
        timeout=30,
    )
    _validate_remote_dataset(dataset, examples)
    return dataset, True


def _artifact_config(predictions_path: Path) -> dict[str, Any]:
    path = predictions_path.parent / "config.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _experiment_metadata(
    *,
    mode: str,
    dataset_path: Path,
    dataset_sha256: str,
    model: str,
    prompt_path: Path,
    prompt_sha256: str,
    predictions_path: Path | None = None,
    artifact_config: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "integration": "github-triage-eval",
        "mode": mode,
        "model": model,
        "prompt_path": str(prompt_path),
        "prompt_sha256": prompt_sha256,
        "dataset_path": str(dataset_path),
        "dataset_sha256": dataset_sha256,
        "evaluation_policy": "deterministic_code_evaluators",
    }
    if predictions_path is not None:
        metadata["predictions_path"] = str(predictions_path)
        metadata["predictions_sha256"] = file_sha256(predictions_path)
    if artifact_config:
        metadata["source_experiment"] = artifact_config.get("experiment")
        metadata["source_git_commit"] = artifact_config.get("git_commit")
    return metadata


def _write_summary(path: Path | None, summary: Mapping[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_replay_experiment(
    *,
    dataset_path: Path,
    predictions_path: Path,
    phoenix_url: str = DEFAULT_PHOENIX_URL,
    dataset_name: str | None = None,
    experiment_name: str | None = None,
    output_path: Path | None = None,
    timeout: int = 120,
) -> dict[str, Any]:
    """Publish saved predictions and deterministic scores without model calls."""

    try:
        from phoenix.client import Client
    except ImportError as exc:
        raise RuntimeError(
            "Phoenix experiments require: pip install -e '.[observability]'"
        ) from exc

    records = load_dataset(dataset_path)
    predictions = load_predictions(predictions_path)
    predictions_by_id = validate_replay_predictions(records, predictions)
    dataset_digest = file_sha256(dataset_path)
    artifact = _artifact_config(predictions_path)
    artifact_digest = artifact.get("dataset_sha256")
    if artifact_digest and artifact_digest != dataset_digest:
        raise ValueError("prediction artifact was produced from a different dataset SHA-256")

    client = Client(base_url=phoenix_url)
    dataset, created = ensure_phoenix_dataset(
        client,
        records=records,
        dataset_sha256=dataset_digest,
        dataset_name=dataset_name,
    )
    prompt_path = Path(artifact.get("prompt_path", "unknown"))
    prompt_digest = str(artifact.get("prompt_sha256", "unknown"))
    model = str(artifact.get("model", "unknown"))
    prompt_version, prompt_created, prompt_name = ensure_phoenix_prompt(
        client,
        prompt_path=prompt_path,
        model=model,
        prompt_sha256=prompt_digest,
    )
    name = experiment_name or f"{artifact.get('experiment', predictions_path.parent.name)}-phoenix"
    metadata = _experiment_metadata(
        mode="saved-prediction-replay",
        dataset_path=dataset_path,
        dataset_sha256=dataset_digest,
        model=model,
        prompt_path=prompt_path,
        prompt_sha256=prompt_digest,
        predictions_path=predictions_path,
        artifact_config=artifact,
    )
    metadata["phoenix_prompt_name"] = prompt_name
    metadata["phoenix_prompt_version_id"] = prompt_version.id
    result = client.experiments.run_experiment(
        dataset=dataset,
        task=replay_task(predictions_by_id),
        evaluators=phoenix_evaluators(),
        experiment_name=name,
        experiment_description=(
            "Imported saved triage predictions and scored them with the same deterministic "
            "correctness and safety rules as the local harness. No model calls were made."
        ),
        experiment_metadata=metadata,
        timeout=timeout,
        retries=1,
    )
    summary = {
        "dataset_created": created,
        "dataset_id": dataset.id,
        "dataset_name": dataset.name,
        "dataset_version_id": dataset.version_id,
        "experiment_id": result["experiment_id"],
        "experiment_name": name,
        "mode": metadata["mode"],
        "model": model,
        "prompt_created": prompt_created,
        "prompt_name": prompt_name,
        "prompt_version_id": prompt_version.id,
        "prompt_sha256": prompt_digest,
        "case_count": len(records),
        "evaluator_count": len(phoenix_evaluators()),
        "phoenix_url": phoenix_url,
    }
    _write_summary(output_path, summary)
    return summary


def live_model_provider(model: str) -> str:
    """Return the supported provider for a live Phoenix model ID."""

    if model in SUPPORTED_GROQ_MODELS:
        return "groq"
    if model.startswith("groq/"):
        supported = ", ".join(sorted(SUPPORTED_GROQ_MODELS))
        raise ValueError(
            f"unsupported Groq model for live Phoenix experiments: {model!r}; "
            f"use one of: {supported}"
        )
    if model.startswith("gemini-"):
        return "gemini"
    raise ValueError(
        "live Phoenix experiments support Gemini model IDs beginning with "
        f"'gemini-' and the verified Groq models; received {model!r}"
    )


def validate_live_credentials(provider: str) -> None:
    """Fail before Phoenix setup when the selected provider has no credential."""

    if provider == "gemini" and not (
        os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    ):
        raise ValueError(
            "live Gemini experiments require GOOGLE_API_KEY or GEMINI_API_KEY"
        )
    if provider == "groq" and not os.getenv("GROQ_API_KEY"):
        raise ValueError("live Groq experiments require GROQ_API_KEY")


async def run_live_experiment(
    *,
    dataset_path: Path,
    model: str,
    prompt_path: Path,
    phoenix_url: str = DEFAULT_PHOENIX_URL,
    dataset_name: str | None = None,
    experiment_name: str | None = None,
    output_path: Path | None = None,
    requests_per_minute: float = 6,
    timeout: int = 120,
) -> dict[str, Any]:
    """Run a traced Phoenix experiment through native Gemini or verified Groq."""

    provider = live_model_provider(model)
    validate_live_credentials(provider)
    if requests_per_minute <= 0:
        raise ValueError("requests_per_minute must be positive")
    try:
        from phoenix.client import AsyncClient, Client
        from phoenix.client.experiments import async_run_experiment
    except ImportError as exc:
        raise RuntimeError(
            "Phoenix experiments require: pip install -e '.[observability]'"
        ) from exc

    records = load_dataset(dataset_path)
    dataset_digest = file_sha256(dataset_path)
    client = Client(base_url=phoenix_url)
    dataset, created = ensure_phoenix_dataset(
        client,
        records=records,
        dataset_sha256=dataset_digest,
        dataset_name=dataset_name,
    )
    prompt_path = _project_path(prompt_path)
    prompt_digest = file_sha256(prompt_path)
    prompt_version, prompt_created, prompt_name = ensure_phoenix_prompt(
        client,
        prompt_path=prompt_path,
        model=model,
        prompt_sha256=prompt_digest,
    )
    metadata = _experiment_metadata(
        mode=f"live-{provider}",
        dataset_path=dataset_path,
        dataset_sha256=dataset_digest,
        model=model,
        prompt_path=prompt_path,
        prompt_sha256=prompt_digest,
    )
    metadata["phoenix_prompt_name"] = prompt_name
    metadata["phoenix_prompt_version_id"] = prompt_version.id

    # The experiment SDK creates the parent task span. ADK/OpenInference spans
    # inherit its context, which links the actual model call to the experiment row.
    configure_phoenix_from_env()
    service = TriageService(AgentConfig(model=model, prompt_path=prompt_path))
    lock = asyncio.Lock()
    last_started: float | None = None
    minimum_interval = 60 / requests_per_minute

    async def live_triage(input: dict[str, Any]) -> dict[str, Any]:
        nonlocal last_started
        async with lock:
            if last_started is not None:
                elapsed = time.monotonic() - last_started
                await asyncio.sleep(max(0, minimum_interval - elapsed))
            last_started = time.monotonic()
            response = await service.triage(IssueInput.model_validate(input))
            return response.decision.model_dump(mode="json")

    live_triage.__name__ = f"run_{provider}_triage_agent"
    async_client = AsyncClient(base_url=phoenix_url)
    model_slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", model).strip("-")
    name = experiment_name or f"github-triage-{model_slug}-live"
    result = await async_run_experiment(
        client=async_client,
        dataset=dataset,
        task=live_triage,
        evaluators=phoenix_evaluators(),
        experiment_name=name,
        experiment_description=(
            f"Live {provider.title()} triage run using the frozen prompt and deterministic "
            "correctness/safety evaluators. Model spans are correlated with Phoenix "
            "experiment rows."
        ),
        experiment_metadata=metadata,
        concurrency=1,
        timeout=timeout,
        retries=3,
    )
    summary = {
        "dataset_created": created,
        "dataset_id": dataset.id,
        "dataset_name": dataset.name,
        "dataset_version_id": dataset.version_id,
        "experiment_id": result["experiment_id"],
        "experiment_name": name,
        "mode": metadata["mode"],
        "provider": provider,
        "model": model,
        "prompt_created": prompt_created,
        "prompt_name": prompt_name,
        "prompt_version_id": prompt_version.id,
        "prompt_sha256": prompt_digest,
        "case_count": len(records),
        "evaluator_count": len(phoenix_evaluators()),
        "phoenix_url": phoenix_url,
    }
    _write_summary(output_path, summary)
    return summary
