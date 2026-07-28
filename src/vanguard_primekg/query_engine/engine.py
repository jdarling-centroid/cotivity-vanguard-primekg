"""Single-SQL query engine for categories A–D.

Every method composes ONE SQL statement (CTE chain) executed by Oracle — the
database does the joins / intersection / aggregation / negation, never the LLM.
Traversal is set-collapsed per hop (no path explosion); evidence is the real
last-hop edge id(s) that directly yield each answer node.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import oracledb

from ..logging import get_logger
from .specs import RelSpec, TARGETS

MAX_EVIDENCE_EDGES = 25  # config/primekg-question-sets.yaml validation_limits

log = get_logger("query_engine")


@dataclass
class QueryResult:
    nodes: list[tuple[str, str, str]]  # (node_id, name, node_type)
    edge_ids: list[str]
    sql: str

    @property
    def node_ids(self) -> list[str]:
        return [n[0] for n in self.nodes]


class _Binds:
    """Accumulates positional-safe named binds."""

    def __init__(self) -> None:
        self.values: dict[str, object] = {}
        self._n = 0

    def add(self, value: object) -> str:
        key = f"b{self._n}"
        self._n += 1
        self.values[key] = value
        return key

    def add_list(self, values) -> str:
        return ", ".join(f":{self.add(v)}" for v in values)


def _base_cte(name: str, ids: list[str], binds: _Binds) -> str:
    parts = [f"SELECT :{binds.add(i)} AS node_id FROM dual" for i in ids]
    return f"{name} AS (\n  " + "\n  UNION ALL ".join(parts) + "\n)"


def _hop_cte(name: str, prev: str, spec: RelSpec, binds: _Binds) -> str:
    where = [f"e.predicate = :{binds.add(spec.predicate)}"]
    if spec.displays:
        where.append(f"e.display_relation IN ({binds.add_list(spec.displays)})")
    return (
        f"{name} AS (\n"
        f"  SELECT DISTINCT e.target_node_id AS node_id\n"
        f"  FROM pk_edges e JOIN {prev} p ON e.source_node_id = p.node_id\n"
        f"  WHERE {' AND '.join(where)}\n"
        f")"
    )


def _levels(prefix: str, base_ids: list[str], steps: list[RelSpec], binds: _Binds) -> tuple[list[str], list[str]]:
    """Build base + hop CTEs; return (cte_sql_list, level_names)."""
    ctes: list[str] = []
    names: list[str] = [f"{prefix}0"]
    ctes.append(_base_cte(names[0], base_ids, binds))
    for k, spec in enumerate(steps, start=1):
        name = f"{prefix}{k}"
        ctes.append(_hop_cte(name, names[-1], spec, binds))
        names.append(name)
    return ctes, names


def _type_filter(alias: str, types: tuple[str, ...] | None, binds: _Binds) -> str:
    if not types:
        return ""
    return f" AND {alias}.node_type IN ({binds.add_list(types)})"


def _exclude_filter(col: str, ids: tuple[str, ...], binds: _Binds) -> str:
    if not ids:
        return ""
    return f" AND {col} NOT IN ({binds.add_list(ids)})"


def _require_edge_filter(node_col: str, spec: "RelSpec | None", binds: _Binds) -> str:
    """AND EXISTS: the answer node must be the source of >=1 edge of ``spec``."""
    if spec is None:
        return ""
    w = [f"re.predicate = :{binds.add(spec.predicate)}"]
    if spec.displays:
        w.append(f"re.display_relation IN ({binds.add_list(spec.displays)})")
    return (
        f" AND EXISTS (SELECT 1 FROM pk_edges re "
        f"WHERE re.source_node_id = {node_col} AND {' AND '.join(w)})"
    )


class QueryEngine:
    def __init__(self, conn: oracledb.Connection) -> None:
        self._conn = conn

    def _execute(self, sql: str, binds: _Binds) -> QueryResult:
        nodes: list[tuple[str, str, str]] = []
        edges: list[str] = []
        try:
            with self._conn.cursor() as cur:
                cur.execute(sql, binds.values)
                for kind, a, b, ctype in cur.fetchall():
                    if kind == "node":
                        nodes.append((a, b, ctype))
                    else:
                        edges.append(a)
        except oracledb.DatabaseError as exc:
            # A pathological/slow query (e.g. call_timeout) becomes an honest
            # empty result rather than a hang; never a fabricated answer.
            log.warning("query failed/aborted: %s", str(exc).splitlines()[0])
            return QueryResult(nodes=[], edge_ids=[], sql=sql)
        return QueryResult(nodes=nodes, edge_ids=edges, sql=sql)

    def walk_hops(
        self,
        base_ids: list[str],
        steps: list[RelSpec],
        *,
        sample: int = 4,
        cap: int = 1000,
    ) -> tuple[list[str], list[dict]]:
        """Walk a chain hop by hop for tracing. Returns (final_node_ids, hops).

        Each hop records the relation traversed, the source/target set sizes, and
        a few concrete example edges (edge_id, from_name -> to_name). This is the
        real graph traversal behind the answer (RFP 8.3 edge_traversal steps).
        """
        current = list(dict.fromkeys(base_ids))
        hops: list[dict] = []
        for spec in steps:
            src = current[:cap]
            with self._conn.cursor() as cur:
                src_binds = {f"s{i}": v for i, v in enumerate(src)}
                in_list = ", ".join(f":{k}" for k in src_binds)
                where = f"e.source_node_id IN ({in_list}) AND e.predicate = :pred"
                binds: dict[str, object] = {**src_binds, "pred": spec.predicate}
                if spec.displays:
                    dl = ", ".join(f":d{i}" for i in range(len(spec.displays)))
                    where += f" AND e.display_relation IN ({dl})"
                    binds.update({f"d{i}": d for i, d in enumerate(spec.displays)})

                cur.execute(
                    "SELECT e.edge_id, ns.name, nt.name FROM pk_edges e "
                    "JOIN pk_nodes ns ON ns.node_id = e.source_node_id "
                    "JOIN pk_nodes nt ON nt.node_id = e.target_node_id "
                    f"WHERE {where} FETCH FIRST {int(sample)} ROWS ONLY",
                    binds,
                )
                samples = [(r[0], r[1], r[2]) for r in cur.fetchall()]
                cur.execute(
                    f"SELECT DISTINCT e.target_node_id FROM pk_edges e WHERE {where}",
                    binds,
                )
                nxt = [r[0] for r in cur.fetchall()]

            hops.append(
                {
                    "predicate": spec.predicate,
                    "displays": list(spec.displays) if spec.displays else None,
                    "from_count": len(src),
                    "to_count": len(nxt),
                    "samples": samples,
                }
            )
            current = nxt
        return current, hops

    def expand(
        self,
        base_ids: list[str],
        steps: list[RelSpec],
        *,
        final_type: tuple[str, ...] | None = None,
        exclude_ids: tuple[str, ...] = (),
        require_edge: RelSpec | None = None,
    ) -> QueryResult:
        """Follow a chain of hops from ``base_ids``; return final nodes + evidence."""
        if not steps:
            raise ValueError("expand needs at least one step")
        binds = _Binds()
        ctes, names = _levels("l", base_ids, steps, binds)
        last = names[-1]
        prev = names[-2]
        ans_where = (
            "1=1"
            + _type_filter("n", final_type, binds)
            + _exclude_filter("n.node_id", exclude_ids, binds)
            + _require_edge_filter("n.node_id", require_edge, binds)
        )

        # last-hop evidence spec re-binds
        final_spec = steps[-1]
        ev_where = [f"e.predicate = :{binds.add(final_spec.predicate)}"]
        if final_spec.displays:
            ev_where.append(f"e.display_relation IN ({binds.add_list(final_spec.displays)})")

        sql = (
            "WITH " + ",\n".join(ctes) + ",\n"
            f"ans AS (\n  SELECT n.node_id, n.name, n.node_type\n"
            f"  FROM {last} lz JOIN pk_nodes n ON n.node_id = lz.node_id\n"
            f"  WHERE {ans_where}\n),\n"
            f"ev AS (\n  SELECT e.edge_id FROM pk_edges e\n"
            f"  JOIN {prev} p ON e.source_node_id = p.node_id\n"
            f"  JOIN ans a ON e.target_node_id = a.node_id\n"
            f"  WHERE {' AND '.join(ev_where)}\n"
            f"  FETCH FIRST {MAX_EVIDENCE_EDGES} ROWS ONLY\n)\n"
            "SELECT 'node' kind, node_id c1, name c2, node_type c3 FROM ans\n"
            "UNION ALL\n"
            "SELECT 'edge', edge_id, NULL, NULL FROM ev"
        )
        return self._execute(sql, binds)

    def intersect(
        self,
        leg_a: tuple[list[str], list[RelSpec]],
        leg_b: tuple[list[str], list[RelSpec]],
        *,
        final_type: tuple[str, ...] | None = None,
        exclude_ids: tuple[str, ...] = (),
        require_edge: RelSpec | None = None,
    ) -> QueryResult:
        """Final nodes reachable by BOTH legs (Category B / C-intersections)."""
        binds = _Binds()
        a_ids, a_steps = leg_a
        b_ids, b_steps = leg_b
        a_ctes, a_names = _levels("a", a_ids, a_steps, binds)
        b_ctes, b_names = _levels("b", b_ids, b_steps, binds)
        a_last, a_prev = a_names[-1], a_names[-2]
        b_last, b_prev = b_names[-1], b_names[-2]

        ans_where = (
            "1=1"
            + _type_filter("n", final_type, binds)
            + _exclude_filter("n.node_id", exclude_ids, binds)
            + _require_edge_filter("n.node_id", require_edge, binds)
        )

        def ev_cte(cte_name: str, prev: str, last_spec: RelSpec) -> str:
            w = [f"e.predicate = :{binds.add(last_spec.predicate)}"]
            if last_spec.displays:
                w.append(f"e.display_relation IN ({binds.add_list(last_spec.displays)})")
            return (
                f"{cte_name} AS (\n  SELECT e.edge_id FROM pk_edges e\n"
                f"  JOIN {prev} p ON e.source_node_id = p.node_id\n"
                f"  JOIN ans a ON e.target_node_id = a.node_id\n"
                f"  WHERE {' AND '.join(w)}\n"
                f"  FETCH FIRST {MAX_EVIDENCE_EDGES} ROWS ONLY\n)"
            )

        ctes = a_ctes + b_ctes
        ctes.append(
            f"ans AS (\n  SELECT n.node_id, n.name, n.node_type\n"
            f"  FROM {a_last} JOIN {b_last} ON {a_last}.node_id = {b_last}.node_id\n"
            f"  JOIN pk_nodes n ON n.node_id = {a_last}.node_id\n"
            f"  WHERE {ans_where}\n)"
        )
        ctes.append(ev_cte("eva", a_prev, a_steps[-1]))
        ctes.append(ev_cte("evb", b_prev, b_steps[-1]))

        sql = (
            "WITH " + ",\n".join(ctes) + "\n"
            "SELECT 'node' kind, node_id c1, name c2, node_type c3 FROM ans\n"
            "UNION ALL SELECT 'edge', edge_id, NULL, NULL FROM eva\n"
            "UNION ALL SELECT 'edge', edge_id, NULL, NULL FROM evb"
        )
        return self._execute(sql, binds)

    def difference(
        self,
        leg_a: tuple[list[str], list[RelSpec]],
        leg_b: tuple[list[str], list[RelSpec]],
        *,
        final_type: tuple[str, ...] | None = None,
        exclude_ids: tuple[str, ...] = (),
    ) -> QueryResult:
        """Final nodes reachable by leg A but NOT leg B (Category B/D negation)."""
        binds = _Binds()
        a_ids, a_steps = leg_a
        b_ids, b_steps = leg_b
        a_ctes, a_names = _levels("a", a_ids, a_steps, binds)
        b_ctes, b_names = _levels("b", b_ids, b_steps, binds)
        a_last, a_prev = a_names[-1], a_names[-2]
        b_last = b_names[-1]

        ans_where = (
            f"n.node_id NOT IN (SELECT node_id FROM {b_last})"
            + _type_filter("n", final_type, binds)
            + _exclude_filter("n.node_id", exclude_ids, binds)
        )
        final_spec = a_steps[-1]
        ev_where = [f"e.predicate = :{binds.add(final_spec.predicate)}"]
        if final_spec.displays:
            ev_where.append(f"e.display_relation IN ({binds.add_list(final_spec.displays)})")

        ctes = a_ctes + b_ctes
        ctes.append(
            f"ans AS (\n  SELECT n.node_id, n.name, n.node_type\n"
            f"  FROM {a_last} lz JOIN pk_nodes n ON n.node_id = lz.node_id\n"
            f"  WHERE {ans_where}\n)"
        )
        ctes.append(
            f"ev AS (\n  SELECT e.edge_id FROM pk_edges e\n"
            f"  JOIN {a_prev} p ON e.source_node_id = p.node_id\n"
            f"  JOIN ans a ON e.target_node_id = a.node_id\n"
            f"  WHERE {' AND '.join(ev_where)}\n"
            f"  FETCH FIRST {MAX_EVIDENCE_EDGES} ROWS ONLY\n)"
        )
        sql = (
            "WITH " + ",\n".join(ctes) + "\n"
            "SELECT 'node' kind, node_id c1, name c2, node_type c3 FROM ans\n"
            "UNION ALL SELECT 'edge', edge_id, NULL, NULL FROM ev"
        )
        return self._execute(sql, binds)

    def difference_many(
        self,
        leg_a: tuple[list[str], list[RelSpec]],
        minus_legs: list[tuple[list[str], list[RelSpec]]],
        *,
        final_type: tuple[str, ...] | None = None,
        exclude_ids: tuple[str, ...] = (),
    ) -> QueryResult:
        """Final nodes reachable by leg A but by NONE of the ``minus_legs``."""
        binds = _Binds()
        a_ctes, a_names = _levels("a", leg_a[0], leg_a[1], binds)
        a_last, a_prev = a_names[-1], a_names[-2]
        ctes = list(a_ctes)
        not_in = ""
        for j, leg in enumerate(minus_legs):
            m_ctes, m_names = _levels(f"m{j}_", leg[0], leg[1], binds)
            ctes += m_ctes
            not_in += f" AND n.node_id NOT IN (SELECT node_id FROM {m_names[-1]})"
        ans_where = "1=1" + not_in + _type_filter("n", final_type, binds) + _exclude_filter("n.node_id", exclude_ids, binds)
        final_spec = leg_a[1][-1]
        ev_where = [f"e.predicate = :{binds.add(final_spec.predicate)}"]
        if final_spec.displays:
            ev_where.append(f"e.display_relation IN ({binds.add_list(final_spec.displays)})")
        ctes.append(
            f"ans AS (\n  SELECT n.node_id, n.name, n.node_type\n"
            f"  FROM {a_last} lz JOIN pk_nodes n ON n.node_id = lz.node_id\n"
            f"  WHERE {ans_where}\n)"
        )
        ctes.append(
            f"ev AS (\n  SELECT e.edge_id FROM pk_edges e\n"
            f"  JOIN {a_prev} p ON e.source_node_id = p.node_id\n"
            f"  JOIN ans a ON e.target_node_id = a.node_id\n"
            f"  WHERE {' AND '.join(ev_where)}\n  FETCH FIRST {MAX_EVIDENCE_EDGES} ROWS ONLY\n)"
        )
        sql = (
            "WITH " + ",\n".join(ctes) + "\n"
            "SELECT 'node' kind, node_id c1, name c2, node_type c3 FROM ans\n"
            "UNION ALL SELECT 'edge', edge_id, NULL, NULL FROM ev"
        )
        return self._execute(sql, binds)

    def edge_between(
        self,
        source_id: str,
        target_id: str,
        spec: RelSpec,
    ) -> QueryResult:
        """Return the target node + edge id if a ``spec`` edge connects source to
        target (e.g. does drug X have side-effect Y). Empty if no such edge.
        """
        binds = _Binds()
        where = [
            f"e.source_node_id = :{binds.add(source_id)}",
            f"e.target_node_id = :{binds.add(target_id)}",
            f"e.predicate = :{binds.add(spec.predicate)}",
        ]
        if spec.displays:
            where.append(f"e.display_relation IN ({binds.add_list(spec.displays)})")
        sql = (
            "SELECT 'node' kind, n.node_id c1, n.name c2, n.node_type c3\n"
            "FROM pk_edges e JOIN pk_nodes n ON n.node_id = e.target_node_id\n"
            f"WHERE {' AND '.join(where)}\n"
            "UNION ALL\n"
            "SELECT 'edge', e.edge_id, NULL, NULL FROM pk_edges e\n"
            f"WHERE {' AND '.join(where)}"
        )
        return self._execute(sql, binds)

    def node_evidence(
        self, node_id: str
    ) -> tuple[str, str, list[tuple[str, str, int]], list[str]]:
        """Everything PrimeKG records about a node: (name, type, per-relation
        summary rows, sample edge ids). Used to ground an insufficient-data
        refusal in the evidence that IS available.
        """
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT name, node_type FROM pk_nodes WHERE node_id = :n", n=node_id
            )
            row = cur.fetchone()
            name, ntype = (row[0], row[1]) if row else (node_id, "")
            cur.execute(
                "SELECT predicate, display_relation, COUNT(*) c FROM pk_edges "
                "WHERE source_node_id = :n GROUP BY predicate, display_relation "
                "ORDER BY c DESC",
                n=node_id,
            )
            summary = [(r[0], r[1], r[2]) for r in cur.fetchall()]
            cur.execute(
                "SELECT edge_id FROM pk_edges WHERE source_node_id = :n "
                f"FETCH FIRST {MAX_EVIDENCE_EDGES} ROWS ONLY",
                n=node_id,
            )
            edge_ids = [r[0] for r in cur.fetchall()]
        return name, ntype, summary, edge_ids

    def ratio_shared(
        self,
        base_ids: list[str],
        *,
        numerator: int = 1,
        denominator: int = 2,
        final_type: tuple[str, ...] | None = None,
        exclude_ids: tuple[str, ...] = (),
    ) -> QueryResult:
        """Drugs whose shared-target fraction with the base drug is at least
        ``numerator/denominator`` and that have >= 1 target (Category D ratio).

        ``shared`` = |targets(D) ∩ targets(base)|, ``total`` = |targets(D)|;
        kept when ``shared * denominator >= total * numerator``.
        """
        binds = _Binds()
        tp = binds.add("drug_protein")
        roles = binds.add_list(TARGETS.displays)
        base_bind = binds.add_list(base_ids)
        # targets of the base drug
        ctes = [
            f"imt AS (\n  SELECT DISTINCT e.target_node_id AS p FROM pk_edges e\n"
            f"  WHERE e.source_node_id IN ({base_bind})\n"
            f"    AND e.predicate = :{tp} AND e.display_relation IN ({roles})\n)"
        ]
        tp2 = binds.add("drug_protein")
        roles2 = binds.add_list(TARGETS.displays)
        # candidate drugs: those targeting at least one base target
        ctes.append(
            f"cand AS (\n  SELECT DISTINCT e.target_node_id AS drug FROM pk_edges e\n"
            f"  JOIN imt ON e.source_node_id = imt.p\n"
            f"  WHERE e.predicate = :{tp2} AND e.display_relation IN ({roles2})\n"
            f"    AND e.target_node_id NOT IN ({binds.add_list(base_ids)})\n)"
        )
        tp3 = binds.add("drug_protein")
        roles3 = binds.add_list(TARGETS.displays)
        # every (candidate drug, target) pair
        ctes.append(
            f"dt AS (\n  SELECT DISTINCT c.drug, e.target_node_id AS p FROM pk_edges e\n"
            f"  JOIN cand c ON e.source_node_id = c.drug\n"
            f"  WHERE e.predicate = :{tp3} AND e.display_relation IN ({roles3})\n)"
        )
        ctes.append(
            "agg AS (\n  SELECT drug,\n"
            "    COUNT(DISTINCT p) total,\n"
            "    COUNT(DISTINCT CASE WHEN p IN (SELECT p FROM imt) THEN p END) shared\n"
            "  FROM dt GROUP BY drug\n)"
        )
        num = binds.add(numerator)
        den = binds.add(denominator)
        ctes.append(
            f"grp AS (SELECT drug AS node_id FROM agg WHERE total >= 1 AND shared * :{den} >= total * :{num})"
        )
        ctes.append(
            "ans AS (\n  SELECT n.node_id, n.name, n.node_type\n"
            "  FROM grp JOIN pk_nodes n ON n.node_id = grp.node_id\n"
            "  WHERE 1=1" + _type_filter("n", final_type, binds)
            + _exclude_filter("n.node_id", exclude_ids, binds) + "\n)"
        )
        tp4 = binds.add("drug_protein")
        roles4 = binds.add_list(TARGETS.displays)
        ctes.append(
            f"ev AS (\n  SELECT e.edge_id FROM pk_edges e JOIN ans a ON e.source_node_id = a.node_id\n"
            f"  WHERE e.predicate = :{tp4} AND e.display_relation IN ({roles4})\n"
            f"  FETCH FIRST {MAX_EVIDENCE_EDGES} ROWS ONLY\n)"
        )
        sql = (
            "WITH " + ",\n".join(ctes) + "\n"
            "SELECT 'node' kind, node_id c1, name c2, node_type c3 FROM ans\n"
            "UNION ALL SELECT 'edge', edge_id, NULL, NULL FROM ev"
        )
        return self._execute(sql, binds)

    def intersect_many(
        self,
        legs: list[tuple[list[str], list[RelSpec]]],
        *,
        final_type: tuple[str, ...] | None = None,
        exclude_ids: tuple[str, ...] = (),
    ) -> QueryResult:
        """Final nodes reachable by ALL legs (N-way intersection)."""
        if len(legs) < 2:
            raise ValueError("intersect_many needs >= 2 legs")
        binds = _Binds()
        ctes: list[str] = []
        lasts: list[str] = []
        prevs: list[str] = []
        specs: list[RelSpec] = []
        for i, (ids, steps) in enumerate(legs):
            prefix = f"g{i}_"
            leg_ctes, names = _levels(prefix, ids, steps, binds)
            ctes += leg_ctes
            lasts.append(names[-1])
            prevs.append(names[-2])
            specs.append(steps[-1])

        joins = lasts[0]
        for last in lasts[1:]:
            joins += f"\n  JOIN {last} ON {last}.node_id = {lasts[0]}.node_id"
        ans_where = "1=1" + _type_filter("n", final_type, binds) + _exclude_filter("n.node_id", exclude_ids, binds)
        ctes.append(
            f"ans AS (\n  SELECT n.node_id, n.name, n.node_type\n"
            f"  FROM {joins}\n  JOIN pk_nodes n ON n.node_id = {lasts[0]}.node_id\n"
            f"  WHERE {ans_where}\n)"
        )

        ev_selects = []
        cap = max(1, MAX_EVIDENCE_EDGES // len(legs))
        for i, (prev, spec) in enumerate(zip(prevs, specs)):
            w = [f"e.predicate = :{binds.add(spec.predicate)}"]
            if spec.displays:
                w.append(f"e.display_relation IN ({binds.add_list(spec.displays)})")
            ctes.append(
                f"ev{i} AS (\n  SELECT e.edge_id FROM pk_edges e\n"
                f"  JOIN {prev} p ON e.source_node_id = p.node_id\n"
                f"  JOIN ans a ON e.target_node_id = a.node_id\n"
                f"  WHERE {' AND '.join(w)}\n  FETCH FIRST {cap} ROWS ONLY\n)"
            )
            ev_selects.append(f"SELECT 'edge', edge_id, NULL, NULL FROM ev{i}")

        sql = (
            "WITH " + ",\n".join(ctes) + "\n"
            "SELECT 'node' kind, node_id c1, name c2, node_type c3 FROM ans\n"
            "UNION ALL " + "\nUNION ALL ".join(ev_selects)
        )
        return self._execute(sql, binds)

    def symmetric_difference(
        self,
        leg_a: tuple[list[str], list[RelSpec]],
        leg_b: tuple[list[str], list[RelSpec]],
        *,
        final_type: tuple[str, ...] | None = None,
    ) -> QueryResult:
        """Final nodes reachable by leg A or leg B but NOT both (XOR)."""
        binds = _Binds()
        a_ctes, a_names = _levels("a", leg_a[0], leg_a[1], binds)
        b_ctes, b_names = _levels("b", leg_b[0], leg_b[1], binds)
        a_last, b_last = a_names[-1], b_names[-1]
        a_prev, b_prev = a_names[-2], b_names[-2]
        ans_where = "1=1" + _type_filter("n", final_type, binds)
        ctes = a_ctes + b_ctes
        ctes.append(
            f"ua AS (SELECT node_id FROM {a_last} WHERE node_id NOT IN (SELECT node_id FROM {b_last}))"
        )
        ctes.append(
            f"ub AS (SELECT node_id FROM {b_last} WHERE node_id NOT IN (SELECT node_id FROM {a_last}))"
        )
        ctes.append(
            f"ans AS (\n  SELECT n.node_id, n.name, n.node_type FROM\n"
            f"  (SELECT node_id FROM ua UNION SELECT node_id FROM ub) u\n"
            f"  JOIN pk_nodes n ON n.node_id = u.node_id WHERE {ans_where}\n)"
        )
        a_spec, b_spec = leg_a[1][-1], leg_b[1][-1]

        def ev(name: str, prev: str, spec: RelSpec) -> str:
            w = [f"e.predicate = :{binds.add(spec.predicate)}"]
            if spec.displays:
                w.append(f"e.display_relation IN ({binds.add_list(spec.displays)})")
            return (
                f"{name} AS (\n  SELECT e.edge_id FROM pk_edges e\n"
                f"  JOIN {prev} p ON e.source_node_id = p.node_id\n"
                f"  JOIN ans a ON e.target_node_id = a.node_id\n"
                f"  WHERE {' AND '.join(w)}\n  FETCH FIRST {MAX_EVIDENCE_EDGES // 2} ROWS ONLY\n)"
            )

        ctes.append(ev("eva", a_prev, a_spec))
        ctes.append(ev("evb", b_prev, b_spec))
        sql = (
            "WITH " + ",\n".join(ctes) + "\n"
            "SELECT 'node' kind, node_id c1, name c2, node_type c3 FROM ans\n"
            "UNION ALL SELECT 'edge', edge_id, NULL, NULL FROM eva\n"
            "UNION ALL SELECT 'edge', edge_id, NULL, NULL FROM evb"
        )
        return self._execute(sql, binds)

    def rank_top(
        self,
        base_ids: list[str],
        steps: list[RelSpec],
        *,
        final_type: tuple[str, ...] | None = None,
        exclude_ids: tuple[str, ...] = (),
    ) -> QueryResult:
        """Peers that share the MOST distinct intermediate nodes with the base
        entity (Category D "share the MOST ..." — all ties at RANK 1).

        Exactly two steps: base -> shared (level 1) -> peer (level 2).
        """
        if len(steps) != 2:
            raise ValueError("rank_top expects exactly two steps")
        binds = _Binds()
        # l0 base, l1 = shared nodes (after step 1, collapsed set)
        ctes, names = _levels("l", base_ids, [steps[0]], binds)
        ctes.append(f"a1 AS (SELECT node_id AS shared, node_id AS cur FROM {names[-1]})")
        spec = steps[1]
        w = [f"e.predicate = :{binds.add(spec.predicate)}"]
        if spec.displays:
            w.append(f"e.display_relation IN ({binds.add_list(spec.displays)})")
        ctes.append(
            f"pairs AS (\n  SELECT DISTINCT p.shared AS shared, e.target_node_id AS peer\n"
            f"  FROM pk_edges e JOIN a1 p ON e.source_node_id = p.cur\n"
            f"  WHERE {' AND '.join(w)}\n)"
        )
        gspec = steps[-1]
        ev_where = [f"e.predicate = :{binds.add(gspec.predicate)}"]
        if gspec.displays:
            ev_where.append(f"e.display_relation IN ({binds.add_list(gspec.displays)})")
        ctes.append(
            "counts AS (\n  SELECT peer, COUNT(DISTINCT shared) c FROM pairs\n"
            "  WHERE 1=1" + _exclude_filter("peer", exclude_ids, binds) + "\n  GROUP BY peer\n)"
        )
        ctes.append(
            "grp AS (SELECT peer AS node_id FROM counts WHERE c = (SELECT MAX(c) FROM counts))"
        )
        ctes.append(
            "ans AS (\n  SELECT n.node_id, n.name, n.node_type\n"
            "  FROM grp JOIN pk_nodes n ON n.node_id = grp.node_id\n"
            "  WHERE 1=1" + _type_filter("n", final_type, binds) + "\n)"
        )
        ctes.append(
            f"ev AS (\n  SELECT e.edge_id FROM pk_edges e\n"
            f"  JOIN ans a ON e.target_node_id = a.node_id\n"
            f"  WHERE {' AND '.join(ev_where)}\n  FETCH FIRST {MAX_EVIDENCE_EDGES} ROWS ONLY\n)"
        )
        sql = (
            "WITH " + ",\n".join(ctes) + "\n"
            "SELECT 'node' kind, node_id c1, name c2, node_type c3 FROM ans\n"
            "UNION ALL SELECT 'edge', edge_id, NULL, NULL FROM ev"
        )
        return self._execute(sql, binds)

    def count_compare(
        self,
        leg_a: tuple[list[str], list[RelSpec]],
        leg_b: tuple[list[str], list[RelSpec]],
        *,
        cmp: str = ">",
        final_type: tuple[str, ...] | None = None,
    ) -> QueryResult:
        """Group nodes where leg A's distinct count ``cmp`` leg B's (Category D
        "more X than Y"). Both legs are two hops ending at the compared node;
        the counted node is the level-1 node of each leg.
        """
        if cmp not in {">", ">=", "<", "<=", "="}:
            raise ValueError(f"bad cmp {cmp!r}")
        binds = _Binds()
        ctes: list[str] = []

        def leg_counts(prefix: str, leg: tuple[list[str], list[RelSpec]]) -> str:
            ids, steps = leg
            sub, names = _levels(f"{prefix}s", ids, [steps[0]], binds)  # level1 set
            ctes.extend(sub)
            ctes.append(f"{prefix}a AS (SELECT node_id AS counted, node_id AS cur FROM {names[-1]})")
            spec = steps[1]
            w = [f"e.predicate = :{binds.add(spec.predicate)}"]
            if spec.displays:
                w.append(f"e.display_relation IN ({binds.add_list(spec.displays)})")
            ctes.append(
                f"{prefix}p AS (\n  SELECT DISTINCT p.counted, e.target_node_id AS grp\n"
                f"  FROM pk_edges e JOIN {prefix}a p ON e.source_node_id = p.cur\n"
                f"  WHERE {' AND '.join(w)}\n)"
            )
            ctes.append(
                f"{prefix}c AS (SELECT grp, COUNT(DISTINCT counted) c FROM {prefix}p GROUP BY grp)"
            )
            return f"{prefix}c"

        ca = leg_counts("x", leg_a)
        cb = leg_counts("y", leg_b)
        gspec = leg_a[1][-1]
        ev_where = [f"e.predicate = :{binds.add(gspec.predicate)}"]
        if gspec.displays:
            ev_where.append(f"e.display_relation IN ({binds.add_list(gspec.displays)})")

        ctes.append(
            f"grp AS (\n  SELECT {ca}.grp AS node_id FROM {ca}\n"
            f"  LEFT JOIN {cb} ON {cb}.grp = {ca}.grp\n"
            f"  WHERE {ca}.c {cmp} NVL({cb}.c, 0)\n)"
        )
        ctes.append(
            f"ans AS (\n  SELECT n.node_id, n.name, n.node_type\n"
            f"  FROM grp JOIN pk_nodes n ON n.node_id = grp.node_id\n"
            f"  WHERE 1=1" + _type_filter("n", final_type, binds) + "\n)"
        )
        ctes.append(
            f"ev AS (\n  SELECT e.edge_id FROM pk_edges e JOIN ans a ON e.target_node_id = a.node_id\n"
            f"  WHERE {' AND '.join(ev_where)}\n  FETCH FIRST {MAX_EVIDENCE_EDGES} ROWS ONLY\n)"
        )
        sql = (
            "WITH " + ",\n".join(ctes) + "\n"
            "SELECT 'node' kind, node_id c1, name c2, node_type c3 FROM ans\n"
            "UNION ALL SELECT 'edge', edge_id, NULL, NULL FROM ev"
        )
        return self._execute(sql, binds)

    def bridge_count(
        self,
        base_ids: list[str],
        *,
        n: int,
        op: str = ">=",
        final_type: tuple[str, ...] | None = None,
        exclude_ids: tuple[str, ...] = (),
    ) -> QueryResult:
        """Drugs linked to the base drug by >= n distinct target->PPI->target
        bridges (Category D). A bridge is a distinct (base_target, peer_target)
        pair connected by a PPI edge.
        """
        if op not in {">=", ">", "=", "<=", "<"}:
            raise ValueError(f"bad op {op!r}")
        binds = _Binds()
        ctes, names = _levels("l", base_ids, [], binds)  # l0 = base drug
        base = names[-1]
        tp = binds.add("drug_protein")
        roles = binds.add_list(TARGETS.displays)
        ppi_p = binds.add("protein_protein")
        ppi_d = binds.add("ppi")
        ctes.append(
            f"pa AS (\n  SELECT DISTINCT e.target_node_id AS pa FROM pk_edges e\n"
            f"  JOIN {base} b ON e.source_node_id = b.node_id\n"
            f"  WHERE e.predicate = :{tp} AND e.display_relation IN ({roles})\n)"
        )
        ctes.append(
            f"br AS (\n  SELECT DISTINCT pa.pa, e.target_node_id AS pb FROM pk_edges e\n"
            f"  JOIN pa ON e.source_node_id = pa.pa\n"
            f"  WHERE e.predicate = :{ppi_p} AND e.display_relation IN (:{ppi_d})\n)"
        )
        tp2 = binds.add("drug_protein")
        roles2 = binds.add_list(TARGETS.displays)
        ctes.append(
            f"bridges AS (\n  SELECT br.pa, br.pb, e.target_node_id AS drug FROM pk_edges e\n"
            f"  JOIN br ON e.source_node_id = br.pb\n"
            f"  WHERE e.predicate = :{tp2} AND e.display_relation IN ({roles2})\n)"
        )
        having = f"COUNT(DISTINCT pa || '|' || pb) {op} :{binds.add(n)}"
        ctes.append(
            f"grp AS (\n  SELECT drug AS node_id FROM bridges\n"
            f"  WHERE 1=1" + _exclude_filter("drug", tuple(base_ids) + exclude_ids, binds) + "\n"
            f"  GROUP BY drug HAVING {having}\n)"
        )
        ctes.append(
            f"ans AS (\n  SELECT n.node_id, n.name, n.node_type\n"
            f"  FROM grp JOIN pk_nodes n ON n.node_id = grp.node_id\n"
            f"  WHERE 1=1" + _type_filter("n", final_type, binds) + "\n)"
        )
        tp3 = binds.add("drug_protein")
        roles3 = binds.add_list(TARGETS.displays)
        ctes.append(
            f"ev AS (\n  SELECT e.edge_id FROM pk_edges e JOIN ans a ON e.source_node_id = a.node_id\n"
            f"  WHERE e.predicate = :{tp3} AND e.display_relation IN ({roles3})\n"
            f"  FETCH FIRST {MAX_EVIDENCE_EDGES} ROWS ONLY\n)"
        )
        sql = (
            "WITH " + ",\n".join(ctes) + "\n"
            "SELECT 'node' kind, node_id c1, name c2, node_type c3 FROM ans\n"
            "UNION ALL SELECT 'edge', edge_id, NULL, NULL FROM ev"
        )
        return self._execute(sql, binds)

    def count_threshold(
        self,
        base_ids: list[str],
        steps: list[RelSpec],
        *,
        group_level: int,
        distinct_level: int,
        op: str,
        n: int,
        final_type: tuple[str, ...] | None = None,
        exclude_ids: tuple[str, ...] = (),
        member_of: tuple[list[str], list[RelSpec]] | None = None,
    ) -> QueryResult:
        """Group by the node at ``group_level``, count DISTINCT nodes at
        ``distinct_level``, keep groups whose count ``op`` ``n`` (Category D).

        Levels before ``min(group_level, distinct_level)`` are collapsed to sets
        (no path explosion). From there only two columns are carried — the group
        node and the counted node — so the working set is bounded by those pairs.
        ``member_of`` optionally restricts answers to a companion reachable set.
        """
        if op not in {">=", ">", "=", "<=", "<"}:
            raise ValueError(f"bad op {op!r}")
        binds = _Binds()
        start = min(group_level, distinct_level)
        end = max(group_level, distinct_level)

        # collapsed set levels 0..start
        set_specs = steps[:start]
        ctes, names = _levels("l", base_ids, list(set_specs), binds)

        # anchor pair chain from `start` to `end`
        ctes.append(
            f"a{start} AS (SELECT node_id AS anchor, node_id AS cur FROM {names[-1]})"
        )
        for k in range(start + 1, end + 1):
            spec = steps[k - 1]
            w = [f"e.predicate = :{binds.add(spec.predicate)}"]
            if spec.displays:
                w.append(f"e.display_relation IN ({binds.add_list(spec.displays)})")
            ctes.append(
                f"a{k} AS (\n  SELECT DISTINCT p.anchor, e.target_node_id AS cur\n"
                f"  FROM pk_edges e JOIN a{k-1} p ON e.source_node_id = p.cur\n"
                f"  WHERE {' AND '.join(w)}\n)"
            )
        pair = f"a{end}"
        group_col = "anchor" if group_level == start else "cur"
        distinct_col = "cur" if group_col == "anchor" else "anchor"
        having = f"COUNT(DISTINCT {distinct_col}) {op} :{binds.add(n)}"

        member_filter = ""
        if member_of is not None:
            m_ctes, m_names = _levels("m", member_of[0], member_of[1], binds)
            ctes += m_ctes
            member_filter = f" WHERE {group_col} IN (SELECT node_id FROM {m_names[-1]})"

        ans_where = "1=1" + _type_filter("nd", final_type, binds) + _exclude_filter("grp.node_id", exclude_ids, binds)
        # evidence: the edge into each answer (group) node from its predecessor
        gspec = steps[group_level - 1] if group_level >= 1 else steps[0]
        ev_where = [f"e.predicate = :{binds.add(gspec.predicate)}"]
        if gspec.displays:
            ev_where.append(f"e.display_relation IN ({binds.add_list(gspec.displays)})")

        ctes.append(
            f"grp AS (\n  SELECT {group_col} AS node_id FROM {pair}{member_filter}\n"
            f"  GROUP BY {group_col} HAVING {having}\n)"
        )
        ctes.append(
            f"ans AS (\n  SELECT nd.node_id, nd.name, nd.node_type\n"
            f"  FROM grp JOIN pk_nodes nd ON nd.node_id = grp.node_id\n"
            f"  WHERE {ans_where}\n)"
        )
        ctes.append(
            f"ev AS (\n  SELECT e.edge_id FROM pk_edges e\n"
            f"  JOIN ans a ON e.target_node_id = a.node_id\n"
            f"  WHERE {' AND '.join(ev_where)}\n"
            f"  FETCH FIRST {MAX_EVIDENCE_EDGES} ROWS ONLY\n)"
        )
        sql = (
            "WITH " + ",\n".join(ctes) + "\n"
            "SELECT 'node' kind, node_id c1, name c2, node_type c3 FROM ans\n"
            "UNION ALL SELECT 'edge', edge_id, NULL, NULL FROM ev"
        )
        return self._execute(sql, binds)
