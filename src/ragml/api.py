"""Local chat API with validated data and explicit dependency availability."""

import sqlite3
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager, closing
from importlib.metadata import version
from typing import Literal
from uuid import UUID, uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException
from starlette.responses import Response

from ragml.chat import ChatService
from ragml.contracts import CommercialDataset, Contract
from ragml.conversation import ChatRequest, ChatResponse, ErrorResponse
from ragml.providers import ModelLock, OllamaClient, ProviderError
from ragml.sessions import OwnerTokens, SessionAccessError, SessionBusyError
from ragml.settings import Settings, load_settings


def check_sqlite() -> str:
    with closing(sqlite3.connect(":memory:")) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("CREATE VIRTUAL TABLE probe USING fts5(text)")
        if connection.execute("PRAGMA foreign_keys").fetchone() != (1,):
            raise RuntimeError("SQLite foreign keys are unavailable")
    return sqlite3.sqlite_version


def read_model_lock(settings: Settings) -> ModelLock:
    lock = ModelLock.model_validate_json(
        settings.resolve_path(settings.model_lock_path).read_text(encoding="utf-8")
    )
    lock.validate_settings(settings)
    return lock


class HealthResponse(Contract):
    status: Literal["ok"] = "ok"
    stage: Literal["integrated"] = "integrated"
    version: str
    rag_available: bool = False


class ReadinessResponse(Contract):
    status: Literal["ready", "not_ready"] = "not_ready"
    dependencies: dict[str, bool]
    rag_available: bool = False
    message: str = (
        "Base técnica disponible; el catálogo, el índice y el RAG se completarán después."
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    configured = settings or load_settings()
    tokens = OwnerTokens()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        client: OllamaClient | None = None
        try:
            client = OllamaClient(configured, read_model_lock(configured))
        except (OSError, ValueError):
            pass
        app.state.model_client = client
        app.state.chat_service = ChatService(configured, client) if client is not None else None
        yield
        if client is not None:
            client.close()

    app = FastAPI(
        title="RAGML local foundation",
        version=version("ragml"),
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
    )

    def error(request: Request, status: int, code: str, message: str) -> JSONResponse:
        body = ErrorResponse.model_validate(
            {
                "code": code,
                "message": message,
                "request_id": str(request.state.request_id),
                "retryable": status in (500, 503),
            }
        )
        return JSONResponse(status_code=status, content=body.model_dump(mode="json"))

    @app.middleware("http")
    async def request_identity(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request.state.request_id = uuid4()
        if request.url.path.startswith("/v1/chat") and request.method in ("POST", "DELETE"):
            origin = request.headers.get("origin")
            expected_origin = f"{request.url.scheme}://{request.url.netloc}"
            if (origin is not None and origin != expected_origin) or request.headers.get(
                "sec-fetch-site"
            ) == "cross-site":
                rejected = error(
                    request, 403, "invalid_input", "El origen de la solicitud no está permitido."
                )
                rejected.headers["X-Request-ID"] = str(request.state.request_id)
                return rejected
        response = await call_next(request)
        response.headers["X-Request-ID"] = str(request.state.request_id)
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_input(request: Request, exc: RequestValidationError) -> JSONResponse:
        return error(request, 422, "invalid_input", "La solicitud no cumple el contrato esperado.")

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        return error(
            request, exc.status_code, "not_found", "El recurso solicitado no está disponible."
        )

    @app.exception_handler(Exception)
    async def internal_error(request: Request, exc: Exception) -> JSONResponse:
        return error(request, 500, "internal_error", "No se pudo completar la solicitud.")

    @app.get("/health")
    def health(request: Request) -> HealthResponse:
        available = False
        service: ChatService | None = request.app.state.chat_service
        if service is not None:
            try:
                service.snapshot()
                available = True
            except (OSError, ValueError):
                pass
        return HealthResponse(version=version("ragml"), rag_available=available)

    @app.get("/ready", response_model=ReadinessResponse, status_code=503)
    def ready(request: Request) -> JSONResponse:
        dependencies = {
            "sqlite": bool(check_sqlite()),
            "generation_model": False,
            "embedding_model": False,
            "catalog_file": configured.resolve_path(configured.catalog_path).is_file(),
            "source_manifest_file": configured.resolve_path(configured.source_manifest).is_file(),
            "rag_implemented": request.app.state.chat_service is not None,
            "validated_corpus": False,
            "commercial_source": False,
        }
        service: ChatService | None = request.app.state.chat_service
        if service is not None:
            try:
                snapshot = service.snapshot()
                dependencies["validated_corpus"] = True
                service.commercial_time(snapshot.catalog)
                commerce = CommercialDataset.model_validate_json(
                    configured.resolve_path(configured.commercial_path).read_bytes()
                )
                commerce.validate_for_catalog(snapshot.catalog)
                dependencies["commercial_source"] = True
            except (OSError, ValueError):
                pass
        client: OllamaClient | None = request.app.state.model_client
        if client is not None:
            try:
                models = client.check_models()
                dependencies["generation_model"] = models["generation"]
                dependencies["embedding_model"] = models["embedding"]
            except (ProviderError, ValidationError):
                pass
        available = all(dependencies.values())
        return JSONResponse(
            status_code=200 if available else 503,
            content=ReadinessResponse(
                dependencies=dependencies,
                rag_available=available,
                status="ready" if available else "not_ready",
                message="Asistente local disponible."
                if available
                else "El asistente requiere catálogo, corpus, comercio y modelos válidos.",
            ).model_dump(mode="json"),
        )

    @app.post(
        "/v1/chat",
        response_model=ChatResponse,
        responses={422: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
    )
    def chat(body: ChatRequest, request: Request) -> JSONResponse:
        service: ChatService | None = request.app.state.chat_service
        if service is not None:
            try:
                owner = tokens.decode(request.cookies.get("ragml_owner")) or uuid4()
                reply = service.answer(body, request.state.request_id, owner)
                result = JSONResponse(content=reply.model_dump(mode="json"))
                result.set_cookie(
                    "ragml_owner",
                    tokens.encode(owner),
                    httponly=True,
                    samesite="strict",
                    max_age=configured.session_ttl_seconds,
                    path="/v1/chat",
                )
                result.headers["Cache-Control"] = "no-store"
                return result
            except SessionAccessError:
                return error(
                    request,
                    404,
                    "session_not_found",
                    "La conversación venció o no está disponible. Inicia una nueva.",
                )
            except SessionBusyError:
                return error(
                    request,
                    503,
                    "provider_unavailable",
                    "Hay una consulta en curso. Reintenta en unos momentos.",
                )
            except (OSError, ValueError):
                pass
        return error(
            request,
            503,
            "rag_not_ready",
            "No se pudo preparar el asistente. Comprueba el catálogo, el índice y los modelos locales.",
        )

    @app.delete(
        "/v1/chat/sessions/{session_id}", status_code=204, responses={404: {"model": ErrorResponse}}
    )
    def delete_session(session_id: UUID, request: Request) -> Response:
        service: ChatService | None = request.app.state.chat_service
        owner = tokens.decode(request.cookies.get("ragml_owner"))
        if service is not None and owner is not None:
            try:
                snapshot = service.snapshot()
                service.sessions.delete(session_id, snapshot.catalog.profile.store_id, owner)
                return Response(status_code=204, headers={"Cache-Control": "no-store"})
            except (SessionAccessError, OSError, ValueError):
                pass
        return error(request, 404, "session_not_found", "La conversación no está disponible.")

    return app
