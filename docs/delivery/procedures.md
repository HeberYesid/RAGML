# Procedure register

Updated 2026-11-09. Current procedures reflect the integrated source; observations
dated 2026-11-04 remain historical. Evidence status applies only to the scope
described, not to final acceptance. Follow each owning guide for its configuration
and constraints. Never stop another chat's shared model process.

| Procedure | Existing instructions / evidence | Status and remaining observation |
| --- | --- | --- |
| Install environment and models | [Environment](../architecture/local-environment.md), [models](../architecture/local-models.md) | Historical installation checked. No clean-machine installation performed in this phase. |
| Configure store and paths | `.env.example`, [contracts](../architecture/contracts.md) | Configuration contracts tested. Real-store adaptation needs authorized data and an actual end-to-end rehearsal. |
| Start local API | `ragml serve`, architecture guide | Integrated API exists; `/ready` checks corpus, commerce and models, while `/health` has a narrower health/publication check. |
| Start web | [Web guide](../web/README.md): `python -m ragml.web` | Interface has historical browser evidence. Re-run against the final integrated candidate. |
| Query documentary CLI | [Phase 4](../evaluation/phase4/README.md): `python -m ragml.rag_cli` | Historical real model probes and retrieved evidence exist; not a multi-turn commercial assistant. |
| Diagnose unavailable service | Check configured paths, model process and `/ready`; preserve the user's input | A 503 `rag_not_ready` means preparation failed in this installation. The chat integration exists; validate catalog, active index and models rather than treating the error as a missing feature. |
| Use demo commerce | Inspect `GET /v1/web/runtime` and the visible notice | `ChatService` validates package identity and replays its explicit simulated clock. A real-clock adapter call can correctly find the same snapshot expired. |
| Start a new conversation | Web action and `DELETE /v1/chat/sessions/{session_id}` | The client discards context and requests deletion of its owner-scoped server session. A failed request leaves expiration as the fallback; the cookie contains ownership, not a transcript. |
| Import/update documents | [Ingestion](../data/ingestion.md) | Publish a new revision with matching hashes/extracts, then ingest. Historical real ingestion and synthetic failure/rollback tests exist. Final operator rehearsal pending. |
| Retire a source | Ingestion guide | Remove/inactivate source and its chunks, repair references, publish a new revision. Synthetic software coverage exists; full assistant retirement rehearsal pending. |
| Update price/stock | Ingestion and advice guides | Update commercial revision/validity, not document authority. Use a declared synthetic reference clock only for replay. Final operator rehearsal pending. |
| Change store | Protocol and ingestion/advice tests | Component isolation has coverage. Full application substitution without core changes remains pending. |
| Verify reserved-set integrity | `python scripts/verify_reference_integrity.py` | Rechecked in the phase-7/8 verification snapshot without unpacking final cases. |
| Record adjustment evidence | `EvaluationRun`, `write_run`, [phase-7 guide](../evaluation/README.md), `ragml.integrated_evaluation` | The integrated runner is being added for this delivery. Keep actual dated outputs under `docs/evaluation/integrated/`; executable availability does not establish a passed run. |
| Explore the dataset | `ragml.analysis`, `docs/analysis/2026-11-09/` | Statistics, figures and CSV retain source hashes and the declared commercial clock. Inspect unknown values and outliers without inventing replacements. |
| Recompute adjustment metrics | Command below | Executed offline against the imported 18-case historical retrieval record. No new inference or human rating. |
| Human review | [Rubric instructions](../evaluation/human-review.md) | Prepared only; apply to actual outputs and evidence sheets. |
| Final evaluation and utility | [Readiness gate](../evaluation/readiness.md), protocol | Pending frozen integrated candidate, reviewers and actual volunteers. |
| Verify/package software | Commands below and verification snapshot | Workspace checks and offline package build, not clean install or final acceptance. |
| Deliver report and slides | [Delivery checklist](README.md), `docs/reports/` | Consolidation and visual verification in progress. Target files are in `outputs/previo3/`; preparation is distinct from a completed live defense. |

## Historical commands checked on 2026-11-04

Run from the project root in PowerShell. The dedicated temp/cache directories
avoid unrelated cache paths. On this Windows host pytest required execution
outside the filesystem isolation because its temporary-directory access failed;
no filesystem permissions or assertions were weakened.

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp .cache/phase78-final-tests
.\.venv\Scripts\python.exe -m ruff check src tests --no-cache
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m mypy src --cache-dir .cache/phase78-final-mypy
node --test --test-isolation=none tests/web/chat-client.test.mjs
uv build --no-sources --offline --cache-dir .cache/uv --out-dir .cache/phase78-dist
.\.venv\Scripts\python.exe scripts/verify_reference_integrity.py
.\.venv\Scripts\python.exe -m ragml.evaluation summarize --input docs/evaluation/runs/phase4-adjustment-import-20261104.json --output .cache/phase78/recomputed-summary.json
```

An existing summary path is intentionally rejected: use a fresh path for another
run. Node checks existing client behavior; it is not a frontend runtime requirement.
The package build uses already cached dependencies and does not download models.

Read the actual [verification snapshot](verification.json) for outcomes, failure
details and limits. Commands listed here must not be assumed to have passed on a
different candidate or environment. No visual/browser check, sustained load test,
fresh model inference, participant session or deployment was run for that historical phase.

## Current verification and candidate identity

Use the [test guide](../../tests/README.md) for the current complete suite. Preserve
new results with their date and source/configuration hashes rather than editing
`verification.json` or earlier measurements. Git exists now: `424485a` is the
starting revision for this delivery, with uncommitted changes in progress.
Fingerprint the files actually executed when identifying a frozen candidate.

The integrated run command and data-analysis command expose their current
arguments through `python -m ragml.integrated_evaluation --help` and
`python -m ragml.analysis --help`. Run from the project root and use a new dated
output destination. Do not replace unknown or failed metrics with values from a
previous candidate.

Final reserved-set evaluation and volunteer utility remain separate procedures
under the broader protocol. The course defense must demonstrate the application
and explain its observed results and limits; it does not authorize fabrication
of those broader studies or their completion status.
