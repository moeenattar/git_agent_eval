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

All five prompt versions were calibrated with `gemini-3.5-flash-lite` on the same 15 cases.

| Metric | Prompt v1 | Prompt v2 | Prompt v3 | Prompt v4 | Prompt v5 |
|---|---:|---:|---:|---:|---:|
| Cases completed | 15/15 | 15/15 | 15/15 | 15/15 | 15/15 |
| Exact match | 53.3% | 80.0% | 86.7% | 86.7% | 86.7% |
| Exact-match 95% bootstrap CI | 26.7%–80.0% | 60.0%–100.0% | 66.7%–100.0% | 66.7%–100.0% | 66.7%–100.0% |
| Type macro-F1 | 0.703 | 0.651 | 0.800 | 0.731 | 0.800 |
| Priority macro-F1 | 0.687 | 0.937 | 0.930 | 0.930 | 0.878 |
| Human-review macro-F1 | 0.700 | 1.000 | 0.932 | 1.000 | 1.000 |
| Human-review false negatives | 4 | 0 | 1 | 0 | 0 |
| Critical high-to-low errors | 1 | 0 | 0 | 0 | 0 |
| Normalized cost / 1,000 issues | $0.3025 | $0.3882 | $0.4482 | $0.4738 | $0.4982 |

Prompt v2 passed both safety gates and was selected before the golden split was opened. V3–v5 were later calibration-only refinements; their held-out results did not justify replacing v2. See [the v1–v2 paired comparison](artifacts/calibration-v1-v2.json) and [the prompt optimization record](docs/prompt_optimization_results.md) for the selection details.

### Evaluation Dataset Results

The table below consolidates every complete saved run on the frozen 35-case golden split. Each run completed 35/35 predictions with no provider errors; repeated configurations are shown separately because their outputs can vary between calls.

| Run | Model + prompt | Exact match | Type F1 | Priority F1 | Human F1 | Human FN | High downgrades | Mean / p95 latency | Cost / 1K |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| [Initial prompt comparison](artifacts/golden-flash-lite-v1) | Gemini 3.5 Flash-Lite + v1 | 48.6% | 0.748 | 0.791 | 0.735 | 8 | 3 | 1.43 / 1.79 s | $0.3013 |
| [Selected baseline](artifacts/golden-flash-lite-v2) | Gemini 3.5 Flash-Lite + v2 | 54.3% | 0.742 | 0.798 | 0.857 | 4 | 2 | 1.77 / 2.18 s | $0.3815 |
| [Model comparison](artifacts/golden-groq-gpt-oss-20b-v2) | Groq GPT-OSS 20B + v2 | 42.9% | 0.666 | 0.575 | 0.702 | 9 | 1 | 0.94 / 1.33 s | $0.1575 |
| [Model comparison, run 2](artifacts/golden-groq-gpt-oss-20b-v2-2) | Groq GPT-OSS 20B + v2 | 42.9% | 0.666 | 0.575 | 0.735 | 8 | 1 | 1.00 / 1.35 s | $0.1547 |
| [Model comparison](artifacts/golden-groq-gpt-oss-120b-v2) | Groq GPT-OSS 120B + v2 | 51.4% | 0.761 | 0.827 | 0.694 | 10 | 1 | 1.27 / 1.99 s | $0.3247 |
| [Stability repeat](artifacts/golden-groq-gpt-oss-120b-v2-repeat) | Groq GPT-OSS 120B + v2 | 51.4% | 0.761 | 0.769 | 0.694 | 10 | 1 | 1.32 / 2.10 s | $0.3322 |
| [Prompt candidate](artifacts/golden-flash-lite-v5) | Gemini 3.5 Flash-Lite + v5 | 60.0% | 0.863 | 0.822 | 0.771 | 4 | 1 | 1.40 / 1.66 s | $0.4969 |
| [Owner verification](artifacts/eval-gemini-3-5-flash-lite-v2) | Gemini 3.5 Flash-Lite + v2 | 54.3% | 0.742 | 0.824 | 0.827 | 5 | 2 | 1.37 / 1.63 s | $0.3815 |
| [Owner verification](artifacts/eval-gemini-3-5-flash-lite-v5) | Gemini 3.5 Flash-Lite + v5 | 57.1% | 0.832 | 0.827 | 0.770 | 3 | 1 | 1.35 / 1.69 s | $0.4976 |
| [Owner verification](artifacts/eval-gemini-3-8-flash-v2) | Gemini 3.8 Flash + v2 | 54.3% | 0.935 | 0.750 | 0.770 | 3 | 0 | 5.66 / 10.36 s | $0.8777 |
| [Owner verification](artifacts/eval-gemini-3-8-flash-v5) | Gemini 3.8 Flash + v5 | 54.3% | 0.950 | 0.775 | 0.735 | 2 | 0 | 5.46 / 11.29 s | $1.1726 |

