"""Chat journeys through HTTP, real local data and an external-model test double."""

import json
import shutil
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ragml.conversation import ChatResponse
from ragml.ingestion import CorpusStore, read_corpus
from ragml.providers import EmbeddingResult, GenerationResult, ModelLock, RuntimeMessage
from ragml.settings import Settings
from ragml.web import create_web_app

ROOT = Path(__file__).resolve().parents[1]


class LocalModelDouble:
    """Only the external inference boundary is replaced; no assistant code is mocked."""

    def __init__(self, settings: Settings, lock: ModelLock) -> None:
        self.lock = lock

    def close(self) -> None:
        pass

    def check_models(self) -> dict[str, bool]:
        return {"generation": True, "embedding": True}

    def embed(self, texts: tuple[str, ...], *, query: bool = False) -> EmbeddingResult:
        return EmbeddingResult(embeddings=[[1.0] + [0.0] * 1023 for _ in texts])

    def generate(
        self, system: str, user: str, *, output_tokens: int | None = None
    ) -> GenerationResult:
        data = json.loads(user)
        evidence = data["evidence"][0]
        quote = evidence["text"].splitlines()[-1]
        return GenerationResult(
            message=RuntimeMessage(
                content=json.dumps(
                    {
                        "status": "answered",
                        "claims": [{"citation_id": evidence["citation_id"], "quote": quote}],
                    }
                )
            ),
            done=True,
        )


