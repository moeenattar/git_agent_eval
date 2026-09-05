"""Command-line interface for inference and evaluation."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from github_triage.config import AgentConfig, ModelPricing
from github_triage.evaluation.comparison import compare_experiments, load_predictions
from github_triage.evaluation.dataset import load_dataset
from github_triage.evaluation.metrics import compute_metrics
from github_triage.evaluation.report import write_experiment
from github_triage.evaluation.runner import evaluate_records
from github_triage.instrumentation import configure_phoenix_from_env
from github_triage.models import IssueInput
from github_triage.service import TriageService


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_commit() -> str | None:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip() if completed.returncode == 0 else None


def _git_worktree_dirty() -> bool | None:
    completed = subprocess.run(
        ["git", "status", "--porcelain"],
        check=False,
        capture_output=True,
        text=True,
    )
    return bool(completed.stdout) if completed.returncode == 0 else None


def _base_config(args: argparse.Namespace) -> AgentConfig:
    defaults = AgentConfig.from_env()
    return AgentConfig(
        model=args.model or defaults.model,
        prompt_path=args.prompt or defaults.prompt_path,
    )


async def _issue(args: argparse.Namespace) -> int:
    configure_phoenix_from_env()
    service = TriageService(_base_config(args))
    result = await service.triage(IssueInput(title=args.title, body=args.body))
    output = {
        **result.decision.model_dump(mode="json"),
        "metadata": {
            "latency_ms": round(result.latency_ms, 2),
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
        },
    }
    print(json.dumps(output, indent=2))
    return 0


async def _evaluate(args: argparse.Namespace) -> int:
    configure_phoenix_from_env()
    agent_config = _base_config(args)
    records = load_dataset(args.dataset)
    service = TriageService(agent_config)
    pricing = ModelPricing(
        input_per_million=args.input_price_per_million,
        output_per_million=args.output_price_per_million,
    )
    results = await evaluate_records(
        records,
        service.triage,
        pricing,
        requests_per_minute=args.requests_per_minute,
        max_attempts=args.max_attempts,
        retry_delay_seconds=args.retry_delay_seconds,
    )
    metrics = compute_metrics(results)
    run_config: dict[str, Any] = {
        "experiment": args.experiment,
        "model": agent_config.model,
        "prompt_path": str(agent_config.prompt_path),
        "prompt_sha256": _sha256(agent_config.prompt_path),
        "dataset_path": str(args.dataset),
        "dataset_sha256": _sha256(args.dataset),
        "dataset_versions": sorted({record.dataset_version for record in records}),
        "input_price_per_million_usd": pricing.input_per_million,
        "output_price_per_million_usd": pricing.output_per_million,
        "requests_per_minute": args.requests_per_minute,
        "max_attempts": args.max_attempts,
        "retry_delay_seconds": args.retry_delay_seconds,
        "git_commit": _git_commit(),
        "git_worktree_dirty": _git_worktree_dirty(),
    }
    output = args.output_root / args.experiment
    write_experiment(output, config=run_config, results=results, metrics=metrics)
    print(json.dumps(metrics, indent=2))
    print(f"\nArtifacts: {output}")
    return 0 if metrics["errors"] == 0 else 1


async def _compare(args: argparse.Namespace) -> int:
    baseline = load_predictions(args.baseline / "predictions.jsonl")
    candidate = load_predictions(args.candidate / "predictions.jsonl")
    comparison = compare_experiments(baseline, candidate)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(comparison, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(comparison, indent=2))
    print(f"\nComparison: {args.output}")
    return 0


async def _phoenix(args: argparse.Namespace) -> int:
    from github_triage.phoenix_integration import (
        run_live_experiment,
        run_replay_experiment,
    )

    if args.live:
        defaults = AgentConfig.from_env()
        model = args.model or defaults.model
        prompt = args.prompt or defaults.prompt_path
        summary = await run_live_experiment(
            dataset_path=args.dataset,
            model=model,
            prompt_path=prompt,
            phoenix_url=args.phoenix_url,
            dataset_name=args.dataset_name,
            experiment_name=args.experiment_name,
            output_path=args.output,
            requests_per_minute=args.requests_per_minute,
            timeout=args.timeout,
        )
    else:
        summary = run_replay_experiment(
            dataset_path=args.dataset,
            predictions_path=args.predictions,
            phoenix_url=args.phoenix_url,
            dataset_name=args.dataset_name,
            experiment_name=args.experiment_name,
            output_path=args.output,
            timeout=args.timeout,
        )
    print(json.dumps(summary, indent=2))
    print(
        f"\nPhoenix experiment: {args.phoenix_url}/datasets/"
        f"{summary['dataset_id']}/compare?experimentId={summary['experiment_id']}"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="triage")
    subparsers = parser.add_subparsers(dest="command", required=True)

    issue = subparsers.add_parser("issue", help="triage one issue")
    issue.add_argument("--title", required=True)
    issue.add_argument("--body", default="")
    issue.add_argument("--model")
    issue.add_argument("--prompt", type=Path)
    issue.set_defaults(handler=_issue)

    evaluate = subparsers.add_parser("evaluate", help="evaluate a frozen JSONL dataset")
    evaluate.add_argument("--dataset", type=Path, required=True)
    evaluate.add_argument("--experiment", required=True)
    evaluate.add_argument("--model")
    evaluate.add_argument("--prompt", type=Path)
    evaluate.add_argument("--input-price-per-million", type=float, required=True)
    evaluate.add_argument("--output-price-per-million", type=float, required=True)
    evaluate.add_argument(
        "--requests-per-minute",
        type=float,
        help="pace calls to fit a provider quota (for example, 12 for a 15 RPM tier)",
    )
    evaluate.add_argument("--max-attempts", type=int, default=3)
    evaluate.add_argument("--retry-delay-seconds", type=float, default=30)
    evaluate.add_argument("--output-root", type=Path, default=Path("artifacts"))
    evaluate.set_defaults(handler=_evaluate)

    compare = subparsers.add_parser("compare", help="compare two paired experiment artifacts")
    compare.add_argument("--baseline", type=Path, required=True)
    compare.add_argument("--candidate", type=Path, required=True)
    compare.add_argument("--output", type=Path, required=True)
    compare.set_defaults(handler=_compare)

    phoenix = subparsers.add_parser(
        "phoenix", help="publish a frozen evaluation as a Phoenix dataset and experiment"
    )
    phoenix.add_argument("--dataset", type=Path, default=Path("datasets/golden_test.jsonl"))
    mode = phoenix.add_mutually_exclusive_group(required=True)
    mode.add_argument("--predictions", type=Path, help="replay a saved predictions.jsonl")
    mode.add_argument(
        "--live", action="store_true", help="run fresh Gemini or verified Groq calls"
    )
    phoenix.add_argument("--model", help="live Gemini or Groq model; defaults to TRIAGE_MODEL")
    phoenix.add_argument("--prompt", type=Path, help="live prompt; defaults to TRIAGE_PROMPT_PATH")
    phoenix.add_argument(
        "--phoenix-url",
        default=os.getenv("PHOENIX_BASE_URL", "http://localhost:6006").rstrip("/"),
    )
    phoenix.add_argument("--dataset-name")
    phoenix.add_argument("--experiment-name")
    phoenix.add_argument("--requests-per-minute", type=float, default=6)
    phoenix.add_argument("--timeout", type=int, default=120)
    phoenix.add_argument("--output", type=Path)
    phoenix.set_defaults(handler=_phoenix)
    return parser


def main() -> int:
    load_dotenv()
    args = build_parser().parse_args()
    return asyncio.run(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
