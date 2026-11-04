"""Worked examples for phase-4 retrieval measurements, not final evaluation cases."""

import pytest

from ragml.rag_evaluation import recall_at_k


def test_recall_counts_unique_evidence_and_respects_k() -> None:
    assert recall_at_k(("a", "b"), ("a", "a", "noise", "b"), 3) == 0.5
    assert recall_at_k(("a", "b"), ("a", "noise", "b"), 3) == 1.0
    assert recall_at_k(("a", "b"), (), 5) == 0.0


def test_no_positive_reference_is_not_applicable() -> None:
    assert recall_at_k((), ("a",), 5) is None


def test_invalid_k_is_rejected() -> None:
    with pytest.raises(ValueError):
        recall_at_k(("a",), ("a",), 0)
