# Experiment eval-gemini-3-8-flash-v5

Model: `gemini-3.8-flash`  
Prompt: `prompts/triage_v5.txt`  
Dataset: `datasets/golden_test.jsonl`

## Results

| Metric | Value |
|---|---:|
| Cases | 35 |
| Successful predictions | 35 |
| Exact match | 54.3% |
| Exact match 95% bootstrap CI | 37.1%–71.4% |
| Type macro-F1 | 0.950 |
| Priority macro-F1 | 0.775 |
| Human-review macro-F1 | 0.735 |
| Human-review false negatives | 2 |
| Critical high-to-low under-triage | 0 |
| Any high-priority downgrade | 0 |
| Mean latency | 5460.0 ms |
| p95 latency | 11288.1 ms |
| Normalized cost per 1,000 issues | $1.1726 |

## Interpretation

This report is descriptive for one configuration. Promotion decisions require a paired comparison
on the same frozen test cases. A candidate must not increase model errors, high-priority
downgrades, critical under-triage, or human-review false negatives.
