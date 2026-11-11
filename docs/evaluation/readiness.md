# Gate before final evaluation

Updated 2026-11-09. This is the gate for the broader reserved-set and participant
evaluation, not a declaration that the course deliverable requires every study
in that protocol. The application is integrated; its current adjustment runs and
academic delivery are being verified separately. This checklist does not declare
final-evaluation acceptance.

| Condition | Current evidence / action still required |
| --- | --- |
| Sources and references fixed | 60 adjustment and 60 reserved cases exist; verify hashes without unpacking final cases. Review semantic relevance and family separation independently where possible. |
| Integrated candidate | `ChatService` connects documentary answers, deterministic advice and web/API sessions. Review complete journeys with actual models and their saved responses; controlled-inference tests are separate evidence. |
| Candidate identity | Git now exists. The delivery starts from `424485a` with uncommitted changes; freeze and hash the actual source/configuration files. A starting commit alone does not identify this modified candidate. |
| Adjustment | Existing 18-case retrieval evidence is partial. Finish applicable adjustment journeys, answer review, error analysis and corrections before freezing. |
| Reference clock | The integrated demo explicitly replays the validated package clock and exposes it in responses/runtime notices. Use each case's declared clock for synthetic commerce and actual time for runtime observations; never silently renew expired records. |
| Performance budget | Existing architecture sets integrated p95 target 60 seconds/turn, generation 30 seconds warm / 90 seconds initial load, and initial executor RAM budget 8 GiB. Record actual hardware, process resources, warm state and concurrency; verify the integrated budget before utility testing. |
| Recording | Preserve actual multi-turn inputs/responses, versions, failures and timing. The integrated runner and its records are being added under `docs/evaluation/integrated/`; inspect capability scope and measured fields rather than assuming all final-protocol observations are covered. Never supply gold assistant history as executed system output. |
| Security scenarios | Implement isolated adversarial document clones and new manifest hashes; preserve legitimate reference mappings. Record session/store isolation and critical events. Existing fixture checks do not establish general security. |
| Human assessment | Apply the rubric and assertion/citation sheets to actual outputs. Declare review independence and unresolved disagreements. |
| Final access | Log date, responsible code, candidate, archive hash and purpose before opening. Access-driven changes invalidate independence of a repeated final evaluation. |
| Participants | Recruit volunteers, record acceptance, rehearse equivalent tasks, set task limits and counterbalance conditions under the protocol. No participant study has been run here. |
| Delivery | Connect each reported result to the inputs and candidate actually executed. Report source and rehearsal material are in `docs/reports/`; academic files are prepared under `outputs/previo3/`. Rendering and rehearsal do not constitute participant utility or reserved-set evaluation. |

Recheck current source and service behavior when starting this gate: documents from
other phases are snapshots. The reserved archive must remain closed while tuning.
For integrity only:

```powershell
.\.venv\Scripts\python.exe scripts/verify_reference_integrity.py
```

Session checks must include owner isolation, expiry and deletion. Ownership uses
a signed `HttpOnly`, `SameSite=Strict` cookie; context is stored only in one server
process with a configurable inactivity TTL, default 1800 seconds. The visible
transcript is not persisted by the interface. These controls do not replace an
independent review or establish universal security.
