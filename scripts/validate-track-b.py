#!/usr/bin/env python3
"""Validate a Stage 1 Track B answer package from its local artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


def _one(directory: Path, pattern: str) -> Path:
    matches = sorted(directory.glob(pattern))
    if len(matches) != 1:
        raise SystemExit(f"expected one {pattern} file, found {len(matches)}")
    return matches[0]


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()

    directory = args.directory.resolve()
    errors: list[str] = []
    qa_path = _one(directory, "vendor_*_stage1_qa-results_v*.jsonl")
    trace_path = _one(directory, "vendor_*_stage1_reasoning-traces_v*.json")
    qa = [
        json.loads(line)
        for line in qa_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    traces = _json(trace_path)
    manifest = _json(directory / "run-manifest.json")
    expected = len(qa) if args.allow_partial else 60
    graph_nodes: dict[str, dict[str, Any]] = {}
    graph_edges: dict[str, dict[str, Any]] = {}
    if not args.allow_partial:
        node_path = _one(directory, "vendor_*_stage1_graph-nodes_v*.jsonl")
        edge_path = _one(directory, "vendor_*_stage1_graph-edges_v*.jsonl")
        graph_manifest_path = _one(
            directory, "vendor_*_stage1_graph-manifest_v*.json"
        )
        package_path = _one(
            directory, "vendor_*_stage1_submission-manifest_v*.json"
        )
        for line_number, line in enumerate(
            node_path.read_text(encoding="utf-8").splitlines(), 1
        ):
            if not line.strip():
                continue
            node = json.loads(line)
            node_id = str(node.get("node_id") or "")
            if not node_id or node_id in graph_nodes:
                errors.append(f"graph node line {line_number}: missing/duplicate ID")
                continue
            if not isinstance(node.get("provenance"), dict) or not node[
                "provenance"
            ].get("doc_id"):
                errors.append(f"{node_id}: missing doc_id provenance")
            graph_nodes[node_id] = node
        for line_number, line in enumerate(
            edge_path.read_text(encoding="utf-8").splitlines(), 1
        ):
            if not line.strip():
                continue
            edge = json.loads(line)
            edge_id = str(edge.get("edge_id") or "")
            if not edge_id or edge_id in graph_edges:
                errors.append(f"graph edge line {line_number}: missing/duplicate ID")
                continue
            if (
                edge.get("subject") not in graph_nodes
                or edge.get("object") not in graph_nodes
            ):
                errors.append(f"{edge_id}: dangling graph endpoint")
            if not isinstance(edge.get("provenance"), dict) or not edge[
                "provenance"
            ].get("doc_id"):
                errors.append(f"{edge_id}: missing doc_id provenance")
            graph_edges[edge_id] = edge
        graph_manifest = _json(graph_manifest_path)
        counts = graph_manifest.get("counts", {})
        if counts.get("documents") != 609:
            errors.append("graph manifest must represent all 609 documents")
        if counts.get("nodes") != len(graph_nodes):
            errors.append("graph manifest node count does not match graph JSONL")
        if counts.get("edges") != len(graph_edges):
            errors.append("graph manifest edge count does not match graph JSONL")
        metrics = graph_manifest.get("metrics", {})
        if metrics.get("documents_represented_percent") != 100.0:
            errors.append("graph does not report 100% document representation")
        if metrics.get("provenance_completeness_percent") != 100.0:
            errors.append("graph does not report complete provenance")

        package = _json(package_path)
        if (
            package.get("track") != "B"
            or package.get("stage") != 1
            or package.get("authoritative") is not True
        ):
            errors.append("submission manifest is not authoritative Stage 1 Track B")
        listed = {
            item.get("name"): item
            for item in package.get("required_artifacts", [])
            if isinstance(item, dict)
        }
        required_stems = (
            "graph-nodes", "graph-edges", "graph-manifest", "qa-results",
            "reasoning-traces", "metrics-self-report", "operations-report",
            "methodology-summary", "clarification-log",
        )
        for stem in required_stems:
            matches = list(directory.glob(f"vendor_*_stage1_{stem}_v*.*"))
            if len(matches) != 1:
                errors.append(f"expected exactly one {stem} artifact")
                continue
            path = matches[0]
            entry = listed.get(path.name)
            if not entry:
                errors.append(f"submission manifest omits {path.name}")
            elif (
                entry.get("size") != path.stat().st_size
                or entry.get("sha256") != _sha256(path)
            ):
                errors.append(f"submission manifest mismatch for {path.name}")
        report_topics = {
            "metrics-self-report": ("§8.4", "p50", "p95", "p99", "cost per query"),
            "operations-report": ("concurrency", "hardware", "database", "cost"),
            "methodology-summary": ("architecture", "oracle", "isolation", "model"),
            "clarification-log": ("cotiviti responses relied upon", "open questions"),
        }
        for stem, topics in report_topics.items():
            path = _one(directory, f"vendor_*_stage1_{stem}_v*.md")
            folded = path.read_text(encoding="utf-8").casefold()
            for topic in topics:
                if topic.casefold() not in folded:
                    errors.append(f"{path.name}: missing topic {topic!r}")
    if len(qa) != expected or not isinstance(traces, list) or len(traces) != expected:
        errors.append(
            f"expected {expected} QA records and traces; got {len(qa)} and "
            f"{len(traces) if isinstance(traces, list) else 'invalid'}"
        )

    qa_ids = [str(item.get("question_id")) for item in qa]
    trace_ids = [str(item.get("question_id")) for item in traces]
    if len(set(qa_ids)) != len(qa_ids) or set(qa_ids) != set(trace_ids):
        errors.append("QA and trace question IDs are not unique and one-to-one")
    for item in qa:
        question_id = str(item.get("question_id"))
        if not question_id.startswith("Q-MH-"):
            errors.append(f"invalid Track B question ID: {question_id}")
        if not isinstance(item.get("latency_ms"), int):
            errors.append(f"{question_id}: missing latency")
        context_refs = {
            str(value.get("source_ref"))
            for value in item.get("retrieved_context", [])
            if isinstance(value, dict)
        }
        citation_refs = {
            str(value.get("source_ref"))
            for value in item.get("citations", [])
            if isinstance(value, dict)
        }
        if not citation_refs.issubset(context_refs):
            errors.append(f"{question_id}: citation is absent from retrieved context")
        if graph_nodes:
            missing_nodes = set(item.get("graph_nodes_used", [])) - set(graph_nodes)
            missing_edges = set(item.get("graph_edges_used", [])) - set(graph_edges)
            if missing_nodes:
                errors.append(f"{question_id}: graph node references do not resolve")
            if missing_edges:
                errors.append(f"{question_id}: graph edge references do not resolve")

    questions = manifest.get("questions", [])
    if len(questions) != expected:
        errors.append(f"manifest contains {len(questions)} question metrics, expected {expected}")
    for item in questions:
        if item.get("status") in {
            "unexpected_insufficient_evidence", "unexpected_answer",
        }:
            errors.append(
                f"{item.get('question_id')}: unexpected outcome "
                f"{item.get('status')}"
            )
        usage = item.get("token_usage", {})
        if not all(
            isinstance(usage.get(key), int) and usage[key] >= 0
            for key in ("input_tokens", "output_tokens", "total_tokens", "requests")
        ):
            errors.append(f"{item.get('question_id')}: invalid token accounting")
        if not isinstance(item.get("model_cost_usd"), (int, float)):
            errors.append(f"{item.get('question_id')}: missing model cost")

    reviews = list((directory / "reviews").glob("*.md"))
    if len(reviews) != expected:
        errors.append(f"review count is {len(reviews)}, expected {expected}")

    if not args.allow_partial:
        secret_pattern = re.compile(
            rb"(BEGIN (?:RSA |EC )?PRIVATE KEY|security_token_file|"
            rb"MC_DATABASE__PASSWORD\s*[=:]\s*\S+)",
            re.IGNORECASE,
        )
        for path in directory.iterdir():
            if path.is_file() and secret_pattern.search(path.read_bytes()):
                errors.append(f"possible secret material in {path.name}")

    report = {
        "validator": "validate-track-b.py",
        "scope": "Stage 1 Track B MultiHopRAG",
        "qa_records": len(qa),
        "reasoning_traces": len(traces) if isinstance(traces, list) else 0,
        "error_count": len(errors),
        "warning_count": 0,
        "errors": errors,
        "warnings": [],
        "result": "pass" if not errors else "fail",
    }
    (directory / "validation-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
