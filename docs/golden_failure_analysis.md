# Golden Test Failure Analysis

This analysis describes the authoritative selection run of `gemini-3.5-flash-lite` with
`prompts/triage_v2.txt`. The 35-case frozen split and prompt were not changed after these
results were observed. A later owner-run repeat is documented separately in
`docs/milestone4_results.md`; it does not alter this original failure analysis.

## Outcome

The model exactly matched all three labels on 19 of 35 cases (54.3%). All 35 calls completed successfully. Field-level performance was stronger than exact match: type macro-F1 was 0.742, priority macro-F1 was 0.798, and human-review macro-F1 was 0.857.

There were 16 cases with at least one mismatched field:

| Failure family | Field errors | Main pattern |
|---|---:|---|
| Type boundary | 7 | Three documentation tasks were called bugs; maintenance was often called enhancement or bug. |
| Priority boundary | 7 | Two security cases labeled high were downgraded to medium; low/medium separation also varied. |
| Human-review decision | 5 | Four required reviews were missed and one unnecessary review was added. |

A case can contribute to more than one family, so these counts do not sum to 16.

## Safety-sensitive misses

The existing critical gate counts only `high -> low` errors and remained at zero. A broader inspection found two `high -> medium` downgrades, both on real security cases (`python-pythondotorg-2787` and `python-pythondotorg-2752`). Four human-review false negatives occurred on release-integrity, security/availability, dependency, and security/availability cases (`2829`, `2752`, `2709`, and `2700`).

These errors make the current configuration unsuitable for autonomous routing. A safe operational use would show the suggested labels to a maintainer and force review for security-sensitive inputs independently of the model.

## Interpretation

Prompt v2's strong calibration result did not transfer fully to the held-out set, and the confidence interval remains wide because the test set is small. This is evidence to enlarge the dataset and compare models in the next milestone, not a reason to rewrite gold labels or tune another prompt on the test failures.

The complete inputs, outputs, usage, metrics, prompt hash, and dataset hash are preserved under `artifacts/golden-flash-lite-v2/`.
