"""Local MCP tool wrappers plus the session trajectory recorder.

The :class:`Toolbox` binds the three retrieval tools the agent is allowed to
use (``hybrid_search``, ``traverse_graph``, ``get_fragment``) to plain Python
callables and records every invocation into a :class:`Recorder`. By default it
binds to the real MCP tool functions in
:mod:`vanguard.api.mcp_server`, calling them directly to bypass the
network. A stub toolbox with in-memory fixtures is available for offline
dry-runs (see :func:`make_stub_toolbox`).

Each recorded step matches the ``reasoning-traces.json`` step shape
(Section 8.3): ``hybrid_search`` maps to ``entity_lookup``, ``traverse_graph``
to ``edge_traversal``, and ``get_fragment`` to ``context_check``.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from copy import deepcopy
from typing import Any

from ..config import load_config
from .models import RetrievedContext

# A tool is any callable returning a JSON-serialisable dict.
ToolFn = Callable[..., dict[str, Any]]

# Agent retrieval is intentionally narrower than the public MCP APIs. A model
# can ask for more, but feeding hundreds of adjacent graph facts into a single
# answer makes synthesis slower and submission evidence less precise.
AGENT_SEARCH_LIMIT = 8
AGENT_SEARCH_CANDIDATE_LIMIT = 32
AGENT_TRAVERSAL_LIMIT = 10
AGENT_TRAVERSAL_DEPTH = 2


class Recorder:
    """Collects the trajectory of one question's agentic session.

    Node and edge ids are de-duplicated while preserving first-seen order so the
    reconciled ``graph_nodes_used`` / ``graph_edges_used`` arrays are stable.
    """

    def __init__(self) -> None:
        self.steps: list[dict[str, Any]] = []
        self.retrieved_context: list[RetrievedContext] = []
        self._step_no = 0
        self._nodes: list[str] = []
        self._node_seen: set[str] = set()
        self._edges: list[str] = []
        self._edge_seen: set[str] = set()

    def next_step(self) -> int:
        self._step_no += 1
        return self._step_no

    def use_node(self, node_id: str | None) -> None:
        if node_id and node_id not in self._node_seen:
            self._node_seen.add(node_id)
            self._nodes.append(node_id)

    def use_edge(self, edge_id: str | None) -> None:
        if edge_id and edge_id not in self._edge_seen:
            self._edge_seen.add(edge_id)
            self._edges.append(edge_id)

    def add_context(self, context: RetrievedContext) -> None:
        self.retrieved_context.append(context)

    def add_step(self, step: dict[str, Any]) -> None:
        self.steps.append(step)

    @property
    def nodes_used(self) -> list[str]:
        return list(self._nodes)

    @property
    def edges_used(self) -> list[str]:
        return list(self._edges)


def _provenance(obj: dict[str, Any]) -> dict[str, Any]:
    """Best-effort extraction of ``doc_id`` / ``page`` / ``span`` from a payload.

    Real ``Node``/``Fragment`` dumps may not expose provenance, so callers must
    tolerate ``None`` page/span. Stub fixtures embed a ``provenance`` block that
    is picked up here.
    """
    prov = obj.get("provenance")
    if isinstance(prov, dict):
        return prov
    return {}


def _first_snippet(strings: list[Any] | None) -> str | None:
    if strings:
        for value in strings:
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


def _source_type(doc_id: str | None, source_ref: str | None, *, edge: bool = False) -> str | None:
    """Classify provenance without treating a graph namespace as a document."""
    if not source_ref:
        return None
    if edge:
        return "primekg_edge" if doc_id == "primekg" else "graph_edge"
    if doc_id == "primekg":
        return "primekg_node"
    return "document_passage" if source_ref else None


class Toolbox:
    """Records every tool call and exposes them to the agent by name."""

    def __init__(
        self,
        recorder: Recorder,
        *,
        hybrid_search: ToolFn,
        traverse_graph: ToolFn,
        get_fragment: ToolFn,
    ) -> None:
        self._recorder = recorder
        retrieval = load_config().retrieval
        self._search_limit = retrieval.agent_search_limit
        self._search_candidate_limit = retrieval.agent_search_candidate_limit
        self._traversal_limit = retrieval.agent_traversal_limit
        self._traversal_depth = retrieval.agent_traversal_depth
        self._fns: dict[str, ToolFn] = {
            "hybrid_search": hybrid_search,
            "traverse_graph": traverse_graph,
            "get_fragment": get_fragment,
        }

    @property
    def names(self) -> list[str]:
        return list(self._fns)

    def invoke(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name == "hybrid_search":
            return self._hybrid_search(arguments)
        if name == "traverse_graph":
            return self._traverse_graph(arguments)
        if name == "get_fragment":
            return self._get_fragment(arguments)
        raise ValueError(f"unknown tool: {name}")

    def _hybrid_search(self, arguments: dict[str, Any]) -> dict[str, Any]:
        arguments = dict(arguments)
        output_limit = min(
            max(int(arguments.get("limit") or self._search_limit), 1),
            self._search_limit,
        )
        # Retrieve a bounded semantic/lexical RRF pool, then return the leading
        # candidates for model selection. Do not impose application-level exact
        # or word-overlap selection here: labels, types, scores, and provenance
        # are supplied to the model so it can resolve the entity in context.
        arguments["limit"] = self._search_candidate_limit
        result = self._fns["hybrid_search"](**arguments)
        query = arguments.get("query")
        hits = result.get("results", []) if isinstance(result, dict) else []
        if isinstance(hits, list):
            hits = hits[:output_limit]
            result = {**result, "results": hits}
        for hit in hits:
            node = hit.get("node", {}) if isinstance(hit, dict) else {}
            node_id = node.get("node_id")
            self._recorder.use_node(node_id)
            prov = _provenance(node)
            doc_id = (
                prov.get("doc_id")
                or node.get("reference_source_id")
                or node_id
                or "unknown"
            )
            snippet = _first_snippet(hit.get("highlights")) or (node.get("label") or "")
            if prov or snippet:
                self._recorder.add_context(
                    RetrievedContext(
                        doc_id=doc_id,
                        snippet=snippet,
                        page=prov.get("page"),
                        span=prov.get("span"),
                        source_ref=node_id,
                        source_type=_source_type(doc_id, node_id),
                    )
                )
        top = hits[0].get("node", {}) if hits else {}
        top_prov = _provenance(top)
        self._recorder.add_step(
            {
                "step": self._recorder.next_step(),
                "operation": "entity_lookup",
                "input": query,
                "node_id": top.get("node_id"),
                "node_type": top.get("node_type"),
                "evidence": {
                    "doc_id": (
                        top_prov.get("doc_id")
                        or top.get("reference_source_id")
                        or top.get("node_id")
                    ),
                    "page": top_prov.get("page"),
                    "span": top_prov.get("span"),
                    "source_ref": top.get("node_id"),
                },
            }
        )
        return result

    def _traverse_graph(self, arguments: dict[str, Any]) -> dict[str, Any]:
        arguments = dict(arguments)
        requested_starts = [
            str(node_id)
            for node_id in (arguments.get("start_node_ids") or [])
            if node_id
        ]
        known_nodes = set(self._recorder.nodes_used)
        unknown_starts = [
            node_id for node_id in requested_starts if node_id not in known_nodes
        ]
        if unknown_starts:
            return {
                "error": "start_node_ids must be copied from prior tool results",
                "unknown_start_node_ids": unknown_starts,
                "allowed_start_node_ids": list(self._recorder.nodes_used),
            }
        arguments["limit"] = min(
            max(int(arguments.get("limit") or self._traversal_limit), 1),
            self._traversal_limit,
        )
        arguments["maximum_depth"] = min(
            max(int(arguments.get("maximum_depth") or 1), 1),
            self._traversal_depth,
        )
        result = self._fns["traverse_graph"](**arguments)
        nodes = result.get("nodes", []) if isinstance(result, dict) else []
        edges = result.get("edges", []) if isinstance(result, dict) else []
        node_labels = {
            node.get("node_id"): node.get("label") or node.get("node_id")
            for node in nodes
            if isinstance(node, dict) and node.get("node_id")
        }
        for node in nodes:
            self._recorder.use_node(node.get("node_id"))
        for edge in edges:
            edge_id = edge.get("edge_id")
            self._recorder.use_node(edge.get("source_node_id"))
            self._recorder.use_node(edge.get("target_node_id"))
            self._recorder.use_edge(edge_id)
            self._recorder.add_context(
                RetrievedContext(
                    doc_id="primekg" if edge_id and str(edge_id).startswith("pk_") else "graph",
                    snippet=(
                        f"{node_labels.get(edge.get('source_node_id'), edge.get('source_node_id'))} "
                        f"({edge.get('source_node_id')}) "
                        f"{edge.get('display_relation') or edge.get('relationship')} "
                        f"{node_labels.get(edge.get('target_node_id'), edge.get('target_node_id'))} "
                        f"({edge.get('target_node_id')})"
                    ),
                    source_ref=edge_id,
                    source_type=_source_type(
                        "primekg" if edge_id and str(edge_id).startswith("pk_") else "graph",
                        edge_id,
                        edge=True,
                    ),
                )
            )
            self._recorder.add_step(
                {
                    "step": self._recorder.next_step(),
                    "operation": "edge_traversal",
                    "edge_id": edge_id,
                    "predicate": edge.get("predicate") or edge.get("relationship"),
                    "relationship": edge.get("relationship"),
                    "display_relation": edge.get("display_relation"),
                    "from": edge.get("source_node_id"),
                    "to": edge.get("target_node_id"),
                }
            )
        return result

    def _get_fragment(self, arguments: dict[str, Any]) -> dict[str, Any]:
        result = self._fns["get_fragment"](**arguments)
        node_id = result.get("node_id") if isinstance(result, dict) else None
        text = result.get("text", "") if isinstance(result, dict) else ""
        self._recorder.use_node(node_id)
        prov = _provenance(result if isinstance(result, dict) else {})
        if text or prov:
            self._recorder.add_context(
                RetrievedContext(
                    doc_id=prov.get("doc_id") or node_id or "unknown",
                    snippet=text,
                    page=prov.get("page"),
                    span=prov.get("span"),
                    source_ref=node_id,
                    source_type=_source_type(prov.get("doc_id"), node_id),
                )
            )
        self._recorder.add_step(
            {
                "step": self._recorder.next_step(),
                "operation": "context_check",
                "node_id": node_id,
                "evidence_text": text,
            }
        )
        return result


def make_real_toolbox(recorder: Recorder) -> Toolbox:
    """Bind the toolbox to the live MCP tool functions (requires a DB pool)."""
    from vanguard.api.mcp_server import (
        get_fragment,
        hybrid_search,
        traverse_graph,
    )

    return Toolbox(
        recorder,
        hybrid_search=hybrid_search,
        traverse_graph=traverse_graph,
        get_fragment=get_fragment,
    )


def make_stub_toolbox(recorder: Recorder) -> Toolbox:
    """An offline toolbox returning fixed evidence for dry-runs and tests.

    The fixtures mirror the shapes returned by the real tools (including an
    embedded ``provenance`` block) so the recording and serialisation logic is
    fully exercised without a database.
    """

    def hybrid_search(**kwargs: Any) -> dict[str, Any]:
        query = kwargs.get("query", "")
        return {
            "results": [
                {
                    "node": {
                        "node_id": "n_encounter_551",
                        "node_type": "encounter",
                        "label": "Admission 2023-04-11",
                        "provenance": {"doc_id": "DOC-0003", "page": 2, "span": [88, 140]},
                    },
                    "score": 0.93,
                    "matched_by": ["semantic", "lexical"],
                    "highlights": [f"Encounter matching: {query}"],
                }
            ],
            "next_cursor": None,
            "provisional_results_present": False,
        }

    def traverse_graph(**kwargs: Any) -> dict[str, Any]:
        start = (kwargs.get("start_node_ids") or ["n_encounter_551"])[0]
        return {
            "nodes": [
                {"node_id": start, "node_type": "encounter"},
                {"node_id": "n_condition_902", "node_type": "condition"},
            ],
            "edges": [
                {
                    "edge_id": "e_hasDiagnosis_77",
                    "source_node_id": start,
                    "target_node_id": "n_condition_902",
                    "relationship": "encounter_has_diagnosis",
                }
            ],
        }

    def get_fragment(**kwargs: Any) -> dict[str, Any]:
        fragment_id = kwargs.get("fragment_id", "frag_n_condition_902")
        return {
            "fragment_id": fragment_id,
            "node_id": "n_condition_902",
            "fragment_type": "text_block",
            "text": "Admitted with suspected sepsis, confirmed by blood culture.",
            "provenance": {"doc_id": "DOC-0003", "page": 5, "span": [180, 240]},
        }

    return Toolbox(
        recorder,
        hybrid_search=hybrid_search,
        traverse_graph=traverse_graph,
        get_fragment=get_fragment,
    )


# OpenAI-style function schemas advertised to the LLM.
TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "hybrid_search",
            "description": (
                "Return ranked graph nodes using semantic, lexical, structured, "
                "and graph retrieval."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "node_types": {"type": "array", "items": {"type": "string"}},
                    "source_scope": {
                        "type": "string", "enum": ["documents", "references", "all"],
                        "default": "all"
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": AGENT_SEARCH_LIMIT,
                        "default": AGENT_SEARCH_LIMIT,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "traverse_graph",
            "description": "Traverse allowed graph relationships from one or more start nodes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_node_ids": {"type": "array", "items": {"type": "string"}},
                    "relationships": {
                        "type": "array",
                        "description": (
                            "Optional platform edge classes. Source predicates such as "
                            "PrimeKG target are returned on each edge; use RELATED_TO "
                            "for PrimeKG relationships."
                        ),
                        "items": {
                            "type": "string",
                            "enum": [
                                "CONTAINS", "DERIVED_FROM", "HAS_FRAGMENT",
                                "RELATED_TO", "MENTIONS", "MAPS_TO", "SUPPORTED_BY"
                            ],
                        },
                    },
                    "predicates": {
                        "type": "array",
                        "description": (
                            "Optional exact source predicates. For PrimeKG use "
                            "drug_protein for targets and drug_effect for side effects."
                        ),
                        "items": {"type": "string"},
                    },
                    "display_relations": {
                        "type": "array",
                        "description": (
                            "Optional exact human-readable edge relations, such as "
                            "target or side effect."
                        ),
                        "items": {"type": "string"},
                    },
                    "direction": {
                        "type": "string",
                        "enum": ["outbound", "inbound", "both"],
                        "default": "both",
                    },
                    "maximum_depth": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": AGENT_TRAVERSAL_DEPTH,
                        "default": 1,
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": AGENT_TRAVERSAL_LIMIT,
                        "default": AGENT_TRAVERSAL_LIMIT,
                    },
                },
                "required": ["start_node_ids"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_fragment",
            "description": "Return bounded fragment text and its source evidence.",
            "parameters": {
                "type": "object",
                "properties": {"fragment_id": {"type": "string"}},
                "required": ["fragment_id"],
            },
        },
    },
]


def configured_tool_schemas() -> list[dict[str, Any]]:
    """Return tool schemas with limits from the active service configuration."""
    retrieval = load_config().retrieval
    schemas = deepcopy(TOOL_SCHEMAS)
    for schema in schemas:
        function = schema["function"]
        properties = function["parameters"]["properties"]
        if function["name"] == "hybrid_search":
            properties["limit"]["maximum"] = retrieval.agent_search_limit
            properties["limit"]["default"] = retrieval.agent_search_limit
        elif function["name"] == "traverse_graph":
            properties["limit"]["maximum"] = retrieval.agent_traversal_limit
            properties["limit"]["default"] = retrieval.agent_traversal_limit
            properties["maximum_depth"]["maximum"] = retrieval.agent_traversal_depth
    return schemas
