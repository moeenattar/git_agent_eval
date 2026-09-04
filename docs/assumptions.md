# Assumptions and Open Questions

The exercise is intentionally open-ended. These are the stakeholder questions I would ask and the working assumptions used to keep implementation moving.

| Question | Working assumption | Consequence |
|---|---|---|
| What does urgency mean to maintainers? | Use impact-based `high`, `medium`, and `low` labels defined before evaluation. | Results are consistent within this project but do not claim to reproduce repository-specific labels. |
| What does human review mean? | A maintainer reviews the triage decision before automation is trusted. | The label is about triage risk, not whether a human implements the issue. |
| May repository metadata be used? | Only title and body are inference inputs. | Labels may support sampling/audit but cannot leak into predictions. |
| What quality metric decides success? | Exact match across all three fields is primary. | One incorrect field fails the case; diagnostic F1 metrics explain why. |
| Which errors are unacceptable? | High-to-low under-triage and missed human escalation are safety gates. | Aggregate accuracy alone cannot promote a candidate. |
| How much data is sufficient? | Fifty carefully selected cases are appropriate for a focused take-home, with uncertainty shown explicitly. | Confidence intervals will be wide and small score differences will not be overstated. |
| Does free-tier usage count as zero cost? | No; compare normalized list-price cost. | Pricing is captured as experiment input even when the actual bill is zero. |
| Should Phoenix own evaluation logic? | No; deterministic Python artifacts are authoritative. | Phoenix can be replaced without losing pass/fail reproducibility. |
| Is live GitHub access part of the service? | No; GitHub is used during dataset construction only. | Runtime is deterministic in shape and avoids unnecessary permissions. |
