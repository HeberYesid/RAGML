"""Optional same-origin web shell; the existing API owns conversational behavior."""

import argparse
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from ragml.api import create_app
from ragml.contracts import CatalogDataset
from ragml.settings import Settings, load_settings

ASSETS = Path(__file__).with_name("web_assets")


def create_web_app(settings: Settings | None = None) -> FastAPI:
    configured = settings or load_settings()
    app = create_app(configured)
    app.mount("/assets", StaticFiles(directory=ASSETS), name="web-assets")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(ASSETS / "index.html", headers={"Cache-Control": "no-store"})

    @app.get("/v1/web/catalog", response_model=CatalogDataset)
    def catalog(response: Response) -> CatalogDataset:
        try:
            data = CatalogDataset.model_validate_json(
                configured.resolve_path(configured.catalog_path).read_text(encoding="utf-8")
            )
            if data.profile.data_mode != configured.data_mode:
                raise ValueError("Catalog mode differs from the configured mode")
        except (OSError, ValueError) as exc:
            raise HTTPException(status_code=503, detail="Catalog unavailable") from exc
        response.headers["Cache-Control"] = "no-store"
        return data

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local RAGML web prototype")
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--env-file", type=Path)
    args = parser.parse_args()
    settings = load_settings(args.project_dir, args.env_file)
    uvicorn.run(create_web_app(settings), host=settings.host, port=settings.port, access_log=False)


if __name__ == "__main__":
    main()