Prompt v2 improved the initial Flash-Lite run's safety profile, but its +5.7-point exact-match gain was not statistically clear (paired 95% bootstrap CI: -11.4 to +20.0 points). Prompt v5 likewise produced no statistically clear held-out gain, lowered human-review macro-F1, and cost about 30% more than v2. The Groq candidates missed substantially more required human reviews, while Gemini 3.8 did not improve exact match and cost more.

Prompt v2 with Gemini 3.5 Flash-Lite therefore remains the cost-oriented assisted-triage baseline. No configuration is approved for unsupervised routing. See [the complete evaluation analysis](docs/milestone4_results.md) and [held-out failure analysis](docs/golden_failure_analysis.md) for paired intervals, stability measurements, and the decision record.

## Quick start

### Prerequisites

- Git and Python 3.11–3.14
- A Gemini Developer API key, or a Groq API key for the optional Groq connector
- Docker with Compose only if you want local Phoenix tracing

Run the remaining commands from the repository root so the default prompt and dataset paths resolve correctly.

### 1. Clone and install

```bash
git clone https://github.com/moeenattar/git_agent_eval.git
cd git_agent_eval
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

On Windows PowerShell, activate the environment with `.venv\Scripts\Activate.ps1`. Activate the environment again whenever you open a new shell in the project.

### 2. Configure Gemini

Copy the checked-in template, then edit `.env` and add your key:

```bash
cp .env.example .env
```

```dotenv
GOOGLE_API_KEY=your-gemini-api-key
TRIAGE_MODEL=gemini-3.5-flash-lite
TRIAGE_PROMPT_PATH=prompts/triage_v2.txt
```

`GEMINI_API_KEY` is also accepted by the Gemini SDK. The CLI loads `.env` automatically, and Git ignores it. Never commit or paste real keys into commands, documentation, artifacts, or issue data.

Sign up on Google Ai Studio to generate an API Key - https://aistudio.google.com/api-keys

### 3. Triage your first issue

```bash
triage issue \
  --title 'Login returns HTTP 500 for every user' \
  --body 'Started after the latest deployment. No workaround is available.'
```

The command prints a JSON triage decision plus latency and token-usage metadata.

### Use Groq instead

Install the optional connector and set the Groq model in `.env`:

```bash
python -m pip install -e '.[dev,groq]'
```

```dotenv
GROQ_API_KEY=your-groq-api-key
TRIAGE_MODEL=groq/openai/gpt-oss-20b
TRIAGE_PROMPT_PATH=prompts/triage_v2.txt
```

The verified Groq models are `groq/openai/gpt-oss-20b` and `groq/openai/gpt-oss-120b`. You can also override `.env` for one call with `--model` and `--prompt`. The Groq extra pins `litellm==1.99.0`; do not downgrade to versions `1.82.7` or `1.82.8` listed in Google ADK's [LiteLLM security advisory](https://google.github.io/adk-docs/agents/models/litellm/#litellm-model-connector-for-adk-agents).

## Run local checks

These commands do not call a model or require an API key:

```bash
python scripts/validate_dataset.py datasets/calibration.jsonl datasets/golden_test.jsonl
pytest
ruff check .
```

## Run the evaluation harness

An evaluation sends every selected dataset row to the configured external provider. Confirm that the provider and dataset are approved before running it. This Gemini example creates a new `artifacts/local-gemini-v2/` directory:

```bash
triage evaluate \
  --dataset datasets/golden_test.jsonl \
  --experiment local-gemini-v2 \
  --model gemini-3.5-flash-lite \
  --prompt prompts/triage_v2.txt \
  --input-price-per-million 0.30 \
  --output-price-per-million 2.50 \
  --requests-per-minute 12
