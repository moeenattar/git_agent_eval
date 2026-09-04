# GitHub Issue Triage Evaluation Harness

An evaluation-first GitHub issue triage service built with Python and Google ADK. It accepts only an issue `title` and `body`, then returns:

```json
{
  "issue_type": "bug",
  "priority": "high",
  "needs_human_review": true
}
```

The service is intentionally small. The main artifact is the harness that compares prompt/model configurations on a frozen golden dataset using deterministic quality, safety, latency, and normalized cost metrics.

## Current milestone

- A single Google ADK `LlmAgent` with a Pydantic output contract
- A written triage and annotation policy
- GitHub issue collection and dataset validation tools
- Deterministic exact-match, macro-F1, escalation, and under-triage metrics
- Bootstrap confidence intervals for exact-match accuracy
- Token-based normalized cost calculation
- JSON/Markdown experiment artifacts
- Optional local Arize Phoenix tracing
- Unit tests that require neither credentials nor model calls

The checked-in 50-case dataset is a review draft containing 40 real `python/pythondotorg` issues and 10 synthetic challenge cases. Its labels are proposed annotations, not claimed model results or frozen ground truth. Review [docs/annotation_review.md](docs/annotation_review.md) before changing `draft-v0` to `v1`.

## Setup

Python 3.11–3.14 is supported.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

For Gemini Developer API access:

```bash
export GOOGLE_API_KEY='...'
```

Copy `.env.example` to `.env` if you prefer a local environment file. Do not commit secrets.

## Triage one issue

```bash
triage issue \
  --title 'Login returns HTTP 500 for every user' \
  --body 'Started after the latest deployment. No workaround is available.'
```

The default model and prompt can be changed without modifying source:

```bash
triage issue --model gemini-2.5-flash --prompt prompts/triage_v1.txt \
  --title 'Broken link in the contributor guide' \
  --body 'The setup link returns 404.'
```

## Build and validate the dataset

Fetch public issues (the GitHub token is optional, but raises the API rate limit):

```bash
export GITHUB_TOKEN='...'
python scripts/fetch_github_issues.py \
  --repo python/pythondotorg \
  --state all \
  --limit 100 \
  --output datasets/raw/issues.jsonl
```

The fetcher retains labels for sampling and audit, filters pull requests, and never feeds those labels to the agent. After manual annotation, validate both structure and split leakage:

```bash
python scripts/validate_dataset.py datasets/calibration.jsonl datasets/golden_test.jsonl
```

See [docs/triage_policy.md](docs/triage_policy.md) before annotating and [docs/dataset.md](docs/dataset.md) for the record format and freezing procedure.

## Run an evaluation

```bash
triage evaluate \
  --dataset datasets/golden_test.jsonl \
  --experiment flash-v1 \
  --model gemini-2.5-flash \
  --prompt prompts/triage_v1.txt \
  --input-price-per-million 0 \
  --output-price-per-million 0
```

Use the current provider list prices rather than `0` for a meaningful normalized production-cost comparison. Pricing is supplied at run time so historical experiments remain reproducible when vendor prices change.

Artifacts are written to `artifacts/<experiment>/`:

- `predictions.jsonl` — per-case output, latency, usage, and error
- `metrics.json` — aggregate quality, safety, latency, and cost metrics
- `report.md` — concise human-readable summary
- `config.json` — frozen experiment configuration

An experiment is not a promotion candidate if critical under-triage or human-review false negatives increase, even when aggregate accuracy improves.

Compare two runs evaluated on the identical case IDs:

```bash
triage compare \
  --baseline artifacts/flash-v1 \
  --candidate artifacts/flash-v2 \
  --output artifacts/flash-v1-vs-v2.json
```

The comparison uses paired bootstrap resampling, reports the confidence interval for the exact-match delta and the cost multiplier, and applies the two safety gates. A promotion is recommended only for a statistically clear improvement with no safety regression; a human should still make the final cost/latency trade-off.

## Local Phoenix tracing

Install the optional integration and start Phoenix:

```bash
python -m pip install -e '.[observability]'
docker compose up phoenix
export TRIAGE_ENABLE_PHOENIX=true
export PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006/v1/traces
triage issue --title '...' --body '...'
```

Phoenix is the trace and experiment-debugging UI; files produced by the harness remain the source of truth for pass/fail decisions.

## Test

```bash
pytest
ruff check .
```

## Key decisions and assumptions

- Priorities are `high`, `medium`, and `low`, because source repositories do not share one incident-priority convention.
- GitHub is a dataset source, not an inference-time dependency.
- The model sees title and body only.
- Existing repository labels are weak sampling evidence, not gold truth.
- Exact match across all three output fields is the primary metric.
- Human-review false negatives and `high -> low` under-triage are explicit safety gates.
- Free-tier billing does not make inference economically free; experiments report normalized list-price cost.
- A small dataset yields wide uncertainty, so the report includes a bootstrap confidence interval and avoids overstating small improvements.

The working plan and deliberately deferred scope are recorded in [docs/implementation_plan.md](docs/implementation_plan.md) and [docs/assumptions.md](docs/assumptions.md).
