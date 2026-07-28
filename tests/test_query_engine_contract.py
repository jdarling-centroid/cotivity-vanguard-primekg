from __future__ import annotations

import re

import pytest

from vanguard_primekg.query_engine import QueryEngine, specs as S


WRITE_SQL = re.compile(r"\b(INSERT|UPDATE|DELETE|MERGE|DROP|ALTER|CREATE|TRUNCATE)\b", re.I)


class Cursor:
    def __init__(self, conn):
        self.conn = conn
        self.sql = ""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def execute(self, sql, binds):
        self.sql = sql
        self.conn.calls.append((sql, dict(binds)))

    def fetchall(self):
        if "SELECT n.name, n.node_type, e.edge_id" in self.sql:
            return [("Drug", "drug", "e1", "n2", "drug_protein", "enzyme", 1, "Protein", "gene/protein")]
        return [
            ("node", "answer", "Answer", "gene/protein", None, None, None),
            (
                "support",
                "answer",
                "source\x1fanswer",
                "edge",
                "drug_protein",
                "enzyme",
                "test witness",
            ),
        ]


class Connection:
    def __init__(self):
        self.calls = []

    def cursor(self):
        return Cursor(self)


def _invoke(engine: QueryEngine, operation: str):
    if operation == "expand":
        return engine.expand(["source"], [S.TARGETS], final_type=("gene/protein",))
    if operation == "intersect":
        return engine.intersect((["a"], [S.TARGETS]), (["b"], [S.DIS_PROTEIN]))
    if operation == "difference":
        return engine.difference((["a"], [S.TARGETS]), (["b"], [S.DIS_PROTEIN]))
    if operation == "difference_many":
        return engine.difference_many(
            (["a"], [S.TARGETS]), [(["a"], [S.INTERACTS]), (["a"], [S.INDICATION, S.INDICATION])]
        )
    if operation == "edge_between":
        return engine.edge_between("source", "answer", S.TARGETS)
    if operation == "ratio":
        return engine.ratio_shared(["source"], final_type=("drug",))
    if operation == "intersect_many":
        return engine.intersect_many(
            [(["a"], [S.INDICATION]), (["b"], [S.CONTRA]), (["c"], [S.TARGETS, S.TARGETS])]
        )
    if operation == "xor":
        return engine.symmetric_difference((["a"], [S.DIS_PROTEIN]), (["b"], [S.DIS_PROTEIN]))
    if operation == "rank":
        return engine.rank_top(["source"], [S.DIS_PROTEIN, S.DIS_PROTEIN])
    if operation == "count_compare":
        return engine.count_compare(
            (["a"], [S.INDICATION, S.TARGETS]), (["b"], [S.INDICATION, S.TARGETS])
        )
    if operation == "bridge":
        return engine.bridge_count(["source"], n=2, final_type=("drug",))
    if operation == "count":
        return engine.count_threshold(
            ["source"], [S.INDICATION, S.SIDE_EFFECT], group_level=2,
            distinct_level=1, op=">=", n=2,
        )
    raise AssertionError(operation)


@pytest.mark.parametrize(
    "operation",
    [
        "expand", "intersect", "difference", "difference_many", "edge_between",
        "ratio", "intersect_many", "xor", "rank", "count_compare", "bridge", "count",
    ],
)
def test_each_composition_operation_executes_once_and_returns_native_path(operation: str) -> None:
    conn = Connection()
    result = _invoke(QueryEngine(conn), operation)
    assert len(conn.calls) == 1
    sql, binds = conn.calls[0]
    assert sql.lstrip().upper().startswith("WITH")
    assert not WRITE_SQL.search(sql)
    assert binds
    assert result.nodes == [("answer", "Answer", "gene/protein")]
    assert result.support[0].path_nodes == ["source", "answer"]
    assert result.support[0].path_edges == ["edge"]
    assert result.support[0].predicates == ["drug_protein"]
    assert result.support[0].display_relations == ["enzyme"]


def test_adjacent_evidence_is_one_read_query_with_audit_metadata() -> None:
    conn = Connection()
    evidence = QueryEngine(conn).node_evidence("source")
    assert len(conn.calls) == 1
    assert evidence.sql.lstrip().upper().startswith("SELECT")
    assert not WRITE_SQL.search(evidence.sql)
    assert evidence.binds == {"node_id": "source"}
    assert evidence.edges[0]["display_relation"] == "enzyme"
