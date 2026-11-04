"""Offline phase-7 metrics and records, independent of assistant orchestration."""

import argparse
import json
import math
import statistics
from hashlib import sha256
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import AwareDatetime, Field, model_validator

from ragml.contracts import Contract, Identifier
from ragml.conversation import ChatResponse
from ragml.rag_evaluation import recall_at_k

NonnegativeInt = Annotated[int, Field(strict=True, ge=0)]
Seconds = Annotated[float, Field(ge=0, allow_inf_nan=False)]
Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class CountMetric(Contract):
    numerator: NonnegativeInt
    denominator: NonnegativeInt

    @model_validator(mode="after")
    def check_counts(self) -> Self:
        if self.numerator > self.denominator:
            raise ValueError("numerator_exceeds_denominator")
        return self

    @property
    def value(self) -> float | None:
        return self.numerator / self.denominator if self.denominator else None


RubricLabel = Literal["meets", "partial", "fails", "not_applicable"]


class Rubric(Contract):
    product_correctness: RubricLabel
    data_accuracy: RubricLabel
    source_sufficiency: RubricLabel
    constraint_compliance: RubricLabel
    response_adequacy: RubricLabel


class HumanReview(Contract):
    reviewer_code: Identifier
    reviewed_at: AwareDatetime
    response_sha256: Sha256
    independent_reviewer: bool = False
    rubric: Rubric
    evidence_references: Annotated[tuple[Identifier, ...], Field(min_length=1)]
    rationale: Identifier
    factual_correctness: CountMetric | None = None
    evidence_support: CountMetric | None = None
    citation_fidelity: CountMetric | None = None
    commercial_identity: CountMetric | None = None
    mandatory_constraints: CountMetric | None = None
    insufficiency_handling: CountMetric | None = None
    task_resolution: CountMetric | None = None
    critical_errors: tuple[Identifier, ...] = ()

    @model_validator(mode="after")
    def check_review(self) -> Self:
        for metric in (self.insufficiency_handling, self.task_resolution):
            if metric is not None and metric.denominator > 1:
                raise ValueError("case_outcome_requires_binary_count")
        if (
            self.factual_correctness is not None
            and self.evidence_support is not None
            and self.factual_correctness.denominator != self.evidence_support.denominator
        ):
            raise ValueError("claim_denominators_must_match")
        if self.critical_errors and self.task_resolution and self.task_resolution.numerator:
            raise ValueError("critical_error_prevents_task_success")
        return self


class CaseResult(Contract):
    case_id: Identifier
    family_id: Identifier
    category_id: Identifier
    task_type: Identifier
    evaluated_at: AwareDatetime
    execution: Literal["completed", "error"]
    error_code: Identifier | None = None
    response_status: (
        Literal[
            "answered", "clarification_required", "insufficient_evidence", "temporarily_unavailable"
        ]
        | None
    ) = None
    gold_chunk_ids: tuple[Identifier, ...] = ()
    retrieved_chunk_ids: tuple[Identifier, ...] = ()
    timings_seconds: dict[Identifier, Seconds]
    warm_state: Literal["cold", "warm", "unknown"] = "unknown"
    usage: dict[Identifier, NonnegativeInt] | None = None
    response: ChatResponse | None = None
    review: HumanReview | None = None

    @model_validator(mode="after")
    def check_execution(self) -> Self:
        if (self.execution == "error") != (self.error_code is not None):
            raise ValueError("execution_error_code_mismatch")
        if self.execution == "error" and (self.response_status is not None or self.response):
            raise ValueError("error_cannot_have_response")
        if self.response_status == "temporarily_unavailable":
            raise ValueError("record_unavailability_as_execution_error")
        if self.response and self.response.status != self.response_status:
            raise ValueError("response_status_mismatch")
        if self.review:
            if self.response is None:
                raise ValueError("review_requires_saved_response")
            digest = sha256(self.response.model_dump_json().encode("utf-8")).hexdigest()
            if digest != self.review.response_sha256:
                raise ValueError("review_response_mismatch")
            if (
                self.review.citation_fidelity is not None
                and self.review.citation_fidelity.denominator != len(self.response.citations)
            ):
                raise ValueError("citation_denominator_must_count_all_emitted_citations")
        if "total" not in self.timings_seconds:
            raise ValueError("total_timing_required")
        return self


class EvaluationRun(Contract):
    schema_version: Literal["0.1"] = "0.1"
    run_id: Identifier
    purpose: Literal["software_example", "adjustment"]
    partition: Literal["adjustment"] = "adjustment"
    system: Literal["retrieval_only", "document_rag", "integrated"]
    created_at: AwareDatetime
    candidate_sha256: Sha256 | None
    candidate_provenance: Literal["recorded_at_execution", "unknown_historical_candidate"] = (
        "recorded_at_execution"
    )
    artifacts: dict[Identifier, Sha256]
    versions: dict[Identifier, Identifier]
    parameters: dict[Identifier, str | int | float | bool | None]
    k: Annotated[int, Field(strict=True, ge=1, le=10)] = 5
    environment: Identifier
    concurrency: Annotated[int, Field(strict=True, ge=1)]
    planned_cases: NonnegativeInt
    cases: tuple[CaseResult, ...]
    limitations: tuple[Identifier, ...] = ()

    @model_validator(mode="after")
    def check_cases(self) -> Self:
        if (self.candidate_sha256 is None) != (
            self.candidate_provenance == "unknown_historical_candidate"
        ):
            raise ValueError("candidate_provenance_mismatch")
        if len({case.case_id for case in self.cases}) != len(self.cases):
            raise ValueError("duplicate_case_id")
        if len(self.cases) > self.planned_cases:
            raise ValueError("more_results_than_planned_cases")
        if not self.artifacts or not self.versions:
            raise ValueError("artifact_hashes_and_versions_required")
        if "k" in self.parameters and self.parameters["k"] != self.k:
            raise ValueError("retrieval_k_mismatch")
        return self


