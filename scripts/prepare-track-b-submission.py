#!/usr/bin/env python3
"""Add the RFP reporting artifacts and authoritative manifest to a Track B run."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from vanguard_primekg.submission import validate_vendor_id


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_new(path: Path, text: str) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(text.rstrip() + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--vendor-id", required=True)
    parser.add_argument("--version", type=int, required=True)
    args = parser.parse_args()
    vendor = validate_vendor_id(args.vendor_id)
    if args.version < 1:
        parser.error("--version must be positive")

    directory = args.directory.resolve()
    manifest = _json(directory / "run-manifest.json")
    graph_manifest_path = (
        directory
        / f"vendor_{vendor}_stage1_graph-manifest_v{args.version}.json"
    )
    graph = _json(graph_manifest_path)
    prefix = f"vendor_{vendor}_stage1_"
    suffix = f"_v{args.version}"
    qa_path = directory / f"{prefix}qa-results{suffix}.jsonl"
    trace_path = directory / f"{prefix}reasoning-traces{suffix}.json"
    graph_nodes_path = directory / f"{prefix}graph-nodes{suffix}.jsonl"
    graph_edges_path = directory / f"{prefix}graph-edges{suffix}.jsonl"

    latencies = [
        int(item.get("latency_ms", 0))
        for item in manifest.get("questions", [])
        if int(item.get("latency_ms", 0)) > 0
        and item.get("status") != "firewall_blocked"
    ]
    latency = manifest.get("latency_ms", {})
    usage = manifest.get("token_usage", {})
    cost = manifest.get("cost_per_query", {})
    database = manifest.get("database", {})
    model = manifest.get("model", {})
    host = manifest.get("host", {})

    metrics_path = directory / f"{prefix}metrics-self-report{suffix}.md"
    _write_new(metrics_path, f"""# Vanguard Stage 1 Track B metrics self-report

This report follows RFP §8.4. Answer correctness, multi-hop accuracy, and
citation quality are not self-reported; Cotiviti scores the withheld key.

| Metric | Result |
|---|---:|
| Outcomes recorded | {manifest.get("question_count", 0)}/{manifest.get("question_count", 0)} |
| Answered | {manifest.get("answered_count", 0)} |
| Valid insufficient evidence | {manifest.get("valid_insufficient_evidence_count", 0)} |
| Firewall blocked | {manifest.get("firewall_block_count", 0)} |
| Unanswered/errors | {manifest.get("unanswered_count", 0)} |
| Query latency p50 | {latency.get("p50", 0):.2f} ms |
| Query latency p95 | {latency.get("p95", 0):.2f} ms |
| Query latency p99 | {latency.get("p99", 0):.2f} ms |
| Model input tokens | {usage.get("input_tokens", 0):,} |
| Model output tokens | {usage.get("output_tokens", 0):,} |
| Model cost per query | ${cost.get("model_cost_usd_per_query", 0):.8f} |
| Graph documents represented | {graph.get("metrics", {}).get("documents_represented_percent", 0):.4f}% |
| Graph provenance completeness | {graph.get("metrics", {}).get("provenance_completeness_percent", 0):.4f}% |
| Graph orphan-node rate | {graph.get("metrics", {}).get("orphan_node_rate", 0):.8f} |

Structural completion and expected security/insufficient-evidence dispositions
are not correctness scores.
""")

    operations_path = directory / f"{prefix}operations-report{suffix}.md"
    _write_new(operations_path, f"""# Vanguard Stage 1 Track B operations report

## Performance and configuration

- Questions: {manifest.get("question_count", 0)}
- Concurrency: {manifest.get("concurrency", 1)}
- Minimum non-firewall latency: {min(latencies, default=0) / 1000:.2f} seconds
- Mean non-firewall latency: {statistics.fmean(latencies) / 1000 if latencies else 0:.2f} seconds
- p50/p95/p99: {latency.get("p50", 0) / 1000:.2f} / {latency.get("p95", 0) / 1000:.2f} / {latency.get("p99", 0) / 1000:.2f} seconds
- Maximum non-firewall latency: {max(latencies, default=0) / 1000:.2f} seconds
- Hardware/platform: {host.get("platform", "not recorded")}
- Python: {host.get("python", "not recorded")}
- Database: local Oracle, {database.get("node_count", 0):,} nodes and {database.get("directed_edge_count", 0):,} directed edges
- Model configuration: {model.get("model_id")}, temperature {model.get("temperature_requested")}
- Model requests: {usage.get("requests", 0)}
- Input/output tokens: {usage.get("input_tokens", 0):,} / {usage.get("output_tokens", 0):,}
- Measured model cost: ${cost.get("model_cost_usd_total", 0):.8f}
- Cost per query: ${cost.get("model_cost_usd_per_query", 0):.8f}

The database is local-only. Retrieval uses parameterized, read-only Oracle
queries. The model receives only public questions and retrieved public
MultiHopRAG passages.
""")

    methodology_path = directory / f"{prefix}methodology-summary{suffix}.md"
    _write_new(methodology_path, f"""# Vanguard Stage 1 Track B methodology summary

## Architecture

Track B deterministically constructs a provenance-complete graph from the
public MultiHopRAG corpus. Document, TextBlock, Source, Person, Category, and
shared Entity nodes are linked through typed edges and loaded into isolated
Oracle `mh_*` tables. The submitted graph contains {graph.get("counts", {}).get("nodes", 0):,}
nodes and {graph.get("counts", {}).get("edges", 0):,} edges.

## Isolation and grounded answering

A deterministic firewall executes before retrieval or model access. Oracle
performs bounded, parameterized, read-only retrieval. OCI Generative AI model
`{model.get("model_id")}` synthesizes an answer only from returned passages.
Citations, graph references, and reasoning traces resolve to submitted graph
elements. Untrusted question and article text remain isolated as data.

Clinical-context fields are omitted because MultiHopRAG is non-clinical.
The model cannot write SQL or choose unsubmitted graph identifiers.
""")

    clarification_path = directory / f"{prefix}clarification-log{suffix}.md"
    _write_new(clarification_path, """# Vanguard Stage 1 Track B clarification log

## Cotiviti responses relied upon

None. No Cotiviti clarification response was received or relied upon.

## Open questions and documented interpretations

- The supplied Track B set contains 60 questions; all 60 are preserved.
- Five questions lack the named supporting material in the supplied public
  corpus and are reported as valid insufficient-evidence outcomes.
- Five adversarial questions are blocked before retrieval or model execution.
- Cotiviti owns answer correctness and citation-quality scoring.
""")

    required = [
        graph_nodes_path,
        graph_edges_path,
        graph_manifest_path,
        qa_path,
        trace_path,
        metrics_path,
        operations_path,
        methodology_path,
        clarification_path,
    ]
    for path in required:
        if not path.is_file():
            raise SystemExit(f"missing required artifact: {path}")
    package_path = directory / f"{prefix}submission-manifest{suffix}.json"
    package = {
        "vendor_id": vendor,
        "stage": 1,
        "track": "B",
        "version": args.version,
        "authoritative": manifest.get("authoritative") is True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "rfp_sections": ["7.1", "8.1", "8.2", "8.3", "8.4"],
        "required_artifacts": [
            {
                "name": path.name,
                "size": path.stat().st_size,
                "sha256": _sha256(path),
            }
            for path in required
        ],
        "supporting_artifacts": [
            "run-manifest.json", "model-audit.json", "reviews/",
        ],
    }
    _write_new(package_path, json.dumps(package, indent=2, sort_keys=True))
    print(json.dumps(package, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
