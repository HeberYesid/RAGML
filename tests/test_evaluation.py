"""Phase-7 worked examples through the public metrics and JSON interfaces."""

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest

from ragml.conversation import ChatResponse
from ragml.evaluation import (
    CountMetric,
    EvaluationRun,
    HumanReview,
    main,
    read_run,
    summarize,
    write_run,
)


def test_counts_keep_empty_denominators_not_applicable_and_reject_impossible_counts() -> None:
    assert CountMetric(numerator=1, denominator=2).value == 0.5
    assert CountMetric(numerator=0, denominator=0).value is None
    with pytest.raises(ValueError):
        CountMetric(numerator=2, denominator=1)


def run_payload() -> dict[str, Any]:
    return {
        "run_id": "worked-example",
        "purpose": "software_example",
        "system": "retrieval_only",
        "created_at": "2026-11-04T18:00:00Z",
        "candidate_sha256": "a" * 64,
        "artifacts": {"references": "b" * 64, "models": "c" * 64},
        "versions": {"corpus": "fixture-v1", "embedding": "fixture-model"},
        "parameters": {"k": 5},
        "environment": "Artificial examples, no model execution",
        "concurrency": 1,
        "planned_cases": 4,
        "cases": [
            {
                "case_id": "example-1",
                "family_id": "family-a",
                "category_id": "category-a",
                "task_type": "document",
                "evaluated_at": "2026-11-04T12:05:00Z",
                "execution": "completed",
                "response_status": "answered",
                "gold_chunk_ids": ["a", "b"],
                "retrieved_chunk_ids": ["a", "a"],
                "timings_seconds": {"total": 1.0},
                "warm_state": "warm",
            },
            {
                "case_id": "example-2",
                "family_id": "family-b",
                "category_id": "category-a",
                "task_type": "document",
                "evaluated_at": "2026-11-04T12:05:00Z",
                "execution": "error",
                "error_code": "provider_unavailable",
                "gold_chunk_ids": ["c"],
                "timings_seconds": {"total": 3.0},
                "warm_state": "cold",
            },
            {
                "case_id": "example-3",
                "family_id": "family-c",
                "category_id": "category-b",
                "task_type": "insufficient",
                "evaluated_at": "2026-11-04T12:05:00Z",
                "execution": "completed",
                "response_status": "insufficient_evidence",
                "timings_seconds": {"total": 2.0},
                "warm_state": "unknown",
            },
        ],
    }


def test_run_roundtrip_and_invalid_records() -> None:
    run = EvaluationRun.model_validate(run_payload())
    assert EvaluationRun.model_validate_json(run.model_dump_json()) == run
    mutations = [
        {"partition": "final"},
        {"candidate_sha256": "unversioned"},
        {"created_at": "2026-11-04T18:00:00"},
        {"planned_cases": 1},
        {"cases": [run_payload()["cases"][0]] * 2},
        {"participant_name": "not-allowed"},
    ]
    for mutation in mutations:
        with pytest.raises(ValueError):
            EvaluationRun.model_validate(run_payload() | mutation)


@pytest.mark.parametrize(
    "change",
    [
        {"timings_seconds": {"total": -1}},
        {"timings_seconds": {"total": float("nan")}},
        {"timings_seconds": {"total": float("inf")}},
        {"execution": "error"},
        {"error_code": "unexpected_error"},
        {"response_status": "temporarily_unavailable"},
    ],
)
def test_invalid_case_records_cannot_enter_a_run(change: dict[str, Any]) -> None:
    payload = deepcopy(run_payload())
    payload["cases"][0].update(change)
    with pytest.raises(ValueError):
        EvaluationRun.model_validate(payload)


def response_payload() -> dict[str, Any]:
    return {
        "request_id": "00000000-0000-0000-0000-000000000001",
        "session_id": "00000000-0000-0000-0000-000000000002",
        "store_id": "fixture",
        "data_mode": "demo",
        "status": "insufficient_evidence",
        "answer": "No supporting evidence.",
        "versions": {"corpus": "fixture-v1"},
    }


def review_payload() -> dict[str, Any]:
    response = ChatResponse.model_validate(response_payload())
    return {
        "reviewer_code": "R01",
        "reviewed_at": "2026-11-04T19:00:00Z",
        "response_sha256": sha256(response.model_dump_json().encode()).hexdigest(),
        "rubric": {
            "product_correctness": "not_applicable",
            "data_accuracy": "not_applicable",
            "source_sufficiency": "meets",
            "constraint_compliance": "not_applicable",
            "response_adequacy": "meets",
        },
        "evidence_references": ["fixture-v1:example-3"],
        "rationale": "Worked human label, not a real evaluation.",
        "insufficiency_handling": {"numerator": 1, "denominator": 1},
    }


