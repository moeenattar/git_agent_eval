# Prompt optimization follow-up

Date: 2026-09-06  
Fixed model: `gemini-3.5-flash-lite`  
Dataset version: `v1`

## Method

Prompt development used only the 15-case calibration split. Prompt v3 targeted the three
prompt-v2 calibration disagreements. V3 improved exact match but introduced a human-review
false negative, so it was rejected. V4 restored the safety gate. V5 made one final general
boundary refinement, after which prompt iteration stopped to limit overfitting.

The selected v5 prompt was frozen before one evaluation on the 35-case golden split. No
prompt rule or gold label was changed after seeing the v5 golden result.

## Calibration results

| Metric | v2 baseline | v3 | v4 | v5 selected |
|---|---:|---:|---:|---:|
| Exact match | 80.0% | 86.7% | 86.7% | 86.7% |
| Type macro-F1 | 0.651 | 0.800 | 0.731 | 0.800 |
| Priority macro-F1 | 0.937 | 0.930 | 0.930 | 0.878 |
| Human-review macro-F1 | 1.000 | 0.932 | 1.000 | 1.000 |
| Human-review false negatives | 0 | 1 | 0 | 0 |
| High-priority downgrades | 0 | 0 | 0 | 0 |
| Critical high-to-low errors | 0 | 0 | 0 | 0 |
| Model errors | 0 | 0 | 0 | 0 |
| Normalized cost / 1,000 | $0.3882 | $0.4482 | $0.4738 | $0.4982 |

V5 classified all 15 calibration issue types correctly. Its two remaining exact-match errors
were conservative low-to-medium priority upgrades. Relative to v2, v5 increased calibration
exact match by 6.7 percentage points, but the paired 95% bootstrap interval was -20.0 to
33.3 points. The improvement was not statistically clear on this small split.

## Frozen golden result

| Metric | v2 baseline | v5 candidate | Change |
|---|---:|---:|---:|
| Exact match | 54.3% | 60.0% | +5.7 points |
| Type macro-F1 | 0.742 | 0.863 | +0.121 |
| Priority macro-F1 | 0.798 | 0.822 | +0.024 |
| Human-review macro-F1 | 0.857 | 0.771 | -0.086 |
| Human-review false negatives | 4 | 4 | 0 |
| High-priority downgrades | 2 | 1 | -1 |
| Critical high-to-low errors | 0 | 0 | 0 |
| Model errors | 0 | 0 | 0 |
| Mean latency | 1.77 s | 1.40 s | -0.37 s |
| Normalized cost / 1,000 | $0.3815 | $0.4969 | 1.303x |

The paired exact-match delta was +5.7 percentage points with a 95% bootstrap interval from
-11.4 to +22.9 points. Exact three-field prediction agreement between v2 and v5 was 65.7%;
agreement for each individual field was 85.7%.

## Decision

Do not promote v5 as the default prompt. It improves the exact-match point estimate and
reduces high-priority downgrades without increasing false negatives, but the accuracy gain
is not statistically clear, human-review macro-F1 is lower, and normalized cost increases by
30.3%. Prompt v2 remains the retained assisted-triage baseline; neither prompt is approved
for unsupervised routing.

V5 is a useful candidate for reevaluation after expanding the independently annotated
dataset. Do not tune another prompt against the v5 golden failures.

## Artifacts

- `artifacts/calibration-flash-lite-v3/`
- `artifacts/calibration-flash-lite-v4/`
- `artifacts/calibration-flash-lite-v5/`
- `artifacts/calibration-prompt-v2-v5.json`
- `artifacts/golden-flash-lite-v5/`
- `artifacts/golden-prompt-v2-v5.json`

Prompt fingerprints:

- v3: `67a6174294b0679469ca46ec73ecd64151b1ed36cbfa8b1e34fb23717c6f3a4f`
- v4: `57dad6d9ff934a4ed38663ff0330efbcacebc7330b24eac620292867bf028ab0`
- v5: `29744625ebf47c6cda1170507e234381b6f1d94bc7d33558157bb581cd7a0724`
