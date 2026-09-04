# Triage and Annotation Policy

Version: draft 1  
Applies to: calibration and golden datasets

This policy defines the ground truth before model evaluation. Annotators must judge only the issue title and body. Repository labels, comments, linked pull requests, and the eventual resolution may help sample candidates, but they must not determine the annotation.

## Output contract

Every issue receives exactly one issue type, one priority, and one human-review decision.

### Issue type

| Label | Definition | Boundary rule |
|---|---|---|
| `bug` | Existing behavior is incorrect, broken, or regressed. | A request to restore documented or clearly expected behavior is a bug. |
| `enhancement` | New capability or an improvement to existing behavior. | A request that changes intended product behavior is an enhancement, even when the reporter calls it a fix. |
| `documentation` | Documentation or public website content is missing, incorrect, or unclear. | Use this when the requested outcome is a content change rather than a code behavior change. |
| `maintenance` | Dependency work, refactoring, tests, infrastructure, internal tooling, or cleanup. | Use this for engineering-health work with no direct user-facing capability. |
| `other` | The report cannot reasonably be assigned to the preceding types. | Do not use `other` merely because information is missing; choose the most likely type and set human review when possible. |

If an issue contains multiple requests, classify its dominant user impact. If no dominant request exists, choose `other` and require human review.

### Priority

| Label | Definition | Typical evidence |
|---|---|---|
| `high` | Immediate maintainer attention is warranted. | Security/privacy concern, service-wide outage, significant data-loss risk, major regression, or a problem blocking many users. |
| `medium` | Meaningful work with noticeable user or operational impact, but not an emergency. | Functional defect, important enhancement, partial degradation, repeated failure with a workaround, or impact limited to a user segment. |
| `low` | Small or non-urgent impact. | Documentation, cosmetic behavior, minor enhancement, routine maintenance, refactoring, or cleanup. |

Priority must be supported by evidence in the title or body. Do not infer that a terse bug report is high priority. Missing severity evidence normally implies `medium` for a plausible functional bug plus human review; it does not imply `high`.

Security and privacy reports are always `high` in this triage taxonomy because they require prompt containment and specialist review. This label does not claim that a vulnerability has been confirmed.

### Human review

`needs_human_review` means a maintainer should inspect the classification before automated triage is trusted. It does not mean a person must eventually implement, approve, or respond to every issue.

Set it to `true` when any of these conditions materially affects the decision:

- critical reproduction, scope, environment, or impact information is missing;
- the report is genuinely ambiguous between types or priorities;
- security, privacy, legal, or abuse concerns appear;
- the impact cannot be established;
- a product or policy choice is required;
- the title and body contradict each other;
- multiple unrelated requests lack one dominant classification.

Set it to `false` for a clear low-risk bug, a specific documentation correction, routine maintenance, or a well-described enhancement whose classification does not need judgment beyond this policy.

## Annotation procedure

1. Read only title and body.
2. Identify the requested or expected outcome and assign one issue type.
3. Identify explicit impact evidence and assign priority.
4. Apply the human-review conditions independently.
5. Write a one-sentence reason that cites the decisive evidence.
6. Add diagnostic slices such as `real`, `synthetic`, `security`, `ambiguous`, `short_body`, or `missing_information`.
7. Record uncertainty as human review; never add unsupported facts to resolve it.

## Quality control

Before freezing version `v1`, a second annotator should independently label at least 20% of cases, including every high-priority and security case. Resolve disagreements against this policy and record policy changes before examining candidate-model test predictions.

Calibration examples may guide prompt development. Golden test labels are frozen and must not be changed merely because a model disagrees. A genuine policy correction creates a new dataset version with a short change note.
