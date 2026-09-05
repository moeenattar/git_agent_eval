# Experiment golden-groq-gpt-oss-20b-v2-2

Model: `groq/openai/gpt-oss-20b`  
Prompt: `prompts/triage_v2.txt`  
Dataset: `datasets/golden_test.jsonl`

## Results

| Metric | Value |
|---|---:|
| Cases | 35 |
| Successful predictions | 35 |
| Exact match | 42.9% |
| Exact match 95% bootstrap CI | 25.7%–60.0% |
| Type macro-F1 | 0.666 |
| Priority macro-F1 | 0.575 |
| Human-review macro-F1 | 0.735 |
| Human-review false negatives | 8 |
| Critical high-to-low under-triage | 0 |
| Any high-priority downgrade | 1 |
| Mean latency | 1003.4 ms |
| p95 latency | 1350.4 ms |
| Normalized cost per 1,000 issues | $0.1547 |

## Interpretation

This report is descriptive for one configuration. Promotion decisions require a paired comparison
on the same frozen test cases. A candidate must not increase model errors, high-priority
downgrades, critical under-triage, or human-review false negatives.
