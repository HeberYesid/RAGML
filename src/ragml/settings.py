"""Validated local-only configuration with an explicit project directory."""

from pathlib import Path
from typing import Annotated, Literal, Self
from urllib.parse import urlsplit

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RAGML_", extra="forbid", frozen=True)

    project_dir: Path = Field(default_factory=Path.cwd)
    env: Literal["local"] = "local"
    data_mode: Literal["demo", "real"] = "demo"
    catalog_path: Path = Path("data/sample/catalog.json")
    commercial_path: Path = Path("data/sample/commercial.json")
    source_manifest: Path = Path("data/sample/sources.json")
    runtime_dir: Path = Path("data/runtime")
    model_lock_path: Path = Path("config/models.lock.json")
    host: Literal["127.0.0.1"] = "127.0.0.1"
    port: Annotated[int, Field(ge=1024, le=65535)] = 8000
    ollama_url: str = "http://127.0.0.1:11435"
    generation_model: str = "qwen3:4b-instruct-2507-q4_K_M"
    embedding_model: str = "qwen3-embedding:0.6b"
    embedding_dimensions: Annotated[int, Field(ge=1024, le=1024)] = 1024
    context_tokens: Annotated[int, Field(ge=1024, le=8192)] = 4096
    output_tokens: Annotated[int, Field(ge=16, le=512)] = 256
    model_timeout_seconds: Annotated[float, Field(ge=1, le=300)] = 180
    session_ttl_seconds: Annotated[int, Field(ge=60, le=7200)] = 1800
    max_message_chars: Annotated[int, Field(ge=4000, le=4000)] = 4000
    retrieval_k: Annotated[int, Field(ge=1, le=10)] = 5
    allow_remote_providers: bool = False

    @field_validator("allow_remote_providers")
    @classmethod
    def forbid_remote_providers(cls, value: bool) -> bool:
        if value:
            raise ValueError("This local prototype does not enable remote providers")
        return value

    @field_validator("ollama_url")
    @classmethod
    def require_loopback(cls, value: str) -> str:
        parsed = urlsplit(value)
        if (
            parsed.scheme != "http"
            or parsed.hostname != "127.0.0.1"
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path not in ("", "/")
            or parsed.query
            or parsed.fragment
            or parsed.port is None
        ):
            raise ValueError("Ollama requires an explicit HTTP IPv4 loopback address and port")
        return value.rstrip("/")

    @field_validator("generation_model", "embedding_model")
    @classmethod
    def local_model_only(cls, value: str) -> str:
        if not value.strip() or "cloud" in value.lower() or "://" in value:
            raise ValueError("A local model tag is required")
        return value

    @model_validator(mode="after")
    def valid_budget(self) -> Self:
        if self.output_tokens >= self.context_tokens:
            raise ValueError("Output allowance must leave room for input")
        return self

    def resolve_path(self, value: Path) -> Path:
        return (self.project_dir / value).resolve()


def load_settings(project_dir: Path | None = None, env_file: Path | None = None) -> Settings:
    root = (project_dir or Path.cwd()).resolve()
    selected_env = env_file if env_file is not None else root / ".env"

    class ProjectSettings(Settings):
        model_config = SettingsConfigDict(
            env_prefix="RAGML_",
            extra="forbid",
            frozen=True,
            env_file=selected_env,
            env_file_encoding="utf-8",
        )

    return ProjectSettings(project_dir=root)
