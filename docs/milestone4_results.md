# Milestone 4 Cost, Quality, and Stability Results

Completed: 2026-09-05

Milestone 4 compared prompts and models on the same frozen 35-case golden split. Prompt v2, dataset version `v1`, case order, output schema, and deterministic metrics remained unchanged during the model comparison. Normalized cost uses provider list prices even when calls ran on a free tier.

## Prompt comparison

Both prompt runs used `gemini-3.5-flash-lite`.

| Metric | Prompt v1 | Prompt v2 |
|---|---:|---:|
| Exact match | 48.6% | 54.3% |
| Human-review false negatives | 8 | 4 |
| High-priority downgrades | 3 | 2 |
| Cost per 1,000 issues | $0.3013 | $0.3815 |

The paired exact-match delta was +5.7 percentage points with a 95% bootstrap interval from -11.4 to +20.0 points. The interval crosses zero, so the improvement was not statistically clear. Prompt v2 nonetheless had the safer error profile and remained the selected prompt.

## Model comparison

| Configuration | Exact match | Type F1 | Priority F1 | Human F1 | Human FN | High downgrades | Mean / p95 latency | Cost / 1K |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Gemini 3.5 Flash-Lite | 54.3% | 0.742 | 0.798 | 0.857 | 4 | 2 | 1.77 / 2.18 s | $0.3815 |
| Groq GPT-OSS 20B | 42.9% | 0.666 | 0.575 | 0.702 | 9 | 1 | 0.94 / 1.33 s | $0.1575 |
| Groq GPT-OSS 120B | 51.4% | 0.761 | 0.827 | 0.694 | 10 | 1 | 1.27 / 1.99 s | $0.3247 |

Relative to Gemini, GPT-OSS 20B changed exact match by -11.4 points (paired 95% CI: -28.6 to +5.7) at a 0.413 cost multiplier. GPT-OSS 120B changed exact match by -2.9 points (paired 95% CI: -20.0 to +14.3) at a 0.851 cost multiplier. Neither difference was statistically clear.

Both Groq candidates had fewer high-priority downgrades, but each materially increased missed human-review escalations. Because human-review false negatives are a predeclared safety gate, neither candidate is eligible for promotion.

Comparing the two Groq models directly, 120B improved exact match by 8.6 points over 20B (paired 95% CI: -5.7 to +22.9) at 2.06 times the normalized cost. It also increased human-review false negatives from 9 to 10, so it failed the safety gate despite better aggregate quality.

## Stability repeat

GPT-OSS 120B was repeated because it was the strongest Groq quality candidate. The repeat matched the first run's 51.4% exact accuracy, 10 human-review false negatives, one high-priority downgrade, and zero critical `high -> low` errors.

| Agreement measure | Result |
|---|---:|
| Exact three-field decision | 88.6% |
| Issue type | 100.0% |
| Priority | 88.6% |
| Human-review decision | 100.0% |

Four priority predictions changed, while issue type and human-review decisions were identical. Normalized cost moved from $0.3247 to $0.3322 per 1,000 issues, a 2.3% difference caused by output-token variation.

## Decision

Retain Gemini 3.5 Flash-Lite with prompt v2 as the assisted-triage baseline. Promote neither Groq model. No configuration is approved for autonomous routing because even the retained baseline missed four required human reviews and downgraded two high-priority security cases to medium.

The complete prediction records, metrics, configs, and paired comparisons are stored under `artifacts/`. All completed runs contain 35 successful predictions and zero provider errors.
