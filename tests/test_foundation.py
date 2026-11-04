"""Observable data, configuration, HTTP and provider boundary checks."""

import json
from datetime import timedelta
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from test_local_contracts import NOW, make_catalog, write_commercial

from ragml.api import check_sqlite, create_app
from ragml.commercial import JsonCommercialAdapter
from ragml.conversation import ChatResponse, CommercialCitation, DocumentCitation, SupportedClaim
from ragml.evidence import Chunk, Location, Source, SourceManifest, SourceScope
from ragml.providers import ModelIdentity, ModelLock, OllamaClient, ProviderError
from ragml.settings import Settings, load_settings


def model_lock(settings: Settings) -> ModelLock:
    return ModelLock(
        runtime_version="0.40.14",
        generation=ModelIdentity(
            tag=settings.generation_model, digest="1" * 64, size_bytes=100, quantization="Q4_K_M"
        ),
        embedding=ModelIdentity(
            tag=settings.embedding_model, digest="2" * 64, size_bytes=100, quantization="Q8_0"
        ),
    )


def manifest() -> SourceManifest:
    text = "La política de prueba permite consultar características."
    source = Source(
        store_id="shop-a",
        source_id="policy",
        title="Synthetic policy",
        version="1",
        content_hash="a" * 64,
        data_mode="demo",
        scope=SourceScope(kind="store"),
        locator="policy.txt",
        provenance="synthetic_created",
    )
    chunk = Chunk(
        store_id="shop-a",
        chunk_id="chunk-1",
        source_id="policy",
        source_version="1",
        source_content_hash="a" * 64,
        content_hash=sha256(text.encode()).hexdigest(),
        text=text,
        location=Location(section="Consulta"),
    )
    return SourceManifest(
        store_id="shop-a", data_mode="demo", revision="1", sources=(source,), chunks=(chunk,)
    )


def response_with(citation: DocumentCitation | CommercialCitation) -> ChatResponse:
    return ChatResponse(
        request_id=uuid4(),
        session_id=uuid4(),
        store_id="shop-a",
        data_mode="demo",
        status="answered",
        answer="Respuesta ficticia respaldada.",
        claims=(
            SupportedClaim(
                text="Respuesta ficticia respaldada.", citation_ids=(citation.citation_id,)
            ),
        ),
        citations=(citation,),
        versions={"corpus": "1"},
    )


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com",
        "http://localhost:11435",
        "http://127.0.0.1:11435/path",
        "http://user@127.0.0.1:11435",
    ],
)
def test_remote_or_ambiguous_model_destinations_are_rejected(url: str) -> None:
    with pytest.raises(ValidationError):
        Settings(ollama_url=url)


