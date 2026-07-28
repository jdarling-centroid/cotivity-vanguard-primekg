"""Classifier maps representative questions to the right category-general plan."""

from __future__ import annotations

from vanguard_primekg.classify import classify


def _preds(steps):
    return [s.predicate for s in steps]


def test_one_hop_targets() -> None:
    p = classify("Which proteins does the drug Naftifine target?")
    assert p.op == "expand"
    assert _preds(p.steps) == ["drug_protein"]
    assert p.slots[0][0] == "Naftifine"


def test_intersection_both_indicated_and_contra() -> None:
    p = classify(
        "Which proteins are targeted by BOTH a drug indicated for rhinitis and a "
        "drug contraindicated for thyrotoxicosis?"
    )
    assert p.op == "intersect"
    assert [i for i, _ in p.legs] == [0, 1]
    assert _preds(p.legs[0][1]) == ["indication", "drug_protein"]
    assert _preds(p.legs[1][1]) == ["contraindication", "drug_protein"]


def test_indicated_but_contra_is_intersection_not_one_hop() -> None:
    # greedy one-hop must NOT swallow the multi-clause question
    p = classify(
        "Which drugs are indicated for the disease familial ovarian cancer but "
        "contraindicated for the disease neuromuscular junction disease?"
    )
    assert p.op == "intersect"
    assert p.slots[0][0] == "familial ovarian cancer"
    assert p.slots[1][0] == "neuromuscular junction disease"


def test_count_threshold() -> None:
    p = classify(
        "Which proteins are targeted by AT LEAST 3 different drugs that are each "
        "indicated for schizophrenia?"
    )
    assert p.op == "count"
    assert p.n == 3 and p.cmp == ">="


def test_out_of_graph_facts_are_grounded_insufficient_data() -> None:
    # PrimeKG lacks these attributes; the entity is still resolved so the refusal
    # can be grounded in the evidence it does record.
    p = classify("What is the recommended dosage of Deferiprone?")
    assert p.op == "insufficient_data"
    assert p.slots[0][0] == "Deferiprone"
    assert classify("What is the price of Deferiprone?").op == "insufficient_data"
    assert classify("What is the prognosis for myasthenia gravis?").op == "insufficient_data"


def test_unmatched_is_insufficient_not_wrong() -> None:
    p = classify("Which targets of Imatinib are NOT in any pathway shared with a "
                 "target of Dasatinib?")
    assert p.op in {"insufficient", "difference"}
