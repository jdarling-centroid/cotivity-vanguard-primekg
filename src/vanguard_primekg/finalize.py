"""Deterministic Track A answer and trace finalization.

Every submitted claim is derived from database-returned rows.  The model never
writes answer prose, citations, IDs, or reasoning traces.
"""

from __future__ import annotations

from typing import Any, Iterable

from ._vendor.models import (
    AgentAnswer,
    Citation,
    Question,
    RetrievedContext,
    SessionResult,
)
from .query_engine import QueryResult, SupportPath

_NONE = ["NONE"]
_CONTEXT_REASON = (
    "PrimeKG is a graph-native biomedical source and does not encode patient-level "
    "negation, temporality, uncertainty, or experiencer for this fact."
)


def _question(number: int, text: str, category: str, answer_type: str) -> Question:
    return Question(
        question_id=f"Q-KG-{number:03d}",
        question=text,
        category=category,
        answer_type=answer_type,
    )


def _unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    return [value for value in values if value and not (value in seen or seen.add(value))]


def _safe_binds(values: dict[str, object]) -> dict[str, object]:
    safe: dict[str, object] = {}
    for key, value in values.items():
        lower = key.lower()
        if any(marker in lower for marker in ("password", "secret", "token", "key", "credential")):
            safe[key] = "[REDACTED]"
        elif isinstance(value, (str, int, float, bool)) or value is None:
            safe[key] = value
        else:
            safe[key] = str(value)
    return safe


def _entity_list_prose(noun: str, names: list[str], *, truncated: bool) -> str:
    if not names:
        return f"No {noun} in PrimeKG satisfy the question."
    prefix = "The fully supported " if truncated else "The "
    prose = f"{prefix}{noun}: {', '.join(names)}."
    if truncated:
        prose += " The result was truncated; only answer nodes with complete returned support paths are listed."
    return prose


def _evidence(
    result: QueryResult,
    node_metadata: dict[str, tuple[str, str]] | None = None,
) -> tuple[list[str], list[str], list[Citation], list[RetrievedContext], list[SupportPath]]:
    paths = list(result.support)
    answer_ids = {node[0] for node in result.nodes}
    paths = [path for path in paths if path.answer_node_id in answer_ids]
    node_meta = dict(node_metadata or {})
    node_meta.update({node_id: (name, node_type) for node_id, name, node_type in result.nodes})
    # Resolved input entities remain legitimate query provenance even when the
    # authoritative composition returns an empty answer set.  Include them in
    # the QA evidence envelope; the trace's recorded SQL establishes the empty
    # set while these source_refs ground the entities actually queried.
    node_ids = _unique(list((node_metadata or {}).keys()) + [
        node for path in paths for node in path.path_nodes
    ])
    edge_ids = _unique(edge for path in paths for edge in path.path_edges)

    citations: list[Citation] = []
    contexts: list[RetrievedContext] = []
    for node_id in node_ids:
        name, node_type = node_meta.get(node_id, (node_id, "PrimeKG node"))
        citations.append(Citation(doc_id="primekg", source_ref=node_id, source_type="primekg_node"))
        contexts.append(
            RetrievedContext(
                doc_id="primekg",
                source_ref=node_id,
                source_type="primekg_node",
                snippet=f"PrimeKG node {node_id}: {name} ({node_type}).",
            )
        )

    edge_context: dict[str, str] = {}
    for path in paths:
        for index, edge_id in enumerate(path.path_edges):
            source = path.path_nodes[index] if index < len(path.path_nodes) else "unknown"
            target = path.path_nodes[index + 1] if index + 1 < len(path.path_nodes) else "unknown"
            predicate = path.predicates[index] if index < len(path.predicates) else "unknown"
            display = (
                path.display_relations[index]
                if index < len(path.display_relations)
                else "unknown"
            )
            edge_context.setdefault(
                edge_id,
                f"PrimeKG edge {edge_id}: {source} -[{predicate} / {display}]-> {target}.",
            )
    for edge_id in edge_ids:
        citations.append(Citation(doc_id="primekg", source_ref=edge_id, source_type="primekg_edge"))
        contexts.append(
            RetrievedContext(
                doc_id="primekg",
                source_ref=edge_id,
                source_type="primekg_edge",
                snippet=edge_context.get(edge_id, f"PrimeKG edge {edge_id} returned by the authoritative query."),
            )
        )
    return node_ids, edge_ids, citations, contexts, paths


