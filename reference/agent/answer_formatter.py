"""Model-backed normalization of raw agent answers into ``AgentAnswer`` values.

The orchestrator owns retrieval and synthesis. The formatter may normalize the
answer, confidence, and citations, but it does not own the Section 8 submission
envelope; the deterministic finalizer does. It may not add facts or cite
evidence the agent did not retrieve. Any formatter failure falls back to a
deterministic, valid ``AgentAnswer``.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ..logging import get_logger
from .llm import ChatModel
from .models import AgentAnswer, Citation, Question
from .tools import Recorder

log = get_logger("agent.answer_formatter")


class _CitationEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    doc_id: str | None = Field(default=None, min_length=1)
    page: int | None = None
    span: list[int] | None = None
    source_ref: str | None = None
    source_type: str | None = None


class _AnswerEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    citations: list[_CitationEnvelope] = Field(default_factory=list)


def _plain_text(value: str) -> str:
    """Remove common Markdown decoration without changing answer wording."""
    lines: list[str] = []
    for line in value.splitlines():
        stripped = line.strip()
        if re.fullmatch(r"-{3,}|_{3,}|\*{3,}", stripped):
            continue
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            if cells and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
                continue
            line = ": ".join(cells) if len(cells) == 2 else "; ".join(cells)
        line = re.sub(r"^\s{0,3}#{1,6}\s+", "", line)
        line = re.sub(r"^\s*[-*+]\s+", "• ", line)
        line = re.sub(r"\*\*([^*]+)\*\*", r"\1", line)
        line = re.sub(r"__([^_]+)__", r"\1", line)
        line = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", line)
        lines.append(line.rstrip())
    return "\n".join(lines).strip()


def _compact_entity_answer(value: str, question: Question | None) -> str:
    """Strip explanatory relative clauses from clearly singular-entity answers."""
    if question is None:
        return value
    prompt = question.question.strip().lower()
    if prompt.startswith(("which ", "what are ")):
        items = [
            re.sub(r"\s*\([^)]*\)\s*$", "", line.removeprefix("•").strip())
            for line in value.splitlines()
            if line.strip().startswith("•")
        ]
        if items:
            return ", ".join(items) + "."
    if prompt.startswith(("what is the name of", "what is the name", "name the")):
        match = re.match(r"^(the\s+[^,;]+?\s+is\s+[^,;]+?)(?:,|;)", value, re.I)
        if match:
            return match.group(1).rstrip(". ") + "."
    if prompt.startswith("which "):
        match = re.match(
            r"^(.+?)\s+is\s+(?:the|a|an)\s+[^,;]+?\s+(?:who|that|which)\b",
            value,
            re.I,
        )
        if match:
            return match.group(1).strip().rstrip(". ") + "."
    return value


def _extract_object(content: str | None) -> dict[str, Any]:
    text = (content or "").strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            return {}
        try:
            payload = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return {}
    return payload if isinstance(payload, dict) else {}


def _ranked_contexts(
    recorder: Recorder,
    raw_content: str | None = None,
    question: Question | None = None,
    *,
    limit: int | None = None,
) -> list[Any]:
    """Return unique evidence ordered by relevance to the answer being formatted."""
    raw_text = raw_content or ""
    question_text = question.question if question else ""
    query_text = " ".join(part for part in (raw_text, question_text) if part)
    raw_terms = {
        term
        for term in re.findall(r"[A-Za-z0-9_]+", raw_text.lower())
        if len(term) >= 3
    }
    question_terms = {
        term
        for term in re.findall(r"[A-Za-z0-9_]+", question_text.lower())
        if len(term) >= 3
    }
    ranked: list[tuple[int, int, Any]] = []
    seen: set[tuple[str, int | None, tuple[int, ...] | None, str | None]] = set()
    for index, context in enumerate(recorder.retrieved_context):
        try:
            page = int(context.page) if context.page is not None else None
            span = [int(value) for value in context.span] if context.span else None
        except (TypeError, ValueError):
            page, span = None, None
        key = (context.doc_id, page, tuple(span) if span else None, context.source_ref)
        if key in seen:
            continue
        seen.add(key)
        snippet_terms = {
            term
            for term in re.findall(r"[A-Za-z0-9_]+", context.snippet.lower())
            if len(term) >= 3
        }
        # Terms from the question describe the requested relation and carry
        # much more signal than generic prose repeated in the raw answer.
        score = len(raw_terms & snippet_terms) + 10 * len(
            question_terms & snippet_terms
        )
        if context.source_ref and context.source_ref.lower() in query_text.lower():
            score += 100
        ranked.append((score, -index, context))
    ranked.sort(reverse=True, key=lambda item: (item[0], item[1]))
    contexts = [item[2] for item in ranked]
    return contexts[:limit] if limit is not None else contexts


def _candidate_citations(
    recorder: Recorder,
    raw_content: str | None = None,
    question: Question | None = None,
    *,
    limit: int | None = None,
) -> list[Citation]:
    citations: list[Citation] = []
    for context in _ranked_contexts(
        recorder, raw_content, question, limit=limit
    ):
        try:
            page = int(context.page) if context.page is not None else None
            span = [int(value) for value in context.span] if context.span else None
        except (TypeError, ValueError):
            page, span = None, None
        citations.append(
            Citation(
                doc_id=context.doc_id,
                page=page,
                span=span,
                source_ref=context.source_ref,
                source_type=context.source_type,
            )
        )
    return citations


_ANSWER_STOPWORDS = {
    "answer",
    "filmmaker",
    "name",
    "platform",
    "the",
}


def _is_evidence_limited_answer(value: str) -> bool:
    """Identify an explicit no-result answer that still needs search provenance."""
    return bool(
        re.search(
            r"\b(?:insufficient evidence|no\s+\w+(?:\s+\w+){0,2}\s+(?:are|is|were)?\s*found|no\s+\w+\s+(?:are|is)|none|not found|cannot identify)\b",
            value,
            re.IGNORECASE,
        )
    )


def _multi_hop_citations(
    answer_text: str,
    declared: list[Citation],
    recorder: Recorder,
    question: Question | None,
) -> list[Citation]:
    """Retain up to two retrieved documents that explicitly name the answer.

    A multi-hop answer normally joins two passages. Ornith sometimes identifies
    the entity correctly but copies only one provenance pointer into its trailer.
    We may recover the omitted pointer only from already-retrieved evidence that
    contains the returned entity; this cannot introduce a model-memory citation.
    """
    if (
        question is None
        or question.category != "multi_hop_traversal"
        or not declared
    ):
        return declared
    answer_terms = {
        term
        for term in re.findall(r"[A-Za-z0-9_]+", answer_text.lower())
        if len(term) >= 3 and term not in _ANSWER_STOPWORDS
    }
    if not answer_terms:
        return declared

    eligible = []
    for index, context in enumerate(recorder.retrieved_context):
        snippet_terms = set(re.findall(r"[A-Za-z0-9_]+", context.snippet.lower()))
        if not (answer_terms & snippet_terms):
            continue
        eligible.append((index, context, snippet_terms))

    clauses = re.split(
        r",\s+(?:and\s+)?(?:is|are|was|were|has|have)\s+(?:also\s+)?",
        question.question,
        maxsplit=1,
        flags=re.IGNORECASE,
    )
    clause_terms = [
        Counter(
            term
            for term in re.findall(r"[A-Za-z0-9_]+", clause.lower())
            if len(term) >= 4
        )
        for clause in clauses
    ]
    terms_by_doc: dict[str, set[str]] = {}
    for _index, context, snippet_terms in eligible:
        terms_by_doc.setdefault(context.doc_id, set()).update(snippet_terms)
    document_frequency = Counter(
        term for document_terms in terms_by_doc.values() for term in document_terms
    )

    # Select one entity-bearing passage per clue. Whole-question ranking can
    # otherwise choose two articles related to the first clue and omit the join.
    selected: list[Citation] = []
    seen_docs: set[str] = set()
    for terms in clause_terms:
        ranked = sorted(
            eligible,
            key=lambda item: (
                -sum(
                    count / document_frequency[term]
                    for term, count in terms.items()
                    if term in item[2]
                ),
                item[0],
            ),
        )
        context = next(
            (item[1] for item in ranked if item[1].doc_id not in seen_docs),
            None,
        )
        if context is None:
            continue
        citation = Citation(
            doc_id=context.doc_id,
            page=context.page,
            span=context.span,
            source_ref=context.source_ref,
            source_type=context.source_type,
        )
        selected.append(citation)
        seen_docs.add(citation.doc_id)
        if len(seen_docs) >= 2:
            break
    return selected or declared[:2]


def _citation_key(
    citation: Citation,
) -> tuple[str, int | None, tuple[int, ...] | None, str | None]:
    return (
        citation.doc_id,
        citation.page,
        tuple(citation.span) if citation.span else None,
        citation.source_ref,
    )


def extract_supported_by(
    raw_content: str | None, recorder: Recorder
) -> tuple[str, list[Citation], bool]:
    """Strip and validate Orinth's final ``SUPPORTED_BY`` declaration.

    Returns answer prose, canonical citations backed by retrieved context, and
    whether the marker was present. Unknown or fabricated pointers are ignored.
    """
    text = raw_content or ""
    marker = re.search(
        r"(?im)^\s*(?:\*\*|__)?SUPPORTED_BY\s*:\s*(?:\*\*|__)?\s*(.*)$",
        text,
    )
    if marker is None:
        malformed = re.search(r"(?i)SUPPORTED_BY\s*:", text)
        if malformed is not None:
            # A malformed inline trailer is still a declaration. Strip it and
            # do not silently replace ``NONE`` with unrelated retrieved evidence.
            return text[: malformed.start()].rstrip(), [], True
        return text.strip(), [], False

    answer_text = text[: marker.start()].rstrip()
    trailer = "\n".join((marker.group(1), text[marker.end() :])).strip()
    candidates = _candidate_citations(recorder)
    by_source_ref = {
        citation.source_ref: citation
        for citation in candidates
        if citation.source_ref
    }
    selected: list[Citation] = []

    # JSON citation objects are the preferred document-pointer syntax.
    for line in trailer.splitlines():
        item = re.sub(r"^\s*[-*+]\s*", "", line).strip().rstrip(",")
        if not item or item.upper() == "NONE":
            continue
        if item.startswith("{") and item.endswith("}"):
            try:
                payload = json.loads(item)
                requested = _CitationEnvelope.model_validate(payload)
            except (json.JSONDecodeError, ValidationError):
                continue
            selected.extend(_reconcile_citations([requested], candidates))

    # Bare graph identifiers are intentionally easy for the orchestrator to
    # copy. Match against the allowlist instead of trying to define every graph
    # identifier grammar here.
    positioned = [
        (match.start(), citation)
        for source_ref, citation in by_source_ref.items()
        if (
            match := re.search(
                rf"(?<![A-Za-z0-9_]){re.escape(source_ref)}(?![A-Za-z0-9_])",
                trailer,
            )
        )
    ]
    selected.extend(citation for _position, citation in sorted(positioned))

    seen: set[tuple[str, int | None, tuple[int, ...] | None, str | None]] = set()
    canonical: list[Citation] = []
    for citation in selected:
        key = _citation_key(citation)
        if key not in seen:
            seen.add(key)
            canonical.append(citation)
    return answer_text, canonical, True


def _preferred_graph_citations(
    recorder: Recorder,
    raw_content: str | None,
    question: Question | None,
    *,
    limit: int = 10,
) -> list[Citation]:
    """Select graph edges whose endpoint ids are actually named in the answer."""
    raw_refs = set(re.findall(r"\bpk_[ne]_[A-Za-z0-9_]+\b", raw_content or ""))
    ranked = _ranked_contexts(recorder, raw_content, question)
    edge_rows: list[tuple[int, Citation]] = []
    for context in ranked:
        if not (context.source_type or "").endswith("_edge"):
            continue
        snippet_refs = set(
            re.findall(r"\bpk_[ne]_[A-Za-z0-9_]+\b", context.snippet)
        )
        edge_rows.append(
            (
                len(raw_refs & snippet_refs),
                Citation(
                    doc_id=context.doc_id,
                    page=context.page,
                    span=context.span,
                    source_ref=context.source_ref,
                    source_type=context.source_type,
                ),
            )
        )
    if not edge_rows:
        return []
    maximum_match = max(matches for matches, _citation in edge_rows)
    if maximum_match:
        return [
            citation
            for matches, citation in edge_rows
            if matches == maximum_match
        ][:limit]
    return [edge_rows[0][1]]


def _explicit_graph_citations(
    recorder: Recorder,
    answer_text: str,
    *,
    limit: int = 10,
) -> list[Citation]:
    """Recover graph edges explicitly printed in answer prose.

    A small orchestrator can finish a complete entity list but have its
    ``SUPPORTED_BY`` trailer clipped by the output-token limit. Edge ids in the
    answer itself are still unambiguous, and are accepted only when they match
    retrieved context. This keeps recovery deterministic and cannot introduce
    an unseen citation.
    """
    selected: list[Citation] = []
    for context in recorder.retrieved_context:
        source_ref = context.source_ref
        if (
            not source_ref
            or not (context.source_type or "").endswith("_edge")
            or re.search(
                rf"(?<![A-Za-z0-9_]){re.escape(source_ref)}(?![A-Za-z0-9_])",
                answer_text,
            )
            is None
        ):
            continue
        selected.append(
            Citation(
                doc_id=context.doc_id,
                page=context.page,
                span=context.span,
                source_ref=source_ref,
                source_type=context.source_type,
            )
        )
        if len(selected) >= limit:
            break
    return selected


def _evidence_catalog(
    recorder: Recorder,
    raw_content: str | None = None,
    question: Question | None = None,
    *,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Expose citation pointers together with the evidence they identify.

    The formatter previously received only opaque pointers.  That made it
    impossible to choose the supporting PrimeKG edge from a large traversal,
    because the model could not see what any ``source_ref`` represented.
    """
    catalog: list[dict[str, Any]] = []
    for context in _ranked_contexts(
        recorder, raw_content, question, limit=limit
    ):
        try:
            page = int(context.page) if context.page is not None else None
            span = [int(value) for value in context.span] if context.span else None
        except (TypeError, ValueError):
            page, span = None, None
        citation = Citation(
            doc_id=context.doc_id,
            page=page,
            span=span,
            source_ref=context.source_ref,
            source_type=context.source_type,
        )
        catalog.append(
            {
                **citation.to_json(),
                "snippet": context.snippet,
            }
        )
    return catalog


