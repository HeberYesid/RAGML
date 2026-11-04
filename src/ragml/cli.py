"""Supported local entry points for preparation, diagnostics and model checks."""

import argparse
import json
import math
import time
from datetime import UTC, datetime
from pathlib import Path

import uvicorn
from pydantic import BaseModel

from ragml.api import check_sqlite, create_app, read_model_lock
from ragml.contracts import CatalogDataset, CommercialDataset
from ragml.conversation import ChatRequest, ChatResponse, ErrorResponse, SessionState
from ragml.evidence import SourceManifest
from ragml.providers import OllamaClient, ProviderError
from ragml.settings import Settings, load_settings


def probe_models(settings: Settings) -> dict[str, object]:
    client = OllamaClient(settings, read_model_lock(settings))
    try:
        measurements: dict[str, object] = {
            "checked_at": datetime.now(UTC).isoformat(),
            "kind": "synthetic_infrastructure_probe_not_rag_evaluation",
            "models": client.lock.model_dump(mode="json"),
            "context_tokens": settings.context_tokens,
            "output_limit_tokens": settings.output_tokens,
        }
        generation_runs = []
        for _ in range(2):
            started = time.monotonic()
            generated = client.generate(
                "Responde en español en una frase de menos de 25 palabras. Usa solo la ficha.",
                "Ficha ficticia: la lámpara Luma de prueba tiene potencia de 8 W. ¿Cuál es su potencia?",
                output_tokens=96,
            )
            generation_runs.append(
                {"wall_seconds": round(time.monotonic() - started, 3), **generated.model_dump()}
            )
        measurements["generation"] = generation_runs
        started = time.monotonic()
        documents = client.embed(
            (
                "Lámpara de escritorio de ocho vatios para iluminar una mesa.",
                "Caja organizadora con capacidad de doce litros.",
            )
        )
        query = client.embed(("¿Qué lámpara puedo usar para iluminar mi escritorio?",), query=True)
        similarities = [
            math.fsum(a * b for a, b in zip(query.embeddings[0], vector, strict=True))
            for vector in documents.embeddings
        ]
        if similarities[0] <= similarities[1]:
            raise ProviderError("synthetic_embedding_relevance_check_failed")
        measurements["embedding"] = {
            "wall_seconds": round(time.monotonic() - started, 3),
            "dimensions": len(query.embeddings[0]),
            "similarities": similarities,
            "document_count": len(documents.embeddings),
        }
        return measurements
    finally:
        client.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="RAGML local prototype foundation")
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--env-file", type=Path)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("serve", help="Start the loopback-only foundation API")
    commands.add_parser("doctor", help="Check local configuration, SQLite and model identities")
    probe = commands.add_parser("probe-models", help="Run a small synthetic local model probe")
    probe.add_argument("--output", type=Path, default=Path(".cache/verification/models-probe.json"))
    export = commands.add_parser(
        "export-contracts", help="Export JSON schemas and foundation OpenAPI"
    )
    export.add_argument("--output", type=Path, default=Path("docs/architecture/schemas"))
    args = parser.parse_args()
    try:
        settings = load_settings(args.project_dir, args.env_file)
        if args.command == "serve":
            uvicorn.run(
                create_app(settings), host=settings.host, port=settings.port, access_log=False
            )
        elif args.command == "doctor":
            client = OllamaClient(settings, read_model_lock(settings))
            try:
                models = client.check_models()
            finally:
                client.close()
            result = {
                "sqlite_version": check_sqlite(),
                "models": models,
                "foundation_ready": all(models.values()),
                "rag_available": False,
            }
            print(json.dumps(result, indent=2))
            return 0 if result["foundation_ready"] else 1
        elif args.command == "probe-models":
            output = settings.resolve_path(args.output)
            result = probe_models(settings)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(
                json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            print(f"Synthetic model probe saved: {output}")
        elif args.command == "export-contracts":
            output = settings.resolve_path(args.output)
            output.mkdir(parents=True, exist_ok=True)
            models_to_export: tuple[type[BaseModel], ...] = (
                CatalogDataset,
                CommercialDataset,
                SourceManifest,
                ChatRequest,
                ChatResponse,
                SessionState,
                ErrorResponse,
            )
            for model in models_to_export:
                (output / f"{model.__name__}.schema.json").write_text(
                    json.dumps(model.model_json_schema(), ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
            (output / "openapi.json").write_text(
                json.dumps(create_app(settings).openapi(), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            print(f"Contracts exported: {output}")
        return 0
    except (ProviderError, OSError, ValueError) as exc:
        code = str(exc) if isinstance(exc, ProviderError) else type(exc).__name__
        print(f"Local preparation failed: {code}. Check configuration and local services.")
        return 1
