"""Validated, atomic publication of a store's document corpus and local vectors."""

import argparse
import json
import math
import sqlite3
import struct
import time
from collections.abc import Callable
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

from ragml.contracts import CatalogDataset, CommercialDataset, Contract
from ragml.evidence import Chunk, SourceManifest
from ragml.ports import EmbeddingPort
from ragml.providers import ModelLock, OllamaClient, ProviderError
from ragml.settings import load_settings


@dataclass(frozen=True)
class ValidatedCorpus:
    catalog: CatalogDataset
    manifest: SourceManifest

    @property
    def fingerprint(self) -> str:
        payload = self.catalog.model_dump_json() + "\n" + self.manifest.model_dump_json()
        return sha256(payload.encode("utf-8")).hexdigest()


def read_corpus(
    project_dir: Path,
    catalog_path: Path,
    manifest_path: Path,
    commercial_path: Path | None = None,
) -> ValidatedCorpus:
    root = project_dir.resolve()
    catalog_path = (root / catalog_path).resolve()
    manifest_path = (root / manifest_path).resolve()
    catalog = CatalogDataset.model_validate_json(catalog_path.read_bytes())
    manifest = SourceManifest.model_validate_json(manifest_path.read_bytes())
    manifest.validate_for_catalog(catalog)
    if commercial_path is not None:
        commercial = CommercialDataset.model_validate_json((root / commercial_path).read_bytes())
        commercial.validate_for_catalog(catalog)
    texts: dict[str, str] = {}
    for source in manifest.sources:
        if not source.active:
            continue
        path = (root / source.locator).resolve()
        if not path.is_relative_to(root):
            raise ValueError("source_outside_project")
        raw = path.read_bytes()
        if sha256(raw).hexdigest() != source.content_hash:
            raise ValueError("source_file_hash_mismatch")
        texts[source.source_id] = raw.decode("utf-8")
    represented: set[str] = set()
    for chunk in manifest.chunks:
        if chunk.text not in texts[chunk.source_id]:
            raise ValueError("chunk_not_in_source")
        represented.add(chunk.source_id)
    if represented != set(texts):
        raise ValueError("active_source_without_chunks")
    return ValidatedCorpus(catalog, manifest)


class IndexInfo(Contract):
    store_id: str
    revision: str
    fingerprint: str
    embedding_model: str
    embedding_digest: str
    dimensions: int
    sources: int
    chunks: int
    published_at: str


@dataclass(frozen=True)
class EmbeddedChunk:
    chunk: Chunk
    vector: tuple[float, ...]


