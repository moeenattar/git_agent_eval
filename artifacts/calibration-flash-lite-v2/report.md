# Experiment calibration-flash-lite-v2

Model: `gemini-3.5-flash-lite`  
Prompt: `prompts/triage_v2.txt`  
Dataset: `datasets/calibration.jsonl`

## Results

| Metric | Value |
|---|---:|
| Cases | 15 |
| Successful predictions | 15 |
| Exact match | 80.0% |
| Exact match 95% bootstrap CI | 60.0%–100.0% |
| Type macro-F1 | 0.651 |
| Priority macro-F1 | 0.937 |
| Human-review macro-F1 | 1.000 |
| Human-review false negatives | 0 |
| Critical high-to-low under-triage | 0 |
| Mean latency | 1485.2 ms |
| p95 latency | 2592.9 ms |
| Normalized cost per 1,000 issues | $0.3882 |

## Interpretation

This report is descriptive for one configuration. Promotion decisions require a paired comparison
on the same frozen test cases. A candidate must not increase critical under-triage or human-review
false negatives.
