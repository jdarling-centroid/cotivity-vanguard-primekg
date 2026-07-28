"""Finalize adapter: SUPPORTED_BY grammar + vendored envelope shape."""

from __future__ import annotations

from vanguard_primekg import finalize
from vanguard_primekg._vendor.finalizer import qa_record, trace_record
from vanguard_primekg.query_engine import QueryResult


def _result() -> QueryResult:
    return QueryResult(
        nodes=[("pk_n_2172", "CSNK1G2", "gene/protein")],
        edge_ids=["pk_e_19484_2172_baf3d098"],
        sql="WITH ... SELECT ...",
    )


def test_answered_supported_by_lists_real_edges() -> None:
    sr = finalize.answered(1, "Which proteins does drug X target?", "expand",
                           "entity_list", _result(), noun="target proteins")
    assert sr.answer_supported_by == ["pk_e_19484_2172_baf3d098"]
    assert sr.raw_answer.endswith("SUPPORTED_BY:\n- pk_e_19484_2172_baf3d098")
    assert "CSNK1G2" in sr.answer.answer
    assert sr.graph_edges_used == ["pk_e_19484_2172_baf3d098"]


def test_refused_uses_none_trailer() -> None:
    sr = finalize.refused(67, "What is the recommended dosage of X?", "out_of_graph",
                          "short_text", "Not in PrimeKG.")
    assert sr.answer_supported_by == ["NONE"]
    assert sr.raw_answer.endswith("SUPPORTED_BY:\n- NONE")
    assert sr.graph_edges_used == []


def test_blocked_envelope() -> None:
    sr = finalize.blocked(96, "... DETACH DELETE ...", "instruction_override")
    assert sr.answer.answer == "Won't do that"
    assert sr.steps[0]["operation"] == "security_block"


def test_vendored_records_grade_cleanly() -> None:
    sr = finalize.answered(1, "Which proteins does drug X target?", "expand",
                           "entity_list", _result(), noun="target proteins")
    qa = qa_record(sr)
    tr = trace_record(sr)
    assert qa["graph_edges_used"] == ["pk_e_19484_2172_baf3d098"]
    assert "pk_e_19484_2172_baf3d098" in tr["answer_supported_by"]
    assert qa["question_id"] == "Q-KG-001"