```

For Groq GPT-OSS 20B, install the `groq` extra first and use:

```bash
triage evaluate \
  --dataset datasets/golden_test.jsonl \
  --experiment local-groq-20b-v2 \
  --model groq/openai/gpt-oss-20b \
  --prompt prompts/triage_v2.txt \
  --input-price-per-million 0.075 \
  --output-price-per-million 0.30 \
  --requests-per-minute 6
```

The example prices are the historical list prices used by this repository on 2026-09-05. Check the current [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing) or [Groq model catalog](https://console.groq.com/docs/models) before recording a new comparison. Use list prices rather than zero even when a call is covered by a free tier. Lower `--requests-per-minute` if your account returns HTTP 429; retries default to three attempts with a 30-second delay.

Experiment names must be unique because the harness will not overwrite an existing artifact directory. Every successful run writes:

- `predictions.jsonl` with per-case outputs, usage, latency, and errors
- `metrics.json` with aggregate quality, safety, latency, and normalized cost
- `report.md` with a readable summary
- `config.json` with model, prompt, dataset, pricing, content hashes, and Git state

Compare two saved runs that contain identical case IDs without making more model calls:

```bash
triage compare \
  --baseline artifacts/golden-flash-lite-v1 \
  --candidate artifacts/golden-flash-lite-v2 \
  --output artifacts/local-v1-v2-comparison.json
```

The paired comparison reports the exact-match delta and bootstrap interval, cost multiplier, and prediction agreement. A candidate is not eligible for promotion if model errors or safety failures increase, regardless of aggregate accuracy.

## Optional: use ADK Web

Start the local development UI:

```bash
adk web --host 127.0.0.1 --port 8000 adk_apps
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000), select `github_issue_triage`, and send:

```json
{
  "title": "Broken link in the contributor guide",
  "body": "The setup link returns 404."
}
```

ADK Web reads `TRIAGE_MODEL` and `TRIAGE_PROMPT_PATH` from `.env`; restart it after changing either value. It is an unauthenticated development tool, so keep it bound to `127.0.0.1`. Use `triage evaluate`, not ADK Web, for repeatable dataset runs.

## Optional: build a custom dataset

The fetcher uses public GitHub data without a token; setting `GITHUB_TOKEN` only raises the API rate limit.

```bash
export GITHUB_TOKEN='your-token'
python scripts/fetch_github_issues.py \
  --repo python/pythondotorg \
  --state all \
  --limit 100 \
  --output datasets/raw/issues.jsonl
```

The fetcher excludes pull requests and retains labels only for sampling and audit. Before evaluating manually annotated data, run the dataset validator shown under local checks. See [the triage policy](docs/triage_policy.md) and [dataset format and freezing procedure](docs/dataset.md).

## Optional: trace with local Phoenix

Install the observability extra and start the checked-in Docker Compose service:

```bash
python -m pip install -e '.[observability]'
docker compose up -d phoenix
```

Replay a saved run into Phoenix without making model calls:

```bash
triage phoenix \
  --dataset datasets/golden_test.jsonl \
  --predictions artifacts/golden-flash-lite-v2/predictions.jsonl \
  --experiment-name local-gemini-v2-replay
```

Browse the result at [http://localhost:6006](http://localhost:6006). To export new `triage issue`, `triage evaluate`, or ADK Web traces, set `TRIAGE_ENABLE_PHOENIX=true` and `TRIAGE_PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006/v1/traces` in `.env`. The optional `PHOENIX_PROJECT_NAME` defaults to `github-triage`.

Phoenix also supports a `--live` mode that makes fresh provider calls. See [the Phoenix guide](docs/phoenix_experiments.md) for setup and evaluator details and [the model comparison runbook](docs/model_comparison_runbook.md) for complete Gemini and Groq workflows. File artifacts remain the source of truth for promotion decisions.

## Provider and data-safety notes

- `--model` determines which provider receives the issue title and body: `gemini-...` uses Google's native connector and `groq/...` uses Groq through LiteLLM.
- Both providers may be configured, but each evaluation uses one model and records it in `config.json`.
- Real cases come from public GitHub issues, but synthetic cases can still describe sensitive scenarios. Approve the provider and dataset combination before transmitting a frozen split.
- Free-tier billing does not imply zero production cost; normalized list prices keep configurations comparable.

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
