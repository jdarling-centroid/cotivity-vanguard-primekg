from __future__ import annotations

import json

from vanguard_primekg.track_b import build_graph


def test_track_b_graph_is_stable_connected_and_provenance_complete(tmp_path) -> None:
    corpus = [
        {
            "title": "Apple meets OpenAI",
            "author": "Jane Smith",
            "source": "Example News",
            "category": "technology",
            "published_at": "2026-01-01T00:00:00Z",
            "url": "https://example.test/one",
            "body": "Apple met OpenAI in Chicago.\n\nJane Smith reported the meeting.",
        },
        {
            "title": "OpenAI update",
            "author": "John Smith",
            "source": "Other News",
            "category": "technology",
            "published_at": "2026-01-02T00:00:00Z",
            "url": "https://example.test/two",
            "body": "OpenAI announced an update.",
        },
    ]
    corpus_path = tmp_path / "corpus.json"
    corpus_path.write_text(json.dumps(corpus), encoding="utf-8")
    out = tmp_path / "out"
    manifest = build_graph(corpus_path, out, vendor_id="centroid", version=1)

    nodes = [
        json.loads(line)
        for line in (out / "vendor_centroid_stage1_graph-nodes_v1.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    edges = [
        json.loads(line)
        for line in (out / "vendor_centroid_stage1_graph-edges_v1.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    node_ids = {node["node_id"] for node in nodes}
    assert manifest["counts"]["documents"] == 2
    assert manifest["metrics"]["provenance_completeness_percent"] == 100.0
    assert manifest["metrics"]["orphan_node_rate"] == 0.0
    assert all(node["provenance"]["doc_id"] for node in nodes)
    assert all(edge["provenance"]["doc_id"] for edge in edges)
    assert all(edge["subject"] in node_ids and edge["object"] in node_ids for edge in edges)
    openai_nodes = [node for node in nodes if node["type"] == "Entity" and node["label"] == "OpenAI"]
    assert len(openai_nodes) == 1
