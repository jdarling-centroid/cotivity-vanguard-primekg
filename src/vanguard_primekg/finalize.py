"""Adapter: turn a query outcome into the reused ``SessionResult`` envelope.

Produces the deterministic answer prose + ``SUPPORTED_BY`` trailer and populates
citations/graph ids so the vendored ``finalizer.qa_record``/``trace_record``
(and the existing ../ai-proposal report) grade the run unchanged. Evidence is
capped to the config validation limits.
"""

from __future__ import annotations

from ._vendor.models import AgentAnswer, Citation, Question, SessionResult
from .query_engine import QueryResult

MAX_NODES = 40
MAX_EDGES = 25
_NONE = ["NONE"]


def _question(number: int, text: str, category: str, answer_type: str) -> Question:
    return Question(
        question_id=f"Q-KG-{number:03d}",
        question=text,
        category=category,
        answer_type=answer_type,
    )


def _entity_list_prose(noun: str, names: list[str]) -> str:
    if not names:
        return f"No {noun} in PrimeKG satisfy the question."
    joined = ", ".join(names)
    return f"The {noun}: {joined}."


def answered(
    number: int,
    text: str,
    category: str,
    answer_type: str,
    result: QueryResult,
    *,
    noun: str = "entities",
    latency_ms: int = 0,
    single_entity: bool = False,
    trace_steps: list[dict] | None = None,
) -> SessionResult:
    names = [n[1] for n in result.nodes]
    if single_entity:
        prose = (
            f"{names[0]}." if names else f"No {noun} in PrimeKG satisfy the question."
        )
    else:
        prose = _entity_list_prose(noun, names)

    nodes = result.nodes[:MAX_NODES]
    edges = result.edge_ids[:MAX_EDGES]
    supported_by = edges if edges else _NONE

    citations = [
        Citation(doc_id="primekg", source_ref=e, source_type="primekg_edge") for e in edges
    ] + [Citation(doc_id="primekg", source_ref=n[0], source_type="primekg_node") for n in nodes]

    if trace_steps:
        # Real hop-by-hop trajectory (RFP 8.3). Stash the executed SQL on the
        # last step so the review markdown can still surface it.
        steps = [dict(s) for s in trace_steps]
        steps[-1]["query"] = result.sql
    else:
        steps = []
        for i, e in enumerate(edges, start=1):
            step = {"step": i, "operation": "graph_edge", "edge_id": e}
            if i == 1:
                step["query"] = result.sql
            steps.append(step)
        if not steps:
            steps = [{"step": 1, "operation": "graph_query", "query": result.sql}]

    raw = prose + "\n\nSUPPORTED_BY:\n" + "\n".join(f"- {s}" for s in supported_by)
    return SessionResult(
        question=_question(number, text, category, answer_type),
        answer=AgentAnswer(
            answer=prose,
            confidence=0.9 if result.nodes else 0.3,
            citations=citations,
        ),
        steps=steps,
        retrieved_context=[],
        graph_nodes_used=[n[0] for n in nodes],
        graph_edges_used=edges,
        answer_supported_by=supported_by,
        latency_ms=latency_ms,
        raw_answer=raw,
    )


def refused(
    number: int,
    text: str,
    category: str,
    answer_type: str,
    prose: str,
    *,
    latency_ms: int = 0,
) -> SessionResult:
    """Honest evidence-free answer (Category E out-of-graph, or empty/insufficient)."""
    raw = prose + "\n\nSUPPORTED_BY:\n- NONE"
    return SessionResult(
        question=_question(number, text, category, answer_type),
        answer=AgentAnswer(answer=prose, confidence=0.0, citations=[]),
        steps=[{"step": 1, "operation": "no_evidence", "status": "insufficient"}],
        retrieved_context=[],
        graph_nodes_used=[],
        graph_edges_used=[],
        answer_supported_by=_NONE,
        latency_ms=latency_ms,
        raw_answer=raw,
    )


_REL_LABEL = {
    ("indication", "indication"): "indications",
    ("contraindication", "contraindication"): "contraindications",
    ("off-label use", "off-label use"): "off-label uses",
    ("drug_effect", "side effect"): "side effects",
    ("drug_drug", "synergistic interaction"): "drug interactions",
    ("drug_protein", "target"): "protein targets",
    ("drug_protein", "enzyme"): "enzyme relations",
    ("drug_protein", "carrier"): "carrier relations",
    ("drug_protein", "transporter"): "transporter relations",
    ("disease_protein", "associated with"): "associated proteins",
    ("disease_phenotype_positive", "phenotype present"): "positive phenotypes",
    ("disease_disease", "parent-child"): "related diseases",
    ("protein_protein", "ppi"): "PPI partners",
    ("pathway_protein", "interacts with"): "pathway relations",
    ("phenotype_protein", "associated with"): "associated proteins",
}


