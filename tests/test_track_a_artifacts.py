from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from vanguard_primekg import finalize
from vanguard_primekg._vendor.finalizer import Finalizer, qa_record, trace_record
from vanguard_primekg.query_engine import QueryResult, SupportPath
from vanguard_primekg.submission import stage1_filename, validate_vendor_id


REPO = Path(__file__).resolve().parents[1]


def _supported_result() -> QueryResult:
    return QueryResult(
        nodes=[("pk_n_answer", "Answer", "gene/protein")],
        support=[
            SupportPath(
                answer_node_id="pk_n_answer",
                path_nodes=["pk_n_source", "pk_n_answer"],
                path_edges=["pk_e_support"],
                predicates=["drug_protein"],
                display_relations=["target"],
                semantics="complete expansion path",
            )
        ],
        sql="WITH x AS (SELECT 1 n FROM dual) SELECT n FROM x",
        binds={"b0": "pk_n_source"},
    )


def test_evidence_complete_record_and_trace() -> None:
    result = finalize.answered(
        1,
        "Which proteins does the drug N-(2-Aminoethyl)-5-Chloroisoquinoline-8-Sulfonamide target?",
        "expand",
        "entity_list",
        _supported_result(),
        noun="target proteins",
    )
    qa = qa_record(result)
    trace = trace_record(result)
    assert {item["source_ref"] for item in qa["citations"]} == {
        "pk_n_source", "pk_n_answer", "pk_e_support"
    }
    assert {item["source_ref"] for item in qa["retrieved_context"]} == {
        "pk_n_source", "pk_n_answer", "pk_e_support"
    }
    support = next(step for step in trace["steps"] if step["operation"] == "support_path")
    assert support["answer_node_id"] == "pk_n_answer"
    assert support["path_edges"] == ["pk_e_support"]
    assert next(step for step in trace["steps"] if step["operation"] == "context_check")[
        "clinical_context_available"
    ] is False


def test_vendor_id_and_version_are_not_hardcoded() -> None:
    assert validate_vendor_id("Example_42") == "example_42"
    assert stage1_filename("example_42", "qa-results", "jsonl", version=3) == (
        "vendor_example_42_stage1_qa-results_v3.jsonl"
    )
    with pytest.raises(ValueError):
        validate_vendor_id("x")


def test_finalizer_refuses_to_overwrite(tmp_path: Path) -> None:
    result = finalize.answered(1, "Question", "expand", "entity_list", _supported_result())
    with Finalizer(tmp_path, vendor_id="example", version=1) as fin:
        fin.write(result)
    with pytest.raises(FileExistsError):
        with Finalizer(tmp_path, vendor_id="example", version=1):
            pass


def test_validator_accepts_partial_evidence_complete_fixture(tmp_path: Path) -> None:
    question = (
        "Which proteins does the drug N-(2-Aminoethyl)-5-Chloroisoquinoline-8-Sulfonamide target?"
    )
    result = finalize.answered(1, question, "expand", "entity_list", _supported_result())
    with Finalizer(tmp_path, vendor_id="example", version=1) as fin:
        fin.write(result)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO / "src")
    completed = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts" / "validate-track-a.py"),
            str(tmp_path),
            "--allow-partial",
        ],
        cwd=REPO,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    report = json.loads((tmp_path / "validation-report.json").read_text())
    assert report["result"] == "pass"
    assert report["database_provenance_checked"] is False
