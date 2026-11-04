"""Checks of the prototype's public contracts and real local-file boundary."""

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from ragml.commercial import JsonCommercialAdapter, evaluate_observation
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

NOW = datetime(2026, 11, 4, 15, tzinfo=UTC)


def make_catalog(store_id: str = "shop-a", currency: str = "COP") -> CatalogDataset:
    return CatalogDataset(
        profile=StoreProfile(
            store_id=store_id,
            display_name="Synthetic store",
            data_mode="demo",
            locale="es-CO",
            currency=currency,
            currency_decimal_places=2,
            categories=(
                Category(
                    category_id="category-a" if currency == "COP" else "another-category",
                    name="Test category",
                    attribute_definitions=(
                        AttributeDefinition(
                            key="width", label="Width", value_type="number", unit="cm"
                        ),
                    ),
                ),
            ),
            revision="profile-1",
        ),
        products=(
            Product(
                store_id=store_id,
                product_id="product-1",
                category_id="category-a" if currency == "COP" else "another-category",
                name="Test product",
                revision="catalog-1",
            ),
        ),
        variants=tuple(
            Variant(
                store_id=store_id,
                variant_id=variant_id,
                product_id="product-1",
                name=variant_id,
                revision="catalog-1",
            )
            for variant_id in ("variant-1", "variant-2")
        ),
    )


def make_observation(value: Money | Stock | None) -> Observation[Money | Stock]:
    return Observation[Money | Stock](
        value=value,
        source_updated_at=NOW - timedelta(minutes=5),
        expires_at=NOW + timedelta(minutes=10),
        source_ref="synthetic-source",
    )


def write_commercial(
    path: Path,
    catalog: CatalogDataset,
    amount: str | None = "100.00",
    revision: str = "commercial-1",
) -> None:
    price = make_observation(
        Money(amount=Decimal(amount), currency=catalog.profile.currency)
        if amount is not None
        else None
    )
    stock = make_observation(Stock(availability="out_of_stock", quantity=0))
    dataset = CommercialDataset(
        store_id=catalog.profile.store_id,
        data_mode="demo",
        revision=revision,
        snapshots=(
            CommercialSnapshot.model_validate(
                {
                    "store_id": catalog.profile.store_id,
                    "variant_id": "variant-1",
                    "snapshot_id": f"snapshot-{revision}",
                    "source_id": "synthetic-source",
                    "revision": revision,
                    "price": price.model_dump(),
                    "stock": stock.model_dump(),
                }
            ),
        ),
    )
    path.write_text(dataset.model_dump_json(), encoding="utf-8")


def test_money_serializes_as_decimal_string_and_preserves_zero() -> None:
    price = Money(amount=Decimal("0.00"), currency="COP")
    assert json.loads(price.model_dump_json()) == {"amount": "0.00", "currency": "COP"}


@pytest.mark.parametrize("amount", [-1, 1.5, True, "-1", "NaN", "Infinity"])
def test_money_rejects_negative_nonfinite_and_numeric_input(amount: object) -> None:
    with pytest.raises(ValidationError):
        Money.model_validate({"amount": amount, "currency": "COP"})


@pytest.mark.parametrize(
    ("availability", "quantity"), [("in_stock", 0), ("out_of_stock", 2), ("in_stock", True)]
)
def test_stock_rejects_contradictory_or_boolean_quantities(
    availability: str, quantity: int
) -> None:
    with pytest.raises(ValidationError):
        Stock.model_validate({"availability": availability, "quantity": quantity})


def test_naive_source_dates_and_reversed_validity_windows_are_rejected() -> None:
    data = make_observation(None).model_dump()
    with pytest.raises(ValidationError):
        Observation[Money].model_validate({**data, "source_updated_at": "2026-11-04T10:00:00"})
    with pytest.raises(ValidationError):
        Observation[Money].model_validate({**data, "expires_at": data["source_updated_at"]})


def test_catalog_rejects_cross_store_variants_and_unknown_attributes() -> None:
    data = make_catalog().model_dump(mode="json")
    data["variants"][0]["store_id"] = "another-store"
    with pytest.raises(ValidationError):
        CatalogDataset.model_validate(data)
    data = make_catalog().model_dump(mode="json")
    data["products"][0]["attributes"] = [
        {"key": "invented", "value": 10, "unit": "cm", "evidence_refs": ["source-1"]}
    ]
    with pytest.raises(ValidationError):
        CatalogDataset.model_validate(data)


def test_known_attributes_require_evidence_and_category_types() -> None:
    with pytest.raises(ValidationError):
        AttributeValue(key="width", value=10, unit="cm")
    data = make_catalog().model_dump(mode="json")
    data["products"][0]["attributes"] = [
        {"key": "width", "value": True, "unit": "cm", "evidence_refs": ["source-1"]}
    ]
    with pytest.raises(ValidationError):
        CatalogDataset.model_validate(data)


