# Adjustment evidence registry

This directory contains run records and summaries, not final evaluation results.

| Artifact | Origin and interpretation |
| --- | --- |
| `phase4-adjustment-import-20261104.json` | Re-encodes the existing phase-4 retrieval report for 18 documentary/policy adjustment cases. No new model execution. Candidate code fingerprint and hardware remain unknown. |
| `phase4-adjustment-summary-20261104.json` | Recomputed metrics from that imported record using the phase-7 calculator. No human correctness, citation-fidelity or utility ratings. |

The original [phase-4 report](../phase4/adjustment-retrieval.json) remains unchanged.
Each imported case is joined to adjustment metadata by ID; the reference file hash
must match the report before joining. Only IDs, reference/retrieved fragments and
measured timing are imported. No final archive is opened and no human labels are
generated. The source report hash is recorded in the run's `artifacts`.

For a new run use a different filename, retain versions/hashes and inspect scope
and coverage. Do not call these 18 cases the full 60-case adjustment or 120-case
quality evaluation. A summary file is derived data; the run and source report
are necessary to interpret and reproduce it.
