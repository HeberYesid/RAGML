"""Canonical local data contracts, independent of a store or model provider."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated, Literal, Self

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictFloat,
    StrictInt,
    StrictStr,
    StringConstraints,
    field_validator,
    model_validator,
)

Identifier = Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=1)]
Currency = Annotated[str, StringConstraints(strict=True, pattern=r"^[A-Z]{3}$")]
DataMode = Literal["demo", "real"]
AttributeScalar = StrictStr | StrictBool | StrictInt | StrictFloat


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class Money(Contract):
    amount: Annotated[Decimal, Field(ge=0, allow_inf_nan=False)]
    currency: Currency

    @field_validator("amount", mode="before")
    @classmethod
    def require_decimal_input(cls, value: object) -> object:
        if not isinstance(value, str | Decimal):
            raise ValueError("Money requires a decimal string, not a JSON number")
        return value


class AttributeDefinition(Contract):
    key: Identifier
    label: Identifier
    value_type: Literal["text", "number", "boolean", "choice"]
    unit: Identifier | None = None
    required_for_comparison: bool = False
    choices: tuple[Identifier, ...] = ()

    @model_validator(mode="after")
    def check_choices(self) -> Self:
        if (self.value_type == "choice") != bool(self.choices):
            raise ValueError("Only choice attributes require a nonempty choices list")
        return self


class AttributeValue(Contract):
    key: Identifier
    value: AttributeScalar | None
    unit: Identifier | None = None
    evidence_refs: tuple[Identifier, ...] = ()

    @model_validator(mode="after")
    def require_evidence(self) -> Self:
        if self.value is not None and not self.evidence_refs:
            raise ValueError("Known attributes require evidence references")
        return self


class Category(Contract):
    category_id: Identifier
    name: Identifier
    attribute_definitions: tuple[AttributeDefinition, ...] = ()

    @model_validator(mode="after")
    def unique_attributes(self) -> Self:
        if len({a.key for a in self.attribute_definitions}) != len(self.attribute_definitions):
            raise ValueError("Duplicate category attribute key")
        return self


class StoreProfile(Contract):
    schema_version: Literal["0.1"] = "0.1"
    store_id: Identifier
    display_name: Identifier
    data_mode: DataMode
    locale: Identifier
    currency: Currency
    currency_decimal_places: Annotated[int, Field(strict=True, ge=0, le=6)]
    categories: tuple[Category, ...]
    revision: Identifier
    human_contact: Identifier | None = None

    @model_validator(mode="after")
    def unique_categories(self) -> Self:
        if len({c.category_id for c in self.categories}) != len(self.categories):
            raise ValueError("Duplicate category identifier")
        return self


class Product(Contract):
    store_id: Identifier
    product_id: Identifier
    category_id: Identifier
    name: Identifier
    attributes: tuple[AttributeValue, ...] = ()
    revision: Identifier


class Variant(Contract):
    store_id: Identifier
    variant_id: Identifier
    product_id: Identifier
    name: Identifier
    attributes: tuple[AttributeValue, ...] = ()
    revision: Identifier
    sku: Identifier | None = None


def validate_attributes(values: tuple[AttributeValue, ...], category: Category) -> None:
    definitions = {a.key: a for a in category.attribute_definitions}
    if len({a.key for a in values}) != len(values):
        raise ValueError("Duplicate entity attribute key")
    for attribute in values:
        definition = definitions.get(attribute.key)
        if definition is None or attribute.unit != definition.unit:
            raise ValueError("Unknown attribute or incompatible unit")
        value = attribute.value
        if value is None:
            continue
        valid_type = {
            "text": isinstance(value, str),
            "number": isinstance(value, int | float) and not isinstance(value, bool),
            "boolean": isinstance(value, bool),
            "choice": isinstance(value, str) and value in definition.choices,
        }[definition.value_type]
        if not valid_type:
            raise ValueError("Attribute value does not match its category definition")


class CatalogDataset(Contract):
    schema_version: Literal["0.1"] = "0.1"
    profile: StoreProfile
    products: tuple[Product, ...]
    variants: tuple[Variant, ...]

    @model_validator(mode="after")
    def validate_relations(self) -> Self:
        categories = {c.category_id: c for c in self.profile.categories}
        products = {p.product_id: p for p in self.products}
        if len(products) != len(self.products):
            raise ValueError("Duplicate product identifier")
        if len({v.variant_id for v in self.variants}) != len(self.variants):
            raise ValueError("Duplicate variant identifier")
        for product in self.products:
            if product.store_id != self.profile.store_id or product.category_id not in categories:
                raise ValueError("Product belongs to another store or an absent category")
            validate_attributes(product.attributes, categories[product.category_id])
        for variant in self.variants:
            if variant.store_id != self.profile.store_id or variant.product_id not in products:
                raise ValueError("Variant belongs to another store or an absent product")
            validate_attributes(
                variant.attributes, categories[products[variant.product_id].category_id]
            )
        return self


class Stock(Contract):
    availability: Literal["in_stock", "out_of_stock"]
    quantity: Annotated[int, Field(strict=True, ge=0)] | None

    @model_validator(mode="after")
    def consistent_quantity(self) -> Self:
        if self.quantity is not None and (self.quantity > 0) != (self.availability == "in_stock"):
            raise ValueError("Quantity contradicts availability")
        return self


class Observation[T](Contract):
    value: T | None
    source_updated_at: AwareDatetime
    expires_at: AwareDatetime
    source_ref: Identifier

    @field_validator("source_updated_at", "expires_at", mode="before")
    @classmethod
    def require_datetime_input(cls, value: object) -> object:
        if not isinstance(value, str | datetime):
            raise ValueError("Timestamps require an ISO 8601 string or aware datetime")
        return value

    @field_validator("source_updated_at", "expires_at")
    @classmethod
    def normalize_timezone(cls, value: datetime) -> datetime:
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def valid_window(self) -> Self:
        if self.expires_at <= self.source_updated_at:
            raise ValueError("Expiry must follow the source update")
        return self


class CommercialSnapshot(Contract):
    store_id: Identifier
    variant_id: Identifier
    snapshot_id: Identifier
    source_id: Identifier
    revision: Identifier
    price: Observation[Money]
    stock: Observation[Stock]


class CommercialDataset(Contract):
    schema_version: Literal["0.1"] = "0.1"
    store_id: Identifier
    data_mode: DataMode
    revision: Identifier
    snapshots: tuple[CommercialSnapshot, ...]

    @model_validator(mode="after")
    def validate_snapshots(self) -> Self:
        if len({s.variant_id for s in self.snapshots}) != len(self.snapshots):
            raise ValueError("Multiple commercial snapshots for the same variant")
        if len({s.snapshot_id for s in self.snapshots}) != len(self.snapshots):
            raise ValueError("Duplicate commercial snapshot identifier")
        if any(s.store_id != self.store_id or s.revision != self.revision for s in self.snapshots):
            raise ValueError("Mixed stores or revisions in commercial data")
        return self

    def validate_for_catalog(self, catalog: CatalogDataset) -> None:
        profile = catalog.profile
        if self.store_id != profile.store_id or self.data_mode != profile.data_mode:
            raise ValueError("Commercial data does not belong to the configured store and mode")
        variants = {v.variant_id for v in catalog.variants}
        for snapshot in self.snapshots:
            if snapshot.variant_id not in variants:
                raise ValueError("Commercial record references an absent variant")
            price = snapshot.price.value
            if price is not None:
                if price.currency != profile.currency:
                    raise ValueError("Commercial currency does not match the store profile")
                scaled = price.amount * Decimal(10) ** profile.currency_decimal_places
                if scaled != scaled.to_integral_value():
                    raise ValueError("Price exceeds the configured currency precision")
