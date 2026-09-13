# GitHub Issue Triage Evaluation Architecture

## High-level flow

    Public GitHub Issues
            |
            v
    Dataset Construction
            |
            v
    Calibration + Golden Datasets
            |
            v
    Evaluation Runner
            |
            v
    Google ADK Triage Agent
            |
            +---------------------+
            |                     |
            v                     v
      Gemini Models         Groq GPT-OSS Models
            |                     |
            +----------+----------+
                       |
                       v
               Triage Decision
                       |
                       v
              Evaluation Metrics
                       |
                       v
             Experiment Artifacts
                       |
             +---------+---------+
             |                   |
             v                   v
      Paired Comparison    Arize Phoenix
             |
             v
       Promotion Decision

---

## 1. Dataset construction

    Public python/pythondotorg issues
                    |
                    v
          GitHub issue fetcher
                    |
                    v
           Raw candidate issues
                    |
          +---------+---------+
          |                   |
          v                   v
    Selected real       Synthetic challenge
       issues                 cases
          |                   |
          +---------+---------+
                    |
                    v
        Triage policy and annotation
                    |
                    v
           Human review and freeze
                    |
          +---------+---------+
          |                   |
          v                   v
    Calibration set       Golden test set
       15 cases              35 cases

The final dataset contains:

- 40 selected real GitHub issues
- 10 synthetic challenge cases
- 15 calibration cases
- 35 held-out golden-test cases

The calibration set is used for prompt development. The golden set is used for final evaluation.

---

## 2. Triage inference

    CLI or ADK Web
           |
           v
    IssueInput
    - title
    - body
           |
           v
    TriageService
    - Creates an isolated session
    - Measures latency
    - Captures token usage
           |
           v
    Tool-free Google ADK LlmAgent
           |
     +-----+------+
     |            |
     v            v
    Prompt       Model
    v1-v5        Gemini or Groq
     |            |
     +-----+------+
           |
           v
    TriageDecision
    - issue_type
    - priority
    - needs_human_review

The model receives only the issue title and body. Gold labels, GitHub labels, annotation reasons, and dataset slices are not included in the inference input.

---

## 3. Evaluation harness

    Calibration or Golden Dataset
                 |
                 v
         Evaluation Runner
         - Sequential execution
         - Request pacing
         - Retry handling
                 |
                 v
          TriageService
                 |
                 v
         PredictionRecord
         - Case ID
         - Gold decision
         - Model prediction
         - Dataset slices
         - Latency
         - Token usage
         - Estimated cost
         - Error, if any
                 |
                 v
        Deterministic Metrics
        - Exact-match accuracy
        - Per-field macro-F1
        - Human-review false negatives
        - High-priority downgrades
        - Critical under-triage
        - Mean and p95 latency
        - Cost per 1,000 issues
                 |
                 v
         Experiment Artifacts

Each completed experiment creates:

- `config.json`
- `predictions.jsonl`
- `metrics.json`
- `report.md`

---

## 4. Experiment comparison

    Baseline experiment
             |
             +-------------------+
                                 |
                                 v
                         Paired comparison
                                 ^
                                 |
             +-------------------+
             |
    Candidate experiment

The comparison calculates:

- Exact-match accuracy difference
- Paired bootstrap 95% confidence interval
- Prediction agreement
- Per-field agreement
- Cost multiplier
- Safety-gate result

The candidate is promoted only when:

1. Its accuracy improvement is statistically clear.
2. Human-review false negatives do not increase.
3. High-priority downgrades do not increase.
4. Critical under-triage does not increase.
5. Provider errors do not increase.

---

## 5. Optional Arize Phoenix observability

    Live Triage Requests
             |
             v
    OpenTelemetry Instrumentation
             |
             v
        Arize Phoenix
        - Model traces
        - Dataset registration
        - Prompt registration
        - Row-level inspection
        - Deterministic annotations

Saved experiment results can also be replayed:

    Existing Prediction Artifacts
                 |
                 v
          Phoenix Replay
          No new model calls
                 |
                 v
            Arize Phoenix

Phoenix is used for debugging and trace exploration. Checked-in experiment artifacts remain the authoritative source for evaluation and promotion decisions.

---

## Final decision flow

    Candidate configuration
              |
              v
    Did accuracy clearly improve?
          /             \
        No               Yes
        |                 |
        v                 v
      Reject       Did safety regress?
                       /       \
                     Yes        No
                      |          |
                      v          v
                    Reject    Retain as
                              assisted-triage
                              candidate

No evaluated configuration is approved for autonomous routing. The selected baseline is intended to assist maintainers, with humans retaining control over operational decisions.