def _catalog_for_citations(
    recorder: Recorder, citations: list[Citation]
) -> list[dict[str, Any]]:
    allowed = {_citation_key(citation) for citation in citations}
    catalog: list[dict[str, Any]] = []
    for context in recorder.retrieved_context:
        try:
            page = int(context.page) if context.page is not None else None
            span = [int(value) for value in context.span] if context.span else None
        except (TypeError, ValueError):
            page, span = None, None
        citation = Citation(
            doc_id=context.doc_id,
            page=page,
            span=span,
            source_ref=context.source_ref,
            source_type=context.source_type,
        )
        if _citation_key(citation) not in allowed:
            continue
        catalog.append({**citation.to_json(), "snippet": context.snippet})
    return catalog


def _fallback(
    raw_content: str | None,
    recorder: Recorder,
    question: Question | None = None,
) -> AgentAnswer:
    """Produce a valid answer without depending on the formatter model."""
    answer_text, declared, marker_present = extract_supported_by(raw_content, recorder)
    declared_candidates = _multi_hop_citations(
        answer_text, declared, recorder, question
    )
    candidates = (
        declared_candidates
        if marker_present and declared_candidates
        else _candidate_citations(recorder, answer_text, question, limit=10)
    )
    payload = _extract_object(answer_text)
    if payload:
        try:
            envelope = _AnswerEnvelope.model_validate(payload)
        except ValidationError:
            envelope = None
        if envelope is not None:
            citations = _reconcile_citations(envelope.citations, candidates)
            if envelope.citations and not citations:
                citations = candidates[:10]
            return AgentAnswer(
                answer=_compact_entity_answer(
                    _plain_text(envelope.answer), question
                ),
                confidence=envelope.confidence,
                citations=citations,
            )
    answer = _compact_entity_answer(
        _plain_text(answer_text.strip()), question
    ) or "No answer produced."
    if marker_present:
        explicit_graph = _explicit_graph_citations(
            recorder, answer_text, limit=10
        )
        # ``SUPPORTED_BY: NONE`` is useful for preventing fabricated claims,
        # but it used to erase all provenance from a legitimate negative
        # result. Preserve the retrieved search path for an explicit
        # no-result answer; every fallback citation is still reconciled against
        # recorder context and therefore cannot invent evidence.
        if not explicit_graph and not declared_candidates and _is_evidence_limited_answer(answer):
            declared_candidates = _preferred_graph_citations(
                recorder, answer_text, question, limit=10
            ) or candidates[:10]
        return AgentAnswer(
            answer=answer,
            confidence=0.5,
            citations=(
                explicit_graph
                if len(explicit_graph) > len(declared_candidates)
                else declared_candidates
            ),
        )
    preferred = _preferred_graph_citations(
        recorder, answer_text, question, limit=10
    )
    return AgentAnswer(
        answer=answer,
        confidence=0.5,
        citations=preferred or candidates[:10],
    )


