"""Reproducible experiment artifact writer."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from github_triage.evaluation.types import PredictionRecord


def write_experiment(
    directory: Path,
    *,
    config: Mapping[str, Any],
    results: Sequence[PredictionRecord],
    metrics: Mapping[str, Any],
) -> None:
    directory.mkdir(parents=True, exist_ok=False)
    _write_json(directory / "config.json", config)
    _write_json(directory / "metrics.json", metrics)
    with (directory / "predictions.jsonl").open("w", encoding="utf-8") as handle:
        for result in results:
            handle.write(result.model_dump_json() + "\n")
    (directory / "report.md").write_text(render_markdown(config, metrics), encoding="utf-8")


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def render_markdown(config: Mapping[str, Any], metrics: Mapping[str, Any]) -> str:
    low, high = metrics["exact_match_bootstrap_95_ci"]
    cost = metrics["estimated_cost_usd"]
    latency = metrics["latency_ms"]
    return f"""# Experiment {config["experiment"]}

Model: `{config["model"]}`  
Prompt: `{config["prompt_path"]}`  
Dataset: `{config["dataset_path"]}`

## Results

| Metric | Value |
|---|---:|
| Cases | {metrics["case_count"]} |
| Successful predictions | {metrics["successful_predictions"]} |
| Exact match | {metrics["exact_match_accuracy"]:.1%} |
| Exact match 95% bootstrap CI | {low:.1%}–{high:.1%} |
| Type macro-F1 | {metrics["type_macro_f1"]:.3f} |
| Priority macro-F1 | {metrics["priority_macro_f1"]:.3f} |
| Human-review macro-F1 | {metrics["human_review_macro_f1"]:.3f} |
| Human-review false negatives | {metrics["human_review_false_negatives"]} |
| Critical high-to-low under-triage | {metrics["critical_under_triage_count"]} |
| Any high-priority downgrade | {metrics["high_priority_downgrades_count"]} |
| Mean latency | {latency["mean"]:.1f} ms |
| p95 latency | {latency["p95"]:.1f} ms |
| Normalized cost per 1,000 issues | ${cost["per_1000_issues"]:.4f} |

## Interpretation

This report is descriptive for one configuration. Promotion decisions require a paired comparison
on the same frozen test cases. A candidate must not increase model errors, high-priority
downgrades, critical under-triage, or human-review false negatives.
"""
