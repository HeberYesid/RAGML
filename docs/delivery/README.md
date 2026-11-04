# Phase 8: delivery preparation

Updated 2026-11-04. Status: **in progress**. This directory organizes evidence and
procedures that can be prepared before final integration. It is not a final user
manual, a final results report, or the academic progress report. Those deliverables
remain pending until the prototype and evaluation are completed.

## Evidence map

| Area | Owning material | What it establishes / remaining limit |
| --- | --- | --- |
| Scope and design | [Project plan](../../plans/001-plan-del-proyecto.md), [architecture](../architecture/README.md), [decisions](../architecture/decisions.md) | Agreed scope, technology and performance targets; no integrated acceptance implied. |
| Environment and models | [Local environment](../architecture/local-environment.md), [model instructions](../architecture/local-models.md), `config/*.lock.json` | Historical local setup and model checks. Clean installation on another machine remains unverified. |
| Contracts | [Contracts](../architecture/contracts.md), `docs/architecture/schemas/` | Data and HTTP boundaries; structural validation does not prove semantic answer quality. |
| Demo data and ingestion | [Data](../data/README.md), [ingestion](../data/ingestion.md), `docs/data/*.json` | Versioned synthetic data and ingestion evidence; no real commercial calibration. |
| Retrieval | [Phase 4](../evaluation/phase4/README.md), `docs/evaluation/phase4/*.json` | Documentary CLI and adjustment measurements; not the complete assistant. |
| Advice | [Phase 5](../advice/README.md) | Deterministic recommendation/comparison helpers; conversation integration pending. |
| Web | [Phase 6](../web/README.md) | Interface and controlled-state checks; real chat integration pending. |
| Evaluation | [Phase 7](../evaluation/README.md), [protocol](../../plans/phase-1/evaluation-protocol.md) | Metrics, schemas and rubric prepared; final results and utility study pending. |
| Current software checks | [Verification snapshot](verification.json) | Commands, observed exit codes and output hashes for this workspace snapshot. Does not replace runtime/visual or participant evaluation. |
| File traceability | [Evidence inventory](evidence-inventory.json) | Relative paths, sizes and SHA256 of selected deliverable files. Not a signed archive or evidence that every procedure passed. |

The inventory excludes `.env`, private data, participant records, model weights,
runtime databases, caches, academic originals and the reserved case payload. The
public partition manifest carries the archive hash; the integrity checker hashes
the archive without unpacking it. Inspect any future material before distribution.

## Delivery contents to consolidate later

Keep source/tests, package and dependency locks, configuration examples, demo
sources and their manifests, public evaluation protocol, selected run records,
verified procedures, limitations and verification evidence together. Provide a
source/configuration fingerprint for the frozen candidate even without Git.

Organize the eventual results by adjustment, final technical evaluation and
participant utility. Do not pool software tests or imported retrieval cases into
the 120 quality scenarios. Record which evidence was produced with synthetic
transports, actual local models or actual browser sessions.

The [procedures register](procedures.md) identifies evidence and pending checks.
Use new dated filenames for reruns and retain the prior records. The inventory
deliberately excludes itself to avoid a self-referential hash.

## Verify the selected evidence files

From the project root, the following read-only PowerShell check compares the
inventory against the current workspace:

```powershell
$deliveryInventory = Get-Content docs/delivery/evidence-inventory.json -Raw | ConvertFrom-Json
$deliveryMismatches = @($deliveryInventory.files | Where-Object {
    -not (Test-Path -LiteralPath $_.path -PathType Leaf) -or
    (Get-FileHash -LiteralPath $_.path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $_.sha256
})
if ($deliveryMismatches.Count -gt 0) { throw 'Delivery evidence differs from the recorded snapshot.' }
```

A mismatch requires investigation or a new dated inventory; never rewrite an old
measurement to make it match updated code. A matching hash proves identity only.

## Remaining before final handoff

1. Finish real RAG/advice/web integration and complete the adjustment journeys.
2. Freeze the candidate and reproduce setup, operation, update/retirement and
   second-store journeys using that package. Verify failure and recovery paths.
3. Apply final technical evaluation and the participant protocol, or explicitly
   report the missing study. Preserve all failed/incomplete task counts.
4. Complete user/operator manuals with observed steps, actual screenshots,
   results and known limits. Redact sensitive data and keep the final set reserved
   until its authorized evaluation stage.
5. Prepare the academic progress report at project completion, with conclusions
   limited to the evidence actually obtained. No final report is fabricated here.
