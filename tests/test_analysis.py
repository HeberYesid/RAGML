"""Observable descriptive statistics and reproducible analysis exports."""

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

from ragml.analysis import describe
from ragml.contracts import (
    AttributeDefinition,
    AttributeValue,
    CatalogDataset,
    Category,
    CommercialDataset,
    CommercialSnapshot,
    Money,
    Observation,
    Product,
    Stock,
    StoreProfile,
    Variant,
)
from ragml.evidence import Chunk, Location, Source, SourceManifest, SourceScope

NOW = datetime(2026, 11, 4, 12, 5, tzinfo=UTC)


def analysis_fixture() -> tuple[CatalogDataset, CommercialDataset, SourceManifest, dict[str, str]]:
    text = "Ancho de prueba 2 cm."
    digest = sha256(text.encode()).hexdigest()
    catalog = CatalogDataset(
        profile=StoreProfile(
            store_id="sample",
            display_name="Sample",
            data_mode="demo",
            locale="es-CO",
            currency="COP",
            currency_decimal_places=0,
            revision="r1",
            categories=(
                Category(
                    category_id="a",
                    name="Anchos",
                    attribute_definitions=(
                        AttributeDefinition(
                            key="width", label="Ancho", value_type="number", unit="cm"
                        ),
                    ),
                ),
                Category(
                    category_id="b",
                    name="Masas",
                    attribute_definitions=(
                        AttributeDefinition(
                            key="mass", label="Masa", value_type="number", unit="g"
                        ),
                    ),
                ),
            ),
        ),
        products=tuple(
            Product(
                store_id="sample",
                product_id=pid,
                category_id=category,
                name=pid,
                attributes=attrs,
                revision="r1",
            )
            for pid, category, attrs in (
                (
                    "p1",
                    "a",
                    (AttributeValue(key="width", value=2, unit="cm", evidence_refs=("s1",)),),
                ),
                ("p2", "a", (AttributeValue(key="width", value=None, unit="cm"),)),
                ("p3", "a", ()),
                (
                    "p4",
                    "b",
                    (AttributeValue(key="mass", value=1000, unit="g", evidence_refs=("s1",)),),
                ),
            )
        ),
        variants=tuple(
            Variant(
                store_id="sample",
                variant_id=f"v{i}",
                product_id=f"p{i}",
                name=f"v{i}",
                revision="r1",
            )
            for i in range(1, 5)
        ),
    )
    commercial = CommercialDataset(
        store_id="sample",
        data_mode="demo",
        revision="r1",
        snapshots=tuple(
            CommercialSnapshot(
                store_id="sample",
                variant_id=f"v{i}",
                snapshot_id=f"snap{i}",
                source_id="commerce",
                revision="r1",
                price=Observation[Money](
                    value=Money(amount=Decimal(amount), currency="COP") if amount else None,
                    source_updated_at=NOW - timedelta(minutes=10),
                    expires_at=NOW + timedelta(minutes=5) if i != 3 else NOW - timedelta(minutes=1),
                    source_ref=f"commerce/v{i}/price",
                ),
                stock=Observation[Stock](
                    value=None
                    if i == 2
                    else Stock(
                        availability="out_of_stock" if i == 4 else "in_stock",
                        quantity=0 if i == 4 else 2,
                    ),
                    source_updated_at=NOW - timedelta(minutes=10),
                    expires_at=NOW + timedelta(minutes=5) if i != 3 else NOW - timedelta(minutes=1),
                    source_ref=f"commerce/v{i}/stock",
                ),
            )
            for i, amount in enumerate(("10", None, "20", "200"), 1)
        ),
    )
    manifest = SourceManifest(
        store_id="sample",
        data_mode="demo",
        revision="r1",
        sources=(
            Source(
                store_id="sample",
                source_id="s1",
                title="Prueba",
                version="r1",
                content_hash=digest,
                data_mode="demo",
                scope=SourceScope(kind="store"),
                locator="source.md",
                provenance="synthetic_created",
            ),
        ),
        chunks=(
            Chunk(
                store_id="sample",
                chunk_id="c1",
                source_id="s1",
                source_version="r1",
                source_content_hash=digest,
                content_hash=digest,
                text=text,
                location=Location(section="Prueba"),
            ),
        ),
    )
    return catalog, commercial, manifest, {"s1": text}


