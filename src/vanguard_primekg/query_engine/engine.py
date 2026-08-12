"""Single-SQL query engine for categories A–D.

Every method composes ONE SQL statement (CTE chain) executed by Oracle — the
database does the joins / intersection / aggregation / negation, never the LLM.
Traversal is set-collapsed per hop (no path explosion); evidence is the real
last-hop edge id(s) that directly yield each answer node.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..oracle_compat import oracledb

from ..logging import get_logger
from .specs import RelSpec, TARGETS

MAX_EVIDENCE_EDGES = 25  # legacy compatibility; paths are now answer-scoped
_PATH_SEP = "\x1f"

log = get_logger("query_engine")


@dataclass(frozen=True)
class SupportPath:
    """One complete database-returned path supporting an answer node."""

    answer_node_id: str
    path_nodes: list[str]
    path_edges: list[str]
    predicates: list[str]
    display_relations: list[str] = field(default_factory=list)
    semantics: str | None = None


@dataclass(frozen=True)
class NodeEvidence:
    """One read-only adjacent-evidence query for describe/refusal records."""

    node_id: str
    name: str
    node_type: str
    summary: list[tuple[str, str, int]]
    edges: list[dict[str, str]]
    sql: str
    binds: dict[str, object]


@dataclass
class QueryResult:
    nodes: list[tuple[str, str, str]]  # (node_id, name, node_type)
    support: list[SupportPath] = field(default_factory=list)
    sql: str = ""
    binds: dict[str, object] = field(default_factory=dict)
    truncated: bool = False
    error: str | None = None
    # Kept for compatibility with the original tests and callers.  New query
    # paths derive this list from ``support``.
    edge_ids: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.support:
            seen: set[str] = set()
            derived: list[str] = []
            for path in self.support:
                for edge_id in path.path_edges:
                    if edge_id not in seen:
                        seen.add(edge_id)
                        derived.append(edge_id)
            self.edge_ids = derived

    @property
    def node_ids(self) -> list[str]:
        return [n[0] for n in self.nodes]

    def support_for(self, node_id: str) -> list[SupportPath]:
        return [path for path in self.support if path.answer_node_id == node_id]


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



def _path_levels(
    prefix: str, base_ids: list[str], steps: list[RelSpec], binds: _Binds
) -> tuple[list[str], list[str]]:
    """Build bounded, path-carrying CTEs and retain one path per reached node.

    This is used only to emit auditable support from the same authoritative SQL
    statement.  Answer-set composition may use the set-collapsed CTEs above.
    """
    base = f"{prefix}p0"
    parts = [
        f"SELECT :{binds.add(node_id)} node_id, :{binds.add(node_id)} path_nodes, "
        "CAST(NULL AS VARCHAR2(4000)) path_edges, "
        "CAST(NULL AS VARCHAR2(4000)) predicates, "
        "CAST(NULL AS VARCHAR2(4000)) displays FROM dual"
        for node_id in base_ids
    ]
    ctes = [f"{base} AS (\n  " + "\n  UNION ALL ".join(parts) + "\n)"]
    names = [base]
    for index, spec in enumerate(steps, 1):
        name = f"{prefix}p{index}"
        where = [f"e.predicate = :{binds.add(spec.predicate)}"]
        if spec.displays:
            where.append(f"e.display_relation IN ({binds.add_list(spec.displays)})")
        order = "e.edge_id, p.path_edges"
        ctes.append(
            f"{name} AS (\n"
            "  SELECT e.target_node_id node_id, "
            f"MIN(p.path_nodes || CHR(31) || e.target_node_id) KEEP (DENSE_RANK FIRST ORDER BY {order}) path_nodes, "
            f"MIN(CASE WHEN p.path_edges IS NULL THEN e.edge_id ELSE p.path_edges || CHR(31) || e.edge_id END) KEEP (DENSE_RANK FIRST ORDER BY {order}) path_edges, "
            f"MIN(CASE WHEN p.predicates IS NULL THEN e.predicate ELSE p.predicates || CHR(31) || e.predicate END) KEEP (DENSE_RANK FIRST ORDER BY {order}) predicates, "
            f"MIN(CASE WHEN p.displays IS NULL THEN e.display_relation ELSE p.displays || CHR(31) || e.display_relation END) KEEP (DENSE_RANK FIRST ORDER BY {order}) displays\n"
            f"  FROM pk_edges e JOIN {names[-1]} p ON e.source_node_id = p.node_id\n"
            f"  WHERE {' AND '.join(where)}\n"
            "  GROUP BY e.target_node_id\n"
            ")"
        )
        names.append(name)
    return ctes, names


def _backtrack_support(
    prefix: str,
    answer_cte: str,
    level_names: list[str],
    steps: list[RelSpec],
    binds: _Binds,
) -> tuple[list[str], str]:
    """Build one complete witness per retained answer by walking levels backward.

    Answer composition uses the lightweight set CTEs.  Starting from the bounded
    answer CTE avoids carrying path strings across every node in broad hops.
    Each reverse hop is constrained to the corresponding forward level, so the
    returned witness is a path admitted by the authoritative composition.
    """
    start = f"{prefix}s0"
    ctes = [
        f"{start} AS (\n"
        f"  SELECT node_id answer_node_id, node_id current_node, node_id path_nodes, "
        "CAST(NULL AS VARCHAR2(4000)) path_edges, "
        "CAST(NULL AS VARCHAR2(4000)) predicates, "
        "CAST(NULL AS VARCHAR2(4000)) displays "
        f"FROM {answer_cte}\n)"
    ]
    previous = start
    for reverse_index, spec in enumerate(reversed(steps), 1):
        forward_level = len(steps) - reverse_index
        name = f"{prefix}s{reverse_index}"
        where = [f"e.predicate = :{binds.add(spec.predicate)}"]
        if spec.displays:
            where.append(f"e.display_relation IN ({binds.add_list(spec.displays)})")
        order = "e.edge_id"
        ctes.append(
            f"{name} AS (\n"
            "  SELECT p.answer_node_id, "
            f"MIN(e.source_node_id) KEEP (DENSE_RANK FIRST ORDER BY {order}) current_node, "
            f"MIN(e.source_node_id || CHR(31) || p.path_nodes) KEEP (DENSE_RANK FIRST ORDER BY {order}) path_nodes, "
            f"MIN(e.edge_id || CASE WHEN p.path_edges IS NULL THEN '' ELSE CHR(31) || p.path_edges END) KEEP (DENSE_RANK FIRST ORDER BY {order}) path_edges, "
            f"MIN(e.predicate || CASE WHEN p.predicates IS NULL THEN '' ELSE CHR(31) || p.predicates END) KEEP (DENSE_RANK FIRST ORDER BY {order}) predicates, "
            f"MIN(NVL(e.display_relation, '') || CASE WHEN p.displays IS NULL THEN '' ELSE CHR(31) || p.displays END) KEEP (DENSE_RANK FIRST ORDER BY {order}) displays\n"
            f"  FROM {previous} p\n"
            "  JOIN pk_edges e ON e.target_node_id = p.current_node\n"
            f"  JOIN {level_names[forward_level]} allowed "
            "ON allowed.node_id = e.source_node_id\n"
            f"  WHERE {' AND '.join(where)}\n"
            "  GROUP BY p.answer_node_id\n"
            ")"
        )
        previous = name
    return ctes, previous


def _node_select(name: str = "ans") -> str:
    return (
        f"SELECT 'node' kind, node_id c1, name c2, node_type c3, "
        f"NULL c4, NULL c5, NULL c6 FROM {name}"
    )


def _support_select(name: str, semantics: str) -> str:
    safe = semantics.replace("'", "''")
    return (
        f"SELECT 'support' kind, answer_node_id c1, path_nodes c2, path_edges c3, "
        f"predicates c4, displays c5, '{safe}' c6 FROM {name}"
    )

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
        legacy_edges: list[str] = []
        support: list[SupportPath] = []
        try:
            with self._conn.cursor() as cur:
                cur.execute(sql, binds.values)
                for row in cur.fetchall():
                    kind = row[0]
                    padded = tuple(row) + (None,) * max(0, 7 - len(row))
                    _, a, b, c, d, e, f = padded[:7]
                    if kind == "node":
                        nodes.append((a, b, c))
                    elif kind == "support":
                        split = lambda value: [] if value in (None, "") else str(value).split(_PATH_SEP)
                        support.append(
                            SupportPath(
                                answer_node_id=str(a),
                                path_nodes=split(b),
                                path_edges=split(c),
                                predicates=split(d),
                                display_relations=split(e),
                                semantics=None if f is None else str(f),
                            )
                        )
                    elif kind == "edge":  # legacy SQL path
                        legacy_edges.append(a)
        except oracledb.DatabaseError as exc:
            message = str(exc).splitlines()[0]
            log.warning("query failed/aborted: %s", message)
            return QueryResult(nodes=[], support=[], sql=sql, binds=dict(binds.values), error=message)

        # A direct-edge join can return the same answer node through more than
        # one native relation row.  Keep one answer record while retaining every
        # returned support path.
        deduped: list[tuple[str, str, str]] = []
        seen_nodes: set[str] = set()
        for node in nodes:
            if node[0] not in seen_nodes:
                seen_nodes.add(node[0])
                deduped.append(node)
        # UNION ALL does not preserve a CTE's internal ordering.  Sort so
        # identical plans always return the same answer-node sequence.
        nodes = sorted(deduped, key=lambda node: node[0])

        # When support rows are present, only database-returned answer nodes with
        # at least one complete path may survive finalization.
        if support:
            supported = {path.answer_node_id for path in support}
            nodes = [node for node in nodes if node[0] in supported]
        return QueryResult(
            nodes=nodes,
            support=support,
            sql=sql,
            binds=dict(binds.values),
            truncated=False,
            edge_ids=legacy_edges,
        )

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
        ans_where = (
            "1=1"
            + _type_filter("n", final_type, binds)
            + _exclude_filter("n.node_id", exclude_ids, binds)
            + _require_edge_filter("n.node_id", require_edge, binds)
        )


        ctes.append(
            f"ans AS (\n  SELECT n.node_id, n.name, n.node_type\n"
            f"  FROM {last} lz JOIN pk_nodes n ON n.node_id = lz.node_id\n"
            f"  WHERE {ans_where}\n"
            f"  ORDER BY n.node_id\n)"
        )
        support_ctes, support_name = _backtrack_support(
            "l", "ans", names, steps, binds
        )
        ctes += support_ctes
        ctes.append(
            f"support_rows AS (\n  SELECT a.node_id answer_node_id, p.path_nodes, "
            f"p.path_edges, p.predicates, p.displays FROM ans a "
            f"JOIN {support_name} p ON p.answer_node_id = a.node_id\n)"
        )
        sql = (
            "WITH " + ",\n".join(ctes) + "\n"
            + _node_select() + "\nUNION ALL\n"
            + _support_select("support_rows", "complete expansion path")
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
        """Final nodes reachable by BOTH legs, with one full path per leg."""
        binds = _Binds()
        a_ids, a_steps = leg_a
        b_ids, b_steps = leg_b
        a_ctes, a_names = _levels("a", a_ids, a_steps, binds)
        b_ctes, b_names = _levels("b", b_ids, b_steps, binds)
        ans_where = (
            "1=1"
            + _type_filter("n", final_type, binds)
            + _exclude_filter("n.node_id", exclude_ids, binds)
            + _require_edge_filter("n.node_id", require_edge, binds)
        )
        ctes = a_ctes + b_ctes
        ctes.append(
            f"ans AS (\n  SELECT n.node_id, n.name, n.node_type\n"
            f"  FROM {a_names[-1]} ax JOIN {b_names[-1]} bx "
            f"ON ax.node_id = bx.node_id\n"
            f"  JOIN pk_nodes n ON n.node_id = ax.node_id\n"
            f"  WHERE {ans_where}\n"
            f"  ORDER BY n.node_id\n)"
        )
        ap_ctes, ap_name = _backtrack_support(
            "a", "ans", a_names, a_steps, binds
        )
        bp_ctes, bp_name = _backtrack_support(
            "b", "ans", b_names, b_steps, binds
        )
        ctes += ap_ctes + bp_ctes
        ctes.append(
            f"support_a AS (SELECT a.node_id answer_node_id, p.path_nodes, "
            f"p.path_edges, p.predicates, p.displays FROM ans a "
            f"JOIN {ap_name} p ON p.answer_node_id = a.node_id)"
        )
        ctes.append(
            f"support_b AS (SELECT a.node_id answer_node_id, p.path_nodes, "
            f"p.path_edges, p.predicates, p.displays FROM ans a "
            f"JOIN {bp_name} p ON p.answer_node_id = a.node_id)"
        )
        sql = (
            "WITH " + ",\n".join(ctes) + "\n"
            + _node_select() + "\nUNION ALL\n"
            + _support_select("support_a", "intersection leg 1")
            + "\nUNION ALL\n"
            + _support_select("support_b", "intersection leg 2")
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
        """Final nodes reachable by leg A but not leg B."""
        binds = _Binds()
        a_ctes, a_names = _levels("a", leg_a[0], leg_a[1], binds)
        b_ctes, b_names = _levels("b", leg_b[0], leg_b[1], binds)
        ap_ctes, ap_names = _path_levels("a", leg_a[0], leg_a[1], binds)
        ans_where = (
            f"n.node_id NOT IN (SELECT node_id FROM {b_names[-1]})"
            + _type_filter("n", final_type, binds)
            + _exclude_filter("n.node_id", exclude_ids, binds)
        )
        ctes = a_ctes + b_ctes + ap_ctes
        ctes.append(
            f"ans AS (\n  SELECT n.node_id, n.name, n.node_type\n"
            f"  FROM {a_names[-1]} lz JOIN pk_nodes n ON n.node_id = lz.node_id\n"
            f"  WHERE {ans_where}\n)"
        )
        ctes.append(
            f"support_rows AS (SELECT a.node_id answer_node_id, p.path_nodes, "
            f"p.path_edges, p.predicates, p.displays FROM ans a "
            f"JOIN {ap_names[-1]} p ON p.node_id = a.node_id)"
        )
        sql = (
            "WITH " + ",\n".join(ctes) + "\n" + _node_select()
            + "\nUNION ALL\n" + _support_select("support_rows", "positive path; exclusion composed in SQL")
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
        """Final nodes reachable by leg A but by none of the negative legs."""
        binds = _Binds()
        a_ctes, a_names = _levels("a", leg_a[0], leg_a[1], binds)
        ap_ctes, ap_names = _path_levels("a", leg_a[0], leg_a[1], binds)
        ctes = list(a_ctes) + ap_ctes
        not_in = ""
        for index, leg in enumerate(minus_legs):
            m_ctes, m_names = _levels(f"m{index}_", leg[0], leg[1], binds)
            ctes += m_ctes
            not_in += f" AND n.node_id NOT IN (SELECT node_id FROM {m_names[-1]})"
        ans_where = (
            "1=1" + not_in + _type_filter("n", final_type, binds)
            + _exclude_filter("n.node_id", exclude_ids, binds)
        )
        ctes.append(
            f"ans AS (\n  SELECT n.node_id, n.name, n.node_type\n"
            f"  FROM {a_names[-1]} lz JOIN pk_nodes n ON n.node_id = lz.node_id\n"
            f"  WHERE {ans_where}\n)"
        )
        ctes.append(
            f"support_rows AS (SELECT a.node_id answer_node_id, p.path_nodes, "
            f"p.path_edges, p.predicates, p.displays FROM ans a "
            f"JOIN {ap_names[-1]} p ON p.node_id = a.node_id)"
        )
        sql = (
            "WITH " + ",\n".join(ctes) + "\n" + _node_select()
            + "\nUNION ALL\n" + _support_select("support_rows", "positive path; all exclusions composed in SQL")
        )
        return self._execute(sql, binds)

    def edge_between(
        self, source_id: str, target_id: str, spec: RelSpec
    ) -> QueryResult:
        """Return the target and the exact connecting edge as one support path."""
        binds = _Binds()
        where = [
            f"e.source_node_id = :{binds.add(source_id)}",
            f"e.target_node_id = :{binds.add(target_id)}",
            f"e.predicate = :{binds.add(spec.predicate)}",
        ]
        if spec.displays:
            where.append(f"e.display_relation IN ({binds.add_list(spec.displays)})")
        sql = (
            "WITH matches AS (SELECT e.* FROM pk_edges e WHERE "
            + " AND ".join(where)
            + "), ans AS (SELECT n.node_id, n.name, n.node_type FROM matches m "
              "JOIN pk_nodes n ON n.node_id = m.target_node_id), "
              "support_rows AS (SELECT m.target_node_id answer_node_id, "
              "m.source_node_id || CHR(31) || m.target_node_id path_nodes, "
              "m.edge_id path_edges, m.predicate predicates, "
              "m.display_relation displays FROM matches m)\n"
            + _node_select() + "\nUNION ALL\n"
            + _support_select("support_rows", "direct edge")
        )
        return self._execute(sql, binds)

    def node_evidence(self, node_id: str) -> NodeEvidence:
        """Return node metadata and adjacent PrimeKG records in one read query."""
        sql = (
            "SELECT n.name, n.node_type, e.edge_id, e.target_node_id, e.predicate, "
            "e.display_relation, COUNT(*) OVER (PARTITION BY e.predicate, e.display_relation) rel_count, "
            "tn.name target_name, tn.node_type target_node_type "
            "FROM pk_nodes n LEFT JOIN pk_edges e ON e.source_node_id = n.node_id "
            "LEFT JOIN pk_nodes tn ON tn.node_id = e.target_node_id "
            "WHERE n.node_id = :node_id ORDER BY rel_count DESC NULLS LAST, e.edge_id "
            f"FETCH FIRST {MAX_EVIDENCE_EDGES} ROWS ONLY"
        )
        with self._conn.cursor() as cur:
            cur.execute(sql, {"node_id": node_id})
            rows = cur.fetchall()
        if not rows:
            return NodeEvidence(
                node_id=node_id, name=node_id, node_type="", summary=[], edges=[],
                sql=sql, binds={"node_id": node_id},
            )
        name, node_type = rows[0][0], rows[0][1]
        summary_map: dict[tuple[str, str], int] = {}
        edges: list[dict[str, str]] = []
        for _, _, edge_id, target_id, predicate, display, count, target_name, target_node_type in rows:
            if edge_id is None:
                continue
            summary_map[(predicate, display)] = int(count)
            edges.append({
                "edge_id": edge_id,
                "source_node_id": node_id,
                "target_node_id": target_id,
                "predicate": predicate,
                "display_relation": display,
                "target_name": target_name,
                "target_node_type": target_node_type,
            })
        summary = [(predicate, display, count) for (predicate, display), count in summary_map.items()]
        return NodeEvidence(
            node_id=node_id, name=name, node_type=node_type, summary=summary, edges=edges,
            sql=sql, binds={"node_id": node_id},
        )

    def ratio_shared(
        self,
        base_ids: list[str],
        *,
        numerator: int = 1,
        denominator: int = 2,
        final_type: tuple[str, ...] | None = None,
        exclude_ids: tuple[str, ...] = (),
    ) -> QueryResult:
        """Drugs whose shared-target fraction meets a threshold, composed in SQL."""
        binds = _Binds()
        tp = binds.add("drug_protein")
        roles = binds.add_list(TARGETS.displays)
        base_bind = binds.add_list(base_ids)
        ctes = [
            f"imt AS (SELECT DISTINCT e.target_node_id p FROM pk_edges e "
            f"WHERE e.source_node_id IN ({base_bind}) AND e.predicate = :{tp} "
            f"AND e.display_relation IN ({roles}))"
        ]
        tp2 = binds.add("drug_protein")
        roles2 = binds.add_list(TARGETS.displays)
        ctes.append(
            f"cand AS (SELECT DISTINCT e.target_node_id drug FROM pk_edges e JOIN imt "
            f"ON e.source_node_id = imt.p WHERE e.predicate = :{tp2} "
            f"AND e.display_relation IN ({roles2}) "
            f"AND e.target_node_id NOT IN ({binds.add_list(base_ids)}))"
        )
        tp3 = binds.add("drug_protein")
        roles3 = binds.add_list(TARGETS.displays)
        ctes.append(
            f"dt AS (SELECT DISTINCT c.drug, e.target_node_id p FROM pk_edges e "
            f"JOIN cand c ON e.source_node_id = c.drug WHERE e.predicate = :{tp3} "
            f"AND e.display_relation IN ({roles3}))"
        )
        ctes.append(
            "agg AS (SELECT drug, COUNT(DISTINCT p) total, "
            "COUNT(DISTINCT CASE WHEN p IN (SELECT p FROM imt) THEN p END) shared "
            "FROM dt GROUP BY drug)"
        )
        num = binds.add(numerator)
        den = binds.add(denominator)
        ctes.append(f"grp AS (SELECT drug node_id FROM agg WHERE total >= 1 AND shared * :{den} >= total * :{num})")
        ctes.append(
            "ans AS (SELECT n.node_id, n.name, n.node_type FROM grp JOIN pk_nodes n "
            "ON n.node_id = grp.node_id WHERE 1=1" + _type_filter("n", final_type, binds)
            + _exclude_filter("n.node_id", exclude_ids, binds) + ")"
        )
        path_ctes, path_names = _path_levels("r", base_ids, [TARGETS, TARGETS], binds)
        ctes += path_ctes
        ctes.append(
            f"support_rows AS (SELECT a.node_id answer_node_id, p.path_nodes, p.path_edges, "
            f"p.predicates, p.displays FROM ans a JOIN {path_names[-1]} p ON p.node_id = a.node_id)"
        )
        sql = ("WITH " + ",\n".join(ctes) + "\n" + _node_select()
               + "\nUNION ALL\n" + _support_select("support_rows", "shared-target ratio qualified in SQL"))
        return self._execute(sql, binds)

    def intersect_many(
        self,
        legs: list[tuple[list[str], list[RelSpec]]],
        *,
        final_type: tuple[str, ...] | None = None,
        exclude_ids: tuple[str, ...] = (),
    ) -> QueryResult:
        """Final nodes reachable by every leg, with one full path per leg."""
        if len(legs) < 2:
            raise ValueError("intersect_many needs >= 2 legs")
        binds = _Binds()
        ctes: list[str] = []
        lasts: list[str] = []
        path_lasts: list[str] = []
        for index, (ids, steps) in enumerate(legs):
            leg_ctes, names = _levels(f"g{index}_", ids, steps, binds)
            path_ctes, path_names = _path_levels(f"g{index}_", ids, steps, binds)
            ctes += leg_ctes + path_ctes
            lasts.append(names[-1])
            path_lasts.append(path_names[-1])
        joins = lasts[0]
        for last in lasts[1:]:
            joins += f"\n  JOIN {last} ON {last}.node_id = {lasts[0]}.node_id"
        ans_where = "1=1" + _type_filter("n", final_type, binds) + _exclude_filter("n.node_id", exclude_ids, binds)
        ctes.append(
            f"ans AS (\n  SELECT n.node_id, n.name, n.node_type\n"
            f"  FROM {joins}\n  JOIN pk_nodes n ON n.node_id = {lasts[0]}.node_id\n"
            f"  WHERE {ans_where}\n)"
        )
        support_selects: list[str] = []
        for index, path_last in enumerate(path_lasts):
            name = f"support_{index}"
            ctes.append(
                f"{name} AS (SELECT a.node_id answer_node_id, p.path_nodes, "
                f"p.path_edges, p.predicates, p.displays FROM ans a "
                f"JOIN {path_last} p ON p.node_id = a.node_id)"
            )
            support_selects.append(_support_select(name, f"intersection leg {index + 1}"))
        sql = "WITH " + ",\n".join(ctes) + "\n" + _node_select()
        for select in support_selects:
            sql += "\nUNION ALL\n" + select
        return self._execute(sql, binds)

    def symmetric_difference(
        self,
        leg_a: tuple[list[str], list[RelSpec]],
        leg_b: tuple[list[str], list[RelSpec]],
        *,
        final_type: tuple[str, ...] | None = None,
    ) -> QueryResult:
        """Final nodes reachable by exactly one leg (XOR)."""
        binds = _Binds()
        a_ctes, a_names = _levels("a", leg_a[0], leg_a[1], binds)
        b_ctes, b_names = _levels("b", leg_b[0], leg_b[1], binds)
        ap_ctes, ap_names = _path_levels("a", leg_a[0], leg_a[1], binds)
        bp_ctes, bp_names = _path_levels("b", leg_b[0], leg_b[1], binds)
        ctes = a_ctes + b_ctes + ap_ctes + bp_ctes
        ctes.append(f"ua AS (SELECT node_id FROM {a_names[-1]} WHERE node_id NOT IN (SELECT node_id FROM {b_names[-1]}))")
        ctes.append(f"ub AS (SELECT node_id FROM {b_names[-1]} WHERE node_id NOT IN (SELECT node_id FROM {a_names[-1]}))")
        ctes.append(
            "ans AS (SELECT n.node_id, n.name, n.node_type FROM "
            "(SELECT node_id FROM ua UNION SELECT node_id FROM ub) u "
            "JOIN pk_nodes n ON n.node_id = u.node_id WHERE 1=1"
            + _type_filter("n", final_type, binds) + ")"
        )
        ctes.append(
            f"support_a AS (SELECT a.node_id answer_node_id, p.path_nodes, p.path_edges, "
            f"p.predicates, p.displays FROM ans a JOIN ua ON ua.node_id = a.node_id "
            f"JOIN {ap_names[-1]} p ON p.node_id = a.node_id)"
        )
        ctes.append(
            f"support_b AS (SELECT a.node_id answer_node_id, p.path_nodes, p.path_edges, "
            f"p.predicates, p.displays FROM ans a JOIN ub ON ub.node_id = a.node_id "
            f"JOIN {bp_names[-1]} p ON p.node_id = a.node_id)"
        )
        sql = ("WITH " + ",\n".join(ctes) + "\n" + _node_select()
               + "\nUNION ALL\n" + _support_select("support_a", "xor leg 1")
               + "\nUNION ALL\n" + _support_select("support_b", "xor leg 2"))
        return self._execute(sql, binds)

    def rank_top(
        self,
        base_ids: list[str],
        steps: list[RelSpec],
        *,
        final_type: tuple[str, ...] | None = None,
        exclude_ids: tuple[str, ...] = (),
    ) -> QueryResult:
        """Peers sharing the most distinct intermediates; ranking stays in SQL."""
        if len(steps) != 2:
            raise ValueError("rank_top expects exactly two steps")
        binds = _Binds()
        ctes, names = _levels("l", base_ids, [steps[0]], binds)
        ctes.append(f"a1 AS (SELECT node_id shared, node_id cur FROM {names[-1]})")
        spec = steps[1]
        where = [f"e.predicate = :{binds.add(spec.predicate)}"]
        if spec.displays:
            where.append(f"e.display_relation IN ({binds.add_list(spec.displays)})")
        ctes.append(
            f"pairs AS (SELECT DISTINCT p.shared, e.target_node_id peer FROM pk_edges e "
            f"JOIN a1 p ON e.source_node_id = p.cur WHERE {' AND '.join(where)})"
        )
        ctes.append(
            "counts AS (SELECT peer, COUNT(DISTINCT shared) c FROM pairs WHERE 1=1"
            + _exclude_filter("peer", exclude_ids, binds) + " GROUP BY peer)"
        )
        ctes.append("grp AS (SELECT peer node_id FROM counts WHERE c = (SELECT MAX(c) FROM counts))")
        ctes.append(
            "ans AS (SELECT n.node_id, n.name, n.node_type FROM grp JOIN pk_nodes n "
            "ON n.node_id = grp.node_id WHERE 1=1" + _type_filter("n", final_type, binds) + ")"
        )
        path_ctes, path_names = _path_levels("rank", base_ids, steps, binds)
        ctes += path_ctes
        ctes.append(
            f"support_rows AS (SELECT a.node_id answer_node_id, p.path_nodes, p.path_edges, "
            f"p.predicates, p.displays FROM ans a JOIN {path_names[-1]} p ON p.node_id = a.node_id)"
        )
        sql = ("WITH " + ",\n".join(ctes) + "\n" + _node_select()
               + "\nUNION ALL\n" + _support_select("support_rows", "rank=1 qualified in SQL"))
        return self._execute(sql, binds)

    def count_compare(
        self,
        leg_a: tuple[list[str], list[RelSpec]],
        leg_b: tuple[list[str], list[RelSpec]],
        *,
        cmp: str = ">",
        final_type: tuple[str, ...] | None = None,
    ) -> QueryResult:
        """Keep nodes where leg-A count compares to leg-B count in SQL."""
        if cmp not in {">", ">=", "<", "<=", "="}:
            raise ValueError(f"bad cmp {cmp!r}")
        binds = _Binds()
        ctes: list[str] = []

        def leg_counts(prefix: str, leg: tuple[list[str], list[RelSpec]]) -> str:
            ids, steps = leg
            sub, names = _levels(f"{prefix}s", ids, [steps[0]], binds)
            ctes.extend(sub)
            ctes.append(f"{prefix}a AS (SELECT node_id counted, node_id cur FROM {names[-1]})")
            spec = steps[1]
            where = [f"e.predicate = :{binds.add(spec.predicate)}"]
            if spec.displays:
                where.append(f"e.display_relation IN ({binds.add_list(spec.displays)})")
            ctes.append(
                f"{prefix}p AS (SELECT DISTINCT p.counted, e.target_node_id grp FROM pk_edges e "
                f"JOIN {prefix}a p ON e.source_node_id = p.cur WHERE {' AND '.join(where)})"
            )
            ctes.append(f"{prefix}c AS (SELECT grp, COUNT(DISTINCT counted) c FROM {prefix}p GROUP BY grp)")
            return f"{prefix}c"

        ca = leg_counts("x", leg_a)
        cb = leg_counts("y", leg_b)
        ctes.append(
            f"grp AS (SELECT {ca}.grp node_id FROM {ca} LEFT JOIN {cb} ON {cb}.grp = {ca}.grp "
            f"WHERE {ca}.c {cmp} NVL({cb}.c, 0))"
        )
        ctes.append(
            "ans AS (SELECT n.node_id, n.name, n.node_type FROM grp JOIN pk_nodes n "
            "ON n.node_id = grp.node_id WHERE 1=1" + _type_filter("n", final_type, binds) + ")"
        )
        ap, an = _path_levels("cmpa", leg_a[0], leg_a[1], binds)
        bp, bn = _path_levels("cmpb", leg_b[0], leg_b[1], binds)
        ctes += ap + bp
        ctes.append(f"support_a AS (SELECT a.node_id answer_node_id, p.path_nodes, p.path_edges, p.predicates, p.displays FROM ans a JOIN {an[-1]} p ON p.node_id=a.node_id)")
        # A leg-B path may not exist when NVL(count,0) is the compared value.
        ctes.append(f"support_b AS (SELECT a.node_id answer_node_id, p.path_nodes, p.path_edges, p.predicates, p.displays FROM ans a JOIN {bn[-1]} p ON p.node_id=a.node_id)")
        sql = ("WITH " + ",\n".join(ctes) + "\n" + _node_select()
               + "\nUNION ALL\n" + _support_select("support_a", "count comparison leg 1")
               + "\nUNION ALL\n" + _support_select("support_b", "count comparison leg 2 when present"))
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
        """Drugs connected by qualifying target-PPI-target bridge counts."""
        if op not in {">=", ">", "=", "<=", "<"}:
            raise ValueError(f"bad op {op!r}")
        binds = _Binds()
        base = _base_cte("base", base_ids, binds)
        tp = binds.add("drug_protein")
        roles = binds.add_list(TARGETS.displays)
        ppi_p = binds.add("protein_protein")
        ppi_d = binds.add("ppi")
        tp2 = binds.add("drug_protein")
        roles2 = binds.add_list(TARGETS.displays)
        ctes = [base]
        ctes.append(
            f"pa AS (SELECT DISTINCT b.node_id base_id, e.target_node_id pa, e.edge_id e1, "
            f"e.predicate p1, e.display_relation d1 "
            f"FROM pk_edges e JOIN base b ON e.source_node_id=b.node_id "
            f"WHERE e.predicate=:{tp} AND e.display_relation IN ({roles}))"
        )
        ctes.append(
            f"br AS (SELECT DISTINCT pa.base_id, pa.pa, e.target_node_id pb, pa.e1, e.edge_id e2, "
            f"pa.p1, pa.d1, e.predicate p2, e.display_relation d2 "
            f"FROM pk_edges e JOIN pa ON e.source_node_id=pa.pa "
            f"WHERE e.predicate=:{ppi_p} AND e.display_relation IN (:{ppi_d}))"
        )
        ctes.append(
            f"bridges AS (SELECT DISTINCT br.base_id, br.pa, br.pb, e.target_node_id drug, "
            f"br.e1, br.e2, e.edge_id e3, br.p1, br.p2, e.predicate p3, "
            f"br.d1, br.d2, e.display_relation d3 FROM pk_edges e JOIN br ON e.source_node_id=br.pb "
            f"WHERE e.predicate=:{tp2} AND e.display_relation IN ({roles2}))"
        )
        ctes.append(
            f"grp AS (SELECT drug node_id FROM bridges WHERE 1=1"
            + _exclude_filter("drug", tuple(base_ids) + exclude_ids, binds)
            + f" GROUP BY drug HAVING COUNT(DISTINCT pa || '|' || pb) {op} :{binds.add(n)})"
        )
        ctes.append(
            "ans AS (SELECT nd.node_id, nd.name, nd.node_type FROM grp JOIN pk_nodes nd "
            "ON nd.node_id=grp.node_id WHERE 1=1" + _type_filter("nd", final_type, binds) + ")"
        )
        ctes.append(
            "support_ranked AS (SELECT b.drug answer_node_id, "
            "b.base_id || CHR(31) || b.pa || CHR(31) || b.pb || CHR(31) || b.drug path_nodes, "
            "b.e1 || CHR(31) || b.e2 || CHR(31) || b.e3 path_edges, "
            "b.p1 || CHR(31) || b.p2 || CHR(31) || b.p3 predicates, "
            "b.d1 || CHR(31) || b.d2 || CHR(31) || b.d3 displays, "
            "ROW_NUMBER() OVER (PARTITION BY b.drug ORDER BY b.e1,b.e2,b.e3) rn "
            "FROM bridges b JOIN ans a ON a.node_id=b.drug)"
        )
        ctes.append("support_rows AS (SELECT answer_node_id,path_nodes,path_edges,predicates,displays FROM support_ranked WHERE rn=1)")
        sql = ("WITH " + ",\n".join(ctes) + "\n" + _node_select()
               + "\nUNION ALL\n" + _support_select("support_rows", "bridge threshold qualified in SQL"))
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
        """Group/count threshold composed in SQL with an answer-scoped path."""
        if op not in {">=", ">", "=", "<=", "<"}:
            raise ValueError(f"bad op {op!r}")
        if not (0 <= group_level <= len(steps) and 0 <= distinct_level <= len(steps)):
            raise ValueError("count levels exceed chain depth")
        binds = _Binds()
        start_level = min(group_level, distinct_level)
        end_level = max(group_level, distinct_level)
        ctes, names = _levels("l", base_ids, list(steps[:start_level]), binds)
        ctes.append(f"a{start_level} AS (SELECT node_id anchor, node_id cur FROM {names[-1]})")
        for level in range(start_level + 1, end_level + 1):
            spec = steps[level - 1]
            where = [f"e.predicate = :{binds.add(spec.predicate)}"]
            if spec.displays:
                where.append(f"e.display_relation IN ({binds.add_list(spec.displays)})")
            ctes.append(
                f"a{level} AS (SELECT DISTINCT p.anchor, e.target_node_id cur FROM pk_edges e "
                f"JOIN a{level-1} p ON e.source_node_id=p.cur WHERE {' AND '.join(where)})"
            )
        pair = f"a{end_level}"
        group_col = "anchor" if group_level == start_level else "cur"
        distinct_col = "cur" if group_col == "anchor" else "anchor"
        member_filter = ""
        if member_of is not None:
            m_ctes, m_names = _levels("m", member_of[0], member_of[1], binds)
            ctes += m_ctes
            member_filter = f" WHERE {group_col} IN (SELECT node_id FROM {m_names[-1]})"
        ctes.append(
            f"grp AS (SELECT {group_col} node_id FROM {pair}{member_filter} "
            f"GROUP BY {group_col} HAVING COUNT(DISTINCT {distinct_col}) {op} :{binds.add(n)})"
        )
        ctes.append(
            "ans AS (SELECT nd.node_id, nd.name, nd.node_type FROM grp JOIN pk_nodes nd "
            "ON nd.node_id=grp.node_id WHERE 1=1"
            + _type_filter("nd", final_type, binds)
            + _exclude_filter("grp.node_id", exclude_ids, binds) + ")"
        )
        path_ctes, path_names = _path_levels("cnt", base_ids, list(steps[:group_level]), binds)
        ctes += path_ctes
        ctes.append(
            f"support_rows AS (SELECT a.node_id answer_node_id, p.path_nodes, p.path_edges, "
            f"p.predicates, p.displays FROM ans a JOIN {path_names[-1]} p ON p.node_id=a.node_id)"
        )
        sql = ("WITH " + ",\n".join(ctes) + "\n" + _node_select()
               + "\nUNION ALL\n" + _support_select("support_rows", "count threshold qualified in SQL"))
        return self._execute(sql, binds)
