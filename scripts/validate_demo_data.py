"""Check the synthetic package against the project's current executable contracts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ragml.commercial import JsonCommercialAdapter  # noqa: E402
from ragml.contracts import CatalogDataset, CommercialDataset  # noqa: E402
from ragml.evidence import SourceManifest  # noqa: E402


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_package(root):
    catalog = CatalogDataset.model_validate_json(
        (root / "catalog.json").read_text(encoding="utf-8")
    )
    commercial = CommercialDataset.model_validate_json(
        (root / "commercial.json").read_text(encoding="utf-8")
    )
    manifest = SourceManifest.model_validate_json(
        (root / "sources.json").read_text(encoding="utf-8")
    )
    metadata = json.loads((root / "package-metadata.json").read_text(encoding="utf-8"))
    commercial.validate_for_catalog(catalog)
    manifest.validate_for_catalog(catalog)
    require(catalog.profile.store_id == "nexo-demo", "Unexpected demonstration store")
    require(catalog.profile.data_mode == "demo", "Real data is not allowed in this package")
    require(metadata["generated_by"] == "ragml-demo-data-v1", "Unknown package provenance")
    require(
        catalog.profile.revision
        == commercial.revision
        == manifest.revision
        == metadata["revision"],
        "Mixed package revisions",
    )
    counts = {
        "categories": len(catalog.profile.categories),
        "products": len(catalog.products),
        "variants": len(catalog.variants),
        "commercial_records": len(commercial.snapshots),
        "sources": len(manifest.sources),
        "chunks": len(manifest.chunks),
    }
    require(counts == metadata["counts"], "Metadata counts do not match the data")
    require(
        counts
        == {
            "categories": 6,
            "products": 60,
            "variants": 90,
            "commercial_records": 90,
            "sources": 72,
            "chunks": 204,
        },
        "The complete demonstration inventory is missing",
    )
    require(
        {v.variant_id for v in catalog.variants} == {s.variant_id for s in commercial.snapshots},
        "Every sellable variant must have a commercial observation",
    )
    require(catalog.profile.human_contact is None, "A fictional human contact must not be invented")

    products = {p.product_id: p for p in catalog.products}
    sources = {s.source_id: s for s in manifest.sources}
    source_texts = {}
    for source in manifest.sources:
        path = (PROJECT_ROOT / source.locator).resolve()
        require(path.is_relative_to(root), f"Source escapes the package: {source.source_id}")
        require(path.is_file(), f"Source file missing: {source.source_id}")
        require(source.provenance == "synthetic_created", "A source lacks synthetic provenance")
        raw = path.read_bytes()
        require(
            hashlib.sha256(raw).hexdigest() == source.content_hash, "Source content hash mismatch"
        )
        source_texts[source.source_id] = raw.decode("utf-8")
    for chunk in manifest.chunks:
        require(
            chunk.text in source_texts[chunk.source_id],
            f"Chunk is not an exact extract: {chunk.chunk_id}",
        )
        require(
            f"## {chunk.location.section}\n" in chunk.text, "Section locator is not in its chunk"
        )
    for entity in (*catalog.products, *catalog.variants):
        product_id = entity.product_id
        for attribute in entity.attributes:
            for source_id in attribute.evidence_refs:
                source = sources[source_id]
                require(
                    source.scope.kind == "product" and source.scope.target_id == product_id,
                    f"Attribute evidence belongs to a different product: {source_id}",
                )
    scopes = Counter(source.scope.kind for source in manifest.sources)
    require(scopes == {"product": 60, "category": 6, "store": 6}, "Unexpected source coverage")
    chunk_counts = Counter(chunk.source_id for chunk in manifest.chunks)
    require(all(chunk_counts[s.source_id] > 0 for s in manifest.sources), "A source has no extract")

    coverage = []
    for category in catalog.profile.categories:
        category_products = [p for p in catalog.products if p.category_id == category.category_id]
        category_variants = [
            v
            for v in catalog.variants
            if products[v.product_id].category_id == category.category_id
        ]
        require(
            len(category_products) == 10 and len(category_variants) == 15, "Category quota mismatch"
        )
        distribution = Counter(
            sum(v.product_id == p.product_id for v in category_variants) for p in category_products
        )
        require(distribution == {1: 5, 2: 5}, "Unexpected per-product variant distribution")
        coverage.append({"category_id": category.category_id, "products": 10, "variants": 15})

    evaluated_at = datetime.fromisoformat(metadata["recommended_test_time"].replace("Z", "+00:00"))
    lookups = JsonCommercialAdapter(root / "commercial.json", catalog).lookup(
        catalog.profile.store_id, tuple(v.variant_id for v in catalog.variants), evaluated_at
    )
    require(all(value.lookup_status == "found" for value in lookups), "Commercial lookup failed")
    price_status = Counter(value.price.status for value in lookups if value.price is not None)
    stock_status = Counter(value.stock.status for value in lookups if value.stock is not None)
    require(
        price_status == {"fresh": 78, "unknown": 6, "stale": 6}, "Unexpected price-state coverage"
    )
    require(stock_status == {"fresh": 84, "unknown": 6}, "Unexpected stock-state coverage")
    require(
        all(value.price.value is None for value in lookups if value.price.status != "fresh"),
        "Unconfirmed prices must not appear as confirmed values",
    )
    require(
        all(value.stock.value is None for value in lookups if value.stock.status != "fresh"),
        "Unconfirmed stock must not appear as a confirmed value",
    )
    for relative, expected in metadata["file_hashes"].items():
        path = (root / relative).resolve()
        require(path.is_relative_to(root), "A metadata path escapes its package")
        require(
            hashlib.sha256(path.read_bytes()).hexdigest() == expected,
            f"Package hash mismatch: {relative}",
        )
    return {
        "status": "passed",
        "revision": metadata["revision"],
        "data_mode": "demo",
        "counts": counts,
        "coverage": coverage,
        "source_scopes": dict(scopes),
        "commercial_reference_time": metadata["recommended_test_time"],
        "price_states_at_reference_time": dict(price_status),
        "stock_states_at_reference_time": dict(stock_status),
        "checks": [
            "current catalog, commercial and source contracts",
            "identifiers, category attributes and variant relations",
            "exact product association for attribute evidence",
            "source paths, file hashes and exact section extracts",
            "complete inventory and per-category quotas",
            "commercial lookup with an explicit synthetic clock",
            "fresh, unknown and stale values kept distinct",
            "package content hashes",
        ],
        "not_verified": [
            "retrieval index, embeddings, generation or browser behavior",
            "independent semantic audit of every invented specification",
            "final academic evaluation or utility with participants",
            "real business conditions or portability to an actual store",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="data/sample")
    parser.add_argument("--output", help="Optional project-relative JSON validation record")
    args = parser.parse_args()
    root = (PROJECT_ROOT / args.root).resolve()
    try:
        require(
            root.is_relative_to(PROJECT_ROOT / "data"),
            "Package must stay in the project data directory",
        )
        result = validate_package(root)
        output_text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            destination = (PROJECT_ROOT / args.output).resolve()
            require(
                destination.is_relative_to(PROJECT_ROOT / "docs" / "data"),
                "Validation output must stay in docs/data",
            )
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(output_text.encode("utf-8"))
        print(output_text, end="")
        return 0
    except (ValueError, OSError, KeyError) as error:
        print(json.dumps({"status": "failed", "error": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