class DeterministicAnswerFormatter:
    """Normalize an orchestrator answer without a second model inference."""

    def format(
        self,
        raw_content: str | None,
        recorder: Recorder,
        *,
        question: Question | None = None,
    ) -> AgentAnswer:
        return _fallback(raw_content, recorder, question)

    def format_with_status(
        self,
        raw_content: str | None,
        recorder: Recorder,
        *,
        question: Question | None = None,
    ) -> tuple[AgentAnswer, bool, str | None]:
        return self.format(raw_content, recorder, question=question), False, None


def _reconcile_citations(
    requested: list[_CitationEnvelope], candidates: list[Citation]
) -> list[Citation]:
    """Allow only citations backed by retrieved context, using canonical spans."""
    by_doc: dict[str, list[Citation]] = {}
    by_source_ref: dict[str, Citation] = {}
    for candidate in candidates:
        by_doc.setdefault(candidate.doc_id, []).append(candidate)
        if candidate.source_ref:
            by_source_ref[candidate.source_ref] = candidate

    accepted: list[Citation] = []
    seen: set[tuple[str, int | None, tuple[int, ...] | None, str | None]] = set()
    for citation in requested:
        if citation.source_ref:
            chosen = by_source_ref.get(citation.source_ref)
            if chosen is None:
                continue
            options = [chosen]
        else:
            options = by_doc.get(citation.doc_id, [])
            # Graph evidence must retain its node/edge identifier. A generic
            # ``doc_id: primekg`` citation is not a valid graph citation.
            if any(
                option.source_ref
                and (
                    option.doc_id == "primekg"
                    or (option.source_type or "").endswith(("_node", "_edge"))
                )
                for option in options
            ):
                continue
        if not options:
            continue
        exact = next(
            (
                option
                for option in options
                if option.page == citation.page and option.span == citation.span
            ),
            None,
        )
        chosen = exact or options[0]
        key = (
            chosen.doc_id,
            chosen.page,
            tuple(chosen.span) if chosen.span else None,
            chosen.source_ref,
        )
        if key not in seen:
            seen.add(key)
            accepted.append(chosen)
    return accepted


