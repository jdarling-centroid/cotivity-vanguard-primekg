from __future__ import annotations

import importlib.util
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "generate-review-markdown.py"


def _module():
    spec = importlib.util.spec_from_file_location("generate_review_markdown", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_render_review_contains_answer_query_binds_and_path() -> None:
    module = _module()
    qa = {
        "question_id": "Q-KG-001",
        "question": "Which proteins does drug X target?",
        "category": "expand",
        "answer_type": "entity_list",
        "vendor_answer": "The protein: P.",
        "confidence": 1.0,
        "confidence_basis": "database evidence",
        "latency_ms": 123,
        "truncated": False,
        "reasoning_trace_ref": "T-KG-001",
        "graph_nodes_used": ["n1", "n2"],
        "graph_edges_used": ["e1"],
        "citations": [{"source_ref": "e1"}],
        "retrieved_context": [{"snippet": "n1 targets n2"}],
    }
    trace = {
        "question_id": "Q-KG-001",
        "answer_supported_by": ["e1"],
        "steps": [
            {
                "operation": "database_composition",
                "composition": "expand",
                "read_only": True,
                "authoritative_query_count": 1,
                "answer_node_count": 1,
                "truncated": False,
                "query": "WITH x AS (SELECT 1 FROM dual) SELECT * FROM x",
                "binds": {"b0": "n1"},
            },
            {
                "operation": "support_path",
                "answer_node_id": "n2",
                "path_nodes": ["n1", "n2"],
                "path_edges": ["e1"],
                "predicates": ["drug_protein"],
                "display_relations": ["target"],
                "semantics": "complete expansion path",
            },
        ],
    }

    rendered = module.render_review(qa, trace)
    assert "The protein: P." in rendered
    assert "## Reasoning and evidence path" in rendered
    assert "WITH x AS" in rendered
    assert '"b0": "n1"' in rendered
    assert "`n1` → `n2`" in rendered
    assert "`drug_protein / target`" in rendered
