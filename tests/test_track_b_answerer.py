import json

from vanguard_primekg.track_b.answerer import (
    answer_question,
    _required_evidence_documents,
    _required_evidence_anchors,
    _context_entity_candidates,
    _deterministic_shared_entity,
    _search_expansion,
    _validated,
)


def test_track_b_model_citations_are_closed_to_retrieved_chunks() -> None:
    value = {
        "answer": "Example",
        "answer_type": "entity",
        "confidence": 0.8,
        "citations": ["c1", "c1"],
        "evidence": [{"claim": "supported", "citations": ["c1"]}],
    }
    assert _validated(value, {"c1"})["citations"] == ["c1"]


def test_track_b_model_rejects_unknown_citation() -> None:
    import pytest

    with pytest.raises(ValueError, match="supplied chunk"):
        _validated(
            {
                "answer": "Example",
                "answer_type": "entity",
                "confidence": 0.8,
                "citations": ["invented"],
                "evidence": [],
            },
            {"c1"},
        )


def test_track_b_model_accepts_entity_list_array() -> None:
    value = _validated(
        {
            "answer": ["Taylor Swift", "Travis Kelce"],
            "answer_type": "entity_list",
            "confidence": 0.9,
            "citations": ["c1"],
            "evidence": [],
        },
        {"c1"},
    )
    assert value["answer"] == "Taylor Swift, Travis Kelce"


def test_track_b_model_promotes_evidence_citations() -> None:
    value = _validated(
        {
            "answer": "Golden State Warriors",
            "answer_type": "entity",
            "confidence": 0.8,
            "citations": [],
            "evidence": [{"claim": "shared team", "citations": ["c1", "c2"]}],
        },
        {"c1", "c2"},
    )
    assert value["citations"] == ["c1", "c2"]


def test_search_expansion_is_bounded_and_closed() -> None:
    class Model:
        def complete(self, **kwargs):
            return json.dumps({
                "candidate_shared_entities": [
                    "Epic Games", "Yelp", "Bing", "DuckDuckGo",
                ],
                "evidence_queries": [
                    {
                        "clue": "870 employees",
                        "source_terms": ["workforce layoff"],
                    },
                    {
                        "clue": "underdog Google",
                        "source_terms": ["legal trial"],
                    },
                ],
            })

    terms, evidence_queries = _search_expansion(Model(), "question", timeout=30)
    assert terms == [
        "Epic Games", "Yelp", "Bing", "DuckDuckGo",
        "870 employees workforce layoff", "underdog Google legal trial",
    ]
    assert evidence_queries == [
        "870 employees workforce layoff", "underdog Google legal trial",
    ]


def test_required_evidence_documents_counts_report_mentions() -> None:
    question = (
        "TechCrunch reports one clue, The Verge reports another, "
        "and TechCrunch reports a third."
    )
    assert _required_evidence_documents(
        question, {"TechCrunch", "The Verge"}
    ) == 3
    assert _required_evidence_documents(
        "TechCrunch reports one clue.", {"TechCrunch"}
    ) == 2


def test_required_evidence_anchors_preserve_quotes_and_versions() -> None:
    assert _required_evidence_anchors(
        'Compared with GPT-3.5 and "app store for AI" before GPT-4.'
    ) == ["gpt-3.5", "gpt-4"]


def test_context_entity_candidates_prefer_repeated_named_entities() -> None:
    from vanguard_primekg.track_b.retrieval import RetrievedChunk

    chunks = [
        RetrievedChunk(
            "c1", "d1", "e1", "Google faces a Google lawsuit.", {},
            {"title": "Google antitrust case"}, 1,
        ),
        RetrievedChunk(
            "c2", "d2", "e2", "Google was discussed alongside OpenAI.", {},
            {"title": "Publishers challenge Google"}, 1,
        ),
    ]
    assert _context_entity_candidates(chunks)[0] == "Google"


def test_deterministic_shared_entity_requires_independent_documents() -> None:
    from vanguard_primekg.track_b.retrieval import RetrievedChunk

    chunks = [
        RetrievedChunk(
            f"c{i}", f"d{i}", f"e{i}", text, {}, {"title": title}, 10 - i,
        )
        for i, (text, title) in enumerate([
            ("Google compared Gemini with GPT-3.5.", "Gemini review"),
            ("Google was the bad actor.", "Epic trial"),
            ("Google faces publisher antitrust claims.", "Publisher suit"),
        ])
    ]
    answer = _deterministic_shared_entity(
        chunks, ["Google", "OpenAI"], minimum_documents=3,
        required_anchors=["gpt-3.5"],
    )
    assert answer is not None
    assert answer["answer"] == "Google"
    assert len(answer["citations"]) == 3


def test_shared_entity_fallback_is_opt_in() -> None:
    import inspect

    parameter = inspect.signature(answer_question).parameters[
        "deterministic_shared_entity_fallback"
    ]
    assert parameter.default is False
