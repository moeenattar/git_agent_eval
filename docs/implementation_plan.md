# Implementation Plan

The project answers one central question: when the prompt or model changes, did triage quality improve enough to justify its operational cost without worsening safety-sensitive errors?

## Milestone 1 Baseline foundation

Status: implemented

- Define the three-field structured contract.
- Write the annotation rubric before model tuning.
- Implement one tool-free Google ADK agent.
- Build dataset collection and validation tools.
- Implement deterministic metrics and normalized cost accounting.
- Produce reproducible file artifacts and optional Phoenix traces.
- Test all deterministic logic without credentials.

## Milestone 2 Trustworthy dataset

Status: complete — dataset `v1` frozen on 2026-09-05

- [x] Fetch open and closed `python/pythondotorg` issues.
- [x] Select 40 diverse real cases.
- [x] Write 10 synthetic cases for explicit coverage gaps.
- [x] Split 15 calibration and 35 golden test cases.
- [x] Independently review all 12 high-priority cases, covering 24% and every security case.
- [x] Approve the security-priority rule and freeze dataset version `v1`.

## Milestone 3 Baseline experiment

Status: complete — selected prompt tested on 2026-09-05

- [x] Run prompt v1 with the cost-oriented `gemini-3.5-flash-lite` model.
- [x] Capture predictions, token usage, latency, and normalized list-price cost in file artifacts.
- [x] Inspect calibration failures only and write `triage_v2.txt` from general policy improvements.
- [x] Select v2 using the paired calibration comparison and safety gates.
- [x] Keep the golden split unseen during prompt iteration, then run the selected candidate once.

Phoenix remained optional and was not required for the authoritative experiment artifacts.

## Milestone 4 Cost and quality comparison

Status: complete — evaluated and decided on 2026-09-05

- [x] Compare prompt v1 and v2 while holding Gemini 3.5 Flash-Lite fixed.
- [x] Compare Groq GPT-OSS 20B and 120B with Gemini while holding prompt v2 fixed.
- [x] Repeat GPT-OSS 120B to measure exact and per-field decision stability.
- [x] Use paired bootstrap differences on identical frozen test cases.
- [x] Reject both Groq candidates because human-review false negatives increased.

Decision: retain Gemini 3.5 Flash-Lite with prompt v2 as the assisted baseline. None of the evaluated configurations is approved for unsupervised routing.

## Milestone 5 Submission

Status: next

- Add actual results and failure analysis to the README.
- Document model IDs, prices and retrieval dates, dataset hashes, prompt hashes, and git commits.
- Make the repository public only after checking history for secrets and private data.
- Link the planning conversation or export in the reasoning trail if appropriate.

## Deliberately deferred

No frontend, RAG, vector database, GitHub write access, multi-agent orchestration, or managed deployment is planned. None improves the evidence required by the exercise at this stage.
