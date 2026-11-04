"""Public HTTP boundaries of the optional local web entry point."""

from pathlib import Path

from fastapi.testclient import TestClient
from test_local_contracts import make_catalog

from ragml.settings import Settings


def test_web_serves_the_interface_without_masking_the_api(tmp_path: Path) -> None:
    from ragml.web import create_web_app

    with TestClient(create_web_app(Settings(project_dir=tmp_path))) as client:
        page = client.get("/")
        assert page.status_code == 200
        assert 'lang="es"' in page.text
        assert 'src="/assets/app.js"' in page.text
        assert client.get("/assets/app.js").status_code == 200
        assert client.get("/assets/styles.css").status_code == 200
        assert client.get("/health").status_code == 200
        response = client.post("/v1/chat", json={"message": "Consulta de prueba"})
        assert response.status_code == 503
        assert response.json()["code"] == "rag_not_ready"
        assert client.get("/assets/../settings.py").status_code == 404


def test_web_catalog_uses_the_configured_store_and_rejects_mode_mismatch(tmp_path: Path) -> None:
    from ragml.web import create_web_app

    catalog = make_catalog()
    path = tmp_path / "catalog.json"
    path.write_text(catalog.model_dump_json(), encoding="utf-8")
    settings = Settings(project_dir=tmp_path, catalog_path=path)
    with TestClient(create_web_app(settings)) as client:
        response = client.get("/v1/web/catalog")
        assert response.status_code == 200
        assert response.json()["profile"]["store_id"] == "shop-a"
        assert response.json()["products"] == catalog.model_dump(mode="json")["products"]
        assert response.headers["cache-control"] == "no-store"
    with TestClient(create_web_app(settings.model_copy(update={"data_mode": "real"}))) as client:
        assert client.get("/v1/web/catalog").status_code == 503
