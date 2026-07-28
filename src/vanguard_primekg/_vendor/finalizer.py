"""The Finalizer: streams session results into the evaluation artifacts.

It writes two files incrementally, one question at a time, so a long batch never
holds more than a single question's data in memory. Filenames follow the Stage 1
submission convention (design Section 8), driven by the ``vendor_id``:

* ``vendor_<vendor_id>_stage1_qa-results_v1.jsonl`` — one compact JSON object per
  line (Section 8.2).
* ``vendor_<vendor_id>_stage1_reasoning-traces_v1.json`` — a pretty-printed JSON
  array (Section 8.3), emitted element-by-element with manual bracket/comma
  handling to stay streamable.

Use it as a context manager so both files are opened once and closed cleanly::

    with Finalizer(output_dir) as fin:
        for result in results:
            fin.write(result)
"""

from __future__ import annotations

import json
from pathlib import Path
from types import TracebackType
from typing import Any

from ..logging import get_logger
from ..submission import stage1_filename
from .models import SessionResult

log = get_logger("agent.finalizer")


def _omit_none(value: Any) -> Any:
    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            if item is None:
                continue
            cleaned = _omit_none(item)
            if key == "page":
                try:
                    cleaned = int(cleaned)
                except (TypeError, ValueError):
                    continue
            elif key == "span":
                try:
                    cleaned = [int(member) for member in cleaned]
                except (TypeError, ValueError):
                    continue
            normalized[key] = cleaned
        return normalized
    if isinstance(value, list):
        return [_omit_none(item) for item in value if item is not None]
    return value


def _citation_matches_context(citation: Any, context: Any) -> bool:
    if citation.source_ref:
        return citation.source_ref == context.source_ref
    return (
        citation.doc_id == context.doc_id
        and citation.page == context.page
        and citation.span == context.span
    )


def _supporting_context(result: SessionResult) -> list[dict[str, Any]]:
    """Return only context directly referenced by the final citations."""
    selected: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for citation in result.answer.citations:
        for context in result.retrieved_context:
            if not _citation_matches_context(citation, context):
                continue
            key = (
                context.doc_id,
                context.page,
                tuple(context.span) if context.span else None,
                context.source_ref,
            )
            if key not in seen:
                seen.add(key)
                selected.append(context.to_json())
            break
    return selected


def _support_graph_elements(result: SessionResult) -> tuple[list[str], list[str]]:
    cited_refs = {
        citation.source_ref
        for citation in result.answer.citations
        if citation.source_ref
    }
    edge_set = set(result.graph_edges_used)
    node_set = set(result.graph_nodes_used)
    edges = [edge for edge in result.graph_edges_used if edge in cited_refs]
    nodes: set[str] = {node for node in result.graph_nodes_used if node in cited_refs}
    for step in result.steps:
        if step.get("edge_id") not in edges:
            continue
        for key in ("from", "to", "node_id"):
            value = step.get(key)
            if value in node_set:
                nodes.add(value)
    # A cited graph node may be represented as context even when it was not an
    # edge endpoint in the recorded path.
    nodes.update(ref for ref in cited_refs if ref in node_set and ref not in edge_set)
    return (
        [node for node in result.graph_nodes_used if node in nodes],
        edges,
    )


def _support_steps(result: SessionResult) -> list[dict[str, Any]]:
    """Reduce the trace to the ordered path that supports the submitted answer."""
    nodes, edges = _support_graph_elements(result)
    node_set, edge_set = set(nodes), set(edges)
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for step in result.steps:
        operation = step.get("operation")
        if (
            operation in {"security_block", "execution_error", "select_ai_sql"}
            or step.get("edge_id") in edge_set
            or step.get("node_id") in node_set
        ):
            candidate = step
        else:
            continue
        normalized = _omit_none(candidate)
        identity = json.dumps(
            {key: value for key, value in normalized.items() if key != "step"},
            sort_keys=True,
            separators=(",", ":"),
        )
        if identity not in seen:
            seen.add(identity)
            selected.append(normalized)
    for index, step in enumerate(selected, 1):
        step["step"] = index
    return selected


def qa_record(result: SessionResult) -> dict[str, Any]:
    """Build the canonical Section 8.2 record for one completed session.

    Both streaming batch output and durable asynchronous transforms must pass
    through this function.  Keeping the submission envelope here prevents a
    formatter model (or a second hand-built serializer) from changing its
    shape or reintroducing null citation members.
    """
    answer = result.answer
    graph_nodes, graph_edges = _support_graph_elements(result)
    return _omit_none({
        "question_id": result.question.question_id,
        "category": result.question.category,
        "question": result.question.question,
        "vendor_answer": answer.answer,
        "answer_type": result.question.answer_type,
        "confidence": round(answer.confidence, 4),
        "retrieved_context": _supporting_context(result),
        "citations": [c.to_json() for c in answer.citations],
        "graph_nodes_used": graph_nodes,
        "graph_edges_used": graph_edges,
        "reasoning_trace_ref": result.trace_id,
        "latency_ms": result.latency_ms,
    })


def trace_record(result: SessionResult) -> dict[str, Any]:
    """Build the canonical Section 8.3 trace record.

    The composer emits a clean, ordered hop-by-hop trajectory (entity_lookup /
    edge_traversal / set-op steps), so we surface those steps directly rather
    than applying the LLM-path support-pruning in ``_support_steps``.
    """
    steps: list[dict[str, Any]] = []
    for index, step in enumerate(result.steps, start=1):
        normalized = _omit_none(step)
        normalized["step"] = index
        steps.append(normalized)
    return _omit_none({
        "trace_id": result.trace_id,
        "question_id": result.question.question_id,
        "steps": steps,
        "final_answer": result.answer.answer,
        "answer_supported_by": result.answer_supported_by,
    })


class Finalizer:
    """Streams :class:`SessionResult` objects to the two artifact files."""

    def __init__(self, output_dir: str | Path, *, vendor_id: str = "acme") -> None:
        self._dir = Path(output_dir)
        # RFP Section 7.1/8: artifact tokens are 'qa-results' (8.2) and
        # 'reasoning-traces' (8.3) for Stage 1 Track A (PrimeKG).
        self._results_path = self._dir / stage1_filename(vendor_id, "qa-results", "jsonl")
        self._trace_path = self._dir / stage1_filename(vendor_id, "reasoning-traces", "json")
        self._results = None
        self._trace = None
        self._first_trace = True
        self.count = 0

    def __enter__(self) -> Finalizer:
        self._dir.mkdir(parents=True, exist_ok=True)
        self._results = self._results_path.open("w", encoding="utf-8")
        self._trace = self._trace_path.open("w", encoding="utf-8")
        self._trace.write("[\n")
        return self

    def write(self, result: SessionResult) -> None:
        if self._results is None or self._trace is None:
            raise RuntimeError("Finalizer must be used as a context manager")
        record = qa_record(result)
        # JSON Lines: one compact object per line.
        self._results.write(json.dumps(record, separators=(",", ":")) + "\n")
        self._results.flush()
        # JSON array: emit elements with manual separators to avoid buffering.
        if not self._first_trace:
            self._trace.write(",\n")
        self._trace.write(json.dumps(trace_record(result), indent=2))
        self._trace.flush()
        self._first_trace = False
        self.count += 1

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self._trace is not None:
            self._trace.write("\n]\n")
            self._trace.close()
        if self._results is not None:
            self._results.close()

    @property
    def results_path(self) -> Path:
        return self._results_path

    @property
    def traces_path(self) -> Path:
        return self._trace_path
