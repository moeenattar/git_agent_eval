# Experiment golden-groq-gpt-oss-120b-v2-repeat

Model: `groq/openai/gpt-oss-120b`  
Prompt: `prompts/triage_v2.txt`  
Dataset: `datasets/golden_test.jsonl`

## Results

| Metric | Value |
|---|---:|
| Cases | 35 |
| Successful predictions | 35 |
| Exact match | 51.4% |
| Exact match 95% bootstrap CI | 34.3%–68.6% |
| Type macro-F1 | 0.761 |
| Priority macro-F1 | 0.769 |
| Human-review macro-F1 | 0.694 |
| Human-review false negatives | 10 |
| Critical high-to-low under-triage | 0 |
| Any high-priority downgrade | 1 |
| Mean latency | 1321.5 ms |
| p95 latency | 2099.1 ms |
| Normalized cost per 1,000 issues | $0.3322 |

## Interpretation

This report is descriptive for one configuration. Promotion decisions require a paired comparison
on the same frozen test cases. A candidate must not increase critical under-triage or human-review
false negatives.
