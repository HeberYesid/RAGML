"""Measure the basic retriever on adjustment documents; never open reserved cases."""

import argparse
import json
import math
import statistics
import time
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ragml.api import read_model_lock
from ragml.ports import RetrievalQuery
from ragml.providers import OllamaClient, ProviderError
from ragml.retrieval import RetrievalError, SqliteRetriever
from ragml.settings import load_settings


def recall_at_k(gold: tuple[str, ...], retrieved: tuple[str, ...], k: int) -> float | None:
    if not 1 <= k <= 10:
        raise ValueError("invalid_retrieval_k")
    relevant = set(gold)
    return len(relevant.intersection(retrieved[:k])) / len(relevant) if relevant else None


class AdjustmentTurn(BaseModel):
    model_config = ConfigDict(extra="ignore")
    role: str
    text: str


class AdjustmentCase(BaseModel):
    model_config = ConfigDict(extra="ignore")
    case_id: str
    partition: Literal["adjustment"]
    task_type: str
    store_id: str
    corpus_revision: str
    turns: tuple[AdjustmentTurn, ...] = Field(min_length=1)
    gold_chunk_ids: tuple[str, ...]


class AdjustmentSet(BaseModel):
    model_config = ConfigDict(extra="ignore")
    partition: Literal["adjustment"]
    store_id: str
    corpus_revision: str
    reference_set_revision: str
    cases: tuple[AdjustmentCase, ...]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--database", type=Path, default=Path("data/runtime/corpus.sqlite3"))
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument(
        "--output", type=Path, default=Path("docs/evaluation/phase4/adjustment-retrieval.json")
    )
    args = parser.parse_args(argv)
    client: OllamaClient | None = None
    try:
        settings = load_settings(args.project_dir)
        # Intentionally fixed to the development partition; no reserved-file option.
        raw = (settings.project_dir / "data/evaluation/adjustment/cases.json").read_bytes()
        cases = AdjustmentSet.model_validate_json(raw)
        lock = read_model_lock(settings)
        client = OllamaClient(settings, lock)
        retriever = SqliteRetriever(
            settings.resolve_path(args.database),
            client,
            model=lock.embedding.tag,
            digest=lock.embedding.digest,
            dimensions=lock.embedding_dimensions,
        )
        snapshot = retriever.snapshot(cases.store_id, cases.corpus_revision)
        selected = [case for case in cases.cases if case.task_type in ("document", "policy")]
        if not selected or len({case.case_id for case in selected}) != len(selected):
            raise ValueError("invalid_adjustment_cases")
        known = {chunk.chunk_id for chunk in snapshot.manifest.chunks}
        records: list[dict[str, object]] = []
        recalls: list[float] = []
        durations: list[float] = []
        failures = 0
        for case in selected:
            if (case.store_id, case.corpus_revision) != (cases.store_id, cases.corpus_revision):
                raise ValueError("reference_corpus_mismatch")
            if not set(case.gold_chunk_ids) <= known:
                raise ValueError("reference_chunk_missing")
            turn = case.turns[0]
            if turn.role != "user" or len(case.turns) != 1:
                raise ValueError("document_case_not_single_turn")
            query = RetrievalQuery(
                store_id=case.store_id, revision=case.corpus_revision, text=turn.text, k=args.k
            )
            started = time.monotonic()
            error_code: str | None = None
            retrieved: tuple[str, ...] = ()
            try:
                hits = retriever.search_snapshot(snapshot, query)
                retrieved = tuple(hit.chunk.chunk_id for hit in hits)
            except (ProviderError, RetrievalError) as error:
                failures += 1
                error_code = str(error)
            seconds = round(time.monotonic() - started, 6)
            recall = recall_at_k(case.gold_chunk_ids, retrieved, args.k)
            if recall is not None:
                recalls.append(recall)  # Failed applicable queries contribute zero.
            durations.append(seconds)
            records.append(
                {
                    "case_id": case.case_id,
                    "task_type": case.task_type,
                    "query": turn.text,
                    "gold_chunk_ids": list(case.gold_chunk_ids),
                    "retrieved_chunk_ids": list(retrieved),
                    "recall": recall,
                    "seconds": seconds,
                    "error": error_code,
                }
            )
            print(f"{case.case_id}: recall={recall}, error={error_code}", flush=True)
        result = {
            "kind": "phase4_adjustment_retrieval_not_final_evaluation",
            "created_at": datetime.now(UTC).isoformat(),
            "partition": "adjustment",
            "reference_revision": cases.reference_set_revision,
            "reference_sha256": sha256(raw).hexdigest(),
            "index": snapshot.info.model_dump(),
            "k": args.k,
            "filters": "none; expected identities not supplied to retrieval",
            "summary": {
                "cases": len(records),
                "applicable_recall_cases": len(recalls),
                "failed_queries": failures,
                "mean_recall": statistics.mean(recalls) if recalls else None,
                "median_seconds": statistics.median(durations),
                "p95_seconds_nearest_rank": sorted(durations)[math.ceil(0.95 * len(durations)) - 1],
            },
            "limits": [
                "Adjustment partition only; no final evaluation or user study.",
                "Retrieval only: no answer correctness, semantic citation fidelity or usefulness score.",
                "Failures contribute zero recall when positive references exist.",
                "Timings describe this sequential run; model warm state is uncontrolled.",
            ],
            "cases": records,
        }
        output = settings.resolve_path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result["summary"], ensure_ascii=False))
        return 1 if failures else 0
    except (OSError, ValueError, ProviderError) as error:
        code = (
            str(error)
            if isinstance(error, RetrievalError | ProviderError)
            else type(error).__name__
        )
        print(json.dumps({"status": "failed", "code": code}))
        return 1
    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    raise SystemExit(main())
