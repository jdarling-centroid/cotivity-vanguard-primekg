"""Integration tests against the loaded local PrimeKG (skipped if DB is down)."""

from __future__ import annotations

import pytest

from vanguard_primekg.query_engine import QueryEngine, specs as S
from vanguard_primekg.relations import DISEASE_TYPES, DRUG_TYPES, PROTEIN_TYPES
from vanguard_primekg.resolve import Resolver

try:
    from vanguard_primekg.db import connect

    _conn = connect()
    _conn.call_timeout = 20000
except Exception:  # pragma: no cover - environment without a live DB
    _conn = None

pytestmark = pytest.mark.skipif(_conn is None, reason="local Oracle not available")


def _resolve(name, types):
    hit = Resolver(_conn).resolve(name, types)
    assert hit is not None, name
    return hit.node_id


def test_q1_exact_target_edge() -> None:
    eng = QueryEngine(_conn)
    drug = _resolve("N-(2-Aminoethyl)-5-Chloroisoquinoline-8-Sulfonamide", DRUG_TYPES)
    res = eng.expand([drug], [S.TARGETS], final_type=PROTEIN_TYPES)
    assert [n[1] for n in res.nodes] == ["CSNK1G2"]
    assert res.edge_ids == ["pk_e_19484_2172_baf3d098"]


def test_q35_intersection_composes_in_db() -> None:
    eng = QueryEngine(_conn)
    rhin = _resolve("rhinitis", DISEASE_TYPES)
    thyro = _resolve("thyrotoxicosis", DISEASE_TYPES)
    res = eng.intersect(
        ([rhin], [S.INDICATION, S.TARGETS]),
        ([thyro], [S.CONTRA, S.TARGETS]),
        final_type=PROTEIN_TYPES,
    )
    names = {n[1] for n in res.nodes}
    # The set-intersection that broke the old system now yields real proteins.
    assert len(names) > 20
    assert "ADRB2" in names
    assert res.edge_ids  # real supporting edges


def test_all_four_target_roles_counted() -> None:
    with _conn.cursor() as cur:
        cur.execute(
            "SELECT DISTINCT display_relation FROM pk_edges WHERE predicate='drug_protein'"
        )
        roles = {r[0] for r in cur.fetchall()}
    assert {"target", "enzyme", "carrier", "transporter"} <= roles


def test_isotope_tracer_resolves_to_parent_compound() -> None:
    # (1,2,6,7-3H)Testosterone has no drug_protein edge itself; PrimeKG holds the
    # targets on the parent Testosterone node (AR target, SHBG carrier).
    hit = Resolver(_conn).resolve("(1,2,6,7-3H)Testosterone", DRUG_TYPES)
    assert hit is not None and hit.name == "Testosterone"
    res = QueryEngine(_conn).expand([hit.node_id], [S.TARGETS], final_type=PROTEIN_TYPES)
    names = {n[1] for n in res.nodes}
    assert {"AR", "SHBG"} <= names


def test_stereo_prefix_is_not_stripped() -> None:
    # "(2S)-..." is stereochemistry, not an isotope label; must not resolve to a parent.
    assert Resolver(_conn).resolve("(2S)-no-such-compound-xyz", DRUG_TYPES) is None

