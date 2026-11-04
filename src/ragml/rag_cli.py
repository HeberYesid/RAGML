"""Run the phase-4 baseline locally without changing the foundation HTTP API."""

import argparse
import json
import time
from pathlib import Path

from ragml.api import read_model_lock
from ragml.contracts import CatalogDataset
from ragml.evidence import SourceManifest
from ragml.ports import RetrievalQuery
from ragml.providers import OllamaClient, ProviderError
from ragml.rag import DocumentRag
from ragml.retrieval import RetrievalError, SqliteRetriever
from ragml.settings import load_settings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question", help="Single-turn Spanish document question")
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--database", type=Path, default=Path("data/runtime/corpus.sqlite3"))
    parser.add_argument("--revision", help="Defaults to the configured source manifest revision")
    parser.add_argument("--product-id", action="append", default=[])
    parser.add_argument("--variant-id", action="append", default=[])
    parser.add_argument("--category-id", action="append", default=[])
    parser.add_argument("--no-store-policies", action="store_true")
    parser.add_argument("--k", type=int)
    parser.add_argument("--retrieval-only", action="store_true")
    parser.add_argument("--output", type=Path, help="Optional local JSON evidence file")
    args = parser.parse_args(argv)
    client: OllamaClient | None = None
    try:
        settings = load_settings(args.project_dir)
        catalog = CatalogDataset.model_validate_json(
            settings.resolve_path(settings.catalog_path).read_bytes()
        )
        manifest = SourceManifest.model_validate_json(
            settings.resolve_path(settings.source_manifest).read_bytes()
        )
        manifest.validate_for_catalog(catalog)
        lock = read_model_lock(settings)
        client = OllamaClient(settings, lock)
        retriever = SqliteRetriever(
            settings.resolve_path(args.database),
            client,
            model=lock.embedding.tag,
            digest=lock.embedding.digest,
            dimensions=lock.embedding_dimensions,
        )
        query = RetrievalQuery(
            store_id=catalog.profile.store_id,
            revision=args.revision or manifest.revision,
            text=args.question,
            k=args.k if args.k is not None else settings.retrieval_k,
            product_ids=tuple(args.product_id),
            variant_ids=tuple(args.variant_id),
            category_ids=tuple(args.category_id),
            include_store_policies=not args.no_store_policies,
        )
        if args.retrieval_only:
            started = time.monotonic()
            snapshot = retriever.snapshot(query.store_id, query.revision)
            hits = retriever.search_snapshot(snapshot, query)
            payload: dict[str, object] = {
                "kind": "phase4_retrieval_probe_not_final_evaluation",
                "index": snapshot.info.model_dump(mode="json"),
                "retrieved": [hit.model_dump(mode="json") for hit in hits],
                "metrics": {"retrieval_seconds": round(time.monotonic() - started, 6)},
            }
            status = 0
        else:
            rag = DocumentRag(
                retriever,
                client,
                generation_model=lock.generation.tag,
                generation_digest=lock.generation.digest,
                data_mode=settings.data_mode,
                context_tokens=settings.context_tokens,
                output_tokens=settings.output_tokens,
            )
            run = rag.answer(query)
            payload = {
                "kind": "phase4_document_probe_not_final_evaluation",
                "response": run.response.model_dump(mode="json"),
                "retrieved": [hit.model_dump(mode="json") for hit in run.retrieved],
                "context_chunk_ids": list(run.context_chunk_ids),
                "metrics": run.metrics,
            }
            status = 1 if run.response.status == "temporarily_unavailable" else 0
        text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            output = settings.resolve_path(args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(text, encoding="utf-8")
        print(text, end="")
        return status
    except (OSError, ValueError, ProviderError) as error:
        code = (
            str(error)
            if isinstance(error, RetrievalError | ProviderError)
            else type(error).__name__
        )
        print(json.dumps({"status": "failed", "code": code}))
        return 1
    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    raise SystemExit(main())
