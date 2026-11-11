# Phase 8: delivery preparation

Updated 2026-11-10. Status: Previo 3 academic materials prepared and inspected. Chat, advice and
web are integrated in the current source. The academic report, exploratory data
analysis and presentation are available for the Previo 3 requirements.
Observed results must be read from their dated records; this status does not
declare the broader final evaluation or participant study complete.

The workspace is now a Git repository. The starting revision for this delivery
was `424485a`, with subsequent uncommitted work; that commit alone does not
identify the final candidate. Earlier records describing a workspace without Git
remain historical descriptions, not statements about the current directory.


## Verified academic delivery on 10 November

The report has 20 rendered and visually inspected pages; its editable DOCX and
matching PDF are in `outputs/previo3/`. The 14-slide presentation was rendered,
visually inspected, structurally validated and reimported with Artifact Tool.
Its literal dataset chart remains editable with an embedded workbook. It was
not opened in native PowerPoint. The rehearsal script and progress report are
also available. See `verification-20261110.json` for the software-check scope.

`docs/evaluation/integrated/complete-20261110/` consolidates two disclosed
segments of the same candidate: 60 cases completed, no execution errors,
50/60 expected-status matches and 38/38 applicable literal-citation checks.
These checks are not semantic accuracy. The observed per-turn p95 of about
184 seconds exceeds the design target. Broader final-set evaluation, human
review, participant utility and a real-store migration remain separate work.

## Evidence map

| Area | Owning material | What it establishes / remaining limit |
| --- | --- | --- |
| Scope and design | [Project plan](../../plans/001-plan-del-proyecto.md), [architecture](../architecture/README.md), [decisions](../architecture/decisions.md) | Agreed scope, technology and performance targets; no integrated acceptance implied. |
| Environment and models | [Local environment](../architecture/local-environment.md), [model instructions](../architecture/local-models.md), `config/*.lock.json` | Historical local setup and model checks. Clean installation on another machine remains unverified. |
| Contracts | [Contracts](../architecture/contracts.md), `docs/architecture/schemas/` | Data and HTTP boundaries; structural validation does not prove semantic answer quality. |
| Demo data and ingestion | [Data](../data/README.md), [ingestion](../data/ingestion.md), `docs/data/*.json` | Versioned synthetic data and ingestion evidence; no real commercial calibration. |
| Retrieval | [Phase 4](../evaluation/phase4/README.md), `docs/evaluation/phase4/*.json` | Documentary CLI and adjustment measurements; not the complete assistant. |
| Advice | [Advice guide](../advice/README.md), `src/ragml/chat.py` | Deterministic recommendation/comparison connected to conversation; quality requires actual run review. |
| Web | [Web guide](../web/README.md), `tests/test_chat_integration.py` | Integrated HTTP/web and controlled-inference journeys; model and browser evidence are separate. |
| Exploratory analysis | `docs/analysis/2026-11-09/` | Dataset statistics, source hashes, CSV and PNG/SVG figures; describes synthetic data rather than a real market. |
| Integrated runs | `docs/evaluation/integrated/` | New dated adjustment-run records when produced; inspect executed cases, failures and timing rather than infer success from the directory. |
| Academic material | `docs/reports/` | Report source, verified bibliography and a rehearsal script; presentation and report files need final rendering and inspection. |
| Evaluation | [Phase 7](../evaluation/README.md), [protocol](../../plans/phase-1/evaluation-protocol.md) | Metrics, schemas and rubric prepared; final results and utility study pending. |
| Historical software checks | [Verification snapshot](verification.json) | Commands, exit codes and output hashes recorded on 2026-11-04; rerun for the current candidate. |
| Historical file traceability | [Evidence inventory](evidence-inventory.json) | Selected-file hashes from that delivery-preparation snapshot; current changes can legitimately differ and require a new dated inventory. |

The inventory excludes `.env`, private data, participant records, model weights,
runtime databases, caches, academic originals and the reserved case payload. The
public partition manifest carries the archive hash; the integrity checker hashes
the archive without unpacking it. Inspect any future material before distribution.

## Delivery contents

Keep source/tests, package and dependency locks, configuration examples, demo
sources and their manifests, public evaluation protocol, selected run records,
verified procedures, limitations and verification evidence together. Provide a
source/configuration fingerprint for the frozen candidate even without Git.

The target academic files are
`outputs/previo3/Informe_Proyecto_RAGML.docx`,
`outputs/previo3/Informe_Proyecto_RAGML.pdf` and
`outputs/previo3/Sustentacion_RAGML.pptx`. Treat these as deliverables only after
they exist and have passed their respective render-and-inspect checks. The
rehearsal script is `docs/reports/guion-sustentacion.md`; preparing it does not
establish that a live defense or participant session has occurred.

Demo commerce uses the package's declared simulated clock and is labelled in
the interface. Model execution uses the actual local runtime. Session ownership
uses an opaque signed cookie; requirements remain in server memory with a
configurable inactivity TTL, and the visible transcript remains in browser-tab
memory. This is a local single-process prototype, not durable transcript storage.

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

1. Finish reviewing the current adjustment records, errors and browser/model
   observations. Integration is implemented; a quality or performance pass must
   be supported by the actual measurements.
2. Freeze the candidate, including uncommitted source/configuration hashes, and reproduce setup, operation, update/retirement and
   second-store journeys using that package. Verify failure and recovery paths.
3. Distinguish the contextual academic delivery from the broader project
   protocol. Final reserved-set evaluation, second-store portability and
   participant utility need their own observed work; preserve failed/incomplete
   task counts and explicitly report any study that has not been performed.
4. Complete user/operator manuals with observed steps, actual screenshots,
   results and known limits. Redact sensitive data and keep the final set reserved
   until its authorized evaluation stage.
5. Complete the report and presentation using only observed results, review
   their rendered files, and rehearse the demonstration. Broader uncompleted
   studies must remain limitations, not fabricated results or automatic blockers
   to documenting the contextualized application required by the course guide.