HUMAN_METRICS = (
    "factual_correctness",
    "evidence_support",
    "citation_fidelity",
    "commercial_identity",
    "mandatory_constraints",
    "insufficiency_handling",
    "task_resolution",
)


def _latency(cases: tuple[CaseResult, ...]) -> dict[str, int | float | None]:
    values = sorted(case.timings_seconds["total"] for case in cases)
    return {
        "count": len(values),
        "median": statistics.median(values) if values else None,
        "p95": values[math.ceil(0.95 * len(values)) - 1] if values else None,
    }


def _metrics(cases: tuple[CaseResult, ...], planned: int, k: int) -> dict[str, object]:
    recalls = [
        value
        for case in cases
        if (
            value := recall_at_k(
                case.gold_chunk_ids,
                case.retrieved_chunk_ids if case.execution == "completed" else (),
                k,
            )
        )
        is not None
    ]
    reviews = [case.review for case in cases if case.review is not None]
    human: dict[str, object] = {}
    for name in HUMAN_METRICS:
        values = [getattr(review, name) for review in reviews]
        assessed = [value for value in values if isinstance(value, CountMetric)]
        metric = CountMetric(
            numerator=sum(value.numerator for value in assessed),
            denominator=sum(value.denominator for value in assessed),
        )
        human[name] = {
            **metric.model_dump(),
            "value": metric.value,
            "assessed_cases": len(assessed),
            "applicable_assessed_cases": sum(value.denominator > 0 for value in assessed),
        }
    return {
        "coverage": {
            "planned": planned,
            "attempted": len(cases),
            "completed": sum(case.execution == "completed" for case in cases),
            "errors": sum(case.execution == "error" for case in cases),
            "not_run": planned - len(cases),
            "human_reviewed": len(reviews),
        },
        "recall_at_k": {
            "k": k,
            "mean": statistics.mean(recalls) if recalls else None,
            "applicable_cases": len(recalls),
        },
        "latency": {
            "all": _latency(cases),
            **{
                state: _latency(tuple(case for case in cases if case.warm_state == state))
                for state in ("cold", "warm", "unknown")
            },
        },
        "human_metrics": human,
        "critical_errors": {
            "events": sum(len(review.critical_errors) for review in reviews),
            "cases": sum(bool(review.critical_errors) for review in reviews),
            "reviewed_cases": len(reviews),
        },
        "response_statuses": {
            status: sum(case.response_status == status for case in cases)
            for status in ("answered", "clarification_required", "insufficient_evidence")
        },
    }


def summarize(run: EvaluationRun) -> dict[str, object]:
    """Report observed denominators; never infer semantic correctness or acceptance."""
    return {
        "kind": "phase7_adjustment_summary_not_final_evaluation",
        "run_id": run.run_id,
        "purpose": run.purpose,
        "system": run.system,
        **_metrics(run.cases, run.planned_cases, run.k),
        "by_task": {
            task: _metrics(selected, len(selected), run.k)
            for task in sorted({case.task_type for case in run.cases})
            if (selected := tuple(case for case in run.cases if case.task_type == task))
        },
        "by_category": {
            category: _metrics(selected, len(selected), run.k)
            for category in sorted({case.category_id for case in run.cases})
            if (selected := tuple(case for case in run.cases if case.category_id == category))
        },
        "limitations": [
            "Adjustment/software evidence only; no final acceptance or participant usefulness.",
            "Failed applicable retrievals contribute zero; duplicate IDs do not raise recall.",
            "Human metrics cover labelled observations only; inspect review and execution coverage.",
            "Unreviewed claims, abstentions and execution errors are not successful tasks.",
            "Subgroup planned counts cover recorded cases only; missing cases have unknown groups.",
            "Latency includes failed attempts; p95 uses nearest rank, warm state is explicit.",
            "Zero reviewed critical events does not establish security or safety.",
            *run.limitations,
        ],
    }


def write_run(run: EvaluationRun, destination: Path) -> None:
    """Create a validated record without replacing previous evidence."""
    validated = EvaluationRun.model_validate_json(run.model_dump_json())
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x", encoding="utf-8") as stream:
        stream.write(validated.model_dump_json(indent=2) + "\n")


def read_run(path: Path) -> EvaluationRun:
    return EvaluationRun.model_validate_json(path.read_bytes())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    report = commands.add_parser("summarize", help="Summarize a recorded adjustment run offline")
    report.add_argument("--input", type=Path, required=True)
    report.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        run = read_run(args.input)
        result = summarize(run)
        result["run_sha256"] = sha256(args.input.read_bytes()).hexdigest()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
        print(json.dumps({"status": "passed", "run_id": run.run_id}))
        return 0
    except (OSError, ValueError) as error:
        print(json.dumps({"status": "failed", "code": type(error).__name__}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