def test_unknown_price_missing_record_and_zero_stock_remain_distinct(tmp_path: Path) -> None:
    catalog = make_catalog()
    path = tmp_path / "commercial.json"
    write_commercial(path, catalog, amount=None)
    first, second = JsonCommercialAdapter(path, catalog).lookup(
        "shop-a", ("variant-1", "variant-2"), NOW
    )
    assert first.lookup_status == "found"
    assert first.price is not None and first.price.status == "unknown" and first.price.value is None
    assert first.stock is not None and first.stock.value == Stock(
        availability="out_of_stock", quantity=0
    )
    assert second.lookup_status == "not_found" and second.stock is None and second.price is None


@pytest.mark.parametrize(
    ("offset_minutes", "expected_status"),
    [(-6, "not_yet_valid"), (-5, "fresh"), (9, "fresh"), (10, "stale")],
)
def test_freshness_uses_source_time_and_exact_expiry_boundary(
    offset_minutes: int, expected_status: str
) -> None:
    observation = make_observation(Money(amount=Decimal("100"), currency="COP"))
    result = evaluate_observation(observation, NOW + timedelta(minutes=offset_minutes))
    assert result.status == expected_status
    assert (result.value is not None) == (expected_status == "fresh")


def test_price_and_stock_are_evaluated_independently(tmp_path: Path) -> None:
    catalog = make_catalog()
    path = tmp_path / "commercial.json"
    write_commercial(path, catalog)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["snapshots"][0]["price"]["expires_at"] = NOW.isoformat()
    path.write_text(json.dumps(data), encoding="utf-8")
    result = JsonCommercialAdapter(path, catalog).lookup("shop-a", ("variant-1",), NOW)[0]
    assert (
        result.price is not None and result.price.status == "stale" and result.price.value is None
    )
    assert result.stock is not None and result.stock.status == "fresh"


def test_next_lookup_observes_new_revision_and_missing_file_is_unavailable(tmp_path: Path) -> None:
    catalog = make_catalog()
    path = tmp_path / "commercial.json"
    adapter = JsonCommercialAdapter(path, catalog)
    write_commercial(path, catalog)
    before = adapter.lookup("shop-a", ("variant-1",), NOW)[0]
    write_commercial(path, catalog, amount="125.00", revision="commercial-2")
    after = adapter.lookup("shop-a", ("variant-1",), NOW)[0]
    assert before.price is not None and before.price.value == Money(
        amount=Decimal("100.00"), currency="COP"
    )
    assert after.revision == "commercial-2"
    assert after.price is not None and after.price.value == Money(
        amount=Decimal("125.00"), currency="COP"
    )
    path.unlink()
    unavailable = adapter.lookup("shop-a", ("variant-1",), NOW)[0]
    assert unavailable.lookup_status == "unavailable" and unavailable.price is None
    assert unavailable.error_code == "source_unavailable"


def test_two_stores_can_reuse_ids_with_different_categories_and_currencies(tmp_path: Path) -> None:
    first_catalog = make_catalog()
    second_catalog = make_catalog("shop-b", "USD")
    first_path, second_path = tmp_path / "a.json", tmp_path / "b.json"
    write_commercial(first_path, first_catalog, "100.00")
    write_commercial(second_path, second_catalog, "2.50")
    first_adapter = JsonCommercialAdapter(first_path, first_catalog)
    second_adapter = JsonCommercialAdapter(second_path, second_catalog)
    first = first_adapter.lookup("shop-a", ("variant-1",), NOW)[0]
    second = second_adapter.lookup("shop-b", ("variant-1",), NOW)[0]
    assert first.price is not None and first.price.value == Money(
        amount=Decimal("100.00"), currency="COP"
    )
    assert second.price is not None and second.price.value == Money(
        amount=Decimal("2.50"), currency="USD"
    )
    with pytest.raises(ValueError, match="configured adapter"):
        first_adapter.lookup("shop-b", ("variant-1",), NOW)
    wrong_file = JsonCommercialAdapter(second_path, first_catalog).lookup(
        "shop-a", ("variant-1",), NOW
    )[0]
    assert wrong_file.error_code == "invalid_source" and wrong_file.price is None


def test_invalid_file_and_orphan_commercial_records_fail_closed(tmp_path: Path) -> None:
    catalog = make_catalog()
    path = tmp_path / "commercial.json"
    adapter = JsonCommercialAdapter(path, catalog)
    path.write_text("not JSON", encoding="utf-8")
    assert adapter.lookup("shop-a", ("variant-1",), NOW)[0].error_code == "invalid_source"
    write_commercial(path, catalog)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["snapshots"][0]["variant_id"] = "orphan-variant"
    path.write_text(json.dumps(data), encoding="utf-8")
    assert adapter.lookup("shop-a", ("variant-1",), NOW)[0].error_code == "invalid_source"
