# Gate before final evaluation

Status on 2026-11-04: **not ready for final evaluation**. This checklist organizes
pending evidence; it is not an automatic approval or a new evaluation protocol.

| Condition | Current evidence / action still required |
| --- | --- |
| Sources and references fixed | 60 adjustment and 60 reserved cases exist; verify hashes without unpacking final cases. Review semantic relevance and family separation independently where possible. |
| Integrated candidate | Documentary CLI, deterministic advice and web shell exist separately. The API still declares the conversational RAG unavailable. Connect and verify complete journeys first. |
| Candidate identity | Freeze an immutable source/configuration manifest and hash it. This workspace has no Git repository; do not invent a commit ID. |
| Adjustment | Existing 18-case retrieval evidence is partial. Finish applicable adjustment journeys, answer review, error analysis and corrections before freezing. |
| Reference clock | Use each case's declared clock for synthetic commercial replay, and wall clock for runtime observations. Never silently renew expired commerce. |
| Performance budget | Existing architecture sets integrated p95 target 60 seconds/turn, generation 30 seconds warm / 90 seconds initial load, and initial executor RAM budget 8 GiB. Record actual hardware, process resources, warm state and concurrency; verify the integrated budget before utility testing. |
| Recording | Use the new run schema; record stage times, retriever ranks/scores, actual prompts only when appropriate for synthetic evaluation, full responses/turns, source/model versions and available usage. Extend the runner for multi-turn sequences without supplying gold assistant history. |
| Security scenarios | Implement isolated adversarial document clones and new manifest hashes; preserve legitimate reference mappings. Record session/store isolation and critical events. Existing fixture checks do not establish general security. |
| Human assessment | Apply the rubric and assertion/citation sheets to actual outputs. Declare review independence and unresolved disagreements. |
| Final access | Log date, responsible code, candidate, archive hash and purpose before opening. Access-driven changes invalidate independence of a repeated final evaluation. |
| Participants | Recruit volunteers, record acceptance, rehearse equivalent tasks, set task limits and counterbalance conditions under the protocol. No participant study has been run here. |
| Delivery | Reproduce procedures against the frozen package and connect every result to its input hashes. Finish manuals, results, conclusions and the progress report only after the required work. |

Recheck current source and service behavior when starting this gate: documents from
other phases are snapshots. The reserved archive must remain closed while tuning.
For integrity only:

```powershell
.\.venv\Scripts\python.exe scripts/verify_reference_integrity.py
```
