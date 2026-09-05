# Experiment golden-flash-lite-v1

Model: `gemini-3.5-flash-lite`  
Prompt: `prompts/triage_v1.txt`  
Dataset: `datasets/golden_test.jsonl`

## Results

| Metric | Value |
|---|---:|
| Cases | 35 |
| Successful predictions | 35 |
| Exact match | 48.6% |
| Exact match 95% bootstrap CI | 31.4%–65.7% |
| Type macro-F1 | 0.748 |
| Priority macro-F1 | 0.791 |
| Human-review macro-F1 | 0.735 |
| Human-review false negatives | 8 |
| Critical high-to-low under-triage | 0 |
| Any high-priority downgrade | 3 |
| Mean latency | 1428.2 ms |
| p95 latency | 1792.9 ms |
| Normalized cost per 1,000 issues | $0.3013 |

## Interpretation

This report is descriptive for one configuration. Promotion decisions require a paired comparison
on the same frozen test cases. A candidate must not increase critical under-triage or human-review
false negatives.
