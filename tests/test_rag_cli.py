"""The document CLI can abstain without starting any model or creating an index."""

import json
from pathlib import Path

import pytest
from test_ingestion import package

from ragml.rag_cli import main


def test_cli_returns_explicit_commercial_abstention_without_a_model(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from shutil import copyfile

    corpus = package(tmp_path / "data" / "sample")
    (tmp_path / "config").mkdir()
    copyfile(Path("config/models.lock.json"), tmp_path / "config/models.lock.json")
    status = main(["¿Cuál es el precio?", "--project-dir", str(tmp_path)])
    assert status == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["response"]["store_id"] == corpus.catalog.profile.store_id
    assert payload["response"]["status"] == "insufficient_evidence"
    assert payload["response"]["warnings"] == ["commercial_lookup_required"]
    assert not (tmp_path / "data" / "runtime" / "corpus.sqlite3").exists()
