# Confusion Matrix and Human-Review Macro-F1

The human-review confusion matrix uses gold labels as the outer keys and model predictions as the inner keys:

```json
"human_review": {
  "False": {
    "False": 10,
    "True": 7
  },
  "True": {
    "False": 2,
    "True": 16
  }
}
```

In table form:

| Gold label | Predicted `False` | Predicted `True` |
|---|---:|---:|
| `False` | 10 | 7 |
| `True` | 2 | 16 |

## F1 for `True`

When `True` means that human review is required:

- True positives: 16
- False positives: 7
- False negatives: 2

```text
F1(True) = 2TP / (2TP + FP + FN)
         = 32 / (32 + 7 + 2)
         = 32 / 41
         = 0.7805
```

## F1 for `False`

Macro-F1 also treats `False` as the positive class. The original true negatives therefore become true positives for this calculation:

- True positives for `False`: 10
- False positives for `False`: 2
- False negatives for `False`: 7

```text
F1(False) = 2TP / (2TP + FP + FN)
          = 20 / (20 + 2 + 7)
          = 20 / 29
          = 0.6897
```

## Human-review macro-F1

The two class-level F1 scores receive equal weight:

```text
Macro-F1 = (F1(True) + F1(False)) / 2
         = (0.7805 + 0.6897) / 2
         = 0.7351
```

The full-precision value produced by the evaluation harness is `0.735071488645921`.

True negatives do not appear directly in the F1 formula for `True` because that score measures how well required reviews were identified. They are still represented in macro-F1 because they become true positives when the `False` class is scored.

The harness calculates macro-F1 from successful predictions. Model-call failures remain failures for exact-match accuracy and count as human-review false negatives when the gold label requires review, but they do not appear in the confusion matrix.