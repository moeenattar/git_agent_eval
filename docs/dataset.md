# Dataset Construction and Governance

The target dataset is 50 cases: approximately 40 public GitHub issues and 10 synthetic challenge cases. Fifteen cases form the calibration split; the remaining 35 form the frozen golden test split. These counts are a target, not a reason to include weak or redundant examples.

## Why use real and synthetic cases

`python/pythondotorg` provides realistic language and a useful range of website, infrastructure, content, and maintenance issues. A random sample is unlikely to contain enough severe security, outage, contradictory, or underspecified reports. Synthetic cases fill those deliberate coverage gaps and are reported as a separate slice.

## Record format

Each line is a JSON object:

```json
{
  "id": "pythondotorg-3044",
  "source": "github",
  "source_url": "https://github.com/python/pythondotorg/issues/3044",
  "title": "Broken link in contributor documentation",
  "body": "The setup link returns 404.",
  "gold": {
    "issue_type": "documentation",
    "priority": "low",
    "needs_human_review": false
  },
  "annotation": {
    "reason": "A specific documentation link is broken and impact is low.",
    "annotator": "initials"
  },
  "slices": ["real", "documentation", "clear"],
  "dataset_version": "v1"
}
```

Raw GitHub records keep repository labels for sampling and audit. Annotated records intentionally omit them so it is structurally difficult to leak labels into model input. The service creates `IssueInput` from `title` and `body` only.

## Selection

Sample across issue types, priorities, human-review outcomes, body lengths, open/closed states, and ambiguity. Avoid selecting many near-duplicates from one component. Synthetic cases must be clearly marked and should test an explicit gap rather than merely inflate the dataset.

Do not derive priority from issue age, reactions, comment count, or open/closed state. Those fields are unavailable to the inference contract and may reflect maintainer workflow rather than impact.

## Split and freeze procedure

1. Collect candidates and preserve the raw immutable export.
2. Remove pull requests returned by GitHub's Issues API.
3. Select diverse candidates without looking at any candidate-model predictions.
4. Annotate against `docs/triage_policy.md`.
5. Split once into calibration and test data.
6. Run `scripts/validate_dataset.py` to reject duplicate IDs and exact content leakage.
7. Review high-priority, security, and human-review-positive examples twice.
8. Rename `dataset_version` from `draft-v0` to `v1`, record the file hashes, and stop using the test set for prompt development.

The checked-in datasets currently use `draft-v0` and exist to exercise the pipeline. They are not yet a trustworthy 50-case golden dataset and must not be presented as final evidence.
