"""Loopback-only Ollama boundary with pinned model identity and bounded work."""

import math
import threading
from typing import Annotated, Literal, Self

import httpx
from pydantic import BaseModel, ConfigDict, Field, model_validator

from ragml.contracts import Contract, Identifier
from ragml.evidence import Sha256
from ragml.settings import Settings


class ModelIdentity(Contract):
    tag: Identifier
    digest: Sha256
    size_bytes: Annotated[int, Field(gt=0)]
    quantization: Identifier


class ModelLock(Contract):
    schema_version: Literal["0.1"] = "0.1"
    runtime_version: Identifier
    generation: ModelIdentity
    embedding: ModelIdentity
    embedding_dimensions: Literal[1024] = 1024

    def validate_settings(self, settings: Settings) -> None:
        if (self.generation.tag, self.embedding.tag) != (
            settings.generation_model,
            settings.embedding_model,
        ):
            raise ValueError("Configured model tags do not match the model lock")


class ProviderError(RuntimeError):
    """Safe error code; response bodies and input text are never embedded in errors."""


class RuntimeResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", allow_inf_nan=False)


class RuntimeModel(RuntimeResponse):
    name: str
    digest: str


class RuntimeTags(RuntimeResponse):
    models: list[RuntimeModel]


class RuntimeMessage(RuntimeResponse):
    content: str


class GenerationResult(RuntimeResponse):
    message: RuntimeMessage
    done: bool
    done_reason: str | None = None
    total_duration: int = 0
    load_duration: int = 0
    prompt_eval_count: int = 0
    eval_count: int = 0

    @model_validator(mode="after")
    def require_complete_output(self) -> Self:
        if not self.done or not self.message.content.strip() or self.done_reason == "length":
            raise ValueError("Generation did not finish with usable complete text")
        return self


class EmbeddingResult(RuntimeResponse):
    embeddings: list[list[float]]
    total_duration: int = 0
    load_duration: int = 0
    prompt_eval_count: int = 0


class OllamaClient:
    def __init__(
        self,
        settings: Settings,
        lock: ModelLock,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        lock.validate_settings(settings)
        self.settings = settings
        self.lock = lock
        self._busy = threading.Lock()
        self._http = httpx.Client(
            base_url=settings.ollama_url,
            timeout=httpx.Timeout(settings.model_timeout_seconds, connect=3, pool=3),
            trust_env=False,
            follow_redirects=False,
            transport=transport,
        )

    def close(self) -> None:
        self._http.close()

    def _request(self, method: str, path: str, payload: dict[str, object] | None = None) -> object:
        try:
            response = self._http.request(method, path, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException as exc:
            raise ProviderError("provider_timeout") from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise ProviderError("provider_unavailable") from exc

    def check_models(self) -> dict[str, bool]:
        try:
            tags = RuntimeTags.model_validate(self._request("GET", "/api/tags"))
        except ValueError as exc:
            raise ProviderError("invalid_provider_response") from exc
        identities = {model.name: model.digest.removeprefix("sha256:") for model in tags.models}
        return {
            "generation": identities.get(self.lock.generation.tag) == self.lock.generation.digest,
            "embedding": identities.get(self.lock.embedding.tag) == self.lock.embedding.digest,
        }

    def _verify_identity(self, kind: str) -> None:
        if not self.check_models()[kind]:
            raise ProviderError("model_missing_or_changed")

    def generate(
        self, system: str, user: str, *, output_tokens: int | None = None
    ) -> GenerationResult:
        if not system.strip() or not user.strip() or len(system) + len(user) > 12000:
            raise ValueError("Generation input must be nonempty and at most 12000 characters")
        budget = output_tokens if output_tokens is not None else self.settings.output_tokens
        if not 1 <= budget <= self.settings.output_tokens:
            raise ValueError("Output exceeds the configured budget")
        if not self._busy.acquire(blocking=False):
            raise ProviderError("provider_busy")
        try:
            self._verify_identity("generation")
            payload: dict[str, object] = {
                "model": self.settings.generation_model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "stream": False,
                "think": False,
                "keep_alive": "2m",
                "options": {
                    "num_ctx": self.settings.context_tokens,
                    "num_predict": budget,
                    "temperature": 0.2,
                    "seed": 42,
                },
            }
            return GenerationResult.model_validate(self._request("POST", "/api/chat", payload))
        except ValueError as exc:
            raise ProviderError("invalid_or_incomplete_generation") from exc
        finally:
            self._busy.release()

    def embed(self, texts: tuple[str, ...], *, query: bool = False) -> EmbeddingResult:
        if not 1 <= len(texts) <= 16 or any(not t.strip() or len(t) > 4000 for t in texts):
            raise ValueError(
                "Embedding batch must have 1-16 nonempty texts of at most 4000 characters"
            )
        inputs = [
            "Instruct: Given a web search query, retrieve relevant passages that answer the query\n"
            f"Query: {text}"
            if query
            else text
            for text in texts
        ]
        if not self._busy.acquire(blocking=False):
            raise ProviderError("provider_busy")
        try:
            self._verify_identity("embedding")
            payload: dict[str, object] = {
                "model": self.settings.embedding_model,
                "input": inputs,
                "truncate": False,
                "keep_alive": "2m",
                "options": {"num_ctx": self.settings.context_tokens},
            }
            result = EmbeddingResult.model_validate(self._request("POST", "/api/embed", payload))
            if len(result.embeddings) != len(texts) or any(
                len(vector) != self.settings.embedding_dimensions
                or not math.isclose(math.fsum(v * v for v in vector), 1, abs_tol=0.01)
                for vector in result.embeddings
            ):
                raise ValueError("Embedding count, dimensions or normalization mismatch")
            return result
        except ValueError as exc:
            raise ProviderError("invalid_embedding_response") from exc
        finally:
            self._busy.release()
