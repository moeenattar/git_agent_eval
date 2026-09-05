# Model comparison runbook

This runbook evaluates the frozen 35-case golden dataset with prompt v2 across four
Gemini models and both verified Groq GPT-OSS models. It then compares every candidate
with Gemini 3.5 Flash-Lite and publishes the saved predictions to Phoenix without making
duplicate model calls.

Every `triage evaluate` or `triage phoenix --live` command sends all dataset inputs to the
selected external provider. The checked-in cases are public or synthetic, but some describe
security-sensitive scenarios. Confirm the provider is approved before running a command.

## Setup

Run commands from the repository root:

```bash
source .venv/bin/activate
python -m pip install -e '.[dev,groq,observability]'
```

Store credentials in `.env`; do not place actual keys in commands, documentation, or
artifacts:

```dotenv
GOOGLE_API_KEY=
GROQ_API_KEY=
```

The commands use paid standard-tier list prices to normalize cost even when requests are
covered by a free tier. Prices were verified on 2026-09-06 from the official
[Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing) and
[Groq model catalog](https://console.groq.com/docs/models).

| Model | Input / 1M tokens | Output / 1M tokens |
|---|---:|---:|
| `gemini-3.8-flash` | $0.75 | $3.75 |
| `gemini-3.6-flash` | $0.75 | $3.75 |
| `gemini-2.5-flash` | $0.30 | $2.50 |
| `gemini-3.5-flash-lite` | $0.30 | $2.50 |
| `groq/openai/gpt-oss-20b` | $0.075 | $0.30 |
| `groq/openai/gpt-oss-120b` | $0.15 | $0.60 |

The Gemini 3.8 and 3.6 values are introductory prices through December 31, 2026.

## 1. Run local evaluations

The six commands deliberately use the same dataset, prompt, and six requests per minute.
Add a unique suffix before repeating a run; reusing a name overwrites that experiment's
files under `artifacts/`.

### Gemini 3.5 Flash-Lite baseline

```bash
triage evaluate \
  --dataset datasets/golden_test.jsonl \
  --experiment eval-gemini-3-5-flash-lite-v2 \
  --model gemini-3.5-flash-lite \
  --prompt prompts/triage_v2.txt \
  --input-price-per-million 0.30 \
  --output-price-per-million 2.50 \
  --requests-per-minute 6
```

### Gemini 3.6 Flash

```bash
triage evaluate \
  --dataset datasets/golden_test.jsonl \
  --experiment eval-gemini-3-6-flash-v2 \
  --model gemini-3.6-flash \
  --prompt prompts/triage_v2.txt \
  --input-price-per-million 0.75 \
  --output-price-per-million 3.75 \
  --requests-per-minute 6
```

### Gemini 3.8 Flash

```bash
triage evaluate \
  --dataset datasets/golden_test.jsonl \
  --experiment eval-gemini-3-8-flash-v2 \
  --model gemini-3.8-flash \
  --prompt prompts/triage_v2.txt \
  --input-price-per-million 0.75 \
  --output-price-per-million 3.75 \
  --requests-per-minute 6
```

### Gemini 2.5 Flash

```bash
triage evaluate \
  --dataset datasets/golden_test.jsonl \
  --experiment eval-gemini-2-5-flash-v2 \
  --model gemini-2.5-flash \
  --prompt prompts/triage_v2.txt \
  --input-price-per-million 0.30 \
  --output-price-per-million 2.50 \
  --requests-per-minute 6
```

### Groq GPT-OSS 20B

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

### Groq GPT-OSS 120B

```bash
triage evaluate \
  --dataset datasets/golden_test.jsonl \
  --experiment eval-groq-gpt-oss-120b-v2 \
  --model groq/openai/gpt-oss-120b \
  --prompt prompts/triage_v2.txt \
  --input-price-per-million 0.15 \
  --output-price-per-million 0.60 \
  --requests-per-minute 6
```

Each run produces `config.json`, `predictions.jsonl`, `metrics.json`, and `report.md` under
`artifacts/<experiment-name>/`.

## 2. Compare every candidate with the baseline

These are paired comparisons: the command rejects mismatched case IDs. Gemini 3.5
Flash-Lite is the baseline because it is the currently retained assisted-triage configuration.

```bash
triage compare \
  --baseline artifacts/eval-gemini-3-5-flash-lite-v2 \
  --candidate artifacts/eval-gemini-3-6-flash-v2 \
  --output artifacts/comparisons/gemini-3-5-lite-vs-gemini-3-6-flash.json

triage compare \
  --baseline artifacts/eval-gemini-3-5-flash-lite-v2 \
  --candidate artifacts/eval-gemini-3-8-flash-v2 \
  --output artifacts/comparisons/gemini-3-5-lite-vs-gemini-3-8-flash.json

triage compare \
  --baseline artifacts/eval-gemini-3-5-flash-lite-v2 \
  --candidate artifacts/eval-gemini-2-5-flash-v2 \
  --output artifacts/comparisons/gemini-3-5-lite-vs-gemini-2-5-flash.json

triage compare \
  --baseline artifacts/eval-gemini-3-5-flash-lite-v2 \
  --candidate artifacts/eval-groq-gpt-oss-20b-v2 \
  --output artifacts/comparisons/gemini-3-5-lite-vs-groq-gpt-oss-20b.json

triage compare \
  --baseline artifacts/eval-gemini-3-5-flash-lite-v2 \
  --candidate artifacts/eval-groq-gpt-oss-120b-v2 \
  --output artifacts/comparisons/gemini-3-5-lite-vs-groq-gpt-oss-120b.json
```

Review exact-match delta and its paired bootstrap confidence interval together with field
agreement, cost multiplier, model errors, human-review false negatives, high-priority
downgrades, and critical high-to-low under-triage. Do not promote a candidate that regresses
a safety gate even if aggregate accuracy improves.

## 3. Publish saved runs to Phoenix

Start the local Phoenix server:

```bash
docker compose up -d phoenix
```

Replay is the recommended path after `triage evaluate`. It uses the saved predictions,
registers the exact prompt, attaches all eight deterministic evaluators, and makes no new
Gemini or Groq calls.

```bash
triage phoenix \
  --dataset datasets/golden_test.jsonl \
  --predictions artifacts/eval-gemini-3-5-flash-lite-v2/predictions.jsonl \
  --experiment-name eval-gemini-3-5-flash-lite-v2-phoenix

triage phoenix \
  --dataset datasets/golden_test.jsonl \
  --predictions artifacts/eval-gemini-3-6-flash-v2/predictions.jsonl \
  --experiment-name eval-gemini-3-6-flash-v2-phoenix

triage phoenix \
  --dataset datasets/golden_test.jsonl \
  --predictions artifacts/eval-gemini-3-8-flash-v2/predictions.jsonl \
  --experiment-name eval-gemini-3-8-flash-v2-phoenix

triage phoenix \
  --dataset datasets/golden_test.jsonl \
  --predictions artifacts/eval-gemini-2-5-flash-v2/predictions.jsonl \
  --experiment-name eval-gemini-2-5-flash-v2-phoenix

triage phoenix \
  --dataset datasets/golden_test.jsonl \
  --predictions artifacts/eval-groq-gpt-oss-20b-v2/predictions.jsonl \
  --experiment-name eval-groq-gpt-oss-20b-v2-phoenix

triage phoenix \
  --dataset datasets/golden_test.jsonl \
  --predictions artifacts/eval-groq-gpt-oss-120b-v2/predictions.jsonl \
  --experiment-name eval-groq-gpt-oss-120b-v2-phoenix
```

Open [http://localhost:6006](http://localhost:6006), select **Datasets & Experiments**, and
use the comparison selector to view models side by side.

## 4. Optional: run fresh calls directly from Phoenix

Use this route instead of evaluation-plus-replay when the primary goal is live trace
inspection. It creates fresh provider calls and Phoenix annotations, but it does not create
the local `metrics.json`, `report.md`, and `predictions.jsonl` artifact set.

Gemini example:

```bash
export TRIAGE_ENABLE_PHOENIX=true
export PHOENIX_BASE_URL=http://localhost:6006
export TRIAGE_PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006/v1/traces

triage phoenix \
  --live \
  --dataset datasets/golden_test.jsonl \
  --model gemini-3.8-flash \
  --prompt prompts/triage_v2.txt \
  --requests-per-minute 6 \
  --experiment-name eval-gemini-3-8-flash-v2-live
```

Groq example:

```bash
triage phoenix \
  --live \
  --dataset datasets/golden_test.jsonl \
  --model groq/openai/gpt-oss-20b \
  --prompt prompts/triage_v2.txt \
  --requests-per-minute 6 \
  --experiment-name eval-groq-gpt-oss-20b-v2-live
```

For another model, replace `--model` and `--experiment-name` with one of the exact pairs
from section 1. Do not run both live Phoenix and evaluation-plus-replay unless a deliberate
repeat is wanted; doing both sends the same 35 cases twice.
