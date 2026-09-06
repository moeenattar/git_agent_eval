# Experiment eval-gemini-3-5-flash-lite-v2

Model: `gemini-3.5-flash-lite`  
Prompt: `prompts/triage_v2.txt`  
Dataset: `datasets/golden_test.jsonl`

## Results

| Metric | Value |
|---|---:|
| Cases | 35 |
| Successful predictions | 35 |
| Exact match | 54.3% |
| Exact match 95% bootstrap CI | 37.1%–71.4% |
| Type macro-F1 | 0.742 |
| Priority macro-F1 | 0.824 |
| Human-review macro-F1 | 0.827 |
| Human-review false negatives | 5 |
| Critical high-to-low under-triage | 0 |
| Any high-priority downgrade | 2 |
| Mean latency | 1371.7 ms |
| p95 latency | 1626.4 ms |
| Normalized cost per 1,000 issues | $0.3815 |

## Interpretation

This report is descriptive for one configuration. Promotion decisions require a paired comparison
on the same frozen test cases. A candidate must not increase model errors, high-priority
downgrades, critical under-triage, or human-review false negatives.