@pytest.fixture
def configured(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Settings:
    shutil.copytree(ROOT / "data/sample", tmp_path / "data/sample")
    (tmp_path / "config").mkdir()
    shutil.copyfile(ROOT / "config/models.lock.json", tmp_path / "config/models.lock.json")
    settings = Settings(project_dir=tmp_path)
    lock = ModelLock.model_validate_json((tmp_path / "config/models.lock.json").read_bytes())
    model = LocalModelDouble(settings, lock)
    store = CorpusStore(tmp_path / "data/runtime/corpus.sqlite3")
    store.publish(
        read_corpus(tmp_path, settings.catalog_path, settings.source_manifest),
        model,
        model=lock.embedding.tag,
        digest=lock.embedding.digest,
    )
    monkeypatch.setattr("ragml.api.OllamaClient", LocalModelDouble)
    return settings


@pytest.fixture
def browser(configured: Settings) -> Iterator[TestClient]:
    with TestClient(create_web_app(configured)) as client:
        yield client


def test_web_chat_recommends_with_current_commerce_and_sources(browser: TestClient) -> None:
    reply = browser.post(
        "/v1/chat",
        json={
            "message": "Recomiéndame iluminación con presupuesto de 100.000 COP",
        },
    )
    assert reply.status_code == 200
    result = ChatResponse.model_validate(reply.json())
    assert result.status == "answered"
    assert result.products and result.citations and result.claims
    assert "HttpOnly" in reply.headers["set-cookie"]
    assert "simulad" in " ".join(result.warnings).lower()


def test_budget_correction_keeps_category_and_session(browser: TestClient) -> None:
    first = browser.post("/v1/chat", json={"message": "Busco iluminación hasta 100 mil COP"}).json()
    second = browser.post(
        "/v1/chat",
        json={
            "message": "Ahora mi presupuesto es de 60 mil COP",
            "session_id": first["session_id"],
        },
    )
    assert second.status_code == 200
    result = ChatResponse.model_validate(second.json())
    assert result.status == "answered"
    assert str(result.session_id) == first["session_id"]
    assert result.products
    assert browser.cookies.get("ragml_owner")


def test_ordinal_commerce_and_comparison_use_the_presented_list(browser: TestClient) -> None:
    first = browser.post("/v1/chat", json={"message": "Busco iluminación hasta 200 mil COP"}).json()
    selected = browser.post(
        "/v1/chat",
        json={
            "message": "¿Cuánto cuesta el segundo?",
            "session_id": first["session_id"],
        },
    )
    assert selected.status_code == 200
    result = ChatResponse.model_validate(selected.json())
    assert result.status == "answered"
    assert result.products[0].variant_id == first["products"][1]["variant_id"]
    compared = browser.post(
        "/v1/chat",
        json={
            "message": "Compara el primero y el segundo",
            "session_id": first["session_id"],
        },
    )
    comparison = ChatResponse.model_validate(compared.json())
    assert comparison.status == "answered"
    assert [p.variant_id for p in comparison.products] == [
        p["variant_id"] for p in first["products"][:2]
    ]
    assert any(c.kind == "document" for c in comparison.citations)


def test_recommendation_applies_spanish_requirements_and_keeps_them(browser: TestClient) -> None:
    first = browser.post(
        "/v1/chat",
        json={
            "message": "Busco una lámpara regulable de máximo 8 W hasta 200 mil COP",
        },
    ).json()
    assert first["status"] == "answered"
    catalog = json.loads((ROOT / "data/sample/catalog.json").read_bytes())
    products = {p["product_id"]: p for p in catalog["products"]}
    for item in first["products"]:
        attributes = {a["key"]: a["value"] for a in products[item["product_id"]]["attributes"]}
        assert attributes["dimmable"] is True
        assert attributes["power_w"] <= 8
        assert products[item["product_id"]]["name"].startswith("Lámpara")
    second = browser.post(
        "/v1/chat",
        json={
            "message": "Ahora hasta 100 mil COP",
            "session_id": first["session_id"],
        },
    ).json()
    assert second["status"] == "answered"
    assert all(
        p["product_id"] in {p["product_id"] for p in first["products"]} for p in second["products"]
    )


def test_readiness_reflects_the_integrated_dependencies(browser: TestClient) -> None:
    response = browser.get("/ready")
    assert response.status_code == 200
    assert response.json()["rag_available"] is True
    assert all(response.json()["dependencies"].values())


def test_sessions_cannot_be_reused_by_another_browser(configured: Settings) -> None:
    app = create_web_app(configured)
    with TestClient(app) as first:
        owned = first.post("/v1/chat", json={"message": "Busco iluminación hasta 100 mil"}).json()
        # Only one lifespan runs in the real server; this second cookie jar shares it.
        stranger = TestClient(app)
        try:
            denied = stranger.post(
                "/v1/chat",
                json={
                    "message": "¿Cuánto cuesta el segundo?",
                    "session_id": owned["session_id"],
                },
            )
            assert denied.status_code == 404
            assert owned["products"][0]["variant_id"] not in denied.text
        finally:
            stranger.close()
        continued = first.post(
            "/v1/chat",
            json={
                "message": "Ahora hasta 60 mil",
                "session_id": owned["session_id"],
            },
        )
        assert continued.status_code == 200


def test_expired_sessions_require_a_new_conversation(
    configured: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = datetime(2026, 11, 4, 18, tzinfo=UTC)
    monkeypatch.setattr("ragml.sessions.utcnow", lambda: now)
    with TestClient(create_web_app(configured)) as client:
        first = client.post("/v1/chat", json={"message": "Busco iluminación hasta 100 mil"}).json()
        now += timedelta(seconds=configured.session_ttl_seconds)
        expired = client.post(
            "/v1/chat", json={"message": "El segundo", "session_id": first["session_id"]}
        )
        assert expired.status_code == 404
        fresh = client.post("/v1/chat", json={"message": "¿Cuánto cuesta el segundo?"}).json()
        assert fresh["status"] == "clarification_required"
        assert fresh["session_id"] != first["session_id"]


def test_new_conversation_deletes_only_its_own_server_state(browser: TestClient) -> None:
    first = browser.post("/v1/chat", json={"message": "Busco iluminación hasta 100 mil"}).json()
    assert browser.delete(f"/v1/chat/sessions/{first['session_id']}").status_code == 204
    assert (
        browser.post(
            "/v1/chat",
            json={
                "message": "El segundo",
                "session_id": first["session_id"],
            },
        ).status_code
        == 404
    )


def test_cross_origin_chat_requests_are_rejected(browser: TestClient) -> None:
    response = browser.post(
        "/v1/chat", json={"message": "Hola"}, headers={"Origin": "https://untrusted.invalid"}
    )
    assert response.status_code == 403


def test_cheaper_option_uses_the_selected_variant_as_a_strict_price_limit(
    browser: TestClient,
) -> None:
    first = browser.post("/v1/chat", json={"message": "Busco iluminación hasta 200 mil"}).json()
    selected = browser.post(
        "/v1/chat",
        json={
            "message": "¿Cuánto cuesta el segundo?",
            "session_id": first["session_id"],
        },
    ).json()
    reply = browser.post(
        "/v1/chat",
        json={
            "message": "Quiero uno más económico",
            "session_id": first["session_id"],
        },
    ).json()
    assert reply["status"] == "answered"
    assert selected["products"][0] not in reply["products"]
    assert reply["products"] == [first["products"][0]]


def test_category_change_does_not_silently_drop_incompatible_requirements(
    browser: TestClient,
) -> None:
    first = browser.post(
        "/v1/chat", json={"message": "Busco iluminación regulable hasta 500 mil"}
    ).json()
    changed = browser.post(
        "/v1/chat",
        json={
            "message": "Ahora busco una silla",
            "session_id": first["session_id"],
        },
    ).json()
    assert changed["status"] == "clarification_required"
    assert not changed["products"]
    confirmed = browser.post(
        "/v1/chat",
        json={
            "message": "Descarta los requisitos anteriores",
            "session_id": first["session_id"],
        },
    ).json()
    assert confirmed["status"] == "answered"
    assert all(p["product_id"].startswith("NEX-MOB-") for p in confirmed["products"])


def test_unknown_requirements_are_clarified_instead_of_ignored(browser: TestClient) -> None:
    reply = browser.post(
        "/v1/chat",
        json={
            "message": "Busco una lámpara que sea impermeable hasta 200 mil COP",
        },
    ).json()
    assert reply["status"] == "clarification_required"
    assert not reply["products"]
    following = browser.post(
        "/v1/chat",
        json={
            "message": "Busco iluminación hasta 300 mil",
            "session_id": reply["session_id"],
        },
    ).json()
    assert following["status"] == "clarification_required"
    assert not following["products"]


def test_web_exposes_the_demo_clock_before_the_first_chat_turn(browser: TestClient) -> None:
    runtime = browser.get("/v1/web/runtime")
    assert runtime.status_code == 200
    assert runtime.json()["commercial_clock"] == "simulated"
    assert runtime.json()["evaluated_at"].startswith("2026-11-04T12:05:00")
    assert runtime.headers["cache-control"] == "no-store"


def test_named_product_clarification_can_be_resolved_on_the_next_turn(browser: TestClient) -> None:
    first = browser.post("/v1/chat", json={"message": "¿Cuánto cuesta la Lámpara Flexo?"}).json()
    assert first["status"] == "clarification_required"
    assert len(first["products"]) == 2
    chosen = browser.post(
        "/v1/chat",
        json={
            "message": "El segundo, ¿cuánto cuesta?",
            "session_id": first["session_id"],
        },
    ).json()
    assert chosen["status"] == "answered"
    assert chosen["products"] == [first["products"][1]]


def test_document_question_uses_real_retrieval_and_keeps_session(browser: TestClient) -> None:
    first = browser.post("/v1/chat", json={"message": "Hola"}).json()
    result = browser.post(
        "/v1/chat",
        json={
            "message": "Según la ficha de Lámpara Flexo, ¿qué potencia tiene?",
            "session_id": first["session_id"],
        },
    ).json()
    assert result["status"] == "answered"
    assert result["session_id"] == first["session_id"]
    assert result["versions"]["answer_mode"] == "verified-extract-v1"
    assert all(c["kind"] == "document" for c in result["citations"])


def test_commerce_refreshes_without_reindexing_and_stale_values_are_not_confirmed(
    browser: TestClient,
    configured: Settings,
) -> None:
    message = "¿Cuánto cuesta NEX-ILU-001-01?"
    first = browser.post("/v1/chat", json={"message": message}).json()
    assert "89000 COP" in first["answer"]
    path = configured.resolve_path(configured.commercial_path)
    commerce = json.loads(path.read_bytes())
    for item in commerce["snapshots"]:
        if item["variant_id"] == "NEX-ILU-001-01":
            item["price"]["value"]["amount"] = "88000"
    path.write_text(json.dumps(commerce), encoding="utf-8")
    refreshed = browser.post("/v1/chat", json={"message": message}).json()
    assert "88000 COP" in refreshed["answer"]
    for item in commerce["snapshots"]:
        if item["variant_id"] == "NEX-ILU-001-01":
            item["price"]["expires_at"] = "2026-11-04T12:04:00Z"
    path.write_text(json.dumps(commerce), encoding="utf-8")
    expired = browser.post("/v1/chat", json={"message": message}).json()
    assert "88000 COP" not in expired["answer"]
    assert not any(
        c["kind"] == "commercial" and c["field"] == "price" for c in expired["citations"]
    )


def test_preferences_never_relax_an_explicit_requirement(browser: TestClient) -> None:
    reply = browser.post(
        "/v1/chat",
        json={
            "message": "Busco iluminación regulable hasta 200 mil COP, prefiero altura máximo 50 cm",
        },
    ).json()
    assert reply["status"] == "answered"
    catalog = json.loads((ROOT / "data/sample/catalog.json").read_bytes())
    products = {p["product_id"]: p for p in catalog["products"]}
    for item in reply["products"]:
        assert (
            next(
                a["value"]
                for a in products[item["product_id"]]["attributes"]
                if a["key"] == "dimmable"
            )
            is True
        )
