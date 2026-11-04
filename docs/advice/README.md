# Phase 5: deterministic advice foundation

Implemented on 2026-11-04. Status: **in progress**. The module is independent of the
phase-4 RAG and the web implementation being developed in parallel. It does not
change HTTP contracts, source datasets, model configuration, or dependencies.

## Implemented behavior

The public boundary is [ragml.advice](../../src/ragml/advice.py):

- `Advisor.recommend(request, evaluated_at, variant_ids=None)` reads commerce
  through the existing `CommercialPort` on every call. `JsonCommercialAdapter`
  remains responsible for loading and validating local commercial data.
- A variant is eligible only when its price and stock have exact provenance,
  are current at the supplied aware timestamp, use the configured currency,
  and indicate availability. A price equal to the budget is allowed; zero is
  a valid price. No exchange rates, discounts, unit conversions, or alternative
  requirements are invented.
- `AttributeConstraint` supports exact equality and inclusive numeric minimum
  and maximum bounds. Attribute keys, units, types and choice values must match
  the selected category. Invalid structured requests raise `ValueError`.
- Mandatory unknown values fail eligibility. Product attributes are inherited,
  and an explicit variant attribute overrides its product value, including
  `None`. Category configuration defines attribute meaning; this module does
  not resolve contradictory documents.
- Preferences rank eligible variants by the number of distinct matching keys,
  then price ascending, then variant ID. They never override the budget,
  mandatory requirements, stock or commercial freshness.
- Each `CandidateDecision` preserves effective attribute evidence references,
  normalized current price and stock, the original lookup, and rejection
  reasons. Use `recommended_variant_ids` for ranked order; `decisions` follows
  catalog order or the explicitly supplied candidate order.
- Commercial citations identify source, revision, snapshot, variant, field and
  validity window. Recommendations cite only eligible variants. Raw lookups
  remain diagnostic data: render the decision's normalized `price` and `stock`,
  and never expose a historical value as a current confirmation.
- Duplicate or foreign commerce results, unexpected variants, mixed revisions,
  and lookup timestamps in the future raise `ValueError` rather than returning
  recommendations. Missing, unavailable or unverified records cannot support
  eligibility.
- `Advisor.compare(variant_ids, evaluated_at)` compares at least two distinct
  variants from one category. It preserves selection order, category units,
  attribute evidence and explicit unknown values. A missing attribute or current
  commercial field produces `incomplete`. Known out-of-stock values can still
  be compared; this does not make the variant eligible for recommendation.

`AdviceResult.status` distinguishes `recommended`, `no_matches` and
`clarification_required`. A budget in a different currency requires clarification.
`no_matches` does **not** prove that no product exists: inspect each decision's
issues and original lookup to distinguish unconfirmed commerce from a genuine
constraint mismatch. The conversation layer must map source unavailability to
the appropriate chat state without inventing an inventory or price confirmation.

## Conversation helpers and integration obligations

`resolve_presented_variant` resolves a one-based ordinal against the supplied
`SessionState.presented_variants`. It checks the expected session ID, store and
profile revision. Invalid ordinals, repeated IDs or removed selections return
`None`, requiring clarification. The session must first be loaded through an
owner-authorized `SessionRepository`; this pure helper does not authenticate
owners or persist sessions. It does not parse the phrase “the second one.”

`change_advice_category` returns a `CategoryTransition`. It preserves the budget
and constraints whose attribute key, label, type, unit and choice definition remain
compatible. Incompatible mandatory constraints and preferences are returned in
separate pending queues, rather than silently discarded. **The conversation
layer must resolve those queues before recommending from `transition.request`.**
No session or presented-product list is updated by this helper. On a category
change the integration must also clear the previous presented list.

Still pending before phase 5 can close:

1. Interpret Spanish requests into typed constraints, handle corrections and
   “a cheaper one,” and generate useful clarification questions.
2. Implement owner-scoped session persistence, expiry, and atomic context updates;
   connect the category-transition clarification gate and presented-product list.
3. Resolve attribute/document references against the exact active manifest, combine
   documentary and commercial claims, and integrate with the phase-4 orchestration.
   A nonempty attribute reference alone does not establish semantic support.
4. Wire the service into chat/web and verify complete multi-turn journeys, failures,
   ownership isolation and source updates. The helpers' software tests do not
   establish these integrated behaviors.
5. Measure quality using the designated adjustment partition. Final reserved cases
   and participant evaluation were not used in this implementation.

## Usage

From the project root in the existing Python environment:

```python
from datetime import UTC, datetime
from pathlib import Path

from ragml.advice import AdviceRequest, Advisor
from ragml.commercial import JsonCommercialAdapter
from ragml.contracts import CatalogDataset

catalog = CatalogDataset.model_validate_json(
    Path("data/sample/catalog.json").read_text(encoding="utf-8")
)
advisor = Advisor(catalog, JsonCommercialAdapter(Path("data/sample/commercial.json"), catalog))
request = AdviceRequest(category_id=catalog.profile.categories[0].category_id)
result = advisor.recommend(request, datetime.now(UTC))
print(result.model_dump_json(indent=2))
```

The demonstration snapshot expires according to its original timestamps. Using
wall-clock time will therefore usually yield no eligible recommendations. For an
explicit **simulated** replay of the existing fixture, pass
`datetime(2026, 11, 4, 12, 5, tzinfo=UTC)` instead. Do not substitute this timestamp
for the production clock or silently renew the snapshot.

## Observed verification

The new [software suite](../../tests/test_advice.py) has 40 passing tests. New
behaviors were developed with observed failing tests before implementation;
additional boundary and regression cases exercise the existing public behavior.
It uses synthetic fixtures and the real JSON adapter, with a supplied commerce
boundary for malformed or cached external results. No model is called.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_advice.py -q -p no:cacheprovider --basetemp .cache/phase5-pytest-check
.\.venv\Scripts\python.exe -m ruff check src/ragml/advice.py tests/test_advice.py --no-cache
.\.venv\Scripts\python.exe -m ruff format --check src/ragml/advice.py tests/test_advice.py
.\.venv\Scripts\python.exe -m mypy src --cache-dir .cache/phase5-mypy-check
```

The initial default pytest invocation failed with Windows access-denied errors
in cache/temporary directories inside the sandbox. The runner worked outside
that isolation, with cacheprovider disabled and a dedicated temporary directory;
the baseline then passed 57 tests before this implementation.

The full suite later passed **138 tests** during parallel development. Repository
lint and mypy passed, and the package built offline into `.cache/phase5-dist/`.
At that snapshot, the global format check reported one concurrently developed
phase-4 file, `src/ragml/rag_evaluation.py`; this implementation did not edit it.
Counts and global checks are snapshots of a shared working directory.

A separate execution used the actual demo catalog, commercial JSON and source
manifest at the explicit simulated timestamp above. All six categories produced
15 candidates and 11 eligible variants each: **90 assessed, 66 eligible, and 132
commercial citations resolved** through `ChatResponse.validate_evidence`.
Each category excluded one out-of-stock variant, two unconfirmed prices and one
unconfirmed stock value. At the observed wall-clock timestamp
`2026-11-04T18:10:21Z`, the first category correctly returned zero eligible variants.
These are software and fixture checks, not academic quality metrics, real store
validation or evidence of conversational usefulness.
