# Submission and Reproducibility Record

This record freezes the evidence used for the take-home submission. It was prepared on
2026-09-06 without making new model calls or changing any experiment result.

## Final decision

The assisted baseline is `gemini-3.5-flash-lite` with `prompts/triage_v2.txt`. It is not
approved for unsupervised routing because the 35-case golden run contained four
human-review false negatives and two `high -> medium` security downgrades. The complete
quality, latency, cost, and stability comparison is in the
[Milestone 4 results](milestone4_results.md); the held-out errors are documented in the
[golden failure analysis](golden_failure_analysis.md).

## Model and price provenance

Normalized cost uses the paid-tier list prices below even when a run used a free tier.
The prices and model availability were retrieved on 2026-09-05 from the official
[Gemini model catalog](https://ai.google.dev/gemini-api/docs/models?hl=en),
[Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing), and
[Groq model catalog](https://console.groq.com/docs/models). Historical runs retain the
exact prices supplied to the CLI in their `config.json` files.

| Provider | Recorded model ID | Input / 1M tokens | Output / 1M tokens | Role in comparison |
|---|---|---:|---:|---|
| Google | `gemini-3.5-flash-lite` | $0.30 | $2.50 | Assisted baseline; prompts v1, v2, and v5 |
| Groq | `groq/openai/gpt-oss-20b` | $0.075 | $0.30 | Lower-cost candidate; rejected by safety gate |
| Groq | `groq/openai/gpt-oss-120b` | $0.15 | $0.60 | Quality candidate and repeat; rejected by safety gate |

These are historical inputs to the normalized comparison, not a promise of current
provider pricing. Recheck the linked provider pages before estimating future spend.

## Frozen input fingerprints

All values are SHA-256 hashes of the checked-in bytes.

| Input | Records / purpose | SHA-256 |
|---|---|---|
| `datasets/calibration.jsonl` | 15 calibration cases | `ed9f4a9ff0e821ba6de8f4a0ff7dbd6d3c56a78b203f3f9a69a519ccf96f9fe3` |
| `datasets/golden_test.jsonl` | 35 held-out cases | `f86c67f69b36362e0d10d466a93847de4b8b64b7a106278f6a8d02ea02ea9017` |
| `datasets/manifest.json` | Dataset v1 manifest | `d1450ef2e43461f9b9bbf217d530dfbfc7e5acb8f4dc04721e5b5aca3e56d644` |
| `prompts/triage_v1.txt` | Original baseline | `b06513f385ebfe0e41d829c841fa00858efb0a6df62361ff773561cc35d879fd` |
| `prompts/triage_v2.txt` | Final prompt | `e57dff9975bdd5a914d6c37b68f484eaaca5f2502ae4ae15d251ba9a8d7d0480` |
| `prompts/triage_v3.txt` | Rejected calibration candidate | `67a6174294b0679469ca46ec73ecd64151b1ed36cbfa8b1e34fb23717c6f3a4f` |
| `prompts/triage_v4.txt` | Rejected calibration candidate | `57dad6d9ff934a4ed38663ff0330efbcacebc7330b24eac620292867bf028ab0` |
| `prompts/triage_v5.txt` | Rejected golden candidate | `29744625ebf47c6cda1170507e234381b6f1d94bc7d33558157bb581cd7a0724` |

The dataset manifest independently stores the two split hashes, and the test suite checks
that the frozen files still match it.

## Experiment provenance

Each artifact directory contains predictions, metrics, a report, and a configuration with
the model, prompt hash, dataset hash, prices, pacing, and source commit. `Dirty` is reported
honestly from the configuration captured when the run began; the content hashes still pin
the exact dataset and prompt inputs.

| Experiment | Source commit | Dirty | Decision |
|---|---|---:|---|
| `golden-flash-lite-v1` | `c57841af56db10fe4c2cce007f62334c0a93c3e8` | Yes | Prompt baseline |
| `golden-flash-lite-v2` | `57bf3859c711117b5253e30e87c471d79af27342` | Yes | Final assisted baseline |
| `golden-groq-gpt-oss-20b-v2` | `c57841af56db10fe4c2cce007f62334c0a93c3e8` | Yes | Rejected: safety regression |
| `golden-groq-gpt-oss-120b-v2` | `a2252659631bfe34671be95f96daccfaf2bfa9b1` | No | Rejected: safety regression |
| `golden-groq-gpt-oss-120b-v2-repeat` | `a2252659631bfe34671be95f96daccfaf2bfa9b1` | No | Stability evidence |
| `golden-flash-lite-v5` | `6697f3fc13256a6e05750700b2133c03fa51ba02` | Yes | Rejected: unclear gain and higher cost |

## Milestone commits

| Milestone | Evidence commit |
|---|---|
| Baseline foundation | [`077cb69d372e321e1464205e86b736ee5d094c85`](https://github.com/moeenattar/git_agent_eval/commit/077cb69d372e321e1464205e86b736ee5d094c85) |
| Dataset v1 freeze | [`57bf3859c711117b5253e30e87c471d79af27342`](https://github.com/moeenattar/git_agent_eval/commit/57bf3859c711117b5253e30e87c471d79af27342) |
| Baseline experiment | [`c57841af56db10fe4c2cce007f62334c0a93c3e8`](https://github.com/moeenattar/git_agent_eval/commit/c57841af56db10fe4c2cce007f62334c0a93c3e8) |
| Model comparison | [`d35cd7d33454b9f0177bd70d2ca5ee545c0cb62d`](https://github.com/moeenattar/git_agent_eval/commit/d35cd7d33454b9f0177bd70d2ca5ee545c0cb62d) |
| Prompt optimization record | [`a1787241522d25b5c3ae618062aa606af896fced`](https://github.com/moeenattar/git_agent_eval/commit/a1787241522d25b5c3ae618062aa606af896fced) |
| Pre-submission documentation baseline | [`eb910f511711affb6121a3208168eaa7e0e9b7c2`](https://github.com/moeenattar/git_agent_eval/commit/eb910f511711affb6121a3208168eaa7e0e9b7c2) |

## Release and privacy audit

The audit was completed on 2026-09-06 before this record was written.

- GitHub's repository API reported `moeenattar/git_agent_eval` as public with `main` as
  its default branch.
- Every commit reachable from every local ref was scanned for Gemini, Groq, GitHub, and
  the previously used `AQ.`-style credential patterns; no match was found.
- Git history contains no `.env`, private-key, or keystore file.
- `.env` is ignored and is not tracked. `.env.example` contains placeholders only.
- Frozen real cases are attributed to public `python/pythondotorg` issue URLs. Synthetic
  cases contain no real credentials. The email-like string found by the audit is the
  public `python-list@python.org` mailing-list path copied from its cited public issue.

This scan checks known credential formats and expected data sources; it cannot prove the
absence of every possible sensitive string. Any credential ever pasted into a chat or
terminal should still be rotated independently of repository history.

## Curated reasoning trail

The private planning conversation, **Create Github Triage Plan** (2026-09-05), started from
the take-home brief and established the decisions later implemented in the repository:

1. Treat the evaluation harness as the product and keep the ADK service deliberately small.
2. Use one tool-free agent receiving only issue title and body; avoid RAG, GitHub writes,
   and multi-agent complexity.
3. Write the triage rubric before annotation, then use `high`/`medium`/`low` because source
   repositories do not share a universal incident-priority convention.
4. Build a 50-case dataset from 40 public issues and 10 synthetic coverage cases, splitting
   15 calibration cases from 35 frozen golden cases to prevent prompt-tuning leakage.
5. Score structured labels deterministically, use exact match as the primary metric, and
   make high-priority downgrades and human-review false negatives promotion blockers.
6. Compare changes on identical cases with paired bootstrap intervals and normalized paid
   list-price cost, even when the provider free tier makes the invoice zero.
7. Keep file artifacts as the decision source of truth and use local Phoenix for tracing,
   replay, and inspection.

This curated export is used instead of publishing the raw chat or its attached interview
brief. It preserves the design rationale without exposing unrelated conversation content.

## Local verification

Run the deterministic submission checks without credentials or model calls:

```bash
pytest
ruff check .
python scripts/validate_dataset.py datasets/calibration.jsonl datasets/golden_test.jsonl
git diff --check
```
