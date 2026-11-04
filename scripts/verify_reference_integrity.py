"""Check frozen case/source hashes without opening reserved questions or answers."""

import argparse
import json
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    manifest_path = ROOT / "data/evaluation/partitions.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    checks = {
        "adjustment_cases": ("data/evaluation/adjustment/cases.json", "adjustment_sha256"),
        "reserved_archive": ("data/evaluation/reserved/final-cases.zip", "reserved_archive_sha256"),
        "catalog": ("data/sample/catalog.json", "catalog_sha256"),
        "sources": ("data/sample/sources.json", "source_manifest_sha256"),
        "commercial": ("data/sample/commercial.json", "commercial_sha256"),
    }
    matched = {
        name: sha256((ROOT / path).read_bytes()).hexdigest() == manifest[field]
        for name, (path, field) in checks.items()
    }
    result = {
        "status": "passed" if all(matched.values()) else "failed",
        "reference_set_revision": manifest["reference_set_revision"],
        "partitions_manifest_sha256": sha256(manifest_path.read_bytes()).hexdigest(),
        "counts": manifest["counts"],
        "hashes_match": matched,
        "reserved_archive_unpacked": False,
        "assistant_evaluation_executed": False,
    }
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        destination = (ROOT / args.output).resolve()
        if not destination.is_relative_to(ROOT / "docs" / "data"):
            parser.error("Verification output must remain in docs/data")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
