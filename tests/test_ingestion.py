"""Data publication checks with real SQLite transactions and synthetic vectors."""

import json
import sqlite3
from contextlib import closing
from hashlib import sha256
from pathlib import Path

import pytest
from test_local_contracts import make_catalog, write_commercial

from ragml.evidence import Chunk, Location, Source, SourceManifest, SourceScope
from ragml.ingestion import CorpusStore, ValidatedCorpus, read_corpus
from ragml.providers import EmbeddingResult, ProviderError

DIGEST = "e" * 64


class FakeEmbeddings:
    def __init__(self, fail: bool = False) -> None:
        self.calls = 0
        self.fail = fail

    def embed(self, texts: tuple[str, ...], *, query: bool = False) -> EmbeddingResult:
        self.calls += 1
        if self.fail:
            raise ProviderError("provider_unavailable")
        return EmbeddingResult(embeddings=[[1.0, 0.0, 0.0, 0.0] for _ in texts])


def package(
    root: Path, store: str = "shop-a", revision: str = "r1", text: str = "Regla A"
) -> ValidatedCorpus:
    root.mkdir(parents=True, exist_ok=True)
    catalog = make_catalog(store, "COP" if store == "shop-a" else "USD")
    section = f"## Consulta\n\n{text}"
    raw = f"# Política\n\n{section}\n".encode()
    (root / "policy.md").write_bytes(raw)
    source = Source(
        store_id=store,
        source_id="policy",
        title="Synthetic rule",
        version=revision,
        content_hash=sha256(raw).hexdigest(),
        data_mode="demo",
        scope=SourceScope(kind="store"),
        locator="policy.md",
        provenance="synthetic_created",
    )
    chunk = Chunk(
        store_id=store,
        chunk_id="chunk-1",
        source_id=source.source_id,
        source_version=revision,
        source_content_hash=source.content_hash,
        content_hash=sha256(section.encode()).hexdigest(),
        text=section,
        location=Location(section="Consulta"),
    )
    manifest = SourceManifest(
        store_id=store,
        data_mode="demo",
        revision=revision,
        sources=(source,),
        chunks=(chunk,),
    )
    (root / "catalog.json").write_text(catalog.model_dump_json(), encoding="utf-8")
    (root / "sources.json").write_text(manifest.model_dump_json(), encoding="utf-8")
    return read_corpus(root, Path("catalog.json"), Path("sources.json"))


def publish(
    store: CorpusStore, corpus: ValidatedCorpus, embedder: FakeEmbeddings | None = None
) -> None:
    store.publish(
        corpus, embedder or FakeEmbeddings(), model="test-model", digest=DIGEST, dimensions=4
    )


def test_publish_survives_reopening_and_retains_source_identity(tmp_path: Path) -> None:
    corpus = package(tmp_path / "input")
    store = CorpusStore(tmp_path / "index.sqlite3")
    publish(store, corpus)
    reopened = CorpusStore(store.database)
    assert reopened.load("shop-a", "r1") == corpus.manifest
    assert reopened.catalog("shop-a", "r1") == corpus.catalog
    assert reopened.vectors("shop-a", "r1")[0].vector == (1, 0, 0, 0)
    assert reopened.info("shop-a").embedding_digest == DIGEST  # type: ignore[union-attr]


def test_unchanged_publication_avoids_embedding_calls(tmp_path: Path) -> None:
    corpus = package(tmp_path / "input")
    store = CorpusStore(tmp_path / "index.sqlite3")
    publish(store, corpus)
    embedder = FakeEmbeddings(fail=True)
    _, changed = store.publish(corpus, embedder, model="test-model", digest=DIGEST, dimensions=4)
    assert not changed
    assert embedder.calls == 0


def test_update_replaces_old_text_and_refuses_old_revision(tmp_path: Path) -> None:
    store = CorpusStore(tmp_path / "index.sqlite3")
    publish(store, package(tmp_path / "input"))
    updated = package(tmp_path / "input", revision="r2", text="Nueva regla")
    publish(store, updated)
    assert "Nueva regla" in store.vectors("shop-a", "r2")[0].chunk.text
    with pytest.raises(ValueError, match="not_active"):
        store.load("shop-a", "r1")
    with closing(sqlite3.connect(store.database)) as connection:
        assert connection.execute("SELECT count(*) FROM corpus_vectors").fetchone() == (1,)


