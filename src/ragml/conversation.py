"""Conversation and citation boundaries; no conversation engine is implemented here."""

from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import AwareDatetime, Field, StringConstraints, model_validator

from ragml.commercial import CommercialLookup
from ragml.contracts import AttributeScalar, Contract, DataMode, Identifier, Money
from ragml.evidence import Location, SourceManifest


class DocumentCitation(Contract):
    citation_id: Identifier
    kind: Literal["document"] = "document"
    store_id: Identifier
    source_id: Identifier
    source_version: Identifier
    chunk_id: Identifier
    location: Location
    excerpt: Identifier


class CommercialCitation(Contract):
    citation_id: Identifier
    kind: Literal["commercial"] = "commercial"
    store_id: Identifier
    source_id: Identifier
    source_version: Identifier
    snapshot_id: Identifier
    variant_id: Identifier
    field: Literal["price", "stock"]
    source_updated_at: AwareDatetime
    expires_at: AwareDatetime

    @model_validator(mode="after")
    def check_window(self) -> Self:
        if self.expires_at <= self.source_updated_at:
            raise ValueError("Commercial citation requires an ordered validity window")
        return self


Citation = Annotated[DocumentCitation | CommercialCitation, Field(discriminator="kind")]


class ChatRequest(Contract):
    schema_version: Literal["0.1"] = "0.1"
    message: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)]
    session_id: UUID | None = None


class SupportedClaim(Contract):
    text: Identifier
    citation_ids: Annotated[tuple[Identifier, ...], Field(min_length=1)]


class ProductReference(Contract):
    product_id: Identifier
    variant_id: Identifier


class ChatResponse(Contract):
    schema_version: Literal["0.1"] = "0.1"
    request_id: UUID
    session_id: UUID
    store_id: Identifier
    data_mode: DataMode
    status: Literal[
        "answered", "clarification_required", "insufficient_evidence", "temporarily_unavailable"
    ]
    answer: Identifier
    claims: tuple[SupportedClaim, ...] = ()
    citations: tuple[Citation, ...] = ()
    products: tuple[ProductReference, ...] = ()
    warnings: tuple[Identifier, ...] = ()
    versions: dict[str, Identifier]

    @model_validator(mode="after")
    def verify_citation_links(self) -> Self:
        ids = {citation.citation_id for citation in self.citations}
        if len(ids) != len(self.citations):
            raise ValueError("Duplicate citation identifier")
        if any(citation.store_id != self.store_id for citation in self.citations):
            raise ValueError("Citation belongs to another store")
        if any(ref not in ids for claim in self.claims for ref in claim.citation_ids):
            raise ValueError("Claim references an absent citation")
        if self.status == "answered" and not self.claims:
            raise ValueError("An answered response requires supported claims")
        return self

    def validate_evidence(
        self, manifest: SourceManifest, lookups: tuple[CommercialLookup, ...] = ()
    ) -> None:
        if (manifest.store_id, manifest.data_mode) != (self.store_id, self.data_mode):
            raise ValueError("Response and evidence store or mode mismatch")
        chunks = {chunk.chunk_id: chunk for chunk in manifest.chunks}
        for citation in self.citations:
            if isinstance(citation, DocumentCitation):
                chunk = chunks.get(citation.chunk_id)
                if (
                    chunk is None
                    or (chunk.source_id, chunk.source_version, chunk.location)
                    != (citation.source_id, citation.source_version, citation.location)
                    or citation.excerpt not in chunk.text
                ):
                    raise ValueError("Document citation does not resolve its exact evidence")
            else:
                matches = [
                    result
                    for result in lookups
                    if result.lookup_status == "found"
                    and result.store_id == citation.store_id
                    and result.data_mode == self.data_mode
                    and result.variant_id == citation.variant_id
                    and result.snapshot_id == citation.snapshot_id
                    and result.source_id == citation.source_id
                    and result.revision == citation.source_version
                ]
                if len(matches) != 1:
                    raise ValueError("Commercial citation does not resolve an exact lookup")
                observation = getattr(matches[0], citation.field)
                if (
                    observation is None
                    or observation.status != "fresh"
                    or observation.source_updated_at != citation.source_updated_at
                    or observation.expires_at != citation.expires_at
                ):
                    raise ValueError("Commercial citation is not backed by a fresh observation")


class SessionRequirement(Contract):
    key: Identifier
    operator: Literal["eq", "min", "max"] = "eq"
    value: AttributeScalar
    unit: Identifier | None = None


class SessionState(Contract):
    session_id: UUID
    store_id: Identifier
    profile_revision: Identifier
    created_at: AwareDatetime
    last_seen_at: AwareDatetime
    budget: Money | None = None
    category_id: Identifier | None = None
    selected_variants: tuple[Identifier, ...] = ()
    candidate_products: tuple[Identifier, ...] = ()
    mandatory_constraints: tuple[SessionRequirement, ...] = ()
    preference_constraints: tuple[SessionRequirement, ...] = ()
    pending_constraints: tuple[Identifier, ...] = ()
    mandatory_requirements: dict[str, str] = Field(default_factory=dict)
    preferences: dict[str, str] = Field(default_factory=dict)
    presented_variants: tuple[Identifier, ...] = ()

    @model_validator(mode="after")
    def check_times(self) -> Self:
        if self.last_seen_at < self.created_at:
            raise ValueError("A session cannot be accessed before creation")
        return self


class ErrorResponse(Contract):
    code: Literal[
        "invalid_input",
        "not_found",
        "rag_not_ready",
        "provider_unavailable",
        "internal_error",
        "session_not_found",
    ]
    message: Identifier
    request_id: UUID
    retryable: bool
