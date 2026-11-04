"""Versioned evidence contracts and catalog/source referential integrity."""

from hashlib import sha256
from typing import Annotated, Literal, Self

from pydantic import Field, StringConstraints, model_validator

from ragml.contracts import CatalogDataset, Contract, DataMode, Identifier, Product, Variant

Sha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]


class SourceScope(Contract):
    kind: Literal["store", "category", "product", "variant"]
    target_id: Identifier | None = None

    @model_validator(mode="after")
    def check_target(self) -> Self:
        if (self.kind == "store") != (self.target_id is None):
            raise ValueError("Only store-wide sources omit a target identifier")
        return self


class Location(Contract):
    page: Annotated[int, Field(strict=True, gt=0)] | None = None
    section: Identifier | None = None
    paragraph: Annotated[int, Field(strict=True, gt=0)] | None = None
    table: Identifier | None = None

    @model_validator(mode="after")
    def require_location(self) -> Self:
        if all(value is None for value in (self.page, self.section, self.paragraph, self.table)):
            raise ValueError("Evidence requires a human-readable location")
        return self


class Source(Contract):
    store_id: Identifier
    source_id: Identifier
    title: Identifier
    version: Identifier
    content_hash: Sha256
    data_mode: DataMode
    scope: SourceScope
    locator: Identifier
    provenance: Literal["synthetic_created", "authorized"]
    active: bool = True


class Chunk(Contract):
    store_id: Identifier
    chunk_id: Identifier
    source_id: Identifier
    source_version: Identifier
    source_content_hash: Sha256
    content_hash: Sha256
    text: Annotated[str, StringConstraints(min_length=1, max_length=4000)]
    location: Location

    @model_validator(mode="after")
    def verify_text_hash(self) -> Self:
        if sha256(self.text.encode("utf-8")).hexdigest() != self.content_hash:
            raise ValueError("Chunk content hash does not match its UTF-8 text")
        return self


class SourceManifest(Contract):
    schema_version: Literal["0.1"] = "0.1"
    store_id: Identifier
    data_mode: DataMode
    revision: Identifier
    sources: tuple[Source, ...]
    chunks: tuple[Chunk, ...]

    @model_validator(mode="after")
    def verify_sources(self) -> Self:
        sources = {s.source_id: s for s in self.sources}
        if len(sources) != len(self.sources) or len({c.chunk_id for c in self.chunks}) != len(
            self.chunks
        ):
            raise ValueError("Duplicate evidence identifier")
        for source in self.sources:
            if source.store_id != self.store_id or source.data_mode != self.data_mode:
                raise ValueError("Source store or data mode mismatch")
            if source.data_mode == "real" and source.provenance != "authorized":
                raise ValueError("Real sources require recorded authorization")
        for chunk in self.chunks:
            chunk_source = sources.get(chunk.source_id)
            if (
                chunk_source is None
                or not chunk_source.active
                or chunk.store_id != self.store_id
                or chunk.source_version != chunk_source.version
                or chunk.source_content_hash != chunk_source.content_hash
            ):
                raise ValueError("Chunk references an inactive, absent or different source version")
        return self

    def validate_for_catalog(self, catalog: CatalogDataset) -> None:
        if (self.store_id, self.data_mode) != (
            catalog.profile.store_id,
            catalog.profile.data_mode,
        ):
            raise ValueError("Manifest belongs to another store or data mode")
        targets = {
            "category": {c.category_id for c in catalog.profile.categories},
            "product": {p.product_id for p in catalog.products},
            "variant": {v.variant_id for v in catalog.variants},
        }
        for source in self.sources:
            if (
                source.scope.kind != "store"
                and source.scope.target_id not in targets[source.scope.kind]
            ):
                raise ValueError("Source scope references an absent catalog entity")
        active_sources = {s.source_id for s in self.sources if s.active}
        by_source = {s.source_id: s for s in self.sources}
        products = {p.product_id: p for p in catalog.products}
        entities: tuple[Product | Variant, ...] = (*catalog.products, *catalog.variants)
        for entity in entities:
            product = entity if isinstance(entity, Product) else products[entity.product_id]
            allowed_targets: dict[str, str | None] = {
                "store": None,
                "category": product.category_id,
                "product": product.product_id,
                "variant": entity.variant_id if isinstance(entity, Variant) else None,
            }
            for attribute in entity.attributes:
                if any(ref not in active_sources for ref in attribute.evidence_refs):
                    raise ValueError("Attribute references an absent or inactive source")
                for ref in attribute.evidence_refs:
                    scope = by_source[ref].scope
                    if scope.kind == "variant" and isinstance(entity, Product):
                        raise ValueError(
                            "Product attribute cannot inherit a variant-specific source"
                        )
                    if scope.target_id != allowed_targets[scope.kind]:
                        raise ValueError("Attribute source does not apply to this entity")
