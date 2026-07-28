"""Importer for the PrimeKG knowledge-graph dataset.

PrimeKG ships as a single edge-list CSV/TSV (``kg.csv``) with the columns::

    relation, display_relation,
    x_index, x_id, x_type, x_name, x_source,
    y_index, y_id, y_type, y_name, y_source

Each row is a relationship between two nodes. This importer maps:

* PrimeKG nodes -> ``nodes`` rows with ``node_type = 'fragment'``. The PrimeKG node
  type/name/source are preserved in ``structural_data`` (``type``, ``label``,
  ``normalized_code``, ``provenance``).
* PrimeKG relationships -> ``edges`` rows. The constrained ``relationship_type`` column
  holds ``CONTAINS`` (for hierarchical ``parent-child`` relations) or ``DERIVED_FROM``
  (everything else); the original PrimeKG predicate is preserved in ``edge_data.predicate``.

Writes are batched with ``cursor.executemany`` (see ``Repository.bulk_create_*``).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
import time
from collections.abc import Iterator

from ..adapters.factory import get_embedder
from ..config import load_config
from ..db import connection, init_pool
from ..logging import configure_logging, get_logger
from ..repository import Repository
from .common import (
    index_reference_fragments,
    prepare_reference_source,
    sync_fragment_text_index,
)

log = get_logger("importers.primekg")

# PrimeKG's edge-list can be very wide; keep the CSV field size generous.
csv.field_size_limit(min(sys.maxsize, 2**31 - 1))


def _detect_delimiter(path: str) -> str:
    if path.lower().endswith((".tsv", ".tab")):
        return "\t"
    with open(path, newline="", encoding="utf-8") as f:
        first = f.readline()
    return "\t" if first.count("\t") > first.count(",") else ","


def _iter_rows(path: str, delimiter: str, limit: int | None) -> Iterator[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for i, row in enumerate(reader):
            if limit is not None and i >= limit:
                return
            yield row


def _node_row(index: str, node_id: str, node_type: str, name: str, source: str, code: str,
              reference_source_id: str, dataset: str) -> dict:
    normalized_code: dict | None = None
    if code or source:
        normalized_code = {"system": source or None, "code": code or None, "display": name or None}
    structural_data: dict = {
        "type": node_type or "Entity",
        "label": name,
        "provenance": {"doc_id": dataset, "source_index": index},
    }
    if normalized_code is not None:
        structural_data["normalized_code"] = normalized_code
    return {
        "node_id": node_id,
        "node_type": "reference_entity",
        "reference_source_id": reference_source_id,
        "status": "ready",
        "structural_data": structural_data,
    }


def _flush_nodes(
    repo: Repository, conn, batch: list[dict], fragments: list[dict], skipped: list[int]
) -> None:
    if not batch:
        return
    errors = repo.bulk_create_nodes(batch)
    conn.commit()
    skipped[0] += len(errors)
    batch.clear()
    if fragments:
        skipped[1] += len(repo.bulk_create_fragments(fragments))
        conn.commit()
        fragments.clear()


def _flush_edges(repo: Repository, conn, batch: list[dict], skipped: list[int]) -> None:
    if not batch:
        return
    errors = repo.bulk_create_edges(batch)
    conn.commit()
    skipped[0] += len(errors)
    batch.clear()


def _reference_edge_type_id(dataset: str, relation: str, display: str) -> int:
    """Return a stable compact Oracle NUMBER for one relationship definition."""
    digest = hashlib.sha256(f"{dataset}\0{relation}\0{display}".encode()).hexdigest()
    return int(digest[:12], 16)


def import_primekg(
    input_path: str,
    reference_source_id: str,
    dataset: str,
    batch_size: int,
    limit: int | None,
) -> tuple[int, int]:
    """Import PrimeKG. Returns ``(nodes_written, edges_written)`` (best-effort counts)."""
    delimiter = _detect_delimiter(input_path)
    node_count = 0
    edge_count = 0
    with connection() as conn:
        repo = Repository(conn)
        _checksum, should_import = prepare_reference_source(
            repo, reference_source_id=reference_source_id, name="PrimeKG",
            source_kind="knowledge_graph", version="2.1", source_path=input_path,
        )
        conn.commit()
        if not should_import:
            source = repo.get_reference_source(reference_source_id)
            return (source.node_count, source.edge_count) if source else (0, 0)

        # Pass 1: nodes (deduplicated by node_id so both endpoints of every edge exist
        # before any edge is inserted, preserving referential integrity).
        seen: set[str] = set()
        relationship_definitions: set[tuple[str, str]] = set()
        node_batch: list[dict] = []
        fragment_batch: list[dict] = []
        node_skipped = [0, 0]
        for row in _iter_rows(input_path, delimiter, limit):
            relationship_definitions.add(
                (
                    (row.get("relation") or "").strip() or "related_to",
                    (row.get("display_relation") or "").strip(),
                )
            )
            for side in ("x", "y"):
                index = (row.get(f"{side}_index") or "").strip()
                if not index:
                    continue
                node_id = f"pk_n_{index}"
                if node_id in seen:
                    continue
                seen.add(node_id)
                node_batch.append(
                    _node_row(
                        index=index,
                        node_id=node_id,
                        node_type=(row.get(f"{side}_type") or "").strip(),
                        name=(row.get(f"{side}_name") or "").strip(),
                        source=(row.get(f"{side}_source") or "").strip(),
                        code=(row.get(f"{side}_id") or "").strip(),
                        reference_source_id=reference_source_id,
                        dataset=dataset,
                    )
                )
                label = (row.get(f"{side}_name") or "").strip()
                code = (row.get(f"{side}_id") or "").strip()
                source = (row.get(f"{side}_source") or "").strip()
                search_text = " ".join(value for value in (label, code, source) if value)
                fragment_batch.append(
                    {
                        "fragment_id": f"pk_fragment_{index}", "node_id": node_id,
                        "fragment_type": "reference_entity_name",
                        "fragment_text": search_text, "normalized_text": None,
                        "processor": "primekg_importer", "processor_version": "2.1",
                    }
                )
                node_count += 1
                if len(node_batch) >= batch_size:
                    _flush_nodes(repo, conn, node_batch, fragment_batch, node_skipped)
        _flush_nodes(repo, conn, node_batch, fragment_batch, node_skipped)

        type_rows = [
            {
                "reference_edge_type_id": _reference_edge_type_id(
                    dataset, relation, display
                ),
                "reference_source_id": reference_source_id,
                "predicate": relation,
                "display_relation": display or None,
            }
            for relation, display in sorted(relationship_definitions)
        ]
        # Duplicate definitions are expected when resuming an interrupted load.
        repo.bulk_create_reference_edge_types(type_rows)
        conn.commit()

        # Pass 2: edges.
        edge_batch: list[dict] = []
        edge_skipped = [0]
        for row in _iter_rows(input_path, delimiter, limit):
            x_index = (row.get("x_index") or "").strip()
            y_index = (row.get("y_index") or "").strip()
            if not x_index or not y_index:
                continue
            relation = (row.get("relation") or "").strip()
            display = (row.get("display_relation") or "").strip()
            hierarchical = display.lower() in {"parent-child", "parent_child"}
            rel_type = "CONTAINS" if hierarchical else "RELATED_TO"
            digest = hashlib.sha256(f"{relation}\0{display}".encode()).hexdigest()[:12]
            edge_id = f"pk_e_{x_index}_{y_index}_{digest}"
            edge_batch.append(
                {
                    "edge_id": edge_id,
                    "source_node_id": f"pk_n_{x_index}",
                    "target_node_id": f"pk_n_{y_index}",
                    "relationship_type": rel_type,
                    "reference_edge_type_id": _reference_edge_type_id(
                        dataset, relation or "related_to", display
                    ),
                    "edge_data": None,
                }
            )
            edge_count += 1
            if len(edge_batch) >= batch_size:
                _flush_edges(repo, conn, edge_batch, edge_skipped)
        _flush_edges(repo, conn, edge_batch, edge_skipped)
        conn.commit()
        log.info("importers.primekg.text_index_sync_started", reference_source_id=reference_source_id)
        sync_fragment_text_index(repo)
        log.info("importers.primekg.text_index_sync_completed", reference_source_id=reference_source_id)
        log.info("importers.primekg.embedding_started", reference_source_id=reference_source_id)
        indexed = index_reference_fragments(
            repo, reference_source_id, get_embedder(load_config())
        )
        log.info(
            "importers.primekg.embedding_completed",
            reference_source_id=reference_source_id,
            embeddings_created=indexed,
        )
        # On a resumed import, skipped rows include records committed by the
        # previous attempt. Read authoritative totals instead of reporting only
        # the rows inserted during this process.
        count_started = time.monotonic()
        log.info(
            "importers.primekg.authoritative_count_started",
            reference_source_id=reference_source_id,
        )
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM nodes
                      WHERE reference_source_id = :source_id),
                    (SELECT COUNT(*) FROM fragments f JOIN nodes n
                       ON n.node_id = f.node_id
                      WHERE n.reference_source_id = :source_id),
                    (SELECT COUNT(*) FROM edges e JOIN nodes en
                       ON en.node_id = e.source_node_id
                      WHERE en.reference_source_id = :source_id)
                FROM dual
                """,
                {"source_id": reference_source_id},
            )
            actual_nodes, actual_fragments, actual_edges = cursor.fetchone()
        log.info(
            "importers.primekg.authoritative_count_completed",
            reference_source_id=reference_source_id,
            elapsed_seconds=round(time.monotonic() - count_started, 3),
            nodes=actual_nodes,
            fragments=actual_fragments,
            edges=actual_edges,
        )
        log.info("importers.primekg.ready_transition_started", reference_source_id=reference_source_id)
        repo.update_reference_source(
            reference_source_id, "ready", node_count=actual_nodes,
            edge_count=actual_edges, fragment_count=actual_fragments,
        )
        conn.commit()
        log.info("importers.primekg.ready_transition_completed", reference_source_id=reference_source_id)

    log.info(
        "importers.primekg.complete",
        nodes=node_count,
        edges=edge_count,
        nodes_skipped=node_skipped[0],
        edges_skipped=edge_skipped[0],
        reference_source_id=reference_source_id,
    )
    return actual_nodes, actual_edges


def main() -> None:
    parser = argparse.ArgumentParser(description="Import the PrimeKG dataset into the graph.")
    parser.add_argument("--input", required=True, help="Path to PrimeKG kg.csv / kg.tsv")
    parser.add_argument(
        "--reference-source-id", default="primekg", help="Reference-source registry id"
    )
    parser.add_argument("--dataset", default="primekg", help="Dataset name recorded in provenance")
    parser.add_argument("--batch-size", type=int, default=5000, help="executemany batch size")
    parser.add_argument("--limit", type=int, default=None, help="Max rows to read (for testing)")
    args = parser.parse_args()

    configure_logging()
    cfg = load_config()
    if cfg.database is None:
        log.error("importers.primekg.no_database_config")
        sys.exit(1)
    init_pool(cfg.database)
    try:
        import_primekg(
            input_path=args.input, reference_source_id=args.reference_source_id,
            dataset=args.dataset, batch_size=args.batch_size, limit=args.limit,
        )
    except Exception:
        with connection() as conn:
            Repository(conn).update_reference_source(args.reference_source_id, "failed")
            conn.commit()
        raise


if __name__ == "__main__":
    main()
