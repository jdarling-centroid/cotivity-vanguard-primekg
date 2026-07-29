#!/usr/bin/env python3
"""Load a generated Stage 1 Track B graph into local Oracle."""

from __future__ import annotations

import argparse
from pathlib import Path

from vanguard_primekg.track_b.load_graph import load_graph


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("graph_dir", type=Path)
    args = parser.parse_args()
    nodes = list(args.graph_dir.glob("vendor_*_stage1_graph-nodes_v*.jsonl"))
    edges = list(args.graph_dir.glob("vendor_*_stage1_graph-edges_v*.jsonl"))
    if len(nodes) != 1 or len(edges) != 1:
        raise SystemExit("expected exactly one graph-nodes and graph-edges artifact")
    node_count, edge_count = load_graph(nodes[0], edges[0])
    print(f"loaded {node_count} nodes and {edge_count} edges")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
