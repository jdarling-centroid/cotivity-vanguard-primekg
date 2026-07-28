"""Idempotent, resumable PrimeKG loader.

Streams ``kg.csv`` once, accumulating distinct nodes in memory (~129k) and
MERGE-ing edges to the DB in batches. MERGE on the primary keys means a re-run
never double-inserts. A journal row (keyed by source fingerprint + relation
subset) makes a completed load a no-op.

Usage::

    python -m vanguard_primekg.load_primekg                 # selected source relations
    python -m vanguard_primekg.load_primekg --relations all # all source facts, materialized both ways
    python -m vanguard_primekg.load_primekg --vectors       # also embed names
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sys
import time
from pathlib import Path

from .oracle_compat import oracledb

from .config import Settings, load_settings
from .db import connect
from .logging import get_logger
from .relations import SUBSET_PREDICATES

log = get_logger("load")

csv.field_size_limit(min(sys.maxsize, 2**31 - 1))

_TOLERATED_ORA = {955, 1408}  # name already used; column list already indexed
_WS = re.compile(r"\s+")
_LOAD_FORMAT_VERSION = "bidirectional-v2"


def normalize_name(value: str) -> str:
    return _WS.sub(" ", (value or "").strip().casefold())


def edge_id(x_index: str, y_index: str, predicate: str, display: str) -> str:
    digest = hashlib.sha1(f"{predicate}\0{display}".encode()).hexdigest()[:8]
    return f"pk_e_{x_index}_{y_index}_{digest}"


def directed_edge_rows(
    x_index: str, y_index: str, predicate: str, display: str
) -> list[dict[str, str | None]]:
    """Return deterministic forward and reverse records for one PrimeKG fact."""
    rows: list[dict[str, str | None]] = []
    seen: set[str] = set()
    for source, target in ((x_index, y_index), (y_index, x_index)):
        eid = edge_id(source, target, predicate, display)
        if eid in seen:  # self-loop
            continue
        seen.add(eid)
        rows.append(
            {
                "edge_id": eid,
                "source_node_id": f"pk_n_{source}",
                "target_node_id": f"pk_n_{target}",
                "predicate": predicate,
                "display_relation": display or None,
            }
        )
    return rows


def _fingerprint(path: Path) -> str:
    """Cheap content fingerprint: size + head + tail (avoids hashing ~1 GB)."""
    size = path.stat().st_size
    h = hashlib.sha256()
    h.update(str(size).encode())
    with path.open("rb") as f:
        h.update(f.read(65536))
        if size > 65536:
            f.seek(-65536, 2)
            h.update(f.read(65536))
    return h.hexdigest()[:32]


def _split_statements(sql: str) -> list[str]:
    statements: list[str] = []
    buf: list[str] = []
    for line in sql.splitlines():
        if line.strip() == "/":
            stmt = "\n".join(buf).strip()
            if stmt:
                statements.append(stmt)
            buf = []
        else:
            buf.append(line)
    tail = "\n".join(buf).strip()
    if tail:
        statements.append(tail)
    return statements


def apply_schema(conn: oracledb.Connection, sql_path: Path) -> None:
    statements = _split_statements(sql_path.read_text(encoding="utf-8"))
    with conn.cursor() as cur:
        for stmt in statements:
            try:
                cur.execute(stmt)
            except oracledb.DatabaseError as exc:
                (error,) = exc.args
                if getattr(error, "code", None) in _TOLERATED_ORA:
                    continue
                log.error("DDL failed: %s\n%s", error.message, stmt[:120])
                raise
    conn.commit()
    log.info("schema applied (%d statements)", len(statements))


_NODE_MERGE = """
MERGE INTO pk_nodes t
USING (SELECT :node_id AS node_id FROM dual) s
ON (t.node_id = s.node_id)
WHEN NOT MATCHED THEN
  INSERT (node_id, node_index, node_type, name, source, code, name_norm)
  VALUES (:node_id, :node_index, :node_type, :name, :source, :code, :name_norm)
"""

_EDGE_MERGE = """
MERGE INTO pk_edges t
USING (SELECT :edge_id AS edge_id FROM dual) s
ON (t.edge_id = s.edge_id)
WHEN NOT MATCHED THEN
  INSERT (edge_id, source_node_id, target_node_id, predicate, display_relation)
  VALUES (:edge_id, :source_node_id, :target_node_id, :predicate, :display_relation)