def _answered_steps(
    category: str,
    result: QueryResult,
    paths: list[SupportPath],
    *,
    planner_audit: dict[str, Any] | None,
    resolved_entities: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    audit = planner_audit or {}
    steps: list[dict[str, Any]] = [
        {"operation": "firewall_check", "status": "allowed", "executed_before_planner": True},
        {
            "operation": "planner_selection",
            "planner": audit.get("planner", "regex"),
            "provider": audit.get("provider", "deterministic"),
            "model_id": audit.get("model_id", "regex-baseline"),
            "prompt_version": audit.get("prompt_version", "classify.py"),
            "validated_operation": category,
            "attempts": audit.get("attempts", 1),
            "deterministic_fallback_used": audit.get(
                "deterministic_fallback_used", False
            ),
        },
    ]
    for entity in resolved_entities or []:
        steps.append(
            {
                "operation": "entity_lookup",
                "input": entity.get("input"),
                "node_id": entity.get("node_id"),
                "node_type": entity.get("node_type"),
                "resolution_method": entity.get("method"),
                "resolution_score": entity.get("score"),
                "evidence": {"source_ref": entity.get("node_id")},
            }
        )
    steps.append(
        {
            "operation": "database_composition",
            "composition": category,
            "authoritative_query_count": 1,
            "read_only": True,
            "query": result.sql,
            "binds": _safe_binds(result.binds),
            "answer_node_count": len(result.nodes),
            "truncated": result.truncated,
            "error": result.error,
        }
    )
    for path_index, path in enumerate(paths, 1):
        steps.append(
            {
                "operation": "support_path",
                "path": path_index,
                "answer_node_id": path.answer_node_id,
                "path_nodes": path.path_nodes,
                "path_edges": path.path_edges,
                "predicates": path.predicates,
                "display_relations": path.display_relations,
                "semantics": path.semantics,
            }
        )
    steps.extend(
        [
            {
                "operation": "context_check",
                "source": "PrimeKG",
                "clinical_context_available": False,
                "reason": _CONTEXT_REASON,
            },
            {
                "operation": "deterministic_finalization",
                "answer_source": "validated database rows only",
                "model_authored_claims": False,
            },
        ]
    )
    return steps


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
    planner_audit: dict[str, Any] | None = None,
    resolved_entities: list[dict[str, Any]] | None = None,
) -> SessionResult:
    del trace_steps  # old sampled trace path is intentionally retired
    resolved_meta = {
        str(entity.get("node_id")): (str(entity.get("name") or entity.get("node_id")), str(entity.get("node_type") or "PrimeKG node"))
        for entity in (resolved_entities or [])
        if entity.get("node_id")
    }
    node_ids, edge_ids, citations, contexts, paths = _evidence(result, resolved_meta)
    supported_answer_ids = {path.answer_node_id for path in paths}
    nodes = [node for node in result.nodes if node[0] in supported_answer_ids]
    names = [node[1] for node in nodes]
    if single_entity:
        prose = names[0] + "." if names else f"No {noun} in PrimeKG satisfy the question."
        if result.truncated and names:
            prose += " Additional results were omitted because the output limit was reached."
    else:
        prose = _entity_list_prose(noun, names, truncated=result.truncated)
    supported_by = _unique(edge_ids) if edge_ids else (_unique(node_ids) if node_ids else _NONE)
    raw = prose + "\n\nSUPPORTED_BY:\n" + "\n".join(f"- {item}" for item in supported_by)
    confidence = 1.0 if nodes and not result.error else 0.5 if not result.error else 0.0
    return SessionResult(
        question=_question(number, text, category, answer_type),
        answer=AgentAnswer(answer=prose, confidence=confidence, citations=citations),
        steps=_answered_steps(
            category,
            result,
            paths,
            planner_audit=planner_audit,
            resolved_entities=resolved_entities,
        ),
        retrieved_context=contexts,
        graph_nodes_used=node_ids,
        graph_edges_used=edge_ids,
        answer_supported_by=supported_by,
        latency_ms=latency_ms,
        raw_answer=raw,
        truncated=result.truncated,
        confidence_basis=(
            "deterministic_execution_with_complete_returned_support"
            if nodes
            else "deterministic_empty_or_failed_execution"
        ),
        audit={"planner": planner_audit or {}, "sql_binds": _safe_binds(result.binds)},
    )


