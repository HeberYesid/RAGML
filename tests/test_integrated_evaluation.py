"""Integrated evaluation records actual HTTP turns without gold assistant history."""

import json
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

import httpx
import pytest

from ragml.evidence import SourceManifest
from ragml.ingestion import CorpusStore, read_corpus
from ragml.integrated_evaluation import (
    IntegratedReferenceCase,
    evaluate_case,
    evaluate_security_fixture,
    prepare_security_fixture,
    run_evaluation,
)
from ragml.providers import EmbeddingResult
from ragml.settings import Settings


def test_multiturn_http_preserves_server_session_and_records_real_responses() -> None:
    session_id = str(uuid4())
    sent: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "DELETE":
            return httpx.Response(204)
        body = json.loads(request.content)
        sent.append(body)
        if len(sent) == 2:
            assert body["session_id"] == session_id
            assert request.headers.get("cookie") == "ragml_owner=test-owner"
        return httpx.Response(
            200,
            headers={"set-cookie": "ragml_owner=test-owner; Path=/v1/chat; HttpOnly"},
            json={
                "request_id": str(uuid4()),
                "session_id": session_id,
                "store_id": "example-store",
                "data_mode": "demo",
                "status": "clarification_required",
                "answer": f"Actual HTTP answer {len(sent)}",
                "versions": {"corpus": "revision-1"},
            },
        )

    case = IntegratedReferenceCase.model_validate(
        {
            "case_id": "DEV-example",
            "partition": "adjustment",
            "family_id": "budget-change",
            "category_id": "lighting",
            "task_type": "multiturn",
            "store_id": "example-store",
            "corpus_revision": "revision-1",
            "evaluated_at": "2026-11-04T12:05:00Z",
            "turns": [
                {"role": "user", "text": "I need a lamp"},
                {"role": "user", "text": "My budget changed"},
            ],
            "gold_chunk_ids": [],
            "expected_status": "clarification_required",
        }
    )
    manifest = SourceManifest.model_validate(
        {
            "schema_version": "0.1",
            "store_id": "example-store",
            "data_mode": "demo",
            "revision": "revision-1",
            "sources": [],
            "chunks": [],
        }
    )
    with httpx.Client(
        base_url="http://127.0.0.1:8000", transport=httpx.MockTransport(handler)
    ) as client:
        record = evaluate_case(case, client, manifest)

    assert record.execution == "completed"
    assert [turn.response.answer for turn in record.turns if turn.response] == [
        "Actual HTTP answer 1",
        "Actual HTTP answer 2",
    ]
    assert sent[0] == {"schema_version": "0.1", "message": "I need a lamp", "session_id": None}
    assert set(sent[1]) == {"schema_version", "message", "session_id"}
    assert record.checks["expected_status_match"] is True
    assert record.result is not None and record.result.warm_state == "unknown"


