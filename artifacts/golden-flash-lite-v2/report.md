# Experiment golden-flash-lite-v2

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
| Priority macro-F1 | 0.798 |
| Human-review macro-F1 | 0.857 |
| Human-review false negatives | 4 |
| Critical high-to-low under-triage | 0 |
| Mean latency | 1769.6 ms |
| p95 latency | 2181.9 ms |
| Normalized cost per 1,000 issues | $0.3815 |

## Interpretation

This report is descriptive for one configuration. Promotion decisions require a paired comparison
on the same frozen test cases. A candidate must not increase critical under-triage or human-review
false negatives.