def write_analysis_fixture(root: Path) -> None:
    catalog, commercial, manifest, texts = analysis_fixture()
    sample = root / "data/sample"
    sample.mkdir(parents=True)
    (sample / "catalog.json").write_text(catalog.model_dump_json(), encoding="utf-8")
    (sample / "commercial.json").write_text(commercial.model_dump_json(), encoding="utf-8")
    (sample / "sources.json").write_text(manifest.model_dump_json(), encoding="utf-8")
    (sample / "package-metadata.json").write_text(
        json.dumps(
            {
                "store_id": "sample",
                "revision": "r1",
                "data_mode": "demo",
                "recommended_test_time": NOW.isoformat(),
            }
        ),
        encoding="utf-8",
    )
    (root / "source.md").write_text(texts["s1"], encoding="utf-8")


def test_descriptive_statistics_keep_unknown_values_and_flag_without_deleting() -> None:
    summary = describe((None, 10.0, 10.0, 10.0, 10.0, 100.0))

    assert summary.count == 5
    assert summary.missing == 1
    assert summary.mean == 28.0
    assert summary.median == 10.0
    assert summary.minimum == 10.0
    assert summary.maximum == 100.0
    assert summary.q1 == summary.q3 == 10.0
    assert summary.outlier_values == (100.0,)
    assert summary.outlier_count == 1


def test_analysis_excludes_stale_commerce_and_separates_attribute_units() -> None:
    from ragml.analysis import analyze_dataset

    catalog, commercial, manifest, texts = analysis_fixture()
    report = analyze_dataset(catalog, commercial, manifest, texts, evaluated_at=NOW)

    assert report.counts == {
        "categories": 2,
        "products": 4,
        "variants": 4,
        "commercial_records": 4,
        "sources": 1,
        "chunks": 1,
    }
    assert report.fresh_prices.count == 2
    assert report.fresh_prices.mean == 105.0
    assert report.price_statuses == {
        "fresh": 2,
        "unknown": 1,
        "stale": 1,
        "not_yet_valid": 0,
        "not_found": 0,
    }
    assert report.stock_states == {
        "in_stock": 1,
        "out_of_stock": 1,
        "unknown": 1,
        "stale": 1,
        "not_yet_valid": 0,
        "not_found": 0,
    }
    width, mass = report.attributes
    assert (width.unit, width.known, width.explicit_null, width.absent) == ("cm", 1, 1, 1)
    assert width.numeric is not None and width.numeric.mean == 2.0
    assert width.numeric.missing == 2
    assert mass.unit == "g" and mass.numeric is not None and mass.numeric.mean == 1000.0
    assert report.chunk_lengths.count == report.document_lengths.count == 1


def test_cli_exports_traceable_tables_without_overwriting(tmp_path: Path) -> None:
    from ragml.analysis import main

    write_analysis_fixture(tmp_path)
    _, _, _, texts = analysis_fixture()
    sample = tmp_path / "data/sample"
    output = tmp_path / "analysis"
    argv = ["--project-dir", str(tmp_path), "--output-dir", str(output), "--no-charts"]

    assert main(argv) == 0
    payload = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    assert payload["evaluated_at"] == "2026-11-04T12:05:00Z"
    assert (
        payload["input_sha256"]["data/sample/catalog.json"]
        == sha256((sample / "catalog.json").read_bytes()).hexdigest()
    )
    assert payload["input_sha256"]["source.md"] == sha256(texts["s1"].encode()).hexdigest()
    assert (
        (output / "categories.csv")
        .read_text(encoding="utf-8-sig")
        .startswith("category_id,name,products,variants")
    )
    assert (output / "attributes.csv").is_file()
    assert (output / "commercial.csv").is_file()
    assert (output / "documents.csv").is_file()
    assert (output / "outliers.csv").is_file()
    before = (output / "summary.json").read_bytes()
    assert main(argv) == 1
    assert (output / "summary.json").read_bytes() == before


def test_cli_produces_all_figures_with_tables(tmp_path: Path) -> None:
    from ragml.analysis import main

    write_analysis_fixture(tmp_path)
    output = tmp_path / "analysis"
    assert main(["--project-dir", str(tmp_path), "--output-dir", str(output)]) == 0
    for stem in ("categories", "prices", "missingness", "commerce", "lengths"):
        assert (output / f"{stem}.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
        assert "<svg" in (output / f"{stem}.svg").read_text(encoding="utf-8")
    assert (output / "README.md").is_file()
