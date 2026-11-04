"""Semantic retrieval through a real published SQLite corpus."""

import sqlite3
from contextlib import closing
from hashlib import sha256
from pathlib import Path

import pytest
from test_ingestion import DIGEST, FakeEmbeddings, package, publish
from test_local_contracts import make_catalog

from ragml.contracts import CatalogDataset, Product
from ragml.evidence import Chunk, Location, Source, SourceManifest, SourceScope
from ragml.ingestion import CorpusStore, ValidatedCorpus
from ragml.ports import RetrievalQuery
from ragml.providers import EmbeddingResult, ProviderError
from ragml.retrieval import RetrievalError, SqliteRetriever


def test_retrieval_returns_versioned_evidence_from_published_corpus(tmp_path: Path) -> None:
    corpus = package(tmp_path / "input")
    store = CorpusStore(tmp_path / "index.sqlite3")
    publish(store, corpus)
    retriever = SqliteRetriever(
        store.database, FakeEmbeddings(), model="test-model", digest=DIGEST, dimensions=4
    )
    found = retriever.search(RetrievalQuery(store_id="shop-a", revision="r1", text="Regla"))
    assert len(found) == 1
    assert found[0].chunk == corpus.manifest.chunks[0]
    assert found[0].score == pytest.approx(1.0)


def scoped_corpus() -> ValidatedCorpus:
    base = make_catalog()
    other = Product(
        store_id="shop-a",
        product_id="product-2",
        category_id="category-a",
        name="Another product",
        revision="catalog-1",
    )
    catalog = CatalogDataset(
        profile=base.profile, products=(*base.products, other), variants=base.variants
    )
    sources = []
    chunks = []
    for source_id, kind, target in (
        ("general", "store", None),
        ("category", "category", "category-a"),
        ("product1", "product", "product-1"),
        ("product2", "product", "product-2"),
        ("variant1", "variant", "variant-1"),
        ("variant2", "variant", "variant-2"),
    ):
        text = f"Synthetic evidence: {source_id}"
        content_hash = sha256(text.encode()).hexdigest()
        source = Source(
            store_id="shop-a",
            source_id=source_id,
            title=source_id,
            version="r1",
            content_hash=content_hash,
            data_mode="demo",
            scope=SourceScope(kind=kind, target_id=target),
            locator=f"{source_id}.md",
            provenance="synthetic_created",
        )
        sources.append(source)
        chunks.append(
            Chunk(
                store_id="shop-a",
                chunk_id=source_id,
                source_id=source_id,
                source_version="r1",
                source_content_hash=content_hash,
                content_hash=content_hash,
                text=text,
                location=Location(section="Test"),
            )
        )
    return ValidatedCorpus(
        catalog,
        SourceManifest(
            store_id="shop-a",
            data_mode="demo",
            revision="r1",
            sources=tuple(sources),
            chunks=tuple(chunks),
        ),
    )


@pytest.mark.parametrize(
    ("filters", "expected"),
    [
        (
            {"product_ids": ("product-1",)},
            {"general", "category", "product1", "variant1", "variant2"},
        ),
        ({"variant_ids": ("variant-1",)}, {"general", "category", "product1", "variant1"}),
        ({"product_ids": ("product-2",)}, {"general", "category", "product2"}),
        (
            {"category_ids": ("category-a",), "include_store_policies": False},
            {"category", "product1", "product2", "variant1", "variant2"},
        ),
        ({"product_ids": ("product-2",), "variant_ids": ("variant-1",)}, set()),
    ],
)
def test_filters_inherit_parent_evidence_without_including_sibling_variants(
    tmp_path: Path, filters: dict[str, object], expected: set[str]
) -> None:
    store = CorpusStore(tmp_path / "index.sqlite3")
    publish(store, scoped_corpus())
    retriever = SqliteRetriever(
        store.database, FakeEmbeddings(), model="test-model", digest=DIGEST, dimensions=4
    )
    query = RetrievalQuery.model_validate(
        {"store_id": "shop-a", "revision": "r1", "text": "test", "k": 10, **filters}
    )
    assert {hit.chunk.source_id for hit in retriever.search(query)} == expected


def test_stores_and_revisions_remain_isolated(tmp_path: Path) -> None:
    store = CorpusStore(tmp_path / "index.sqlite3")
    publish(store, package(tmp_path / "a"))
    publish(store, package(tmp_path / "b", store="shop-b", text="Different rule"))
    retriever = SqliteRetriever(
        store.database, FakeEmbeddings(), model="test-model", digest=DIGEST, dimensions=4
    )
    found = retriever.search(RetrievalQuery(store_id="shop-b", revision="r1", text="rule"))
    assert found[0].chunk.store_id == "shop-b"
    assert "Different rule" in found[0].chunk.text
    publish(store, package(tmp_path / "a", revision="r2", text="Updated"))
    with pytest.raises(RetrievalError, match="not_active"):
        retriever.search(RetrievalQuery(store_id="shop-a", revision="r1", text="rule"))


