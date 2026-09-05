# Experiment calibration-flash-lite-v4

Model: `gemini-3.5-flash-lite`  
Prompt: `prompts/triage_v4.txt`  
Dataset: `datasets/calibration.jsonl`

## Results

| Metric | Value |
|---|---:|
| Cases | 15 |
| Successful predictions | 15 |
| Exact match | 86.7% |
| Exact match 95% bootstrap CI | 66.7%–100.0% |
| Type macro-F1 | 0.731 |
| Priority macro-F1 | 0.930 |
| Human-review macro-F1 | 1.000 |
| Human-review false negatives | 0 |
| Critical high-to-low under-triage | 0 |
| Any high-priority downgrade | 0 |
| Mean latency | 1533.2 ms |
| p95 latency | 1885.2 ms |
| Normalized cost per 1,000 issues | $0.4738 |

## Interpretation

This report is descriptive for one configuration. Promotion decisions require a paired comparison
on the same frozen test cases. A candidate must not increase model errors, high-priority
downgrades, critical under-triage, or human-review false negatives.
