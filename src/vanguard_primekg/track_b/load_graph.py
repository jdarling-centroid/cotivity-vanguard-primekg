"""Idempotently load exported Track B graph artifacts into local Oracle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ..db import connect
from ..load_primekg import apply_schema

_NODE_MERGE = """
MERGE INTO mh_nodes t
USING (SELECT :node_id node_id FROM dual) s ON (t.node_id=s.node_id)
WHEN MATCHED THEN UPDATE SET
  t.node_type=:node_type,t.label=:label,t.text_content=:text_content,
  t.provenance_json=:provenance_json,t.attributes_json=:attributes_json
WHEN NOT MATCHED THEN INSERT
  (node_id,node_type,label,text_content,provenance_json,attributes_json)
VALUES
  (:node_id,:node_type,:label,:text_content,:provenance_json,:attributes_json)
"""
_EDGE_MERGE = """
MERGE INTO mh_edges t
USING (SELECT :edge_id edge_id FROM dual) s ON (t.edge_id=s.edge_id)
WHEN NOT MATCHED THEN INSERT
  (edge_id,subject_id,predicate,object_id,provenance_json)
VALUES
  (:edge_id,:subject_id,:predicate,:object_id,:provenance_json)
"""


def _sha256(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()


def load_graph(nodes_path: Path, edges_path: Path, *, batch_size: int = 2000) -> tuple[int, int]:
    fingerprint = _sha256([nodes_path, edges_path])
    with connect() as conn:
        repo_root = Path(__file__).resolve().parents[3]
        apply_schema(conn, repo_root / "schemas" / "trackb-o26.sql")
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT nodes_loaded,edges_loaded FROM mh_load_journal "
                "WHERE artifact_sha256=:fingerprint AND status='completed'",
                {"fingerprint": fingerprint},
            )
            row = cursor.fetchone()
            if row:
                return int(row[0]), int(row[1])

            node_batch: list[dict] = []
            node_count = 0
            for line in nodes_path.read_text(encoding="utf-8").splitlines():
                item = json.loads(line)
                node_batch.append(
                    {
                        "node_id": item["node_id"],
                        "node_type": item["type"],
                        "label": item["label"][:2000],
                        "text_content": item.get("text"),
                        "provenance_json": json.dumps(item["provenance"], separators=(",", ":")),
                        "attributes_json": (
                            json.dumps(item["attributes"], separators=(",", ":"))
                            if item.get("attributes") is not None
                            else None
                        ),
                    }
                )
                if len(node_batch) >= batch_size:
                    cursor.executemany(_NODE_MERGE, node_batch)
                    conn.commit()
                    node_count += len(node_batch)
                    node_batch.clear()
            if node_batch:
                cursor.executemany(_NODE_MERGE, node_batch)
                conn.commit()
                node_count += len(node_batch)

            edge_batch: list[dict] = []
            edge_count = 0
            for line in edges_path.read_text(encoding="utf-8").splitlines():
                item = json.loads(line)
                edge_batch.append(
                    {
                        "edge_id": item["edge_id"],
                        "subject_id": item["subject"],
                        "predicate": item["predicate"],
                        "object_id": item["object"],
                        "provenance_json": json.dumps(item["provenance"], separators=(",", ":")),
                    }
                )
                if len(edge_batch) >= batch_size:
                    cursor.executemany(_EDGE_MERGE, edge_batch)
                    conn.commit()
                    edge_count += len(edge_batch)
                    edge_batch.clear()
            if edge_batch:
                cursor.executemany(_EDGE_MERGE, edge_batch)
                conn.commit()
                edge_count += len(edge_batch)
            try:
                cursor.execute("BEGIN CTX_DDL.SYNC_INDEX('MH_NODES_TEXT_IX'); END;")
            except Exception:
                # ON COMMIT synchronization is configured; an explicit sync is
                # only an availability optimization for the immediate run.
                pass
            cursor.execute(
                "MERGE INTO mh_load_journal t USING "
                "(SELECT :fingerprint artifact_sha256 FROM dual) s "
                "ON (t.artifact_sha256=s.artifact_sha256) "
                "WHEN NOT MATCHED THEN INSERT "
                "(artifact_sha256,nodes_loaded,edges_loaded,status) "
                "VALUES (:fingerprint,:nodes,:edges,'completed')",
                {"fingerprint": fingerprint, "nodes": node_count, "edges": edge_count},
            )
            conn.commit()
            return node_count, edge_count
