"""Document answers must resolve to exact retrieved quotations."""

import json
from pathlib import Path

import pytest
from test_ingestion import DIGEST, FakeEmbeddings, package, publish

from ragml.ingestion import CorpusStore
from ragml.ports import RetrievalQuery
from ragml.providers import GenerationResult, ProviderError, RuntimeMessage
from ragml.rag import DocumentRag
from ragml.retrieval import SqliteRetriever


class QuotationModel:
    def __init__(self, payload: str | None = None) -> None:
        self.payload = payload

    def generate(
        self, system: str, user: str, *, output_tokens: int | None = None
    ) -> GenerationResult:
        payload = self.payload or json.dumps(
            {"status": "answered", "claims": [{"citation_id": "E1", "quote": "Regla A"}]}
        )
        return GenerationResult(
            message=RuntimeMessage(content=payload), done=True, prompt_eval_count=120, eval_count=30
        )


def service(tmp_path: Path, model: QuotationModel | None = None) -> DocumentRag:
    store = CorpusStore(tmp_path / "index.sqlite3")
    publish(store, package(tmp_path / "input"))
    retriever = SqliteRetriever(
        store.database, FakeEmbeddings(), model="test-model", digest=DIGEST, dimensions=4
    )
    return DocumentRag(
        retriever,
        model or QuotationModel(),
        generation_model="test-generation",
        generation_digest="f" * 64,
        data_mode="demo",
    )


def test_document_answer_contains_exact_quote_with_resolvable_citation(tmp_path: Path) -> None:
    run = service(tmp_path).answer(
        RetrievalQuery(store_id="shop-a", revision="r1", text="¿Cuál es la regla?")
    )
    assert run.response.status == "answered"
    assert run.response.answer == "Regla A [E1]"
    assert run.response.claims[0].text == "Regla A"
    assert run.response.citations[0].excerpt == "Regla A"
    assert run.response.citations[0].location.section == "Consulta"
    assert run.metrics["generation_output_tokens"] == 30


@pytest.mark.parametrize(
    "question",
    [
        "¿Cuánto cuesta?",
        "¿Cuál es el precio actual?",
        "¿Hay existencias?",
        "¿Está disponible?",
        "Tengo un presupuesto de 100 COP",
        "¿Cuánto vale la lámpara?",
    ],
)
def test_document_baseline_does_not_confirm_commercial_information(
    tmp_path: Path, question: str
) -> None:
    response = (
        service(tmp_path)
        .answer(RetrievalQuery(store_id="shop-a", revision="r1", text=question))
        .response
    )
    assert response.status == "insufficient_evidence"
    assert response.claims == ()
    assert "commercial_lookup_required" in response.warnings


def test_unresolved_conversational_reference_requests_clarification(tmp_path: Path) -> None:
    response = (
        service(tmp_path)
        .answer(RetrievalQuery(store_id="shop-a", revision="r1", text="¿Y el segundo?"))
        .response
    )
    assert response.status == "clarification_required"
    assert response.citations == ()


@pytest.mark.parametrize(
    "payload",
    [
        "not JSON",
        '{"status":"answered","claims":[]}',
        '{"status":"answered","claims":[{"citation_id":"missing","quote":"Regla A"}]}',
        '{"status":"answered","claims":[{"citation_id":"E1","quote":"Invented fact"}]}',
        '{"status":"answered","claims":[{"citation_id":"E1","quote":"Regla A"}],"extra":true}',
    ],
)
def test_unverified_model_output_never_becomes_an_answer(tmp_path: Path, payload: str) -> None:
    response = (
        service(tmp_path, QuotationModel(payload))
        .answer(RetrievalQuery(store_id="shop-a", revision="r1", text="Regla"))
        .response
    )
    assert response.status == "insufficient_evidence"
    assert response.citations == ()
    assert "unverified_generation" in response.warnings


@pytest.mark.parametrize("status", ["clarification_required", "insufficient_evidence"])
def test_model_can_report_ambiguity_or_insufficient_evidence(tmp_path: Path, status: str) -> None:
    response = (
        service(tmp_path, QuotationModel(json.dumps({"status": status, "claims": []})))
        .answer(RetrievalQuery(store_id="shop-a", revision="r1", text="Regla"))
        .response
    )
    assert response.status == status
    assert response.claims == ()


def test_generation_failure_is_explicit_and_does_not_reuse_an_answer(tmp_path: Path) -> None:
    class UnavailableModel(QuotationModel):
        def generate(
            self, system: str, user: str, *, output_tokens: int | None = None
        ) -> GenerationResult:
            raise ProviderError("provider_timeout")

    response = (
        service(tmp_path, UnavailableModel())
        .answer(RetrievalQuery(store_id="shop-a", revision="r1", text="Regla"))
        .response
    )
    assert response.status == "temporarily_unavailable"
    assert response.claims == ()


def test_insufficient_context_does_not_generate_from_cut_fragments(tmp_path: Path) -> None:
    rag = service(tmp_path)
    rag.context_tokens = 800
    response = rag.answer(RetrievalQuery(store_id="shop-a", revision="r1", text="Regla")).response
    assert response.status == "insufficient_evidence"
    assert response.warnings == ("context_budget_exceeded",)


def test_historical_commercial_quote_is_not_confirmed_as_a_document_answer(tmp_path: Path) -> None:
    rag = service(
        tmp_path,
        QuotationModel(
            json.dumps(
                {
                    "status": "answered",
                    "claims": [{"citation_id": "E1", "quote": "El precio es 99 COP."}],
                }
            )
        ),
    )
    store = CorpusStore(rag.retriever.database)
    publish(store, package(tmp_path / "input", revision="r2", text="El precio es 99 COP."))
    response = rag.answer(
        RetrievalQuery(store_id="shop-a", revision="r2", text="¿Cuánto debo pagar?")
    ).response
    assert response.status == "insufficient_evidence"
    assert response.citations == ()
    assert response.warnings == ("commercial_lookup_required",)