def test_withdrawal_removes_fragments_and_keeps_other_store(tmp_path: Path) -> None:
    store = CorpusStore(tmp_path / "index.sqlite3")
    original = package(tmp_path / "a")
    publish(store, original)
    publish(store, package(tmp_path / "b", store="shop-b", text="Other store"))
    payload = original.manifest.model_dump(mode="json")
    payload["revision"] = "withdrawn-r2"
    payload["sources"][0]["active"] = False
    payload["chunks"] = []
    withdrawn = SourceManifest.model_validate(payload)
    publish(store, ValidatedCorpus(original.catalog, withdrawn))
    assert store.vectors("shop-a", "withdrawn-r2") == ()
    assert store.load("shop-a", "withdrawn-r2").sources[0].active is False
    assert "Other store" in store.vectors("shop-b", "r1")[0].chunk.text
    assert store.catalog("shop-b", "r1").profile.currency == "USD"


def test_failed_provider_keeps_the_previous_corpus(tmp_path: Path) -> None:
    store = CorpusStore(tmp_path / "index.sqlite3")
    publish(store, package(tmp_path / "input"))
    updated = package(tmp_path / "input", revision="r2")
    with pytest.raises(ProviderError):
        publish(store, updated, FakeEmbeddings(fail=True))
    assert store.load("shop-a", "r1").revision == "r1"


def test_sqlite_failure_rolls_back_the_entire_replacement(tmp_path: Path) -> None:
    store = CorpusStore(tmp_path / "index.sqlite3")
    old = package(tmp_path / "input")
    publish(store, old)
    with closing(sqlite3.connect(store.database)) as connection, connection:
        connection.execute(
            "CREATE TRIGGER reject_vectors BEFORE INSERT ON corpus_vectors "
            "BEGIN SELECT RAISE(ABORT, 'controlled failure'); END"
        )
    with pytest.raises(sqlite3.IntegrityError):
        publish(store, package(tmp_path / "input", revision="r2", text="Replacement"))
    assert store.load("shop-a", "r1") == old.manifest
    assert len(store.vectors("shop-a", "r1")) == 1


def test_changed_data_cannot_reuse_the_same_revision(tmp_path: Path) -> None:
    store = CorpusStore(tmp_path / "index.sqlite3")
    publish(store, package(tmp_path / "input"))
    with pytest.raises(ValueError, match="new_revision"):
        publish(store, package(tmp_path / "input", text="Changed"))


def test_commercial_update_does_not_rebuild_document_vectors(tmp_path: Path) -> None:
    root = tmp_path / "input"
    corpus = package(root)
    write_commercial(root / "commercial.json", corpus.catalog, revision="commercial-r1")
    store = CorpusStore(tmp_path / "index.sqlite3")
    publish(store, corpus)
    write_commercial(
        root / "commercial.json", corpus.catalog, amount="90.00", revision="commercial-r2"
    )
    reread = read_corpus(root, Path("catalog.json"), Path("sources.json"), Path("commercial.json"))
    embedder = FakeEmbeddings(fail=True)
    _, changed = store.publish(reread, embedder, model="test-model", digest=DIGEST, dimensions=4)
    assert not changed
    assert embedder.calls == 0


def test_concurrent_publication_is_not_overwritten_by_a_slow_job(tmp_path: Path) -> None:
    store = CorpusStore(tmp_path / "index.sqlite3")
    publish(store, package(tmp_path / "input"))
    newer = package(tmp_path / "input", revision="newer", text="Newer published text")
    slow = package(tmp_path / "input", revision="slow", text="Slow job text")

    class ConcurrentEmbedder(FakeEmbeddings):
        def embed(self, texts: tuple[str, ...], *, query: bool = False) -> EmbeddingResult:
            publish(store, newer)
            return super().embed(texts, query=query)

    with pytest.raises(ValueError, match="changed_during_ingest"):
        publish(store, slow, ConcurrentEmbedder())
    assert store.load("shop-a", "newer") == newer.manifest
    with pytest.raises(ValueError, match="not_active"):
        store.load("shop-a", "slow")


@pytest.mark.parametrize("corruption", ["file", "chunk", "path"])
def test_corrupt_sources_are_rejected_before_indexing(tmp_path: Path, corruption: str) -> None:
    package(tmp_path)
    data = json.loads((tmp_path / "sources.json").read_text(encoding="utf-8"))
    if corruption == "file":
        (tmp_path / "policy.md").write_text("changed file", encoding="utf-8")
    elif corruption == "chunk":
        text = "not in the document"
        data["chunks"][0]["text"] = text
        data["chunks"][0]["content_hash"] = sha256(text.encode()).hexdigest()
    else:
        data["sources"][0]["locator"] = "../outside.md"
    (tmp_path / "sources.json").write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError):
        read_corpus(tmp_path, Path("catalog.json"), Path("sources.json"))


@pytest.mark.parametrize("vector", [(0.0, 0.0, 0.0, 0.0), (1.0, 0.0), (float("nan"), 0, 0, 0)])
def test_invalid_vectors_are_rejected(vector: tuple[float, ...]) -> None:
    with pytest.raises(ValueError):
        CorpusStore._validate_vector(vector, 4)
