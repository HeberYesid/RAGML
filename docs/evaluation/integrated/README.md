# Integrated HTTP adjustment evaluation

This runner records the actual application over loopback HTTP. It sends only the
user turns from the existing adjustment set, keeps the session and cookie issued
by the server within each case, and starts a new identity for the next case. It
does not insert reference assistant answers or supply expected product IDs to the
application. The reserved final archive is never opened.

## Run

Start the project models and web application using the root README. Then use a
new output directory for each measurement:

```powershell
.\.venv\Scripts\python.exe -m ragml.integrated_evaluation --output-dir docs/evaluation/integrated/run-20261109-1 --base-url http://127.0.0.1:8000 --include-security-fixtures
```

Use repeated `--case-id DEV-001 --case-id DEV-055` options for a declared subset.
The default timeout is 240 seconds per HTTP operation; `--timeout-seconds` accepts
values from 1 to 600. The target must be an explicit IPv4 loopback HTTP URL with a
port. Credentials, remote hosts, redirects and environment proxy settings are
not used.

Without `--include-security-fixtures`, the four adversarial-document cases are
recorded as `not_run` with reason `isolated_source_fixture_required`. They remain
in the planned coverage denominator. Including the flag prepares each case in a
separate `fixtures/<case-id>/` directory: only synthetic data, source documents,
demo metadata and the model lock are copied. The untrusted text is appended to a
versioned source and indexed as its own additional fragment. Source and fragment
hashes are recomputed, and a separate SQLite index is built using the declared
embedding model. A temporary web server uses that clone on an automatically
assigned loopback port and is stopped after the case. The original source files,
active index and web server are not modified. The model provider is shared;
model loading order can therefore affect latency.

## Evidence

- `candidate.json` fingerprints the imported Python package, web resources,
  relevant locks, configured demo data and original source documents. It contains
  an allowlist of parameters, never the `.env` file, request cookies or secrets.
- `metadata.json` records the selected cases, endpoint, reference hash, candidate
  hash and observation clock. Reference commercial time and measurement time are
  distinct. Actual commercial-clock information remains in each server response.
- `initial-run.json` records the planned evaluation before the first request.
- `cases.jsonl` is flushed after each case and preserves every actual HTTP answer,
  partial sequence and execution error. It is append-only within the new run.
- `progress.jsonl` preserves an incremental summary after every case. An
  interruption still leaves the completed observations and progress records.
- `run.json` and `summary.json` use the existing validated evaluation contracts.
  Failed requests are errors, not successful responses. Unknown model warm state
  remains `unknown`; absent human ratings remain unknown.
- `mechanical-summary.json` reports coverage by task and category, expected status
  matches, returned-product membership in declared acceptable sets and literal
  documentary citation checks. It includes unexecuted fixture reasons.
- `completion.json` reports whether all selected cases were recorded and whether
  candidate file hashes still match after execution. A candidate that changed
  during measurement cannot support an exact-version conclusion.
- Each included security fixture has its own `fixture.json`, changed-source hash,
  changed-manifest hash, source version and index fingerprint. Its preparation
  time is kept separate from successful case HTTP latency.

Existing output directories are rejected before requests are made. Prior runs
must be retained rather than overwritten. Exit code `0` means all selected cases
executed without transport/application errors; `1` indicates execution or setup
errors; `2` indicates unexecuted planned cases. None of these codes declares
semantic acceptance. A status or product-membership mismatch remains visible in
the mechanical summary even when execution itself completed successfully.

## Interpretation and limits

Expected status agreement is not factual answer accuracy. Literal excerpts and
valid source identifiers establish textual provenance, not relevance or semantic
support. Returned products can identify an unsuitable item while explaining why
it was rejected, so simple set membership is not a task-resolution judgement.
The public chat API does not expose retrieval ranks; this runner therefore does
not invent a Recall@k measurement from emitted citations. No human ratings,
participant utility, deployment claim or final-set result is inferred.

An adversarial fragment's presence in the isolated index does not prove it entered
the model context. These fixture observations are narrow tests of the declared
inputs, not general security validation. Retain failed examples and review the
complete responses, sources, constraints and reference clock before drawing
conclusions.

Software tests replace only external model or HTTP boundaries. Their results
verify the recorder and isolation mechanism, not the quality of real inference.

## Interrupted measurements

An interruption may leave `cases.jsonl` and `progress.jsonl` without a completion
record. Preserve them. Select only unrecorded case IDs in a new directory using
repeated `--case-id` options; do not append observations to the interrupted run.
Before combining segments, verify identical candidate manifests, model/data and
parameter fingerprints, unique case IDs and complete coverage of the declared
set. Validate the combined `EvaluationRun` and identify every source segment and
its file hashes. Never manufacture a completion record for an interrupted run.
Report the execution as segmented, retain unknown warm states, and do not claim
an uninterrupted or controlled benchmark.

The 10 November delivery uses `run-20261110-2` and `run-20261110-3` as disjoint
segments. Its validated consolidation is `complete-20261110` when that directory
has been produced. `run-20261110-1` is a separate interrupted development run
before parser corrections and must not be pooled with the corrected candidate.
The 2048-token probe is also a separate configuration, not part of the main
4096-token measurement.
