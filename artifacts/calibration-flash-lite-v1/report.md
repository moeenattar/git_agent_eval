# Experiment calibration-flash-lite-v1

Model: `gemini-3.5-flash-lite`  
Prompt: `prompts/triage_v1.txt`  
Dataset: `datasets/calibration.jsonl`

## Results

| Metric | Value |
|---|---:|
| Cases | 15 |
| Successful predictions | 15 |
| Exact match | 53.3% |
| Exact match 95% bootstrap CI | 26.7%–80.0% |
| Type macro-F1 | 0.703 |
| Priority macro-F1 | 0.687 |
| Human-review macro-F1 | 0.700 |
| Human-review false negatives | 4 |
| Critical high-to-low under-triage | 1 |
| Mean latency | 2219.4 ms |
| p95 latency | 5366.3 ms |
| Normalized cost per 1,000 issues | $0.3025 |

## Interpretation

This report is descriptive for one configuration. Promotion decisions require a paired comparison
on the same frozen test cases. A candidate must not increase critical under-triage or human-review
false negatives.
