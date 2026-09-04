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

## Implemented scope

- A single Google ADK `LlmAgent` with a Pydantic output contract
- A written triage and annotation policy
- GitHub issue collection and dataset validation tools
- Deterministic exact-match, macro-F1, escalation, and under-triage metrics
- Bootstrap confidence intervals for exact-match accuracy
- Token-based normalized cost calculation
- JSON/Markdown experiment artifacts
- Optional local Arize Phoenix tracing
- Unit tests that require neither credentials nor model calls

The checked-in 50-case dataset contains 40 real `python/pythondotorg` issues and 10 synthetic challenge cases. The project owner independently approved all 12 high-priority cases, covering 24% of the dataset and every security case, before the dataset was frozen as `v1`. The review evidence and labels are documented in [docs/annotation_review.md](docs/annotation_review.md).

## Experiment results

All results below use `gemini-3.5-flash-lite`. Normalized cost uses the standard paid-tier list prices retrieved on 2026-09-05: $0.30 per million input tokens and $2.50 per million output tokens. The model ID and prices come from the official [Gemini model catalog](https://ai.google.dev/gemini-api/docs/models?hl=en) and [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing).

### Calibration prompt comparison

| Metric | Prompt v1 | Prompt v2 |
|---|---:|---:|
| Cases completed | 15/15 | 15/15 |
| Exact match | 53.3% | 80.0% |
| Exact-match 95% bootstrap CI | 26.7%–80.0% | 60.0%–100.0% |
| Human-review false negatives | 4 | 0 |
| Critical high-to-low errors | 1 | 0 |
| Normalized cost / 1,000 issues | $0.3025 | $0.3882 |

The paired exact-match improvement was +26.7 percentage points with a 95% bootstrap interval of +6.7 to +53.3 points. Prompt v2 passed both safety gates at 1.28× the normalized cost, so it was selected before opening the golden split. See [the paired comparison](artifacts/calibration-v1-v2.json).

### Frozen golden test

Prompt v2 was then run once on all 35 held-out cases. It completed 35/35 calls with no model errors and achieved 54.3% exact match (95% bootstrap CI 37.1%–71.4%), type macro-F1 0.742, priority macro-F1 0.798, and human-review macro-F1 0.857. Normalized cost was $0.3815 per 1,000 issues; mean latency was 1.77 seconds and p95 was 2.18 seconds.

The test had no `high -> low` errors, but it did have two `high -> medium` security downgrades and four human-review false negatives. This means the candidate is useful as an assisted triage baseline, not ready for unsupervised routing. The held-out failures are documented without post-test tuning in [docs/golden_failure_analysis.md](docs/golden_failure_analysis.md); the complete run is in [artifacts/golden-flash-lite-v2](artifacts/golden-flash-lite-v2).

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
triage issue --model gemini-3.5-flash-lite --prompt prompts/triage_v2.txt \
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
  --experiment golden-flash-lite-v2 \
  --model gemini-3.5-flash-lite \
  --prompt prompts/triage_v2.txt \
  --input-price-per-million 0.30 \
  --output-price-per-million 2.50 \
  --requests-per-minute 12
```

Use the current provider list prices rather than `0` for a meaningful normalized production-cost comparison. Pricing is supplied at run time so historical experiments remain reproducible when vendor prices change.

`--requests-per-minute` is optional. Set it below the provider quota for sequential, reproducible free-tier runs. Quota failures are retried up to three times by default; these controls can be changed with `--max-attempts` and `--retry-delay-seconds`.

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
