"""Record actual integrated HTTP adjustment journeys, not semantic accuracy."""

import argparse
import json
import math
import platform
import re
import shutil
import socket
import threading
import time
from collections import Counter
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit
from uuid import UUID

import httpx
import uvicorn
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from ragml.contracts import Contract
from ragml.conversation import ChatRequest, ChatResponse, DocumentCitation
from ragml.evaluation import CaseResult, EvaluationRun, summarize, write_run
from ragml.evidence import Chunk, Location, SourceManifest
from ragml.ingestion import CorpusStore, read_corpus
from ragml.ports import EmbeddingPort
from ragml.providers import ModelLock, OllamaClient, ProviderError
from ragml.settings import Settings, load_settings
from ragml.web import create_web_app


class ReferenceUserTurn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Literal["user"]
    text: str


class IntegratedReferenceCase(BaseModel):
    model_config = ConfigDict(extra="ignore")
    case_id: str
    partition: Literal["adjustment"]
    family_id: str
    category_id: str
    task_type: str
    store_id: str
    corpus_revision: str
    evaluated_at: AwareDatetime
    turns: tuple[ReferenceUserTurn, ...] = Field(min_length=1)
    gold_chunk_ids: tuple[str, ...]
    expected_status: str
    acceptable_variant_ids: tuple[str, ...] | None = None
    fixture: dict[str, str] | None = None


class IntegratedReferenceSet(BaseModel):
    model_config = ConfigDict(extra="ignore")
    partition: Literal["adjustment"]
    reference_set_revision: str
    store_id: str
    corpus_revision: str
    cases: tuple[IntegratedReferenceCase, ...] = Field(min_length=1)


class HttpTurnRecord(Contract):
    message: str
    started_at: AwareDatetime
    seconds: float = Field(ge=0, allow_inf_nan=False)
    http_status: int | None = None
    response: ChatResponse | None = None
    error_code: str | None = None


class IntegratedCaseRecord(Contract):
    case_id: str
    task_type: str
    category_id: str
    execution: Literal["completed", "error", "not_run"]
    reason: str | None = None
    turns: tuple[HttpTurnRecord, ...] = ()
    result: CaseResult | None = None
    checks: dict[str, bool | None] = Field(default_factory=dict)
    session_cleanup_status: int | None = None
    fixture_preparation_seconds: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    fixture_artifacts: dict[str, object] = Field(default_factory=dict)


@dataclass(frozen=True)
class SecurityFixture:
    settings: Settings
    case: IntegratedReferenceCase
    manifest: SourceManifest
    provenance: dict[str, object]


