# Experiment golden-flash-lite-v5

Model: `gemini-3.5-flash-lite`  
Prompt: `prompts/triage_v5.txt`  
Dataset: `datasets/golden_test.jsonl`

## Results

| Metric | Value |
|---|---:|
| Cases | 35 |
| Successful predictions | 35 |
| Exact match | 60.0% |
| Exact match 95% bootstrap CI | 42.9%–77.1% |
| Type macro-F1 | 0.863 |
| Priority macro-F1 | 0.822 |
| Human-review macro-F1 | 0.771 |
| Human-review false negatives | 4 |
| Critical high-to-low under-triage | 0 |
| Any high-priority downgrade | 1 |
| Mean latency | 1395.9 ms |
| p95 latency | 1658.5 ms |
| Normalized cost per 1,000 issues | $0.4969 |

## Interpretation

This report is descriptive for one configuration. Promotion decisions require a paired comparison
on the same frozen test cases. A candidate must not increase model errors, high-priority
downgrades, critical under-triage, or human-review false negatives.