"""


def _journal_completed(conn: oracledb.Connection, fingerprint: str, relations: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM pk_load_journal "
            "WHERE kg_checksum = :c AND relations = :r AND status = 'completed' "
            "FETCH FIRST 1 ROWS ONLY",
            c=fingerprint,
            r=relations,
        )
        return cur.fetchone() is not None


def load(
    input_path: Path,
    *,
    relations: tuple[str, ...] | None,
    batch_size: int = 5000,
    limit: int | None = None,
    with_vectors: bool = False,
    force: bool = False,
    settings: Settings | None = None,
) -> tuple[int, int]:
    settings = settings or load_settings()
    relation_filter = set(relations) if relations else None
    relation_scope = "all" if relation_filter is None else ",".join(sorted(relation_filter))
    relations_label = f"{_LOAD_FORMAT_VERSION}:{relation_scope}"
    fingerprint = _fingerprint(input_path)

    with connect(settings) as conn:
        apply_schema(conn, settings.repo_root / "schemas" / "primekg-o26.sql")

        if not force and _journal_completed(conn, fingerprint, relations_label):
            log.info("load already completed for this source+relations; skipping")
            return _counts(conn)

        nodes: dict[str, dict] = {}
        edge_batch: list[dict] = []
        edges_seen: set[str] = set()
        edges_written = 0
        started = time.monotonic()

        with input_path.open(newline="", encoding="utf-8") as f, conn.cursor() as cur:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if limit is not None and i >= limit:
                    break
                predicate = (row.get("relation") or "").strip()
                if relation_filter is not None and predicate not in relation_filter:
                    continue
                display = (row.get("display_relation") or "").strip()
                x_index = (row.get("x_index") or "").strip()
                y_index = (row.get("y_index") or "").strip()
                if not x_index or not y_index:
                    continue

                for side, index in (("x", x_index), ("y", y_index)):
                    node_id = f"pk_n_{index}"
                    if node_id not in nodes:
                        name = (row.get(f"{side}_name") or "").strip()
                        nodes[node_id] = {
                            "node_id": node_id,
                            "node_index": int(index),
                            "node_type": ((row.get(f"{side}_type") or "").strip() or None),
                            "name": (name[:2000] or None),
                            "source": ((row.get(f"{side}_source") or "").strip()[:64] or None),
                            "code": ((row.get(f"{side}_id") or "").strip()[:512] or None),
                            "name_norm": (normalize_name(name)[:1000] or None),
                        }

                for edge in directed_edge_rows(x_index, y_index, predicate, display):
                    eid = str(edge["edge_id"])
                    if eid in edges_seen:
                        continue
                    edges_seen.add(eid)
                    edge_batch.append(edge)
                    if len(edge_batch) >= batch_size:
                        cur.executemany(_EDGE_MERGE, edge_batch)
                        conn.commit()
                        edges_written += len(edge_batch)
                        edge_batch.clear()
                        if edges_written % (batch_size * 20) == 0:
                            log.info("directed edges merged: %d", edges_written)

            if edge_batch:
                cur.executemany(_EDGE_MERGE, edge_batch)
                conn.commit()
                edges_written += len(edge_batch)

            log.info("merging %d distinct nodes", len(nodes))
            node_rows = list(nodes.values())
            for start in range(0, len(node_rows), batch_size):
                cur.executemany(_NODE_MERGE, node_rows[start : start + batch_size])
                conn.commit()

        if with_vectors:
            _embed_nodes(conn, batch_size=512)

        _record_journal(conn, fingerprint, relations_label, len(nodes), edges_written)
        elapsed = time.monotonic() - started
        log.info(
            "load complete: %d nodes, %d directed edges in %.1fs", len(nodes), edges_written, elapsed
        )
        return len(nodes), edges_written


def _counts(conn: oracledb.Connection) -> tuple[int, int]:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM pk_nodes")
        (n,) = cur.fetchone()
        cur.execute("SELECT COUNT(*) FROM pk_edges")
        (e,) = cur.fetchone()
    return n, e


def _record_journal(
    conn: oracledb.Connection, fingerprint: str, relations: str, nodes: int, edges: int
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO pk_load_journal (kg_checksum, relations, nodes_loaded, "
            "edges_loaded, status) VALUES (:c, :r, :n, :e, 'completed')",
            c=fingerprint,
            r=relations,
            n=nodes,
            e=edges,
        )
    conn.commit()


def _embed_nodes(conn: oracledb.Connection, *, batch_size: int) -> None:
    from sentence_transformers import SentenceTransformer  # lazy: optional extra

    model = SentenceTransformer("all-MiniLM-L6-v2")
    with conn.cursor() as read_cur, conn.cursor() as write_cur:
        read_cur.execute(
            "SELECT node_id, name FROM pk_nodes WHERE name_vec IS NULL AND name IS NOT NULL"
        )
        total = 0
        while True:
            rows = read_cur.fetchmany(batch_size)
            if not rows:
                break
            ids = [r[0] for r in rows]
            vecs = model.encode([r[1] for r in rows], normalize_embeddings=True)
            write_cur.executemany(
                "UPDATE pk_nodes SET name_vec = :vec WHERE node_id = :nid",
                [{"vec": list(map(float, v)), "nid": nid} for nid, v in zip(ids, vecs)],
            )
            conn.commit()
            total += len(rows)
            log.info("embedded %d node names", total)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Load PrimeKG into Oracle 26ai.")
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Path to kg.csv (default: data/datasets/primekg/kg.csv).",
    )
    parser.add_argument(
        "--relations",
        default="subset",
        help="'subset' (default), 'all', or a comma list of predicates.",
    )
    parser.add_argument("--batch-size", type=int, default=5000)
    parser.add_argument("--limit", type=int, default=None, help="Row cap (debug).")
    parser.add_argument("--vectors", action="store_true", help="Also embed node names.")
    parser.add_argument("--force", action="store_true", help="Ignore the load journal.")
    args = parser.parse_args(argv)

    settings = load_settings()
    input_path = args.input or (settings.repo_root / "data" / "datasets" / "primekg" / "kg.csv")

    if args.relations == "subset":
        relations: tuple[str, ...] | None = SUBSET_PREDICATES
    elif args.relations == "all":
        relations = None
    else:
        relations = tuple(r.strip() for r in args.relations.split(",") if r.strip())

    load(
        input_path,
        relations=relations,
        batch_size=args.batch_size,
        limit=args.limit,
        with_vectors=args.vectors,
        force=args.force,
        settings=settings,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
