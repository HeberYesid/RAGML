"""Exact cosine retrieval over one consistent, read-only corpus snapshot."""

import math
import sqlite3
import struct
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from ragml.contracts import CatalogDataset
from ragml.evidence import SourceManifest
from ragml.ingestion import EmbeddedChunk, IndexInfo, ValidatedCorpus
from ragml.ports import EmbeddingPort, RetrievalQuery, RetrievedChunk


class RetrievalError(ValueError):
    """Safe index error codes without database paths or document contents."""


@dataclass(frozen=True)
class CorpusSnapshot:
    info: IndexInfo
    catalog: CatalogDataset
    manifest: SourceManifest
    vectors: tuple[EmbeddedChunk, ...]


class SqliteRetriever:
    def __init__(
        self,
        database: Path,
        embedder: EmbeddingPort,
        *,
        model: str,
        digest: str,
        dimensions: int = 1024,
    ) -> None:
        if dimensions < 1:
            raise ValueError("invalid_embedding_dimensions")
        self.database = database
        self.embedder = embedder
        self.model = model
        self.digest = digest
        self.dimensions = dimensions

    def snapshot(self, store_id: str, revision: str) -> CorpusSnapshot:
        """Read metadata and vectors together, without creating or changing an index."""
        try:
            uri = self.database.resolve().as_uri() + "?mode=ro"
            with closing(sqlite3.connect(uri, uri=True, timeout=10)) as connection:
                connection.execute("BEGIN")
                row = connection.execute(
                    "SELECT info_json, catalog_json, manifest_json FROM corpus_publications "
                    "WHERE store_id = ? AND revision = ?",
                    (store_id, revision),
                ).fetchone()
                if row is None:
                    raise RetrievalError("corpus_revision_not_active")
                info = IndexInfo.model_validate_json(row[0])
                if (info.embedding_model, info.embedding_digest, info.dimensions) != (
                    self.model,
                    self.digest,
                    self.dimensions,
                ):
                    raise RetrievalError("embedding_index_mismatch")
                catalog = CatalogDataset.model_validate_json(row[1])
                manifest = SourceManifest.model_validate_json(row[2])
                manifest.validate_for_catalog(catalog)
                if (
                    (info.store_id, manifest.store_id, catalog.profile.store_id)
                    != (store_id, store_id, store_id)
                    or (info.revision, manifest.revision) != (revision, revision)
                    or info.fingerprint != ValidatedCorpus(catalog, manifest).fingerprint
                    or info.chunks != len(manifest.chunks)
                    or info.sources != sum(source.active for source in manifest.sources)
                ):
                    raise RetrievalError("index_metadata_mismatch")
                rows = connection.execute(
                    "SELECT chunk_id, chunk_json, vector FROM corpus_vectors "
                    "WHERE store_id = ? ORDER BY chunk_id",
                    (store_id,),
                ).fetchall()
            expected = {chunk.chunk_id: chunk for chunk in manifest.chunks}
            if len(rows) != len(expected):
                raise RetrievalError("index_chunk_mismatch")
            vectors = []
            for chunk_id, chunk_json, raw in rows:
                chunk = expected.get(chunk_id)
                if chunk is None or chunk.model_dump_json() != chunk_json:
                    raise RetrievalError("index_chunk_mismatch")
                if len(raw) != self.dimensions * 4:
                    raise RetrievalError("invalid_stored_vector")
                vector = struct.unpack(f"<{self.dimensions}f", raw)
                self._validate_vector(vector)
                vectors.append(EmbeddedChunk(chunk, vector))
            return CorpusSnapshot(info, catalog, manifest, tuple(vectors))
        except RetrievalError:
            raise
        except (OSError, sqlite3.Error) as exc:
            raise RetrievalError("index_unavailable") from exc
        except (ValueError, TypeError, struct.error) as exc:
            raise RetrievalError("index_invalid") from exc

    def _validate_vector(self, vector: tuple[float, ...]) -> None:
        if (
            len(vector) != self.dimensions
            or any(not math.isfinite(value) for value in vector)
            or not math.isclose(math.fsum(value * value for value in vector), 1, abs_tol=0.01)
        ):
            raise RetrievalError("invalid_embedding_vector")

    def search(self, query: RetrievalQuery) -> tuple[RetrievedChunk, ...]:
        return self.search_snapshot(self.snapshot(query.store_id, query.revision), query)

    @staticmethod
    def _candidates(snapshot: CorpusSnapshot, query: RetrievalQuery) -> tuple[EmbeddedChunk, ...]:
        catalog = snapshot.catalog
        all_products = {product.product_id: product for product in catalog.products}
        all_variants = {variant.variant_id: variant for variant in catalog.variants}
        all_categories = {category.category_id for category in catalog.profile.categories}
        if (
            not set(query.product_ids) <= all_products.keys()
            or not set(query.variant_ids) <= all_variants.keys()
            or not set(query.category_ids) <= all_categories
        ):
            raise RetrievalError("unknown_filter_id")
        variant_parents = {all_variants[key].product_id for key in query.variant_ids}
        products = {
            key
            for key, product in all_products.items()
            if (not query.product_ids or key in query.product_ids)
            and (not query.category_ids or product.category_id in query.category_ids)
            and (not query.variant_ids or key in variant_parents)
        }
        if (query.product_ids or query.category_ids or query.variant_ids) and not products:
            return ()
        variants = {
            key
            for key, variant in all_variants.items()
            if variant.product_id in products
            and (not query.variant_ids or key in query.variant_ids)
        }
        categories = {all_products[key].category_id for key in products}
        allowed: dict[str, set[str | None]] = {
            "store": {None} if query.include_store_policies else set(),
            "category": set(categories),
            "product": set(products),
            "variant": set(variants),
        }
        sources = {
            source.source_id
            for source in snapshot.manifest.sources
            if source.active and source.scope.target_id in allowed[source.scope.kind]
        }
        return tuple(item for item in snapshot.vectors if item.chunk.source_id in sources)

    def search_snapshot(
        self, snapshot: CorpusSnapshot, query: RetrievalQuery
    ) -> tuple[RetrievedChunk, ...]:
        if (snapshot.info.store_id, snapshot.info.revision) != (query.store_id, query.revision):
            raise RetrievalError("snapshot_query_mismatch")
        if len(query.text) > 4000:
            raise ValueError("query_too_long")
        candidates = self._candidates(snapshot, query)
        if not candidates:
            return ()
        result = self.embedder.embed((query.text,), query=True)
        if len(result.embeddings) != 1:
            raise RetrievalError("invalid_query_embedding_count")
        vector = tuple(result.embeddings[0])
        self._validate_vector(vector)
        norm = math.sqrt(math.fsum(value * value for value in vector))
        scored = []
        for item in candidates:
            denominator = norm * math.sqrt(math.fsum(value * value for value in item.vector))
            score = math.fsum(a * b for a, b in zip(vector, item.vector, strict=True)) / denominator
            scored.append(RetrievedChunk(chunk=item.chunk, score=max(-1.0, min(1.0, score))))
        return tuple(sorted(scored, key=lambda hit: (-hit.score, hit.chunk.chunk_id))[: query.k])