def test_missing_database_is_not_created(tmp_path: Path) -> None:
    database = tmp_path / "missing.sqlite3"
    retriever = SqliteRetriever(
        database, FakeEmbeddings(), model="test-model", digest=DIGEST, dimensions=4
    )
    with pytest.raises(RetrievalError, match="index_unavailable"):
        retriever.search(RetrievalQuery(store_id="shop-a", revision="r1", text="test"))
    assert not database.exists()


def test_wrong_embedding_identity_is_rejected_before_provider_use(tmp_path: Path) -> None:
    store = CorpusStore(tmp_path / "index.sqlite3")
    publish(store, package(tmp_path / "input"))
    retriever = SqliteRetriever(
        store.database, FakeEmbeddings(fail=True), model="changed", digest=DIGEST, dimensions=4
    )
    with pytest.raises(RetrievalError, match="embedding_index_mismatch"):
        retriever.search(RetrievalQuery(store_id="shop-a", revision="r1", text="test"))


def test_ties_are_deterministic_and_k_limits_results(tmp_path: Path) -> None:
    store = CorpusStore(tmp_path / "index.sqlite3")
    publish(store, scoped_corpus())
    retriever = SqliteRetriever(
        store.database, FakeEmbeddings(), model="test-model", digest=DIGEST, dimensions=4
    )
    found = retriever.search(RetrievalQuery(store_id="shop-a", revision="r1", text="test", k=2))
    assert [hit.chunk.chunk_id for hit in found] == ["category", "general"]


def test_corrupt_stored_vector_is_rejected(tmp_path: Path) -> None:
    store = CorpusStore(tmp_path / "index.sqlite3")
    publish(store, package(tmp_path / "input"))
    with closing(sqlite3.connect(store.database)) as connection, connection:
        connection.execute("UPDATE corpus_vectors SET vector = ?", (b"invalid",))
    retriever = SqliteRetriever(
        store.database, FakeEmbeddings(), model="test-model", digest=DIGEST, dimensions=4
    )
    with pytest.raises(RetrievalError, match="invalid_stored_vector"):
        retriever.search(RetrievalQuery(store_id="shop-a", revision="r1", text="test"))


@pytest.mark.parametrize("vector", [[1.0], [0.0] * 4, [float("nan"), 0, 0, 0]])
def test_invalid_query_vectors_are_rejected(tmp_path: Path, vector: list[float]) -> None:
    class BadEmbeddings:
        def embed(self, texts: tuple[str, ...], *, query: bool = False) -> EmbeddingResult:
            return EmbeddingResult(embeddings=[vector])

    store = CorpusStore(tmp_path / "index.sqlite3")
    publish(store, package(tmp_path / "input"))
    retriever = SqliteRetriever(
        store.database, BadEmbeddings(), model="test-model", digest=DIGEST, dimensions=4
    )
    with pytest.raises(ValueError):
        retriever.search(RetrievalQuery(store_id="shop-a", revision="r1", text="test"))


def test_empty_corpus_does_not_require_a_working_model(tmp_path: Path) -> None:
    store = CorpusStore(tmp_path / "index.sqlite3")
    original = package(tmp_path / "input")
    manifest = original.manifest.model_copy(update={"sources": (), "chunks": ()})
    publish(store, ValidatedCorpus(original.catalog, manifest))
    retriever = SqliteRetriever(
        store.database, FakeEmbeddings(fail=True), model="test-model", digest=DIGEST, dimensions=4
    )
    assert retriever.search(RetrievalQuery(store_id="shop-a", revision="r1", text="test")) == ()


def test_unknown_filter_and_provider_failure_are_explicit(tmp_path: Path) -> None:
    store = CorpusStore(tmp_path / "index.sqlite3")
    publish(store, package(tmp_path / "input"))
    retriever = SqliteRetriever(
        store.database, FakeEmbeddings(fail=True), model="test-model", digest=DIGEST, dimensions=4
    )
    with pytest.raises(RetrievalError, match="unknown_filter_id"):
        retriever.search(
            RetrievalQuery(store_id="shop-a", revision="r1", text="test", product_ids=("missing",))
        )
    with pytest.raises(ProviderError):
        retriever.search(RetrievalQuery(store_id="shop-a", revision="r1", text="test"))


def test_publication_during_query_cannot_mix_revisions(tmp_path: Path) -> None:
    store = CorpusStore(tmp_path / "index.sqlite3")
    original = package(tmp_path / "input", text="Old evidence")
    publish(store, original)

    class PublishingEmbeddings(FakeEmbeddings):
        def embed(self, texts: tuple[str, ...], *, query: bool = False) -> EmbeddingResult:
            updated = package(tmp_path / "input", revision="r2", text="New evidence")
            publish(store, updated)
            return super().embed(texts, query=query)

    retriever = SqliteRetriever(
        store.database, PublishingEmbeddings(), model="test-model", digest=DIGEST, dimensions=4
    )
    found = retriever.search(RetrievalQuery(store_id="shop-a", revision="r1", text="test"))
    assert found[0].chunk == original.manifest.chunks[0]
    assert "Old evidence" in found[0].chunk.text
    with pytest.raises(RetrievalError, match="not_active"):
        retriever.search(RetrievalQuery(store_id="shop-a", revision="r1", text="test"))
