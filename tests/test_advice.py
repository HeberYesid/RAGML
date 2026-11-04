"""Public phase-5 advice behavior with synthetic data and a real JSON adapter."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from ragml.advice import (
    AdviceRequest,
    Advisor,
    AttributeConstraint,
    change_advice_category,
    resolve_presented_variant,
)
from ragml.commercial import CommercialLookup, JsonCommercialAdapter
from ragml.contracts import (
    AttributeDefinition,
    AttributeValue,
    CatalogDataset,
    Category,
    CommercialDataset,
    CommercialSnapshot,
    Money,
    Observation,
    Product,
    Stock,
    StoreProfile,
    Variant,
)
from ragml.conversation import SessionState

NOW = datetime(2026, 11, 4, 15, tzinfo=UTC)


def catalog() -> CatalogDataset:
    return CatalogDataset(
        profile=StoreProfile(
            store_id="test-store",
            display_name="Synthetic store",
            data_mode="demo",
            locale="es-CO",
            currency="COP",
            currency_decimal_places=2,
            revision="profile-1",
            categories=(
                Category(
                    category_id="chairs",
                    name="Chairs",
                    attribute_definitions=(
                        AttributeDefinition(
                            key="width",
                            label="Width",
                            value_type="number",
                            unit="cm",
                            required_for_comparison=True,
                        ),
                        AttributeDefinition(key="color", label="Color", value_type="text"),
                    ),
                ),
            ),
        ),
        products=(
            Product(
                store_id="test-store",
                product_id="chair",
                category_id="chairs",
                name="Chair",
                revision="catalog-1",
                attributes=(
                    AttributeValue(key="width", value=50, unit="cm", evidence_refs=("doc-width",)),
                ),
            ),
        ),
        variants=tuple(
            Variant(
                store_id="test-store",
                variant_id=key,
                product_id="chair",
                name=key,
                revision="catalog-1",
                attributes=(
                    AttributeValue(key="color", value=color, evidence_refs=("doc-color",)),
                ),
            )
            for key, color in (("red", "red"), ("blue", "blue"), ("green", "green"))
        ),
    )


def write_commercial(
    path: Path, amounts: tuple[str | None, ...] = ("100.00", "100.01", "90")
) -> None:
    dataset = CommercialDataset(
        store_id="test-store",
        data_mode="demo",
        revision="commercial-1",
        snapshots=tuple(
            CommercialSnapshot(
                store_id="test-store",
                variant_id=variant,
                snapshot_id=f"snapshot-{variant}",
                source_id="commercial-source",
                revision="commercial-1",
                price=Observation[Money](
                    value=Money(amount=amount, currency="COP") if amount is not None else None,
                    source_updated_at=NOW - timedelta(minutes=5),
                    expires_at=NOW + timedelta(minutes=5),
                    source_ref=f"price-{variant}",
                ),
                stock=Observation[Stock](
                    value=Stock(availability="in_stock", quantity=2),
                    source_updated_at=NOW - timedelta(minutes=5),
                    expires_at=NOW + timedelta(minutes=5),
                    source_ref=f"stock-{variant}",
                ),
            )
            for variant, amount in zip(("red", "blue", "green"), amounts, strict=True)
        ),
    )
    path.write_text(dataset.model_dump_json(), encoding="utf-8")


def test_recommendations_respect_exact_decimal_budget_and_retain_commercial_evidence(
    tmp_path: Path,
) -> None:
    path = tmp_path / "commercial.json"
    write_commercial(path)
    data = catalog()
    result = Advisor(data, JsonCommercialAdapter(path, data)).recommend(
        AdviceRequest(category_id="chairs", budget=Money(amount="100.00", currency="COP")), NOW
    )
    assert result.status == "recommended"
    assert result.recommended_variant_ids == ("green", "red")
    assert result.decisions[1].issues[0].code == "over_budget"
    assert result.decisions[0].price == Money(amount="100.00", currency="COP")
    assert {(c.variant_id, c.field) for c in result.citations} == {
        ("red", "price"),
        ("red", "stock"),
        ("green", "price"),
        ("green", "stock"),
    }
    assert all(c.source_version == "commercial-1" for c in result.citations)


class SuppliedCommerce:
    """External commerce boundary supplying already-observed values."""

    def __init__(self, lookups: tuple[CommercialLookup, ...]) -> None:
        self.lookups = lookups

    def lookup(
        self, store_id: str, variant_ids: tuple[str, ...], evaluated_at: datetime
    ) -> tuple[CommercialLookup, ...]:
        return self.lookups


@pytest.mark.parametrize("offset", [-6, 5])
def test_previously_fresh_commerce_cannot_be_used_outside_its_validity_window(
    tmp_path: Path, offset: int
) -> None:
    path = tmp_path / "commercial.json"
    write_commercial(path)
    data = catalog()
    lookups = JsonCommercialAdapter(path, data).lookup("test-store", ("red", "blue", "green"), NOW)
    # Isolate observation windows from the separately tested future-lookup guard.
    lookups = tuple(
        CommercialLookup.model_validate(
            {
                **item.model_dump(),
                "checked_at": NOW - timedelta(minutes=10),
            }
        )
        for item in lookups
    )
    result = Advisor(data, SuppliedCommerce(lookups)).recommend(
        AdviceRequest(category_id="chairs"), NOW + timedelta(minutes=offset)
    )
    assert result.status == "no_matches"
    assert result.recommended_variant_ids == ()
    assert result.citations == ()
    assert all(d.price is None and d.stock is None for d in result.decisions)


def test_mandatory_requirements_use_inherited_attributes_and_exact_variant(tmp_path: Path) -> None:
    path = tmp_path / "commercial.json"
    write_commercial(path)
    data = catalog()
    result = Advisor(data, JsonCommercialAdapter(path, data)).recommend(
        AdviceRequest(
            category_id="chairs",
            mandatory=(
                AttributeConstraint(key="width", operator="min", value=50, unit="cm"),
                AttributeConstraint(key="color", value="red"),
            ),
        ),
        NOW,
    )
    assert result.recommended_variant_ids == ("red",)
    assert [
        (d.variant_id, [(i.code, i.attribute_key) for i in d.issues])
        for d in result.decisions
        if not d.eligible
    ] == [
        ("blue", [("requirement_not_met", "color")]),
        ("green", [("requirement_not_met", "color")]),
    ]


def test_preferences_rank_eligible_options_without_becoming_mandatory(tmp_path: Path) -> None:
    path = tmp_path / "commercial.json"
    write_commercial(path)
    data = catalog()
    result = Advisor(data, JsonCommercialAdapter(path, data)).recommend(
        AdviceRequest(
            category_id="chairs", preferences=(AttributeConstraint(key="color", value="blue"),)
        ),
        NOW,
    )
    assert result.recommended_variant_ids == ("blue", "green", "red")
    assert result.decisions[1].preference_matches == ("color",)


@pytest.mark.parametrize(
    "constraint",
    [
        AttributeConstraint(key="missing", value="yes"),
        AttributeConstraint(key="width", value=50, unit="m"),
        AttributeConstraint(key="width", value=True, unit="cm"),
        AttributeConstraint(key="color", operator="min", value="red"),
    ],
)
def test_incompatible_constraints_are_rejected_instead_of_silently_ignored(
    tmp_path: Path, constraint: AttributeConstraint
) -> None:
    data = catalog()
    advisor = Advisor(data, JsonCommercialAdapter(tmp_path / "missing.json", data))
    with pytest.raises(ValueError, match="constraint"):
        advisor.recommend(AdviceRequest(category_id="chairs", mandatory=(constraint,)), NOW)


def test_budget_currency_requires_clarification_without_currency_conversion(tmp_path: Path) -> None:
    path = tmp_path / "commercial.json"
    write_commercial(path)
    data = catalog()
    result = Advisor(data, JsonCommercialAdapter(path, data)).recommend(
        AdviceRequest(category_id="chairs", budget=Money(amount="200", currency="USD")), NOW
    )
    assert result.status == "clarification_required"
    assert result.recommended_variant_ids == ()
    assert result.warnings == ("budget_currency_mismatch",)


def test_unknown_category_requires_an_explicit_correction(tmp_path: Path) -> None:
    data = catalog()
    with pytest.raises(ValueError, match="category"):
        Advisor(data, JsonCommercialAdapter(tmp_path / "missing.json", data)).recommend(
            AdviceRequest(category_id="other"),
            NOW,
        )


@pytest.mark.parametrize(
    "mutation", ["store", "mode", "duplicate", "variant", "revision", "future"]
)
def test_commercial_results_cannot_cross_scopes_or_mix_revisions(
    tmp_path: Path, mutation: str
) -> None:
    path = tmp_path / "commercial.json"
    write_commercial(path)
    data = catalog()
    lookups = list(
        JsonCommercialAdapter(path, data).lookup("test-store", ("red", "blue", "green"), NOW)
    )
    changes: dict[str, object] = {
        "store": {"store_id": "other-store"},
        "mode": {"data_mode": "real"},
        "variant": {"variant_id": "invented"},
        "revision": {"revision": "commercial-2"},
        "future": {"checked_at": NOW + timedelta(seconds=1)},
    }
    if mutation == "duplicate":
        lookups.append(lookups[0])
    else:
        change = changes[mutation]
        assert isinstance(change, dict)
        lookups[0] = CommercialLookup.model_validate({**lookups[0].model_dump(), **change})
    with pytest.raises(ValueError, match="Commercial"):
        Advisor(data, SuppliedCommerce(tuple(lookups))).recommend(
            AdviceRequest(category_id="chairs"), NOW
        )


@pytest.mark.parametrize("field", ["source_id", "snapshot_id", "revision"])
def test_commerce_without_exact_provenance_cannot_support_a_recommendation(
    tmp_path: Path, field: str
) -> None:
    path = tmp_path / "commercial.json"
    write_commercial(path)
    data = catalog()
    lookups = JsonCommercialAdapter(path, data).lookup("test-store", ("red", "blue", "green"), NOW)
    incomplete = tuple(
        CommercialLookup.model_validate({**v.model_dump(), field: None}) for v in lookups
    )
    result = Advisor(data, SuppliedCommerce(incomplete)).recommend(
        AdviceRequest(category_id="chairs"), NOW
    )
    assert result.recommended_variant_ids == ()
    assert result.citations == ()


def test_foreign_commercial_currency_cannot_be_compared_with_store_budget(tmp_path: Path) -> None:
    path = tmp_path / "commercial.json"
    write_commercial(path)
    data = catalog()
    lookups = JsonCommercialAdapter(path, data).lookup("test-store", ("red", "blue", "green"), NOW)
    altered = []
    for lookup in lookups:
        raw = lookup.model_dump(mode="json")
        raw["price"]["value"]["currency"] = "USD"
        altered.append(CommercialLookup.model_validate(raw))
    result = Advisor(data, SuppliedCommerce(tuple(altered))).recommend(
        AdviceRequest(category_id="chairs"), NOW
    )
    assert result.status == "no_matches"
    assert all("currency_mismatch" in {i.code for i in d.issues} for d in result.decisions)


def test_comparison_retains_units_provenance_and_unknown_variant_overrides(tmp_path: Path) -> None:
    path = tmp_path / "commercial.json"
    write_commercial(path)
    raw = catalog().model_dump(mode="json")
    raw["variants"][1]["attributes"].append({"key": "width", "value": None, "unit": "cm"})
    data = CatalogDataset.model_validate(raw)
    result = Advisor(data, JsonCommercialAdapter(path, data)).compare(("red", "blue"), NOW)
    assert result.status == "incomplete"
    assert tuple(d.variant_id for d in result.decisions) == ("red", "blue")
    width = next(row for row in result.rows if row.key == "width")
    assert width.unit == "cm"
    assert width.values[0] == AttributeValue(
        key="width",
        value=50,
        unit="cm",
        evidence_refs=("doc-width",),
    )
    assert width.values[1] is not None and width.values[1].value is None
    assert {(c.variant_id, c.field) for c in result.citations} == {
        ("red", "price"),
        ("red", "stock"),
        ("blue", "price"),
        ("blue", "stock"),
    }


def test_ordinal_references_resolve_only_against_the_expected_session_order() -> None:
    data = catalog()
    state = SessionState(
        session_id=uuid4(),
        store_id="test-store",
        profile_revision="profile-1",
        created_at=NOW,
        last_seen_at=NOW,
        presented_variants=("green", "red"),
    )
    chosen = resolve_presented_variant(data, state, session_id=state.session_id, position=2)
    assert chosen is not None and chosen.variant_id == "red"
    assert resolve_presented_variant(data, state, session_id=state.session_id, position=3) is None
    with pytest.raises(ValueError, match="session"):
        resolve_presented_variant(data, state, session_id=uuid4(), position=2)


def test_category_changes_preserve_budget_and_compatible_constraints_and_request_clarification() -> (
    None
):
    raw = catalog().model_dump(mode="json")
    raw["profile"]["categories"].append(
        {
            "category_id": "bags",
            "name": "Bags",
            "attribute_definitions": [
                {"key": "color", "label": "Color", "value_type": "text"},
                {"key": "width", "label": "Width", "value_type": "number", "unit": "mm"},
            ],
        }
    )
    data = CatalogDataset.model_validate(raw)
    request = AdviceRequest(
        category_id="chairs",
        budget=Money(amount="100", currency="COP"),
        mandatory=(AttributeConstraint(key="width", operator="max", value=50, unit="cm"),),
        preferences=(AttributeConstraint(key="color", value="red"),),
    )
    transition = change_advice_category(data, request, "bags")
    assert transition.request.budget == request.budget
    assert transition.request.category_id == "bags"
    assert transition.request.mandatory == ()
    assert transition.request.preferences == request.preferences
    assert transition.pending_mandatory == request.mandatory
    assert transition.needs_clarification is True
    assert request.category_id == "chairs"


def test_out_of_stock_options_are_explained_and_attribute_provenance_is_preserved(
    tmp_path: Path,
) -> None:
    path = tmp_path / "commercial.json"
    write_commercial(path)
    dataset = CommercialDataset.model_validate_json(path.read_text(encoding="utf-8"))
    raw = dataset.model_dump(mode="json")
    raw["snapshots"][0]["stock"]["value"] = {"availability": "out_of_stock", "quantity": 0}
    path.write_text(CommercialDataset.model_validate(raw).model_dump_json(), encoding="utf-8")
    data = catalog()
    result = Advisor(data, JsonCommercialAdapter(path, data)).recommend(
        AdviceRequest(category_id="chairs"), NOW
    )
    red = result.decisions[0]
    assert "out_of_stock" in {issue.code for issue in red.issues}
    assert result.recommended_variant_ids == ("green", "blue")
    assert red.attributes[0].evidence_refs == ("doc-width",)


def test_unknown_variant_attribute_does_not_inherit_known_product_value(tmp_path: Path) -> None:
    path = tmp_path / "commercial.json"
    write_commercial(path)
    raw = catalog().model_dump(mode="json")
    raw["variants"][0]["attributes"].append({"key": "width", "value": None, "unit": "cm"})
    data = CatalogDataset.model_validate(raw)
    result = Advisor(data, JsonCommercialAdapter(path, data)).recommend(
        AdviceRequest(
            category_id="chairs",
            mandatory=(AttributeConstraint(key="width", value=50, unit="cm"),),
        ),
        NOW,
    )
    assert result.recommended_variant_ids == ("green", "blue")
    assert result.decisions[0].issues[0].code == "requirement_unknown"


def test_preferences_never_override_mandatory_requirements_or_budget(tmp_path: Path) -> None:
    path = tmp_path / "commercial.json"
    write_commercial(path)
    data = catalog()
    result = Advisor(data, JsonCommercialAdapter(path, data)).recommend(
        AdviceRequest(
            category_id="chairs",
            budget=Money(amount="100", currency="COP"),
            preferences=(AttributeConstraint(key="color", value="blue"),),
        ),
        NOW,
    )
    assert result.recommended_variant_ids == ("green", "red")
    impossible = Advisor(data, JsonCommercialAdapter(path, data)).recommend(
        AdviceRequest(
            category_id="chairs",
            mandatory=(AttributeConstraint(key="width", operator="max", value=49, unit="cm"),),
        ),
        NOW,
    )
    assert impossible.status == "no_matches" and impossible.recommended_variant_ids == ()
    assert all(d.issues[0].code == "requirement_not_met" for d in impossible.decisions)


def test_commercial_updates_are_visible_without_reindexing_and_zero_is_a_valid_price(
    tmp_path: Path,
) -> None:
    path = tmp_path / "commercial.json"
    write_commercial(path)
    data = catalog()
    advisor = Advisor(data, JsonCommercialAdapter(path, data))
    request = AdviceRequest(category_id="chairs", budget=Money(amount="0", currency="COP"))
    assert advisor.recommend(request, NOW).status == "no_matches"
    write_commercial(path, ("0", "100.01", "90"))
    result = advisor.recommend(request, NOW)
    assert result.recommended_variant_ids == ("red",)
    assert result.decisions[0].price == Money(amount="0", currency="COP")


def test_missing_price_and_source_failure_never_produce_commercial_confirmation(
    tmp_path: Path,
) -> None:
    data = catalog()
    path = tmp_path / "commercial.json"
    advisor = Advisor(data, JsonCommercialAdapter(path, data))
    unavailable = advisor.recommend(AdviceRequest(category_id="chairs"), NOW)
    assert unavailable.status == "no_matches" and unavailable.citations == ()
    assert all(
        d.commercial is not None and d.commercial.lookup_status == "unavailable"
        for d in unavailable.decisions
    )
    write_commercial(path, (None, None, None))
    unknown = advisor.recommend(AdviceRequest(category_id="chairs"), NOW)
    assert unknown.status == "no_matches" and unknown.citations == ()
    assert all(d.stock is not None and d.price is None for d in unknown.decisions)


def test_comparison_requires_distinct_known_variants_of_one_category(tmp_path: Path) -> None:
    data = catalog()
    advisor = Advisor(data, JsonCommercialAdapter(tmp_path / "missing.json", data))
    for selection in (("red",), ("red", "red"), ("red", "invented")):
        with pytest.raises(ValueError):
            advisor.compare(selection, NOW)
    raw = data.model_dump(mode="json")
    raw["profile"]["categories"].append({"category_id": "bags", "name": "Bags"})
    raw["products"].append(
        {
            "store_id": "test-store",
            "product_id": "bag",
            "category_id": "bags",
            "name": "Bag",
            "revision": "catalog-1",
        }
    )
    raw["variants"].append(
        {
            "store_id": "test-store",
            "variant_id": "bag",
            "product_id": "bag",
            "name": "Bag",
            "revision": "catalog-1",
        }
    )
    another = CatalogDataset.model_validate(raw)
    with pytest.raises(ValueError, match="single category"):
        Advisor(another, JsonCommercialAdapter(tmp_path / "missing.json", another)).compare(
            ("red", "bag"), NOW
        )


def test_comparison_with_expired_commerce_cannot_emit_commercial_citations(tmp_path: Path) -> None:
    path = tmp_path / "commercial.json"
    write_commercial(path)
    data = catalog()
    advisor = Advisor(data, JsonCommercialAdapter(path, data))
    assert advisor.compare(("red", "blue"), NOW).status == "ready"
    expired = advisor.compare(("red", "blue"), NOW + timedelta(minutes=5))
    assert expired.status == "incomplete"
    assert expired.citations == ()


@pytest.mark.parametrize(
    "presented,position",
    [
        (("red", "red"), 1),
        (("removed", "red"), 2),
        ((), 1),
        (("red",), 0),
        (("red",), True),
    ],
)
def test_ambiguous_or_removed_session_selections_require_clarification(
    presented: tuple[str, ...],
    position: int,
) -> None:
    state = SessionState(
        session_id=uuid4(),
        store_id="test-store",
        profile_revision="profile-1",
        created_at=NOW,
        last_seen_at=NOW,
        presented_variants=presented,
    )
    assert (
        resolve_presented_variant(catalog(), state, session_id=state.session_id, position=position)
        is None
    )


@pytest.mark.parametrize(
    "store_id,revision", [("other-store", "profile-1"), ("test-store", "profile-2")]
)
def test_session_scope_cannot_cross_stores_or_profile_revisions(
    store_id: str, revision: str
) -> None:
    state = SessionState(
        session_id=uuid4(),
        store_id=store_id,
        profile_revision=revision,
        created_at=NOW,
        last_seen_at=NOW,
        presented_variants=("red",),
    )
    with pytest.raises(ValueError, match="session"):
        resolve_presented_variant(catalog(), state, session_id=state.session_id, position=1)


def test_new_budget_and_requirements_do_not_mutate_previous_request(tmp_path: Path) -> None:
    path = tmp_path / "commercial.json"
    write_commercial(path)
    data = catalog()
    advisor = Advisor(data, JsonCommercialAdapter(path, data))
    previous = AdviceRequest(category_id="chairs", budget=Money(amount="100", currency="COP"))
    changed = AdviceRequest(
        category_id="chairs",
        budget=Money(amount="101", currency="COP"),
        mandatory=(AttributeConstraint(key="color", value="blue"),),
    )
    assert advisor.recommend(changed, NOW).recommended_variant_ids == ("blue",)
    assert advisor.recommend(previous, NOW).recommended_variant_ids == ("green", "red")


def test_naive_evaluation_time_and_invalid_candidate_selection_are_rejected(tmp_path: Path) -> None:
    data = catalog()
    advisor = Advisor(data, JsonCommercialAdapter(tmp_path / "missing.json", data))
    request = AdviceRequest(category_id="chairs")
    with pytest.raises(ValueError, match="timezone"):
        advisor.recommend(request, NOW.replace(tzinfo=None))
    with pytest.raises(ValueError, match="variant"):
        advisor.recommend(request, NOW, variant_ids=("invented",))
