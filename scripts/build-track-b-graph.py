#!/usr/bin/env python3
"""Build the Stage 1 Track B MultiHopRAG graph artifact triplet."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from vanguard_primekg.track_b import build_graph


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--corpus",
        type=Path,
        default=Path("data/datasets/multihop/corpus.json"),
    )
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--vendor-id", required=True)
    parser.add_argument("--version", type=int, default=1)
    args = parser.parse_args()
    manifest = build_graph(
        args.corpus,
        args.out,
        vendor_id=args.vendor_id,
        version=args.version,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
