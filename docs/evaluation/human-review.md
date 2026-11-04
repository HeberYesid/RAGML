# Human review instructions

Status: prepared, not applied to final responses. Follow the
[protocol](../../plans/phase-1/evaluation-protocol.md) and use reviewer codes only.
The [review template](templates/human-review.json) is deliberately incomplete;
`null` placeholders must be filled before validation. It contains no real ratings.

1. Confirm run, case, source/model versions and reference clock. Inspect the actual
   saved response and intermediate turns, not a reference answer inserted as
   assistant history. Mark source/reference defects separately from system errors.
2. Enumerate all verifiable emitted claims, including uncited claims. Preserve an
   annotation sheet with claim text, correctness, support, evidence location,
   source version and explanation. Count correct and supported claims against the
   same denominator. An abstention without factual claims has denominator zero.
3. Inspect every emitted citation against its associated assertion. Correct ID,
   location and extract are necessary structural checks; semantic support requires
   reading the source. A merely relevant citation is not automatically supporting.
4. For each commercial confirmation, inspect product, variant, currency, version
   and validity at the reference clock. Count all confirmations, including ones
   in free text. Historical documentation cannot confirm current stock or price.
5. Count recommendations explicitly presented as suitable and check every mandatory
   constraint. Unknown attributes are not confirmed compliance; preferences do not
   replace requirements. Explain the denominator and acceptable alternatives.
6. Score insufficiency behavior only where the reference calls for clarification,
   abstention or referral. Score resolution only for resolvable scenarios: 1/1 for
   completed without critical error, 0/1 otherwise. An execution failure on a
   resolvable case is unsuccessful in the analysis. Unresolvable cases are 0/0.
7. Apply all five qualitative rubric dimensions: product correctness, data
   accuracy, source sufficiency, constraint compliance and response adequacy.
   Use `meets`, `partial`, `fails` or `not_applicable`, with rationale. Do not
   translate `partial` into 0.5 automatically.
8. List every critical error explicitly. A critical error prevents task success.
   Review a second time where possible, preserve disagreements and decisions,
   and declare when only the developer acted as reviewer.

Use `null` for a count metric not yet reviewed; use `{numerator: 0, denominator: 0}`
for an assessed but inapplicable metric. Missing and inapplicable are distinct.
`evidence_references` should point to the annotation sheet and versioned evidence;
the record stores totals, not a substitute for that sheet.

Compute the response binding with the same public contract used by the recorder:

```python
from hashlib import sha256
from ragml.conversation import ChatResponse

response = ChatResponse.model_validate(response_payload)
response_sha256 = sha256(response.model_dump_json().encode("utf-8")).hexdigest()
```

This is a hash of the canonical response, not the run file. Review changes require
a new record and summary; never overwrite the original. Do not publish participant
text or recruit participants through the evaluation logger. The existing protocol
governs consent, coded sessions, withdrawal and retention.