def _summary_phrase(summary: list[tuple[str, str, int]]) -> str:
    parts = []
    for predicate, display, count in summary:
        label = _REL_LABEL.get((predicate, display), display or predicate)
        parts.append(f"{count} {label}")
    return ", ".join(parts)


def insufficient(
    number: int,
    text: str,
    missing: str,
    entity_name: str,
    node_id: str,
    summary: list[tuple[str, str, int]],
    edge_ids: list[str],
    *,
    latency_ms: int = 0,
) -> SessionResult:
    """Grounded refusal: the specific fact is not in PrimeKG, evidenced by the
    entity's actual (non-matching) edges. requires_evidence is still honored —
    the SUPPORTED_BY edges prove what PrimeKG *does* record for the entity.
    """
    edges = edge_ids[:MAX_EDGES]
    if summary:
        prose = (
            f"PrimeKG does not represent {missing}; it models only entity "
            f"relationships. For {entity_name} it records: {_summary_phrase(summary)}. "
            f"There is therefore insufficient evidence in PrimeKG to answer this question."
        )
        supported_by = edges if edges else _NONE
    else:
        prose = (
            f"PrimeKG does not represent {missing}, and it holds no relationships "
            f"for {entity_name} either. There is insufficient evidence to answer."
        )
        supported_by = _NONE
    citations = [Citation(doc_id="primekg", source_ref=e, source_type="primekg_edge") for e in edges]
    citations.append(Citation(doc_id="primekg", source_ref=node_id, source_type="primekg_node"))
    raw = prose + "\n\nSUPPORTED_BY:\n" + "\n".join(f"- {s}" for s in supported_by)
    return SessionResult(
        question=_question(number, text, "insufficient_data", "short_text"),
        answer=AgentAnswer(answer=prose, confidence=0.2, citations=citations),
        steps=[{"step": 1, "operation": "insufficient_data", "node_id": node_id, "missing": missing}],
        retrieved_context=[],
        graph_nodes_used=[node_id],
        graph_edges_used=edges,
        answer_supported_by=supported_by,
        latency_ms=latency_ms,
        raw_answer=raw,
    )


def describe(
    number: int,
    text: str,
    name: str,
    node_type: str,
    node_id: str,
    summary: list[tuple[str, str, int]],
    edge_ids: list[str],
    *,
    latency_ms: int = 0,
) -> SessionResult:
    """Positive summary of everything PrimeKG records about an entity."""
    edges = edge_ids[:MAX_EDGES]
    if summary:
        prose = f"In PrimeKG, {name} ({node_type}) has: {_summary_phrase(summary)}."
        supported_by = edges if edges else _NONE
    else:
        prose = f"PrimeKG contains {name} ({node_type}) but records no relationships for it."
        supported_by = _NONE
    citations = [Citation(doc_id="primekg", source_ref=e, source_type="primekg_edge") for e in edges]
    citations.append(Citation(doc_id="primekg", source_ref=node_id, source_type="primekg_node"))
    raw = prose + "\n\nSUPPORTED_BY:\n" + "\n".join(f"- {s}" for s in supported_by)
    return SessionResult(
        question=_question(number, text, "describe", "short_text"),
        answer=AgentAnswer(answer=prose, confidence=0.8 if summary else 0.2, citations=citations),
        steps=[
            {"step": 1, "operation": "entity_lookup", "node_id": node_id, "node_type": node_type},
            {"step": 2, "operation": "summarize", "detail": "aggregate the node's relationships"},
        ],
        retrieved_context=[],
        graph_nodes_used=[node_id],
        graph_edges_used=edges,
        answer_supported_by=supported_by,
        latency_ms=latency_ms,
        raw_answer=raw,
    )


def blocked(
    number: int,
    text: str,
    reason: str | None,
    *,
    latency_ms: int = 0,
) -> SessionResult:
    return SessionResult(
        question=_question(number, text, "adversarial", "firewall_block"),
        answer=AgentAnswer(answer="Won't do that", confidence=0.0, citations=[]),
        steps=[
            {"step": 1, "operation": "security_block", "status": "blocked", "reason": reason}
        ],
        retrieved_context=[],
        graph_nodes_used=[],
        graph_edges_used=[],
        answer_supported_by=[],
        latency_ms=latency_ms,
        raw_answer="Won't do that",
    )
