# Phoenix datasets and experiments

The Phoenix integration complements the local evaluation harness. The checked-in prediction files, metrics, and reports remain the reproducible source of truth; Phoenix adds row-level exploration, task/evaluator traces, prompt registration, and filterable annotations.

Prompt v2 is the final project prompt. Use `prompts/triage_v2.txt` for both replay metadata and live Phoenix comparisons; v3–v5 are retained only as rejected experiment history.

## Install and configure

Install the Phoenix client together with the existing tracing and optional Groq integration:

```bash
python -m pip install -e '.[dev,groq,observability]'
docker compose up -d phoenix
```

The defaults target the local server. These values can also be set in `.env`:

```bash
PHOENIX_BASE_URL=http://localhost:6006
TRIAGE_ENABLE_PHOENIX=true
PHOENIX_PROJECT_NAME=github-triage
TRIAGE_PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006/v1/traces
```

No Phoenix API key is needed for the unauthenticated local server. Do not expose that server to an untrusted network.

## Import an existing run without model calls

This is the recommended first command. It creates or reuses a fingerprinted Phoenix dataset, registers the exact frozen prompt, imports saved predictions as an experiment, and runs all deterministic code evaluators:

```bash
triage phoenix \
  --dataset datasets/golden_test.jsonl \
  --predictions artifacts/golden-groq-gpt-oss-20b-v2/predictions.jsonl \
  --experiment-name golden-groq-20b-v2-phoenix-replay
```

The dataset name contains the dataset version and SHA-256 prefix. Every example uses the repository case ID as its stable Phoenix ID. The Phoenix input contains only `title` and `body`; the expected output contains the three approved labels; source, slices, annotation review information, and dataset fingerprint are metadata.

The experiment metadata records the model ID, prompt path and SHA-256, Phoenix prompt-version ID, dataset path and SHA-256, prediction artifact and SHA-256, and source git commit when present. It never records provider credentials.

Replay creates task traces that link each imported output to its Phoenix experiment row, but it cannot reconstruct historical LLM child spans because the original artifacts did not store trace IDs. Existing model traces remain in the `github-triage` tracing project.

## Run a live traced experiment

Use live mode only when fresh model calls are wanted. Gemini uses ADK's native connector and requires `GOOGLE_API_KEY` or `GEMINI_API_KEY`:

```bash
triage phoenix \
  --live \
  --dataset datasets/golden_test.jsonl \
  --model gemini-3.5-flash-lite \
  --prompt prompts/triage_v2.txt \
  --requests-per-minute 6 \
  --experiment-name golden-gemini-flash-lite-v2-live
```

Gemini model IDs must begin with `gemini-`. Use a specific stable model ID for reproducible comparisons; moving `*-latest` aliases can change underneath an experiment.

Groq requires `GROQ_API_KEY` and remains deliberately restricted to the two verified models, `groq/openai/gpt-oss-20b` and `groq/openai/gpt-oss-120b`:

```bash
triage phoenix \
  --live \
  --dataset datasets/golden_test.jsonl \
  --model groq/openai/gpt-oss-20b \
  --prompt prompts/triage_v2.txt \
  --requests-per-minute 6 \
  --experiment-name golden-groq-20b-v2-live
```

Live mode runs sequentially and paces calls for either provider. The Phoenix experiment task span is the parent context for the ADK/OpenInference spans, so each experiment row links to the actual agent/model trace. Restart or re-run with a new experiment name when changing the model or prompt. The command sends every dataset input to the selected provider, so provider approval is required before running it on a frozen dataset.

## Code evaluators

The integration attaches eight deterministic annotations to every experiment row:

- `valid_output`
- `issue_type_correct`
- `priority_correct`
- `human_review_correct`
- `exact_match`
- `human_review_false_negative`
- `high_priority_downgrade`
- `critical_under_triage`

Correctness scores use `1=correct`. Safety-gate scores intentionally use `1=violation` and `0=clear`, so their Phoenix averages are violation rates. Explanations and labels are stored with every annotation.

In Phoenix 20.8, these SDK code evaluators appear as annotations in **Datasets & Experiments**, including the Grid/List views, filters, and per-run details. The separate top-level **Evaluators** page is for persistent server-managed evaluator tasks, so it can still show zero even though all experiment annotations are present. No LLM judge is used because the reference labels are objective.

## Verified local parity

The saved Groq GPT-OSS 20B run was imported into the local Phoenix 20.8 server as `golden-groq-20b-v2-phoenix-parity`. Phoenix stored 35 task runs and 280 evaluation annotations. Read-back aggregates matched the checked-in harness:

| Signal | Phoenix | Harness |
|---|---:|---:|
| Exact match | 15/35 (42.9%) | 42.9% |
| Human-review false negatives | 9 | 9 |
| High-priority downgrades | 1 | 1 |
| Critical high-to-low errors | 0 | 0 |
| Valid structured outputs | 35/35 | 35/35 successful |

Phoenix does not replace bootstrap confidence intervals, macro-F1, normalized cost, or promotion gates in the generated local report.
