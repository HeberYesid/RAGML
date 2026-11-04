"""Local foundation API. RAG readiness stays false until later phases implement it."""

import sqlite3
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager, closing
from importlib.metadata import version
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException
from starlette.responses import Response

from ragml.contracts import Contract
from ragml.conversation import ChatRequest, ErrorResponse
from ragml.providers import ModelLock, OllamaClient, ProviderError
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
    stage: Literal["foundation"] = "foundation"
    version: str
    rag_available: Literal[False] = False


class ReadinessResponse(Contract):
    status: Literal["not_ready"] = "not_ready"
    dependencies: dict[str, bool]
    rag_available: Literal[False] = False
    message: str = (
        "Base técnica disponible; el catálogo, el índice y el RAG se completarán después."
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    configured = settings or load_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        client: OllamaClient | None = None
        try:
            client = OllamaClient(configured, read_model_lock(configured))
        except (OSError, ValueError):
            pass
        app.state.model_client = client
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
    def health() -> HealthResponse:
        return HealthResponse(version=version("ragml"))

    @app.get("/ready", response_model=ReadinessResponse, status_code=503)
    def ready(request: Request) -> JSONResponse:
        dependencies = {
            "sqlite": bool(check_sqlite()),
            "generation_model": False,
            "embedding_model": False,
            "catalog_file": configured.resolve_path(configured.catalog_path).is_file(),
            "source_manifest_file": configured.resolve_path(configured.source_manifest).is_file(),
            "rag_implemented": False,
        }
        client: OllamaClient | None = request.app.state.model_client
        if client is not None:
            try:
                models = client.check_models()
                dependencies["generation_model"] = models["generation"]
                dependencies["embedding_model"] = models["embedding"]
            except (ProviderError, ValidationError):
                pass
        return JSONResponse(
            status_code=503,
            content=ReadinessResponse(dependencies=dependencies).model_dump(mode="json"),
        )

    @app.post(
        "/v1/chat",
        status_code=503,
        response_model=ErrorResponse,
        responses={422: {"model": ErrorResponse}},
    )
    def chat(body: ChatRequest, request: Request) -> JSONResponse:
        return error(
            request,
            503,
            "rag_not_ready",
            "La consulta RAG todavía no está implementada; esta ejecución prepara su base técnica.",
        )

    return app