def refused(
    number: int,
    text: str,
    category: str,
    answer_type: str,
    prose: str,
    *,
    latency_ms: int = 0,
    planner_audit: dict[str, Any] | None = None,
) -> SessionResult:
    raw = prose + "\n\nSUPPORTED_BY:\n- NONE"
    return SessionResult(
        question=_question(number, text, category, answer_type),
        answer=AgentAnswer(answer=prose, confidence=0.0, citations=[]),
        steps=[
            {"operation": "firewall_check", "status": "allowed", "executed_before_planner": True},
            {
                "operation": "planner_selection",
                "planner": (planner_audit or {}).get("planner", "regex"),
                "validated_operation": category,
            },
            {"operation": "no_evidence", "status": "insufficient"},
            {
                "operation": "context_check",
                "source": "PrimeKG",
                "clinical_context_available": False,
                "reason": _CONTEXT_REASON,
            },
            {"operation": "deterministic_finalization", "answer_source": "disposition only"},
        ],
        retrieved_context=[],
        graph_nodes_used=[],
        graph_edges_used=[],
        answer_supported_by=_NONE,
        latency_ms=latency_ms,
        raw_answer=raw,
        confidence_basis="deterministic_out_of_graph_or_unresolved_disposition",
        audit={"planner": planner_audit or {}},
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
    return ", ".join(
        f"{count} {_REL_LABEL.get((predicate, display), display or predicate)}"
        for predicate, display, count in summary
    )


def _grounded_context(
    node_id: str,
    entity_name: str,
    node_type: str,
    edge_records: list[dict[str, str]],
) -> tuple[list[Citation], list[RetrievedContext], list[str], list[str]]:
    citations = [Citation(doc_id="primekg", source_ref=node_id, source_type="primekg_node")]
    contexts = [
        RetrievedContext(
            doc_id="primekg",
            source_ref=node_id,
            source_type="primekg_node",
            snippet=f"PrimeKG node {node_id}: {entity_name} ({node_type}).",
        )
    ]
    edge_ids: list[str] = []
    node_ids = [node_id]
    for edge in edge_records:
        edge_id = edge["edge_id"]
        edge_ids.append(edge_id)
        node_ids.append(edge["target_node_id"])
        citations.append(Citation(doc_id="primekg", source_ref=edge_id, source_type="primekg_edge"))
        contexts.append(
            RetrievedContext(
                doc_id="primekg",
                source_ref=edge_id,
                source_type="primekg_edge",
                snippet=(
                    f"PrimeKG edge {edge_id}: {edge['source_node_id']} "
                    f"-[{edge['predicate']} / {edge['display_relation']}]-> {edge['target_node_id']}."
                ),
            )
        )
        target_id = edge["target_node_id"]
        if not any(c.source_ref == target_id for c in citations):
            target_name = edge.get("target_name") or target_id
            target_type = edge.get("target_node_type") or "PrimeKG node"
            citations.append(Citation(doc_id="primekg", source_ref=target_id, source_type="primekg_node"))
            contexts.append(
                RetrievedContext(
                    doc_id="primekg",
                    source_ref=target_id,
                    source_type="primekg_node",
                    snippet=f"PrimeKG node {target_id}: {target_name} ({target_type}).",
                )
            )
    return citations, contexts, _unique(node_ids), _unique(edge_ids)


def insufficient(
    number: int,
    text: str,
    missing: str,
    entity_name: str,
    node_id: str,
    node_type: str,
    summary: list[tuple[str, str, int]],
    edge_records: list[dict[str, str]],
    *,
    latency_ms: int = 0,
    planner_audit: dict[str, Any] | None = None,
    resolution: dict[str, Any] | None = None,
    query: str | None = None,
    binds: dict[str, object] | None = None,
) -> SessionResult:
    if summary:
        prose = (
            f"PrimeKG does not represent {missing}; it models entity relationships. "
            f"For {entity_name} it records: {_summary_phrase(summary)}. There is therefore "
            "insufficient evidence in PrimeKG to answer the requested attribute."
        )
    else:
        prose = f"PrimeKG does not represent {missing}, and no adjacent relationships were returned for {entity_name}."
    citations, contexts, node_ids, edge_ids = _grounded_context(
        node_id, entity_name, node_type, edge_records
    )
    supported_by = _unique(edge_ids + [node_id]) if (edge_ids or node_id) else _NONE
    raw = prose + "\n\nSUPPORTED_BY:\n" + "\n".join(f"- {item}" for item in supported_by)
    steps = [
        {"operation": "firewall_check", "status": "allowed", "executed_before_planner": True},
        {"operation": "planner_selection", "planner": (planner_audit or {}).get("planner", "regex"), "validated_operation": "insufficient_data"},
        {"operation": "entity_lookup", **(resolution or {"node_id": node_id, "node_type": node_type})},
        {"operation": "database_composition", "composition": "adjacent_evidence", "authoritative_query_count": 1, "read_only": True, "query": query, "binds": _safe_binds(binds or {})},
        {"operation": "insufficient_data", "node_id": node_id, "missing": missing},
        {"operation": "context_check", "source": "PrimeKG", "clinical_context_available": False, "reason": _CONTEXT_REASON},
        {"operation": "deterministic_finalization", "answer_source": "validated database rows only"},
    ]
    return SessionResult(
        question=_question(number, text, "insufficient_data", "short_text"),
        answer=AgentAnswer(answer=prose, confidence=1.0, citations=citations),
        steps=steps,
        retrieved_context=contexts,
        graph_nodes_used=node_ids,
        graph_edges_used=edge_ids,
        answer_supported_by=supported_by,
        latency_ms=latency_ms,
        raw_answer=raw,
        confidence_basis="deterministic_grounded_attribute_absence",
        audit={"planner": planner_audit or {}},
    )


def describe(
    number: int,
    text: str,
    name: str,
    node_type: str,
    node_id: str,
    summary: list[tuple[str, str, int]],
    edge_records: list[dict[str, str]],
    *,
    latency_ms: int = 0,
    planner_audit: dict[str, Any] | None = None,
    resolution: dict[str, Any] | None = None,
    query: str | None = None,
    binds: dict[str, object] | None = None,
) -> SessionResult:
    prose = (
        f"In PrimeKG, {name} ({node_type}) has: {_summary_phrase(summary)}."
        if summary
        else f"PrimeKG contains {name} ({node_type}) but returned no adjacent relationships."
    )
    citations, contexts, node_ids, edge_ids = _grounded_context(
        node_id, name, node_type, edge_records
    )
    supported_by = _unique(edge_ids + [node_id]) if node_id else _NONE
    raw = prose + "\n\nSUPPORTED_BY:\n" + "\n".join(f"- {item}" for item in supported_by)
    return SessionResult(
        question=_question(number, text, "describe", "short_text"),
        answer=AgentAnswer(answer=prose, confidence=1.0, citations=citations),
        steps=[
            {"operation": "firewall_check", "status": "allowed", "executed_before_planner": True},
            {"operation": "planner_selection", "planner": (planner_audit or {}).get("planner", "regex"), "validated_operation": "describe"},
            {"operation": "entity_lookup", **(resolution or {"node_id": node_id, "node_type": node_type})},
            {"operation": "database_composition", "composition": "adjacent_evidence", "authoritative_query_count": 1, "read_only": True, "query": query, "binds": _safe_binds(binds or {})},
            {"operation": "context_check", "source": "PrimeKG", "clinical_context_available": False, "reason": _CONTEXT_REASON},
            {"operation": "deterministic_finalization", "answer_source": "validated database rows only"},
        ],
        retrieved_context=contexts,
        graph_nodes_used=node_ids,
        graph_edges_used=edge_ids,
        answer_supported_by=supported_by,
        latency_ms=latency_ms,
        raw_answer=raw,
        confidence_basis="deterministic_grounded_summary",
        audit={"planner": planner_audit or {}},
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
        answer=AgentAnswer(answer="Won't do that", confidence=1.0, citations=[]),
        steps=[
            {
                "operation": "security_block",
                "stage": "firewall_check",
                "status": "blocked",
                "reason": reason,
                "executed_before_planner": True,
                "planner_executed": False,
                "database_executed": False,
            },
            {"operation": "deterministic_finalization", "answer_source": "firewall disposition"},
        ],
        retrieved_context=[],
        graph_nodes_used=[],
        graph_edges_used=[],
        answer_supported_by=[],
        latency_ms=latency_ms,
        raw_answer="Won't do that",
        confidence_basis="deterministic_firewall_disposition",
    )
