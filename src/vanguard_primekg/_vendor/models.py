"""Typed data structures shared by the orchestrator loop and the Finalizer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_span(value: Any) -> list[int] | None:
    if not value:
        return None
    try:
        return [int(item) for item in value]
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True)
class Question:
    """A single evaluation question loaded from the input file."""

    question_id: str
    question: str
    category: str = "multi_hop_traversal"
    answer_type: str = "boolean_with_evidence"


@dataclass
class RetrievedContext:
    """A snippet of evidence surfaced during retrieval."""

    doc_id: str
    snippet: str
    page: int | None = None
    span: list[int] | None = None
    source_ref: str | None = None
    source_type: str | None = None

    def to_json(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "doc_id": self.doc_id,
            "snippet": self.snippet,
        }
        page = _optional_int(self.page)
        span = _optional_span(self.span)
        if page is not None:
            payload["page"] = page
        if span is not None:
            payload["span"] = span
        if self.source_ref is not None:
            payload["source_ref"] = self.source_ref
        if self.source_type is not None:
            payload["source_type"] = self.source_type
        return payload


@dataclass(frozen=True)
class Citation:
    """A pointer to the exact source span that supports the answer."""

    doc_id: str
    page: int | None = None
    span: list[int] | None = None
    source_ref: str | None = None
    source_type: str | None = None

    def to_json(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"doc_id": self.doc_id}
        page = _optional_int(self.page)
        span = _optional_span(self.span)
        if page is not None:
            payload["page"] = page
        if span is not None:
            payload["span"] = span
        if self.source_ref is not None:
            payload["source_ref"] = self.source_ref
        if self.source_type is not None:
            payload["source_type"] = self.source_type
        return payload


@dataclass
class AgentAnswer:
    """The final answer produced by the LLM for one question."""

    answer: str
    confidence: float
    citations: list[Citation] = field(default_factory=list)


@dataclass
class SessionResult:
    """Everything produced by a single question's agentic session.

    Instances are short-lived: the runner yields one per question and the
    Finalizer serialises and discards it immediately, so nothing accumulates
    across a long batch.
    """

    question: Question
    answer: AgentAnswer
    steps: list[dict[str, Any]]
    retrieved_context: list[RetrievedContext]
    graph_nodes_used: list[str]
    graph_edges_used: list[str]
    answer_supported_by: list[str]
    latency_ms: int
    # The orchestrator's unmodified final message. Interactive conversations
    # preserve this separately so MiniCPM formatting is optional and auditable.
    raw_answer: str | None = None

    @property
    def trace_id(self) -> str:
        """Derive the trace id from the question id (``Q-MH-0042`` -> ``T-MH-0042``)."""
        return "T-" + self.question.question_id.removeprefix("Q-")