def test_explicit_project_config_is_loaded_without_changing_shell_directory(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text(
        "RAGML_PORT=8081\nRAGML_CATALOG_PATH=demo/catalog.json\n", encoding="utf-8"
    )
    settings = load_settings(tmp_path)
    assert settings.port == 8081
    assert settings.resolve_path(settings.catalog_path) == tmp_path / "demo/catalog.json"
    (tmp_path / ".env").write_text("RAGML_ALLOW_REMOTE_PROVIDERS=true\n", encoding="utf-8")
    with pytest.raises(ValidationError):
        load_settings(tmp_path)


def test_example_configuration_is_usable_and_paths_are_not_required_yet() -> None:
    root = Path(__file__).resolve().parents[1]
    settings = load_settings(root, root / ".env.example")
    assert settings.allow_remote_providers is False
    assert settings.generation_model == "qwen3:4b-instruct-2507-q4_K_M"
    assert check_sqlite()


def test_general_policy_needs_no_fake_product_and_resolves_document_citation() -> None:
    evidence = manifest()
    evidence.validate_for_catalog(make_catalog())
    citation = DocumentCitation(
        citation_id="c1",
        store_id="shop-a",
        source_id="policy",
        source_version="1",
        chunk_id="chunk-1",
        location=Location(section="Consulta"),
        excerpt="permite consultar características",
    )
    response_with(citation).validate_evidence(evidence)


@pytest.mark.parametrize("change", ["source_version", "source_content_hash", "store_id"])
def test_chunks_cannot_mix_source_revisions_or_stores(change: str) -> None:
    data = manifest().model_dump(mode="json")
    data["chunks"][0][change] = "b" * 64 if change == "source_content_hash" else "different"
    with pytest.raises(ValidationError):
        SourceManifest.model_validate(data)


def test_chunk_hash_and_location_are_validated() -> None:
    data = manifest().chunks[0].model_dump(mode="json")
    data["text"] = "Texto sustituido sin actualizar su hash."
    with pytest.raises(ValidationError):
        Chunk.model_validate(data)
    with pytest.raises(ValidationError):
        Location()


def test_withdrawn_sources_and_inapplicable_attribute_sources_are_rejected() -> None:
    data = manifest().model_dump(mode="json")
    data["sources"][0]["active"] = False
    with pytest.raises(ValidationError):
        SourceManifest.model_validate(data)
    catalog_data = make_catalog().model_dump(mode="json")
    catalog_data["products"][0]["attributes"] = [
        {"key": "width", "value": 10, "unit": "cm", "evidence_refs": ["absent"]}
    ]
    with pytest.raises(ValueError, match="absent or inactive"):
        manifest().validate_for_catalog(type(make_catalog()).model_validate(catalog_data))


def test_quoted_text_must_exist_in_the_exact_fragment() -> None:
    citation = DocumentCitation(
        citation_id="c1",
        store_id="shop-a",
        source_id="policy",
        source_version="1",
        chunk_id="chunk-1",
        location=Location(section="Consulta"),
        excerpt="invented guarantee",
    )
    with pytest.raises(ValueError, match="exact evidence"):
        response_with(citation).validate_evidence(manifest())


def test_claim_cannot_reference_an_absent_citation() -> None:
    with pytest.raises(ValidationError, match="absent citation"):
        ChatResponse(
            request_id=uuid4(),
            session_id=uuid4(),
            store_id="shop-a",
            data_mode="demo",
            status="answered",
            answer="text",
            versions={},
            claims=(SupportedClaim(text="claim", citation_ids=("absent",)),),
        )


def test_commercial_citation_requires_a_fresh_matching_lookup(tmp_path: Path) -> None:
    catalog = make_catalog()
    path = tmp_path / "commercial.json"
    write_commercial(path, catalog)
    adapter = JsonCommercialAdapter(path, catalog)
    lookup = adapter.lookup("shop-a", ("variant-1",), NOW)[0]
    assert lookup.price is not None
    citation = CommercialCitation(
        citation_id="price-1",
        store_id="shop-a",
        source_id="synthetic-source",
        source_version="commercial-1",
        snapshot_id="snapshot-commercial-1",
        variant_id="variant-1",
        field="price",
        source_updated_at=lookup.price.source_updated_at,
        expires_at=lookup.price.expires_at,
    )
    response_with(citation).validate_evidence(manifest(), (lookup,))
    expired = adapter.lookup("shop-a", ("variant-1",), NOW + timedelta(minutes=10))
    with pytest.raises(ValueError, match="fresh observation"):
        response_with(citation).validate_evidence(manifest(), expired)


def provider_handler(settings: Settings, request: httpx.Request) -> httpx.Response:
    if request.url.path == "/api/tags":
        return httpx.Response(
            200,
            json={
                "models": [
                    {"name": settings.generation_model, "digest": "1" * 64},
                    {"name": settings.embedding_model, "digest": "2" * 64},
                ]
            },
        )
    if request.url.path == "/api/chat":
        body = json.loads(request.content)
        assert body["stream"] is False and body["think"] is False
        assert body["options"]["num_predict"] <= settings.output_tokens
        return httpx.Response(
            200,
            json={
                "done": True,
                "done_reason": "stop",
                "message": {"content": "La potencia es 8 W."},
            },
        )
    body = json.loads(request.content)
    assert body["truncate"] is False
    assert all(text.startswith("Instruct:") for text in body["input"])
    return httpx.Response(200, json={"embeddings": [[1.0] + [0.0] * 1023]})


def test_provider_speaks_the_local_api_contract_without_real_network_calls() -> None:
    settings = Settings()
    client = OllamaClient(
        settings,
        model_lock(settings),
        httpx.MockTransport(lambda request: provider_handler(settings, request)),
    )
    try:
        assert (
            client.generate("Use only evidence", "Synthetic question").message.content
            == "La potencia es 8 W."
        )
        assert len(client.embed(("consulta ficticia",), query=True).embeddings[0]) == 1024
    finally:
        client.close()


def test_model_digest_change_prevents_sending_generation_input() -> None:
    settings = Settings()
    paths = []

    def changed(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        return httpx.Response(200, json={"models": []})

    client = OllamaClient(settings, model_lock(settings), httpx.MockTransport(changed))
    try:
        with pytest.raises(ProviderError, match="model_missing_or_changed"):
            client.generate("instruction", "question")
        assert paths == ["/api/tags"]
    finally:
        client.close()


@pytest.mark.parametrize("failure", ["redirect", "timeout", "truncated", "dimensions"])
def test_provider_failures_do_not_return_unsupported_or_partial_results(failure: str) -> None:
    settings = Settings()

    def handler(request: httpx.Request) -> httpx.Response:
        if failure == "redirect":
            return httpx.Response(302, headers={"Location": "https://example.com"})
        if failure == "timeout":
            raise httpx.ReadTimeout("synthetic-private-input", request=request)
        if request.url.path == "/api/tags":
            return provider_handler(settings, request)
        if failure == "truncated":
            return httpx.Response(
                200, json={"done": True, "done_reason": "length", "message": {"content": "partial"}}
            )
        return httpx.Response(200, json={"embeddings": [[1.0]]})

    client = OllamaClient(settings, model_lock(settings), httpx.MockTransport(handler))
    try:
        with pytest.raises(ProviderError) as error:
            if failure == "dimensions":
                client.embed(("synthetic",))
            else:
                client.generate("instruction", "question")
        assert "synthetic-private-input" not in str(error.value)
    finally:
        client.close()


def test_foundation_http_reports_health_and_rag_absence_honestly(tmp_path: Path) -> None:
    settings = Settings(project_dir=tmp_path)
    with TestClient(create_app(settings)) as client:
        health = client.get("/health")
        assert health.status_code == 200 and health.json()["rag_available"] is False
        ready = client.get("/ready")
        assert ready.status_code == 503 and ready.json()["dependencies"]["sqlite"] is True
        chat = client.post("/v1/chat", json={"message": "Consulta de prueba"})
        assert chat.status_code == 503 and chat.json()["code"] == "rag_not_ready"
        assert chat.headers["x-request-id"] == chat.json()["request_id"]
        bad = client.post("/v1/chat", json={"message": "hidden-input", "api_key": "do-not-echo"})
        assert bad.status_code == 422
        assert "do-not-echo" not in bad.text and "hidden-input" not in bad.text
        assert client.get("/missing").json()["code"] == "not_found"
        assert client.get("/docs").status_code == 404
        responses = client.get("/openapi.json").json()["paths"]["/v1/chat"]["post"]["responses"]
        assert responses["200"]["content"]["application/json"]["schema"]["$ref"].endswith("ChatResponse")
        assert "503" in responses