class ModelAnswerFormatter:
    """Use a separate model to normalize an orchestrator answer, then validate it."""

    def __init__(self, model: ChatModel, system_prompt: str) -> None:
        self._model = model
        self._system_prompt = system_prompt

    def format_strict(
        self,
        raw_content: str | None,
        recorder: Recorder,
        *,
        question: Question | None = None,
    ) -> AgentAnswer:
        """Format and validate, surfacing model/contract failures to the caller."""
        answer_text, declared, marker_present = extract_supported_by(
            raw_content, recorder
        )
        candidates = (
            declared
            if marker_present and declared
            else _candidate_citations(recorder, answer_text, question, limit=12)
        )
        support_mode = "declared" if marker_present else "fallback"
        payload = {
            "question": (
                {
                    "question_id": question.question_id,
                    "question": question.question,
                    "category": question.category,
                    "answer_type": question.answer_type,
                }
                if question is not None
                else None
            ),
            "raw_answer": answer_text,
            "support_mode": support_mode,
            "support_marker_present": marker_present,
            "declared_support": [citation.to_json() for citation in declared],
            "allowed_citations": [citation.to_json() for citation in candidates],
            "evidence_catalog": (
                _catalog_for_citations(recorder, declared)
                if marker_present
                else _evidence_catalog(recorder, answer_text, question, limit=12)
            ),
        }
        turn = self._model.respond(
            [
                {"role": "system", "content": self._system_prompt},
                {
                    "role": "user",
                    "content": json.dumps(payload, separators=(",", ":")),
                },
            ],
            [],
        )
        if turn.tool_calls:
            raise ValueError("answer formatter returned tool calls")
        envelope = _AnswerEnvelope.model_validate(_extract_object(turn.content))
        citations = _reconcile_citations(envelope.citations, candidates)
        if envelope.citations and not citations:
            raise ValueError("formatter did not preserve a valid source reference")
        if marker_present:
            citations = declared
            if not citations and _is_evidence_limited_answer(answer_text):
                citations = _preferred_graph_citations(
                    recorder, answer_text, question, limit=10
                ) or candidates[:10]
        else:
            preferred_graph = _preferred_graph_citations(
                recorder, answer_text, question, limit=10
            )
            if preferred_graph:
                citations = preferred_graph
        # Small local formatters sometimes return every related edge even for a
        # one-entity answer.  For a terse PrimeKG answer, retain the single
        # highest-ranked relationship rather than an inaccurate bibliography.
        if not marker_present and len(envelope.answer.split()) <= 8:
            ranked_edges = [
                candidate
                for candidate in candidates
                if (candidate.source_type or "").endswith("_edge")
            ]
            if ranked_edges:
                citations = ranked_edges[:1]
        return AgentAnswer(
            answer=_compact_entity_answer(_plain_text(envelope.answer), question),
            confidence=envelope.confidence,
            citations=citations,
        )

    def format(
        self,
        raw_content: str | None,
        recorder: Recorder,
        *,
        question: Question | None = None,
    ) -> AgentAnswer:
        answer, _model_applied, _error = self.format_with_status(
            raw_content, recorder, question=question
        )
        return answer

    def format_with_status(
        self,
        raw_content: str | None,
        recorder: Recorder,
        *,
        question: Question | None = None,
    ) -> tuple[AgentAnswer, bool, str | None]:
        """Return a valid envelope plus whether the formatter model produced it."""
        try:
            return (
                self.format_strict(raw_content, recorder, question=question),
                True,
                None,
            )
        except Exception as exc:
            error = str(exc)
            log.warning("answer_formatter.fallback", error=error)
            return _fallback(raw_content, recorder, question), False, error
