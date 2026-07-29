from vanguard_primekg.track_b.retrieval import search_tokens


def test_search_tokens_are_bounded_and_drop_question_filler() -> None:
    tokens = search_tokens(
        "Which company, according to TechCrunch, launched GPT-4 with vision "
        "and is associated with Sam Altman?",
        limit=8,
    )
    assert "which" not in tokens
    assert "company" not in tokens
    assert "techcrunch" in tokens
    assert "gpt-4" in tokens
    assert "altman" in tokens
    assert len(tokens) <= 8