def test_review_requires_matching_saved_response_and_cannot_score_partial_as_half() -> None:
    payload = run_payload()
    payload["system"] = "document_rag"
    payload["cases"][2].update(response=response_payload(), review=review_payload())
    run = EvaluationRun.model_validate(payload)
    assert run.cases[2].review.insufficiency_handling.value == 1.0
    bad = deepcopy(payload)
    bad["cases"][2]["response"]["answer"] = "Changed after review."
    with pytest.raises(ValueError, match="review_response_mismatch"):
        EvaluationRun.model_validate(bad)
    for change in [
        {"rubric": {}},
        {"rationale": ""},
        {"evidence_references": []},
        {"task_resolution": {"numerator": 2, "denominator": 2}},
        {"factual_correctness": {"numerator": 0.5, "denominator": 1}},
    ]:
        with pytest.raises(ValueError):
            HumanReview.model_validate(review_payload() | change)


def test_summary_separates_failures_coverage_human_labels_and_warm_latency() -> None:
    run = EvaluationRun.model_validate(run_payload())
    report = summarize(run)
    assert report["coverage"] == {
        "planned": 4,
        "attempted": 3,
        "completed": 2,
        "errors": 1,
        "not_run": 1,
        "human_reviewed": 0,
    }
    assert report["recall_at_k"] == {"k": 5, "mean": 0.25, "applicable_cases": 2}
    assert report["latency"]["all"] == {"count": 3, "median": 2.0, "p95": 3.0}
    assert report["latency"]["warm"] == {"count": 1, "median": 1.0, "p95": 1.0}
    assert report["human_metrics"]["factual_correctness"]["value"] is None
    assert report["critical_errors"]["reviewed_cases"] == 0
    assert report["by_category"]["category-b"]["recall_at_k"]["mean"] is None
    assert report["by_task"]["document"]["coverage"]["errors"] == 1


def test_reviewed_abstention_is_not_task_success_and_empty_run_is_not_perfect() -> None:
    payload = run_payload()
    payload["system"] = "document_rag"
    review = review_payload() | {"task_resolution": {"numerator": 0, "denominator": 1}}
    payload["cases"][2].update(response=response_payload(), review=review)
    report = summarize(EvaluationRun.model_validate(payload))
    assert report["human_metrics"]["insufficiency_handling"]["value"] == 1.0
    assert report["human_metrics"]["task_resolution"]["value"] == 0.0
    empty = summarize(EvaluationRun.model_validate(payload | {"cases": []}))
    assert empty["recall_at_k"]["mean"] is None
    assert empty["latency"]["all"]["p95"] is None


def test_run_files_preserve_evidence_and_cli_generates_summary(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    run = EvaluationRun.model_validate(run_payload())
    path = tmp_path / "run.json"
    write_run(run, path)
    assert read_run(path) == run
    original = path.read_bytes()
    with pytest.raises(FileExistsError):
        write_run(run, path)
    assert path.read_bytes() == original
    output = tmp_path / "summary.json"
    assert main(["summarize", "--input", str(path), "--output", str(output)]) == 0
    assert '"mean": 0.25' in output.read_text(encoding="utf-8")
    assert main(["summarize", "--input", str(path), "--output", str(output)]) == 1
    bad = tmp_path / "invalid.json"
    bad.write_text('{"private_text": "must-not-be-logged"}', encoding="utf-8")
    assert main(["summarize", "--input", str(bad), "--output", str(tmp_path / "bad.json")]) == 1
    assert "must-not-be-logged" not in capsys.readouterr().out


def test_imported_historical_measurements_do_not_invent_a_candidate_fingerprint() -> None:
    payload = run_payload() | {
        "candidate_sha256": None,
        "candidate_provenance": "unknown_historical_candidate",
    }
    run = EvaluationRun.model_validate(payload)
    assert run.candidate_sha256 is None
    with pytest.raises(ValueError):
        EvaluationRun.model_validate(payload | {"candidate_provenance": "recorded_at_execution"})
    with pytest.raises(ValueError):
        EvaluationRun.model_validate(payload | {"candidate_sha256": "a" * 64})