def test_run_keeps_errors_and_unexecuted_fixtures_in_coverage_without_overwriting(
    tmp_path: Path,
) -> None:
    data = tmp_path / "data/sample"
    data.mkdir(parents=True)
    (data / "catalog.json").write_text("{}", encoding="utf-8")
    (data / "commercial.json").write_text("{}", encoding="utf-8")
    (data / "sources.json").write_text(
        json.dumps(
            {
                "schema_version": "0.1",
                "store_id": "example-store",
                "data_mode": "demo",
                "revision": "revision-1",
                "sources": [],
                "chunks": [],
            }
        ),
        encoding="utf-8",
    )
    cases = []
    for index in range(3):
        case: dict[str, object] = {
            "case_id": f"DEV-{index}",
            "partition": "adjustment",
            "family_id": f"example-{index}",
            "category_id": "lighting",
            "task_type": "document",
            "store_id": "example-store",
            "corpus_revision": "revision-1",
            "evaluated_at": "2026-11-04T12:05:00Z",
            "turns": [{"role": "user", "text": f"Question {index}"}],
            "gold_chunk_ids": [],
            "expected_status": "clarification_required",
        }
        if index == 2:
            case["fixture"] = {"kind": "untrusted_document_append", "text": "untrusted"}
        cases.append(case)
    reference_path = tmp_path / "data/evaluation/adjustment/cases.json"
    reference_path.parent.mkdir(parents=True)
    reference_path.write_text(
        json.dumps(
            {
                "partition": "adjustment",
                "reference_set_revision": "reference-1",
                "store_id": "example-store",
                "corpus_revision": "revision-1",
                "cases": cases,
            }
        ),
        encoding="utf-8",
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "DELETE":
            return httpx.Response(204)
        if json.loads(request.content)["message"] == "Question 1":
            return httpx.Response(503, json={"code": "provider_unavailable"})
        return httpx.Response(
            200,
            json={
                "request_id": str(uuid4()),
                "session_id": str(uuid4()),
                "store_id": "example-store",
                "data_mode": "demo",
                "status": "clarification_required",
                "answer": "Which product?",
                "versions": {"corpus": "revision-1"},
            },
        )

    output = tmp_path / "observations"
    result = run_evaluation(
        Settings(project_dir=tmp_path),
        output,
        base_url="http://127.0.0.1:8000",
        transport=httpx.MockTransport(handler),
    )
    assert result["coverage"] == {
        "planned": 3,
        "attempted": 2,
        "completed": 1,
        "errors": 1,
        "not_run": 1,
        "human_reviewed": 0,
    }
    saved = (output / "cases.jsonl").read_bytes()
    traces = [json.loads(line) for line in saved.splitlines()]
    assert [r["execution"] for r in traces] == ["completed", "error", "not_run"]
    assert result["human_metrics"]["factual_correctness"]["value"] is None
    assert json.loads((output / "mechanical-summary.json").read_bytes())["not_run_reasons"] == {
        "isolated_source_fixture_required": 1
    }
    with pytest.raises(FileExistsError):
        run_evaluation(
            Settings(project_dir=tmp_path),
            output,
            base_url="http://127.0.0.1:8000",
            transport=httpx.MockTransport(handler),
        )
    assert (output / "cases.jsonl").read_bytes() == saved


def test_security_fixture_reindexes_a_versioned_clone_without_changing_source_data(
    tmp_path: Path,
) -> None:
    project = Path(__file__).resolve().parents[1]
    source_path = project / "data/sample/documents/products/nex-ilu-001.md"
    original = sha256(source_path.read_bytes()).hexdigest()
    cases = json.loads((project / "data/evaluation/adjustment/cases.json").read_bytes())
    case = IntegratedReferenceCase.model_validate(
        next(c for c in cases["cases"] if c["case_id"] == "DEV-027")
    )

    class ExternalEmbedder:
        def embed(self, texts: tuple[str, ...], *, query: bool = False) -> EmbeddingResult:
            return EmbeddingResult(embeddings=[[1.0] + [0.0] * 1023 for _ in texts])

    fixture = prepare_security_fixture(
        Settings(project_dir=project),
        case,
        tmp_path / "isolated-case",
        ExternalEmbedder(),
    )
    corpus = read_corpus(
        fixture.settings.project_dir,
        fixture.settings.catalog_path,
        fixture.settings.source_manifest,
        fixture.settings.commercial_path,
    )
    info = CorpusStore(
        fixture.settings.resolve_path(fixture.settings.runtime_dir) / "corpus.sqlite3"
    ).info(case.store_id)
    assert sha256(source_path.read_bytes()).hexdigest() == original
    assert fixture.case.fixture is None
    assert fixture.case.corpus_revision != case.corpus_revision
    assert info is not None and info.chunks == 205
    assert corpus.manifest == fixture.manifest
    assert any(c.text == case.fixture["text"] for c in corpus.manifest.chunks)
    legitimate = next(c for c in corpus.manifest.chunks if c.chunk_id == "doc-ilu-001-s2")
    assert "power_w" in legitimate.text and legitimate.source_version != "demo-20261104-v2"


def test_security_case_uses_clone_revision_and_keeps_preparation_outside_http_latency(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = Path(__file__).resolve().parents[1]
    cases = json.loads((project / "data/evaluation/adjustment/cases.json").read_bytes())
    case = IntegratedReferenceCase.model_validate(
        next(c for c in cases["cases"] if c["case_id"] == "DEV-027")
    )

    class ExternalModel:
        def __init__(self, settings: object, lock: object) -> None:
            pass

        def embed(self, texts: tuple[str, ...], *, query: bool = False) -> EmbeddingResult:
            return EmbeddingResult(embeddings=[[1.0] + [0.0] * 1023 for _ in texts])

        def close(self) -> None:
            pass

    monkeypatch.setattr("ragml.integrated_evaluation.OllamaClient", ExternalModel)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "DELETE":
            return httpx.Response(204)
        return httpx.Response(
            200,
            json={
                "request_id": str(uuid4()),
                "session_id": str(uuid4()),
                "store_id": "nexo-demo",
                "data_mode": "demo",
                "status": "clarification_required",
                "answer": "Which property?",
                "versions": {"corpus": "demo-20261104-v2-fixture-dev-027"},
            },
        )

    record = evaluate_security_fixture(
        Settings(project_dir=project),
        case,
        tmp_path / "isolated-http",
        transport=httpx.MockTransport(handler),
    )
    assert record.execution == "completed"
    assert record.result is not None
    assert record.result.response is not None
    assert record.result.response.versions["corpus"] == "demo-20261104-v2-fixture-dev-027"
    assert record.fixture_preparation_seconds is not None
    assert set(record.result.timings_seconds) == {"total"}
    assert record.fixture_artifacts["untrusted_chunk_id"] == "doc-ilu-001-untrusted-fixture"
    assert record.checks["expected_status_match"] is False
