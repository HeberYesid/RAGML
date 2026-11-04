# Project continuity

## 2026-11-04 — phases 7 and 8 preparation

- `src/ragml/evaluation.py` provides offline adjustment metrics, validated JSON
  records and human-review linkage without changing the assistant API. Current
  instructions require TDD; older phase-2 documents describe historical non-TDD work.
- `docs/evaluation/README.md` and `docs/delivery/README.md` own the current
  preparation status. See `docs/delivery/verification.json` for observed checks;
  rerun them before relying on results after changes.
- The 18-case phase-4 retrieval report was reorganized, not rerun. Its historical
  candidate fingerprint and warm state are unknown. No reserved archive contents
  were opened and no human ratings or participant results were generated.
- Pending: integrated conversation, full adjustment, frozen candidate, actual
  final evaluation/participants, rehearsed final manuals and completion report.
- The workspace has no Git repository; no commit, publication or deployment was
  authorized or performed for this task. The root README changed concurrently;
  this phase did not edit it or the shared phase-2 through phase-6 source files.
