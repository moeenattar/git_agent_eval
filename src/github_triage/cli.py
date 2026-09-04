"""Command-line interface for inference and evaluation."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

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
    results = await evaluate_records(records, service.triage, pricing)
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
        "git_commit": _git_commit(),
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
    evaluate.add_argument("--output-root", type=Path, default=Path("artifacts"))
    evaluate.set_defaults(handler=_evaluate)

    compare = subparsers.add_parser("compare", help="compare two paired experiment artifacts")
    compare.add_argument("--baseline", type=Path, required=True)
    compare.add_argument("--candidate", type=Path, required=True)
    compare.add_argument("--output", type=Path, required=True)
    compare.set_defaults(handler=_compare)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return asyncio.run(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