def prepare_security_fixture(
    settings: Settings,
    case: IntegratedReferenceCase,
    destination: Path,
    embedder: EmbeddingPort,
) -> SecurityFixture:
    """Version an adversarial demo document and rebuild only an isolated index."""
    if (
        settings.data_mode != "demo"
        or case.fixture is None
        or case.fixture.get("kind") != "untrusted_document_append"
        or re.fullmatch(r"[A-Za-z0-9_-]+", case.case_id) is None
    ):
        raise ValueError("unsupported_security_fixture")
    corpus = read_corpus(
        settings.project_dir,
        settings.catalog_path,
        settings.source_manifest,
        settings.commercial_path,
    )
    matching = [s for s in corpus.manifest.sources if s.source_id == case.fixture.get("source_id")]
    if len(matching) != 1 or not case.fixture.get("text", "").strip():
        raise ValueError("invalid_security_fixture_source")
    source = matching[0]
    source_path = (settings.project_dir / source.locator).resolve()
    paths = {
        settings.resolve_path(settings.catalog_path),
        settings.resolve_path(settings.commercial_path),
        settings.resolve_path(settings.source_manifest),
        settings.resolve_path(settings.model_lock_path),
        *((settings.project_dir / s.locator).resolve() for s in corpus.manifest.sources),
    }
    metadata_path = settings.resolve_path(settings.catalog_path).parent / "package-metadata.json"
    if metadata_path.is_file():
        paths.add(metadata_path)
    relative_paths = {path: path.relative_to(settings.project_dir.resolve()) for path in paths}
    destination.mkdir(parents=True, exist_ok=False)
    for path, relative in relative_paths.items():
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    clone = settings.model_copy(update={"project_dir": destination.resolve()})
    clone_source_path = clone.project_dir / relative_paths[source_path]
    original_bytes = clone_source_path.read_bytes()
    appended = original_bytes + (
        "\n\n## Untrusted fixture\n\n" + case.fixture["text"] + "\n"
    ).encode("utf-8")
    clone_source_path.write_bytes(appended)
    source_hash = sha256(appended).hexdigest()
    suffix = "-fixture-" + case.case_id.lower()
    source_version = source.version + suffix
    new_source = source.model_copy(update={"version": source_version, "content_hash": source_hash})
    chunks = [
        chunk.model_copy(
            update={"source_version": source_version, "source_content_hash": source_hash}
        )
        if chunk.source_id == source.source_id
        else chunk
        for chunk in corpus.manifest.chunks
    ]
    chunks.append(
        Chunk(
            store_id=case.store_id,
            chunk_id=source.source_id + "-untrusted-fixture",
            source_id=source.source_id,
            source_version=source_version,
            source_content_hash=source_hash,
            content_hash=sha256(case.fixture["text"].encode("utf-8")).hexdigest(),
            text=case.fixture["text"],
            location=Location(section="Untrusted fixture"),
        )
    )
    updated = SourceManifest.model_validate(
        corpus.manifest.model_copy(
            update={
                "revision": corpus.manifest.revision + suffix,
                "sources": tuple(
                    new_source if s.source_id == source.source_id else s
                    for s in corpus.manifest.sources
                ),
                "chunks": tuple(chunks),
            }
        ).model_dump()
    )
    clone.resolve_path(clone.source_manifest).write_text(
        updated.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    clone_metadata = clone.resolve_path(clone.catalog_path).parent / "package-metadata.json"
    if clone_metadata.is_file():
        metadata = json.loads(clone_metadata.read_bytes())
        for relative in metadata.get("file_hashes", {}):
            path = (clone.project_dir / relative).resolve()
            path.relative_to(clone.project_dir)
            if path.is_file():
                metadata["file_hashes"][relative] = sha256(path.read_bytes()).hexdigest()
        metadata["security_fixture"] = {
            "case_id": case.case_id,
            "original_revision": source.version,
        }
        clone_metadata.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    validated = read_corpus(
        clone.project_dir, clone.catalog_path, clone.source_manifest, clone.commercial_path
    )
    lock = ModelLock.model_validate_json(clone.resolve_path(clone.model_lock_path).read_bytes())
    info, _ = CorpusStore(clone.resolve_path(clone.runtime_dir) / "corpus.sqlite3").publish(
        validated,
        embedder,
        model=lock.embedding.tag,
        digest=lock.embedding.digest,
        dimensions=lock.embedding_dimensions,
    )
    provenance: dict[str, object] = {
        "case_id": case.case_id,
        "source_id": source.source_id,
        "original_source_sha256": sha256(original_bytes).hexdigest(),
        "fixture_source_sha256": source_hash,
        "fixture_manifest_sha256": sha256(
            clone.resolve_path(clone.source_manifest).read_bytes()
        ).hexdigest(),
        "fixture_index": info.model_dump(),
        "untrusted_chunk_id": chunks[-1].chunk_id,
        "limit": "Inclusion in the index does not establish that this chunk reached model context.",
    }
    _write_json(clone.project_dir / "fixture.json", provenance)
    return SecurityFixture(
        clone,
        case.model_copy(update={"fixture": None, "corpus_revision": updated.revision}),
        updated,
        provenance,
    )


@contextmanager
def _fixture_client(
    settings: Settings, timeout_seconds: float, transport: httpx.BaseTransport | None
) -> Iterator[httpx.Client]:
    if transport is not None:
        with httpx.Client(
            base_url="http://127.0.0.1:8000",
            timeout=timeout_seconds,
            trust_env=False,
            follow_redirects=False,
            transport=transport,
        ) as client:
            yield client
        return
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(128)
        port = listener.getsockname()[1]
        server = uvicorn.Server(
            uvicorn.Config(
                create_web_app(settings.model_copy(update={"port": port})),
                host="127.0.0.1",
                port=port,
                loop="asyncio",
                ws="none",
                log_level="error",
                access_log=False,
                timeout_graceful_shutdown=5,
            )
        )
        worker = threading.Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
        worker.start()
        try:
            deadline = time.monotonic() + 30
            while not server.started:
                if not worker.is_alive() or time.monotonic() > deadline:
                    raise RuntimeError("fixture_http_server_start_failed")
                time.sleep(0.02)
            with httpx.Client(
                base_url=f"http://127.0.0.1:{port}",
                timeout=timeout_seconds,
                trust_env=False,
                follow_redirects=False,
            ) as client:
                yield client
        finally:
            server.should_exit = True
            worker.join(timeout=8)
            if worker.is_alive():
                server.force_exit = True
                worker.join(timeout=2)
            if worker.is_alive():
                raise RuntimeError("fixture_http_server_stop_failed")


def evaluate_security_fixture(
    settings: Settings,
    case: IntegratedReferenceCase,
    destination: Path,
    *,
    timeout_seconds: float = 240,
    transport: httpx.BaseTransport | None = None,
) -> IntegratedCaseRecord:
    """Execute the source fixture against its own versioned loopback web server."""
    preparation_started = time.monotonic()
    provider: OllamaClient | None = None
    try:
        lock = ModelLock.model_validate_json(
            settings.resolve_path(settings.model_lock_path).read_bytes()
        )
        provider = OllamaClient(settings, lock)
        fixture = prepare_security_fixture(settings, case, destination, provider)
        preparation_seconds = round(time.monotonic() - preparation_started, 6)
        with _fixture_client(fixture.settings, timeout_seconds, transport) as client:
            record = evaluate_case(fixture.case, client, fixture.manifest)
        return record.model_copy(
            update={
                "fixture_preparation_seconds": preparation_seconds,
                "fixture_artifacts": fixture.provenance,
            }
        )
    except (OSError, ValueError, RuntimeError, ProviderError) as error:
        elapsed = round(time.monotonic() - preparation_started, 6)
        code = "security_fixture_" + type(error).__name__
        return IntegratedCaseRecord(
            case_id=case.case_id,
            task_type=case.task_type,
            category_id=case.category_id,
            execution="error",
            reason=code,
            fixture_preparation_seconds=elapsed,
            result=CaseResult(
                case_id=case.case_id,
                family_id=case.family_id,
                category_id=case.category_id,
                task_type=case.task_type,
                evaluated_at=case.evaluated_at,
                execution="error",
                error_code=code,
                timings_seconds={"total": elapsed, "fixture_preparation": elapsed},
            ),
        )
    finally:
        if provider is not None:
            provider.close()


def _literal_citations(response: ChatResponse, manifest: SourceManifest) -> bool | None:
    citations = [c for c in response.citations if isinstance(c, DocumentCitation)]
    if not citations:
        return None
    chunks = {chunk.chunk_id: chunk for chunk in manifest.chunks}
    return all(
        (chunk := chunks.get(citation.chunk_id)) is not None
        and (chunk.source_id, chunk.source_version, chunk.location)
        == (citation.source_id, citation.source_version, citation.location)
        and citation.excerpt in chunk.text
        for citation in citations
    )


def evaluate_case(
    case: IntegratedReferenceCase, client: httpx.Client, manifest: SourceManifest
) -> IntegratedCaseRecord:
    """Run user turns with fresh cookies; retain server answers and fail explicitly."""
    if case.fixture:
        return IntegratedCaseRecord(
            case_id=case.case_id,
            task_type=case.task_type,
            category_id=case.category_id,
            execution="not_run",
            reason="isolated_source_fixture_required",
        )
    client.cookies.clear()
    session_id: UUID | None = None
    turns: list[HttpTurnRecord] = []
    last_response: ChatResponse | None = None
    error_code: str | None = None
    started = time.monotonic()
    for turn in case.turns:
        turn_started = time.monotonic()
        observed_at = datetime.now(UTC)
        response: ChatResponse | None = None
        http_status: int | None = None
        try:
            raw = client.post(
                "/v1/chat",
                json=ChatRequest(message=turn.text, session_id=session_id).model_dump(mode="json"),
            )
            http_status = raw.status_code
            if raw.status_code != 200:
                error_code = f"http_{raw.status_code}"
            else:
                response = ChatResponse.model_validate_json(raw.content)
                if response.store_id != case.store_id or response.versions.get("corpus") != (
                    case.corpus_revision
                ):
                    error_code = "response_reference_scope_mismatch"
                elif response.status == "temporarily_unavailable":
                    error_code = "assistant_temporarily_unavailable"
                else:
                    session_id = response.session_id
                    last_response = response
        except httpx.HTTPError:
            error_code = "http_request_failed"
        except ValueError:
            error_code = "invalid_http_response"
        turns.append(
            HttpTurnRecord(
                message=turn.text,
                started_at=observed_at,
                seconds=round(time.monotonic() - turn_started, 6),
                http_status=http_status,
                response=response,
                error_code=error_code,
            )
        )
        if error_code is not None:
            break
    elapsed = round(time.monotonic() - started, 6)
    cleanup: int | None = None
    if session_id is not None:
        try:
            cleanup = client.delete(f"/v1/chat/sessions/{session_id}").status_code
        except httpx.HTTPError:
            pass
    succeeded = error_code is None and last_response is not None
    result = CaseResult(
        case_id=case.case_id,
        family_id=case.family_id,
        category_id=case.category_id,
        task_type=case.task_type,
        evaluated_at=case.evaluated_at,
        execution="completed" if succeeded else "error",
        error_code=error_code,
        response_status=last_response.status if succeeded and last_response else None,
        timings_seconds={"total": elapsed},
        response=last_response if succeeded else None,
        warm_state="unknown",
    )
    checks = {
        "expected_status_match": last_response.status == case.expected_status
        if succeeded and last_response
        else False,
        "returned_products_in_acceptable_set": all(
            product.variant_id in case.acceptable_variant_ids for product in last_response.products
        )
        if succeeded and last_response and case.acceptable_variant_ids is not None
        else None,
        "literal_document_citations_valid": _literal_citations(last_response, manifest)
        if succeeded and last_response
        else None,
    }
    return IntegratedCaseRecord(
        case_id=case.case_id,
        task_type=case.task_type,
        category_id=case.category_id,
        execution="completed" if succeeded else "error",
        reason=error_code,
        turns=tuple(turns),
        result=result,
        checks=checks,
        session_cleanup_status=cleanup,
    )


def _write_json(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def _loopback_url(value: str) -> str:
    parsed = urlsplit(value)
    if (
        parsed.scheme != "http"
        or parsed.hostname != "127.0.0.1"
        or parsed.port is None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("explicit_ipv4_loopback_http_url_required")
    return value.rstrip("/")


def _candidate_files(settings: Settings, manifest: SourceManifest) -> dict[str, Path]:
    package = Path(__file__).resolve().parent
    files = {f"package/{path.name}": path for path in package.glob("*.py")}
    files.update(
        {
            f"package/web_assets/{path.name}": path
            for path in (package / "web_assets").glob("*")
            if path.is_file()
        }
    )
    for name, path in (
        ("catalog", settings.resolve_path(settings.catalog_path)),
        ("commercial", settings.resolve_path(settings.commercial_path)),
        ("source_manifest", settings.resolve_path(settings.source_manifest)),
        ("model_lock", settings.resolve_path(settings.model_lock_path)),
        ("dependency_lock", settings.project_dir / "uv.lock"),
        ("project_config", settings.project_dir / "pyproject.toml"),
        ("runtime_lock", settings.project_dir / "config/runtime.lock.json"),
        (
            "demo_metadata",
            settings.resolve_path(settings.catalog_path).parent / "package-metadata.json",
        ),
    ):
        if path.is_file():
            files[name] = path
    for source in manifest.sources:
        path = (settings.project_dir / source.locator).resolve()
        path.relative_to(settings.project_dir.resolve())
        files[f"document/{source.source_id}"] = path
    return files


def _mechanical_summary(
    records: list[IntegratedCaseRecord], selected: tuple[IntegratedReferenceCase, ...]
) -> dict[str, object]:
    def group(members: list[IntegratedCaseRecord], planned: int) -> dict[str, object]:
        return {
            "coverage": {
                "planned": planned,
                "attempted": sum(r.execution != "not_run" for r in members),
                "completed": sum(r.execution == "completed" for r in members),
                "errors": sum(r.execution == "error" for r in members),
                "not_run": planned - sum(r.execution != "not_run" for r in members),
            },
            "checks": {
                key: {
                    "matched": sum(r.checks.get(key) is True for r in members),
                    "assessed": sum(r.checks.get(key) is not None for r in members),
                }
                for key in (
                    "expected_status_match",
                    "returned_products_in_acceptable_set",
                    "literal_document_citations_valid",
                )
            },
        }

    return {
        "kind": "integrated_adjustment_mechanical_checks_not_semantic_accuracy",
        **group(records, len(selected)),
        "not_run_reasons": dict(Counter(r.reason for r in records if r.execution == "not_run")),
        "by_task": {
            task: group(
                [r for r in records if r.task_type == task],
                sum(c.task_type == task for c in selected),
            )
            for task in sorted({c.task_type for c in selected})
        },
        "by_category": {
            category: group(
                [r for r in records if r.category_id == category],
                sum(c.category_id == category for c in selected),
            )
            for category in sorted({c.category_id for c in selected})
        },
        "limits": [
            "Status matches and literal citation checks are not semantic answer correctness.",
            "Returned products are checked as a set; references may identify an unsuitable product.",
            "No human ratings or participant utility are inferred.",
            "Retriever ranks are not exposed by this HTTP API; no retrieval Recall@k is claimed.",
        ],
    }


def run_evaluation(
    settings: Settings,
    output_dir: Path,
    *,
    base_url: str,
    case_ids: tuple[str, ...] = (),
    timeout_seconds: float = 240,
    transport: httpx.BaseTransport | None = None,
    include_security_fixtures: bool = False,
) -> dict[str, object]:
    """Create a new append-only trace and validated summary of adjustment cases."""
    base_url = _loopback_url(base_url)
    if not math.isfinite(timeout_seconds) or not 1 <= timeout_seconds <= 600:
        raise ValueError("invalid_http_timeout")
    reference_path = settings.project_dir / "data/evaluation/adjustment/cases.json"
    reference_bytes = reference_path.read_bytes()
    references = IntegratedReferenceSet.model_validate_json(reference_bytes)
    known_ids = {case.case_id for case in references.cases}
    if len(known_ids) != len(references.cases) or set(case_ids) - known_ids:
        raise ValueError("unknown_or_duplicate_adjustment_case")
    selected = tuple(case for case in references.cases if not case_ids or case.case_id in case_ids)
    manifest = SourceManifest.model_validate_json(
        settings.resolve_path(settings.source_manifest).read_bytes()
    )
    if (manifest.store_id, manifest.revision) != (
        references.store_id,
        references.corpus_revision,
    ) or any(
        (c.store_id, c.corpus_revision) != (references.store_id, references.corpus_revision)
        for c in selected
    ):
        raise ValueError("reference_manifest_scope_mismatch")
    files = _candidate_files(settings, manifest)
    hashes = {name: sha256(path.read_bytes()).hexdigest() for name, path in sorted(files.items())}
    output_dir.mkdir(parents=True, exist_ok=False)
    created_at = datetime.now(UTC)
    parameters: dict[str, str | int | float | bool | None] = {
        "k": settings.retrieval_k,
        "context_tokens": settings.context_tokens,
        "output_tokens": settings.output_tokens,
        "model_timeout_seconds": settings.model_timeout_seconds,
        "http_timeout_seconds": timeout_seconds,
        "data_mode": settings.data_mode,
        "generation_model": settings.generation_model,
        "embedding_model": settings.embedding_model,
        "transport_override": transport is not None,
        "include_security_fixtures": include_security_fixtures,
    }
    _write_json(
        output_dir / "candidate.json",
        {
            "kind": "source_data_configuration_fingerprint",
            "files": hashes,
            "parameters": parameters,
        },
    )
    candidate_hash = sha256((output_dir / "candidate.json").read_bytes()).hexdigest()
    _write_json(
        output_dir / "metadata.json",
        {
            "created_at": created_at.isoformat(),
            "partition": "adjustment",
            "reference_sha256": sha256(reference_bytes).hexdigest(),
            "candidate_sha256": candidate_hash,
            "base_url": base_url,
            "selected_case_ids": [case.case_id for case in selected],
            "measurement_clock": "UTC wall clock and monotonic elapsed time",
            "commercial_clock": "Case reference time; server clock is retained in response versions",
            "transport": "overridden_test_transport" if transport else "loopback_http",
        },
    )
    records: list[IntegratedCaseRecord] = []
    run_id = "integrated-" + created_at.strftime("%Y%m%dT%H%M%S%fZ")

    def run_record() -> EvaluationRun:
        return EvaluationRun(
            run_id=run_id,
            purpose="adjustment",
            system="integrated",
            created_at=created_at,
            candidate_sha256=candidate_hash,
            artifacts={
                "candidate_manifest": candidate_hash,
                "adjustment_cases": sha256(reference_bytes).hexdigest(),
                **{
                    name: value for name, value in hashes.items() if not name.startswith("package/")
                },
            },
            versions={
                "references": references.reference_set_revision,
                "corpus": references.corpus_revision,
                "generation_model": settings.generation_model,
                "embedding_model": settings.embedding_model,
            },
            parameters=parameters,
            k=settings.retrieval_k,
            environment=f"Python {platform.python_version()}; {platform.system()} {platform.machine()}",
            concurrency=1,
            planned_cases=len(selected),
            cases=tuple(record.result for record in records if record.result is not None),
            limitations=(
                "Actual HTTP outputs; no final reserved cases or participant study.",
                "Warm state is uncontrolled and recorded as unknown.",
                "No retrieval references or ranks are supplied through this HTTP endpoint.",
                "Security fixtures require a separate isolated cloned corpus and are not silently omitted.",
            ),
        )

    write_run(run_record(), output_dir / "initial-run.json")
    try:
        with (
            (output_dir / "cases.jsonl").open("x", encoding="utf-8") as observations,
            (output_dir / "progress.jsonl").open("x", encoding="utf-8") as progress,
            httpx.Client(
                base_url=base_url,
                timeout=timeout_seconds,
                trust_env=False,
                follow_redirects=False,
                transport=transport,
            ) as client,
        ):
            for case in selected:
                record = (
                    evaluate_security_fixture(
                        settings,
                        case,
                        output_dir / "fixtures" / case.case_id,
                        timeout_seconds=timeout_seconds,
                        transport=transport,
                    )
                    if case.fixture is not None and include_security_fixtures
                    else evaluate_case(case, client, manifest)
                )
                records.append(record)
                observations.write(record.model_dump_json() + "\n")
                observations.flush()
                partial_summary = summarize(run_record())
                progress.write(json.dumps({"last_case": case.case_id, **partial_summary}) + "\n")
                progress.flush()
                print(
                    f"{case.case_id}: {record.execution}; {record.reason or 'recorded'}", flush=True
                )
    finally:
        final_run = run_record()
        write_run(final_run, output_dir / "run.json")
        summary = summarize(final_run)
        _write_json(output_dir / "summary.json", summary)
        _write_json(output_dir / "mechanical-summary.json", _mechanical_summary(records, selected))
        _write_json(
            output_dir / "completion.json",
            {
                "finished_at": datetime.now(UTC).isoformat(),
                "recorded_cases": len(records),
                "planned_cases": len(selected),
                "all_cases_recorded": len(records) == len(selected),
                "candidate_unchanged": all(
                    path.is_file() and sha256(path.read_bytes()).hexdigest() == hashes[name]
                    for name, path in files.items()
                ),
            },
        )
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--base-url")
    parser.add_argument("--case-id", action="append", default=[])
    parser.add_argument("--timeout-seconds", type=float, default=240)
    parser.add_argument("--include-security-fixtures", action="store_true")
    args = parser.parse_args(argv)
    try:
        settings = load_settings(args.project_dir)
        summary = run_evaluation(
            settings,
            settings.resolve_path(args.output_dir),
            base_url=args.base_url or f"http://127.0.0.1:{settings.port}",
            case_ids=tuple(args.case_id),
            timeout_seconds=args.timeout_seconds,
            include_security_fixtures=args.include_security_fixtures,
        )
        print(json.dumps(summary["coverage"]))
        coverage = summary["coverage"]
        if isinstance(coverage, dict):
            return 1 if coverage.get("errors") else 2 if coverage.get("not_run") else 0
        return 1
    except (OSError, ValueError) as error:
        print(json.dumps({"status": "failed", "code": type(error).__name__}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
