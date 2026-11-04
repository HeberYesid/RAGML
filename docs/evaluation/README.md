# Phase 7: evaluation preparation

Updated 2026-11-04. Status: **in progress**. This is an executable preparation
package, not the final evaluation, a participant study, or the academic progress
report. The authoritative definitions and targets remain in the
[evaluation protocol](../../plans/phase-1/evaluation-protocol.md).

## Available now

- [Metrics and JSON records](../../src/ragml/evaluation.py), independent of the
  assistant API. The existing phase-4 `recall_at_k` function is reused.
- [Worked software examples](../../tests/test_evaluation.py): duplicate retrievals,
  execution errors, empty denominators, coverage, warm-state latency, human
  annotations, historical provenance and preservation of saved evidence.
- [Run schema](schemas/EvaluationRun.schema.json), generated from `EvaluationRun`.
  Runtime validation also enforces cross-field rules beyond JSON Schema.
- [Human review instructions](human-review.md), with an unfilled review template.
- [Final-evaluation readiness gate](readiness.md).
- [Run records and summaries](runs/README.md), separated from final results.

There is no new quality dataset. Use the existing 60 adjustment cases, while
keeping the 60 final cases reserved. Neither the reserved archive nor its case
generator is needed by the metrics module. Participant conversations are outside
this module's scope; there are no prompt, participant-name or contact fields.
Saved synthetic responses still need inspection before sharing.

## Record and calculate

`EvaluationRun` groups a single system and candidate with artifact hashes,
versions, configuration, environment, concurrency and planned case count.
`CaseResult` records family/category/task, reference clock, execution outcome,
retrieved and reference chunk IDs, timing stages, explicit model warm state,
optional available usage, optional `ChatResponse` and optional human review.
The response preserves its citations and source versions. Usage is `null` when
unavailable, rather than an invented zero cost.

New runs should fingerprint a frozen source manifest in `candidate_sha256` and
record that manifest among `artifacts`, together with references, sources, model
lock, data and configuration hashes. Do not include secrets. A hash of one file
does not identify an entire candidate. Historical measurements without a recorded
code fingerprint use `candidate_sha256: null` and
`candidate_provenance: unknown_historical_candidate`; the current code hash must
not be attributed retroactively to an earlier execution.

`write_run(run, destination)` creates a validated JSON file exclusively.
`read_run(path)` validates it again. Neither replaces an existing file. Use a new
run ID and path for every execution, reannotation and summary. Keep the previous
artifacts to preserve traceability. These are local files, not tamper-proof audit
storage or a concurrent multi-process logging service.

From the project root:

```powershell
.\.venv\Scripts\python.exe -m ragml.evaluation summarize --input docs/evaluation/runs/phase4-adjustment-import-20261104.json --output .cache/phase78/recomputed-summary.json
```

The command is offline and does not call a model. It rejects final partitions,
unknown fields, duplicate case IDs, impossible counts, nonfinite/negative timing,
timezone-free clocks and inconsistent execution statuses. It fails if the output
already exists. Its error output includes the error class, not the input content.
An HTTP `temporarily_unavailable` result must be recorded as `execution: error`
with an error code and no successful response status.

## Metric interpretation

| Measure | Calculation and limits |
| --- | --- |
| Recall@k | Macro mean of unique positive reference IDs found within the first k retrieved positions. Duplicates occupy ranks but do not increase the numerator. Cases without positive references are not applicable. Applicable failed queries contribute zero, even if partial hits were saved. |
| Coverage | Planned, attempted, completed, errors, not run and human-reviewed counts. A completed retrieval is not a resolved user task. |
| Human metrics | Sum of reviewed numerators divided by sum of reviewed denominators, with assessed/applicable case counts. A missing review is unknown; a zero denominator produces `null`. No correctness is inferred from citation structure or status. |
| Latency | Median and nearest-rank p95 of recorded total duration, including failed attempts. Cold, warm and unknown samples remain separate. Stage durations are retained in the run. No warm state is inferred from a fast response. |
| Critical errors | Event and affected-case counts from human annotations, with review coverage. Zero annotations without reviews is not evidence of safety. |
| Task/category breakdown | The same measurements for recorded cases. Subgroup planned counts describe recorded membership only; missing cases cannot be assigned to an unknown group. |

The seven human count metrics are factual correctness, evidence support, citation
fidelity, commercial identity, mandatory constraints, insufficiency handling and
task resolution. Partial rubric labels are qualitative; they never become an
automatic half point. Reviewers must include all verifiable assertions, including
uncited assertions in free text. Citation fidelity counts all emitted citations.
Human labels bind to the canonical saved response SHA256; changing that response
invalidates the review. This checks linkage, not the truth of a review.

Targets are not automatically declared passed. Review coverage, failed tasks,
critical errors and capability scope must be examined before any acceptance
decision. Correct abstention can pass insufficiency handling while failing to
resolve a task that was actually resolvable. Report execution errors for resolvable
tasks as unsuccessful in the final analysis, never silently exclude them from
its denominator. The current module reports reviewed resolution counts alongside
execution coverage; it does not infer resolvability or impute missing labels.

## Remaining work

An integrated multi-turn runner, adversarial source cloning/versioning, blinded
reference review, final candidate freeze and final-set execution remain pending.
The current importer record only reorganizes an existing retrieval measurement;
it is not a new model run. Retrieval rank IDs are available there; original hit
scores, hardware inventory, warm state and the historical source fingerprint
were not recorded and must remain unknown.

Do not merge different systems, model versions, reference sets or capability
scopes into one score. Compare documentary tasks shared by both systems separately
from tasks requiring commerce. Utility, participant timing and opinions require
the actual protocol with volunteers and cannot be produced by software fixtures.