class CorpusStore:
    """One active corpus revision per store; no obsolete fragments remain queryable."""

    def __init__(self, database: Path) -> None:
        self.database = database
        database.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS corpus_publications (
                    store_id TEXT PRIMARY KEY, revision TEXT NOT NULL,
                    fingerprint TEXT NOT NULL, info_json TEXT NOT NULL,
                    catalog_json TEXT NOT NULL, manifest_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS corpus_vectors (
                    store_id TEXT NOT NULL REFERENCES corpus_publications(store_id)
                        ON DELETE CASCADE,
                    chunk_id TEXT NOT NULL, source_id TEXT NOT NULL,
                    chunk_json TEXT NOT NULL, vector BLOB NOT NULL,
                    PRIMARY KEY (store_id, chunk_id)
                );
                CREATE INDEX IF NOT EXISTS corpus_source_idx
                    ON corpus_vectors(store_id, source_id);
                CREATE TABLE IF NOT EXISTS corpus_audit (
                    event_id INTEGER PRIMARY KEY,
                    store_id TEXT NOT NULL, revision TEXT NOT NULL,
                    fingerprint TEXT NOT NULL, published_at TEXT NOT NULL,
                    chunks INTEGER NOT NULL
                );
            """)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database, timeout=10)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def info(self, store_id: str) -> IndexInfo | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT info_json FROM corpus_publications WHERE store_id = ?", (store_id,)
            ).fetchone()
        return IndexInfo.model_validate_json(row[0]) if row else None

    def load(self, store_id: str, revision: str) -> SourceManifest:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT manifest_json FROM corpus_publications WHERE store_id = ? AND revision = ?",
                (store_id, revision),
            ).fetchone()
        if row is None:
            raise ValueError("corpus_revision_not_active")
        return SourceManifest.model_validate_json(row[0])

    def catalog(self, store_id: str, revision: str) -> CatalogDataset:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT catalog_json FROM corpus_publications WHERE store_id = ? AND revision = ?",
                (store_id, revision),
            ).fetchone()
        if row is None:
            raise ValueError("corpus_revision_not_active")
        return CatalogDataset.model_validate_json(row[0])

    def vectors(self, store_id: str, revision: str) -> tuple[EmbeddedChunk, ...]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT v.chunk_json, v.vector, p.info_json FROM corpus_vectors v "
                "JOIN corpus_publications p ON v.store_id = p.store_id "
                "WHERE p.store_id = ? AND p.revision = ? ORDER BY v.chunk_id",
                (store_id, revision),
            ).fetchall()
            active = connection.execute(
                "SELECT 1 FROM corpus_publications WHERE store_id = ? AND revision = ?",
                (store_id, revision),
            ).fetchone()
        if active is None:
            raise ValueError("corpus_revision_not_active")
        result = []
        for chunk_json, raw, info_json in rows:
            dimensions = IndexInfo.model_validate_json(info_json).dimensions
            if len(raw) != dimensions * 4:
                raise ValueError("invalid_stored_vector")
            vector = struct.unpack(f"<{dimensions}f", raw)
            self._validate_vector(vector, dimensions)
            result.append(EmbeddedChunk(Chunk.model_validate_json(chunk_json), vector))
        return tuple(result)

    @staticmethod
    def _validate_vector(vector: tuple[float, ...], dimensions: int) -> None:
        if len(vector) != dimensions or any(not math.isfinite(v) for v in vector):
            raise ValueError("invalid_embedding_dimensions_or_values")
        if not math.isclose(math.fsum(v * v for v in vector), 1, abs_tol=0.01):
            raise ValueError("embedding_not_normalized")

    def publish(
        self,
        corpus: ValidatedCorpus,
        embedder: EmbeddingPort,
        *,
        model: str,
        digest: str,
        dimensions: int = 1024,
        batch_size: int = 16,
        progress: Callable[[int, int], None] | None = None,
    ) -> tuple[IndexInfo, bool]:
        if not 1 <= batch_size <= 16 or dimensions < 1:
            raise ValueError("invalid_embedding_batch_or_dimensions")
        if (
            not model.strip()
            or len(digest) != 64
            or any(c not in "0123456789abcdef" for c in digest)
        ):
            raise ValueError("invalid_embedding_identity")
        manifest = corpus.manifest
        manifest.validate_for_catalog(corpus.catalog)
        old = self.info(manifest.store_id)
        fingerprint = corpus.fingerprint
        if old and old.revision == manifest.revision and old.fingerprint != fingerprint:
            raise ValueError("changed_corpus_requires_new_revision")
        if old and (old.fingerprint, old.embedding_model, old.embedding_digest, old.dimensions) == (
            fingerprint,
            model,
            digest,
            dimensions,
        ):
            return old, False
        vectors: list[tuple[float, ...]] = []
        for offset in range(0, len(manifest.chunks), batch_size):
            batch = manifest.chunks[offset : offset + batch_size]
            embedded = embedder.embed(tuple(c.text for c in batch))
            if len(embedded.embeddings) != len(batch):
                raise ValueError("embedding_count_mismatch")
            for values in embedded.embeddings:
                vector = tuple(values)
                self._validate_vector(vector, dimensions)
                vectors.append(vector)
            if progress:
                progress(len(vectors), len(manifest.chunks))
        info = IndexInfo(
            store_id=manifest.store_id,
            revision=manifest.revision,
            fingerprint=fingerprint,
            embedding_model=model,
            embedding_digest=digest,
            dimensions=dimensions,
            sources=sum(s.active for s in manifest.sources),
            chunks=len(manifest.chunks),
            published_at=datetime.now(UTC).isoformat(),
        )
        with closing(self._connect()) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT info_json FROM corpus_publications WHERE store_id = ?", (manifest.store_id,)
            ).fetchone()
            current = IndexInfo.model_validate_json(row[0]) if row else None
            if current != old:
                raise ValueError("index_changed_during_ingest")
            connection.execute(
                "DELETE FROM corpus_publications WHERE store_id = ?", (manifest.store_id,)
            )
            connection.execute(
                "INSERT INTO corpus_publications VALUES (?, ?, ?, ?, ?, ?)",
                (
                    manifest.store_id,
                    manifest.revision,
                    fingerprint,
                    info.model_dump_json(),
                    corpus.catalog.model_dump_json(),
                    manifest.model_dump_json(),
                ),
            )
            connection.executemany(
                "INSERT INTO corpus_vectors VALUES (?, ?, ?, ?, ?)",
                [
                    (
                        manifest.store_id,
                        chunk.chunk_id,
                        chunk.source_id,
                        chunk.model_dump_json(),
                        struct.pack(f"<{dimensions}f", *vector),
                    )
                    for chunk, vector in zip(manifest.chunks, vectors, strict=True)
                ],
            )
            connection.execute(
                "INSERT INTO corpus_audit(store_id, revision, fingerprint, published_at, chunks) "
                "VALUES (?, ?, ?, ?, ?)",
                (info.store_id, info.revision, info.fingerprint, info.published_at, info.chunks),
            )
        return info, True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--database", type=Path, default=Path("data/runtime/corpus.sqlite3"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--batch-size", type=int, default=16)
    args = parser.parse_args()
    started = time.monotonic()
    client: OllamaClient | None = None
    try:
        settings = load_settings(args.project_dir)
        corpus = read_corpus(
            settings.project_dir,
            settings.resolve_path(settings.catalog_path),
            settings.resolve_path(settings.source_manifest),
            settings.resolve_path(settings.commercial_path),
        )
        if corpus.catalog.profile.data_mode != settings.data_mode:
            raise ValueError("configured_data_mode_mismatch")
        lock = ModelLock.model_validate_json(
            settings.resolve_path(settings.model_lock_path).read_bytes()
        )
        client = OllamaClient(settings, lock)
        store = CorpusStore(settings.resolve_path(args.database))
        info, changed = store.publish(
            corpus,
            client,
            model=lock.embedding.tag,
            digest=lock.embedding.digest,
            dimensions=lock.embedding_dimensions,
            batch_size=args.batch_size,
            progress=lambda done, total: print(f"Embedded {done}/{total}", flush=True),
        )
        result = {
            "status": "published" if changed else "unchanged",
            "kind": "local_corpus_ingestion_not_rag_evaluation",
            "index": info.model_dump(mode="json"),
            "wall_seconds": round(time.monotonic() - started, 3),
            "database_bytes": store.database.stat().st_size,
        }
        text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            output = settings.resolve_path(args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(text, encoding="utf-8")
        print(text, end="")
        return 0
    except (OSError, ValueError, sqlite3.Error, ProviderError) as error:
        print(
            json.dumps(
                {
                    "status": "failed",
                    "code": str(error)
                    if isinstance(error, ProviderError)
                    else type(error).__name__,
                }
            )
        )
        return 1
    finally:
        if client:
            client.close()


if __name__ == "__main__":
    raise SystemExit(main())
