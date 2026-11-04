"""Store-independent interfaces for the implementations in subsequent phases."""

from typing import Annotated, Protocol
from uuid import UUID

from pydantic import Field

from ragml.contracts import Contract, Identifier, Product, Variant
from ragml.conversation import SessionState
from ragml.evidence import Chunk, SourceManifest
from ragml.providers import EmbeddingResult, GenerationResult


class CatalogQuery(Contract):
    text: Identifier
    category_ids: tuple[Identifier, ...] = ()
    mandatory_attributes: dict[str, str] = Field(default_factory=dict)


class RetrievalQuery(Contract):
    store_id: Identifier
    text: Identifier
    revision: Identifier
    k: Annotated[int, Field(ge=1, le=10)] = 5
    category_ids: tuple[Identifier, ...] = ()
    product_ids: tuple[Identifier, ...] = ()
    variant_ids: tuple[Identifier, ...] = ()
    include_store_policies: bool = True


class RetrievedChunk(Contract):
    chunk: Chunk
    score: Annotated[float, Field(ge=-1, le=1)]


class CatalogPort(Protocol):
    def get_product(self, store_id: str, product_id: str) -> Product | None: ...
    def get_variant(self, store_id: str, variant_id: str) -> Variant | None: ...
    def search(self, store_id: str, query: CatalogQuery) -> tuple[Variant, ...]: ...


class SourceRepository(Protocol):
    def load(self, store_id: str, revision: str) -> SourceManifest: ...


class RetrievalPort(Protocol):
    def search(self, query: RetrievalQuery) -> tuple[RetrievedChunk, ...]: ...


class GenerationPort(Protocol):
    def generate(
        self, system: str, user: str, *, output_tokens: int | None = None
    ) -> GenerationResult: ...


class EmbeddingPort(Protocol):
    def embed(self, texts: tuple[str, ...], *, query: bool = False) -> EmbeddingResult: ...


class SessionRepository(Protocol):
    def load(self, session_id: UUID, store_id: str, owner_id: UUID) -> SessionState | None: ...
    def save(self, state: SessionState, owner_id: UUID) -> None: ...
    def delete(self, session_id: UUID, store_id: str, owner_id: UUID) -> None: ...
