# GitHub Issue Triage Evaluation Harness

An evaluation-first GitHub issue triage service built with Python and Google ADK. It can run with the native Gemini connector or with Groq through ADK's LiteLLM connector. It accepts only an issue `title` and `body`, then returns:

```json
{
  "issue_type": "bug",
  "priority": "high",
  "needs_human_review": true
}
```

The service is intentionally small. The main artifact is the harness that compares prompt/model configurations on a frozen golden dataset using deterministic quality, safety, latency, and normalized cost metrics.

## Implemented scope

- A single provider-portable Google ADK `LlmAgent` with a Pydantic output contract
- Native Gemini and optional Groq/LiteLLM model support
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

Normalized cost uses standard paid-tier list prices retrieved on 2026-09-05. Model and pricing sources are the official [Gemini model catalog](https://ai.google.dev/gemini-api/docs/models?hl=en), [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing), and [Groq model catalog](https://console.groq.com/docs/models). Free-tier billing does not change the normalized comparison.

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

### Milestone 4 status

Milestone 4 is complete. Holding `gemini-3.5-flash-lite` fixed, prompt v2 improved exact match from 48.6% to 54.3%, reduced human-review false negatives from 8 to 4, and reduced high-priority downgrades from 3 to 2. The +5.7 percentage-point exact-match delta was not statistically clear on 35 cases (paired bootstrap 95% CI: -11.4 to +20.0 points), so this is evidence of a safer prompt rather than a conclusive aggregate-quality win.

The locked model comparison held prompt v2 and all 35 golden cases fixed:

| Configuration | Exact match | Priority F1 | Human-review F1 | Human-review FN | High downgrades | Mean latency | Cost / 1K |
|---|---:|---:|---:|---:|---:|---:|---:|
| Gemini 3.5 Flash-Lite | 54.3% | 0.798 | 0.857 | 4 | 2 | 1.77 s | $0.3815 |
| Groq GPT-OSS 20B | 42.9% | 0.575 | 0.702 | 9 | 1 | 0.94 s | $0.1575 |
| Groq GPT-OSS 120B | 51.4% | 0.827 | 0.694 | 10 | 1 | 1.27 s | $0.3247 |

Neither Groq model is promoted. The 20B candidate was 58.7% cheaper and faster than Gemini, but exact match fell 11.4 points and human-review false negatives rose from 4 to 9. The 120B candidate was 14.9% cheaper with comparable exact match, but false negatives rose from 4 to 10. Both therefore failed the human-review safety gate.

The GPT-OSS 120B repeat produced the same 51.4% exact match and the same safety counts. Exact three-field agreement was 88.6%; issue-type and human-review agreement were 100%, while priority agreement was 88.6%. This is reasonably stable but does not reverse the safety rejection. The final configuration is prompt v2; Gemini 3.5 Flash-Lite with v2 remains the assisted baseline. See [docs/milestone4_results.md](docs/milestone4_results.md) for paired intervals, agreement, and the decision record.

### Prompt optimization follow-up

A calibration-only v3–v5 iteration advanced prompt v5 to one frozen golden run. Relative to v2, v5 increased exact match from 54.3% to 60.0% and reduced high-priority downgrades from two to one, while human-review false negatives remained at four and critical under-triage remained zero. The paired accuracy interval (-11.4 to +22.9 points) crossed zero, human-review macro-F1 fell from 0.857 to 0.771, and normalized cost increased 30.3%. A subsequent GPT-OSS 120B attempt with v5 also hit the provider rate limit; v5's larger input footprint adds pressure to the token-per-minute quota. V5 is rejected, and prompt v2 is the final prompt for all model comparisons. See [docs/prompt_optimization_results.md](docs/prompt_optimization_results.md) for the calibration protocol, full metrics, fingerprints, and final decision.

## Setup

Python 3.11–3.14 is supported.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

Install the optional Groq connector when needed:

```bash
python -m pip install -e '.[dev,groq]'
```

The Groq extra pins `litellm==1.99.0`. Do not downgrade to LiteLLM `1.82.7` or `1.82.8`; Google ADK reports those releases in its [LiteLLM security advisory](https://google.github.io/adk-docs/agents/models/litellm/#litellm-model-connector-for-adk-agents).

Configure one or both providers:

```bash
export GOOGLE_API_KEY='...'
export GROQ_API_KEY='...'
```

Alternatively, copy `.env.example` to `.env`. The CLI loads that file automatically, and Git ignores it. Never commit or paste API keys into documentation, commands, experiment artifacts, or issue data.

## Triage one issue

```bash
triage issue \
  --title 'Login returns HTTP 500 for every user' \
  --body 'Started after the latest deployment. No workaround is available.'
```

The default is Gemini Flash-Lite with prompt v2. Select either provider without changing application code:

```bash
# Google Gemini
triage issue --model gemini-3.5-flash-lite --prompt prompts/triage_v2.txt \
  --title 'Broken link in the contributor guide' \
  --body 'The setup link returns 404.'

# Groq GPT-OSS
triage issue --model groq/openai/gpt-oss-20b --prompt prompts/triage_v2.txt \
  --title 'Broken link in the contributor guide' \
  --body 'The setup link returns 404.'
```

The verified Groq allowlist is limited to `openai/gpt-oss-20b` and `openai/gpt-oss-120b` (written as `groq/openai/...` in this application's model setting). Other listed Groq chat, compound, prompt-guard, safeguard, and Qwen models are not accepted by this harness. The connector excludes GPT-OSS's separate reasoning field so the public service response remains exactly the three-field contract.

## Triage interactively with ADK Web

Start the local development UI from the repository root:

```bash
source .venv/bin/activate
adk web --host 127.0.0.1 --port 8000 adk_apps
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000), select `github_issue_triage`, and paste an issue as JSON into the message box:

```json
{
  "title": "Broken link in the contributor guide",
  "body": "The setup link returns 404."
}
```

The app uses `TRIAGE_MODEL` and `TRIAGE_PROMPT_PATH` from `.env`, so either Gemini or Groq works without code changes. Restart ADK Web after changing those settings. When Phoenix is enabled, Web requests are also exported to the `github-triage` Phoenix project.

ADK Web is an unauthenticated development tool. Keep it bound to `127.0.0.1`; do not expose it directly to a public or untrusted network. Use the CLI evaluation command—not ADK Web—for repeatable golden-dataset runs and promotion decisions.

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

Gemini example:

```bash
triage evaluate \
  --dataset datasets/golden_test.jsonl \
  --experiment eval-gemini-3-5-flash-lite-v2 \
  --model gemini-3.5-flash-lite \
  --prompt prompts/triage_v2.txt \
  --input-price-per-million 0.30 \
  --output-price-per-million 2.50 \
  --requests-per-minute 12
```

Groq cost-model example:

```bash
triage evaluate \
  --dataset datasets/golden_test.jsonl \
  --experiment eval-groq-gpt-oss-20b-v2 \
  --model groq/openai/gpt-oss-20b \
  --prompt prompts/triage_v2.txt \
  --input-price-per-million 0.075 \
  --output-price-per-million 0.30 \
  --requests-per-minute 6
```

For the quality arm, use `groq/openai/gpt-oss-120b` with $0.15 input and $0.60 output per million tokens. These Groq prices and free-tier limits were retrieved on 2026-09-05 from the official [model catalog](https://console.groq.com/docs/models) and [rate-limit table](https://console.groq.com/docs/rate-limits). Although the free tier permits 30 requests per minute and 1,000 requests per day for each candidate, its 8,000-token-per-minute limit is the practical bottleneck. Six requests per minute worked for the recorded prompt-v2 runs, but rolling usage and account limits can vary; reduce the value to four after an HTTP 429 response.

Use the current provider list prices rather than `0` for a meaningful normalized production-cost comparison. Pricing is supplied at run time so historical experiments remain reproducible when vendor prices change.

`--requests-per-minute` is optional. Set it below the provider quota for sequential, reproducible free-tier runs. Quota failures are retried up to three times by default; these controls can be changed with `--max-attempts` and `--retry-delay-seconds`.

Artifacts are written to `artifacts/<experiment>/`:

- `predictions.jsonl` — per-case output, latency, usage, and error
- `metrics.json` — aggregate quality, safety, latency, and cost metrics
- `report.md` — concise human-readable summary
- `config.json` — frozen experiment configuration

An experiment is not a promotion candidate if model errors, any high-priority downgrade, critical `high -> low` under-triage, or human-review false negatives increase, even when aggregate accuracy improves.

Compare two runs evaluated on the identical case IDs:

```bash
triage compare \
  --baseline artifacts/golden-flash-lite-v1 \
  --candidate artifacts/golden-flash-lite-v2 \
  --output artifacts/comparisons/golden-prompt-v1-v2.json
```

The comparison uses paired bootstrap resampling, reports the confidence interval for the exact-match delta, cost multiplier, exact prediction agreement, and per-field agreement. A promotion is recommended only for a statistically clear improvement with no safety or reliability regression; a human should still make the final cost/latency trade-off.

## Provider and data-safety notes

- `--model` determines which provider receives the issue title and body. Gemini model IDs use Google's native connector; `groq/...` IDs use Groq through LiteLLM.
- Both providers may be configured simultaneously, but each evaluation uses exactly one model and records that model ID in `config.json`.
- The checked-in real cases are sourced from public GitHub issues, while synthetic cases may still describe security, credentials, availability, or customer-data scenarios. Obtain approval for the intended external provider before transmitting a frozen dataset.
- Free-tier billing does not imply zero production cost. Reports use normalized list prices so configurations remain economically comparable.

## Local Phoenix tracing

Install the optional integration and start Phoenix:

```bash
python -m pip install -e '.[observability]'
docker compose up phoenix
export TRIAGE_ENABLE_PHOENIX=true
export PHOENIX_BASE_URL=http://localhost:6006
export TRIAGE_PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006/v1/traces
triage issue --title '...' --body '...'
```

Publish a saved golden run as a Phoenix dataset and fully scored experiment without making new model calls:

```bash
triage phoenix \
  --dataset datasets/golden_test.jsonl \
  --predictions artifacts/golden-groq-gpt-oss-20b-v2/predictions.jsonl \
  --experiment-name golden-groq-20b-v2-phoenix-replay
```

This registers the frozen prompt, creates or reuses the fingerprinted dataset, traces every replayed task row, and attaches eight deterministic correctness/safety annotations per row. A separate `--live` mode runs fresh, fully traced Gemini or verified Groq calls. The selected provider must have its API key in the environment.

Run Gemini live in Phoenix:

```bash
triage phoenix \
  --live \
  --dataset datasets/golden_test.jsonl \
  --model gemini-3.5-flash-lite \
  --prompt prompts/triage_v2.txt \
  --requests-per-minute 6 \
  --experiment-name golden-gemini-flash-lite-v2-live
```

Live mode sends every dataset input to the selected external provider. Use it only after approving that provider and dataset combination. Gemini IDs must begin with `gemini-`; Groq remains restricted to the two verified GPT-OSS models.

Browse Phoenix at [http://localhost:6006](http://localhost:6006). See [docs/phoenix_experiments.md](docs/phoenix_experiments.md) for exact setup, evaluator semantics, and the verified local parity result. The [model comparison runbook](docs/model_comparison_runbook.md) contains copy-paste evaluation, paired comparison, Phoenix replay, and live-run commands for all selected Gemini and Groq models. Files produced by the harness remain the source of truth for pass/fail decisions.

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
- Human-review false negatives, any high-priority downgrade, and `high -> low` under-triage are explicit safety gates.
- Free-tier billing does not make inference economically free; experiments report normalized list-price cost.
- A small dataset yields wide uncertainty, so the report includes a bootstrap confidence interval and avoids overstating small improvements.

The working plan and deliberately deferred scope are recorded in [docs/implementation_plan.md](docs/implementation_plan.md) and [docs/assumptions.md](docs/assumptions.md).
