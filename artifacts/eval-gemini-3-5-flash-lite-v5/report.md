# Experiment eval-gemini-3-5-flash-lite-v5

Model: `gemini-3.5-flash-lite`  
Prompt: `prompts/triage_v5.txt`  
Dataset: `datasets/golden_test.jsonl`

## Results

| Metric | Value |
|---|---:|
| Cases | 35 |
| Successful predictions | 35 |
| Exact match | 57.1% |
| Exact match 95% bootstrap CI | 40.0%–74.3% |
| Type macro-F1 | 0.832 |
| Priority macro-F1 | 0.827 |
| Human-review macro-F1 | 0.770 |
| Human-review false negatives | 3 |
| Critical high-to-low under-triage | 0 |
| Any high-priority downgrade | 1 |
| Mean latency | 1349.5 ms |
| p95 latency | 1687.4 ms |
| Normalized cost per 1,000 issues | $0.4976 |

## Interpretation

This report is descriptive for one configuration. Promotion decisions require a paired comparison
on the same frozen test cases. A candidate must not increase model errors, high-priority
downgrades, critical under-triage, or human-review false negatives.
