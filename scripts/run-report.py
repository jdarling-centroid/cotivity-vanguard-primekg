#!/usr/bin/env python3
"""Print concise final metrics for a versioned Track A or Track B run."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"{path}: expected one JSON object")
    return value


def _seconds(value: Any) -> str:
    if not isinstance(value, (int, float)):
        return "not recorded"
    return f"{value / 1000:.2f} seconds"


def _artifacts(directory: Path) -> tuple[list[dict[str, Any]], int]:
    qa_files = sorted(directory.glob("vendor_*_stage1_qa-results_v*.jsonl"))
    trace_files = sorted(directory.glob("vendor_*_stage1_reasoning-traces_v*.json"))
    if len(qa_files) != 1 or len(trace_files) != 1:
        return [], 0
    qa_records = [
        json.loads(line)
        for line in qa_files[0].read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    traces = json.loads(trace_files[0].read_text(encoding="utf-8"))
    return qa_records, len(traces) if isinstance(traces, list) else 0


def _percentile(values: list[int], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = (len(ordered) - 1) * fraction
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    weight = rank - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _is_firewall(record: dict[str, Any]) -> bool:
    return (
        record.get("answer_type") == "firewall_block"
        or record.get("vendor_answer") == "Won't do that"
    )


def _is_unanswered(record: dict[str, Any]) -> bool:
    answer = str(record.get("vendor_answer") or "").casefold()
    return (
        not answer
        or answer.startswith("insufficient")
        or record.get("answer_type") in {
            "insufficient_data", "out_of_graph", "unanswered",
        }
    )


def _database_counts(manifest: dict[str, Any]) -> tuple[Any, Any]:
    database = manifest.get("database") or {}
    return database.get("node_count"), database.get("directed_edge_count")


def _load_ground_truth(repo_root: Path, dataset: str) -> dict[int, list[str]]:
    """Load actual_nodes from ground truth YAML by dataset."""
    import yaml  # pyyaml; available in project venv

    if dataset == "PrimeKG":
        yaml_file = repo_root / "config" / "primekg-question-sets.yaml"
    else:
        yaml_file = repo_root / "config" / "multihop-question-sets.yaml"

    if not yaml_file.is_file():
        return {}

    with open(yaml_file, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    ground_truth = {}
    for section in data.get("sections", []):
        for q in section.get("questions", []):
            qnum = q.get("number")
            nodes = q.get("metadata", {}).get("actual_nodes", [])
            if qnum is not None and nodes:
                ground_truth[qnum] = [str(n) for n in nodes]
    
    return ground_truth


def _node_matching_metrics(
    manifest_questions: list[dict[str, Any]], ground_truth: dict[int, list[str]]
) -> dict[str, Any]:
    """Calculate precision, recall, and exact match for returned nodes."""
    total = 0
    exact_matches = 0
    precisions = []
    recalls = []
    per_question = []
    full_coverage_count = 0
    
    for q in manifest_questions:
        qnum = q.get("number")
        if qnum not in ground_truth:
            continue
        
        returned = set(q.get("answer_node_ids", []))
        expected = set(ground_truth[qnum])
        
        if not expected:
            continue
        
        total += 1
        
        # Precision: of what we returned, how much was correct
        if returned:
            tp = len(returned & expected)
            precision = tp / len(returned)
            precisions.append(precision)
        else:
            precision = 0.0
        
        # Recall: of what we should have returned, how much did we get
        tp = len(returned & expected)
        recall = tp / len(expected)
        recalls.append(recall)
        
        # Exact match: did we get exactly the right set
        if returned == expected:
            exact_matches += 1
            full_coverage_count += 1
        
        per_question.append({
            "number": qnum,
            "expected_count": len(expected),
            "returned_count": len(returned),
            "recall": recall,
            "precision": precision,
            "exact_match": returned == expected,
        })
    
    return {
        "total_questions_with_ground_truth": total,
        "exact_matches": exact_matches,
        "full_coverage_count": full_coverage_count,
        "exact_match_rate": exact_matches / total if total > 0 else None,
        "mean_precision": statistics.fmean(precisions) if precisions else None,
        "mean_recall": statistics.fmean(recalls) if recalls else None,
        "per_question": per_question,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_directory", type=Path)
    parser.add_argument("--verbose", action="store_true", help="Show per-question node matching details")
    parser.add_argument("--input-cost-per-million", type=float, default=1.25)
    parser.add_argument("--output-cost-per-million", type=float, default=2.50)
    args = parser.parse_args()
    if any(
        value < 0
        for value in (
            args.input_cost_per_million,
            args.output_cost_per_million,
        )
    ):
        parser.error("token costs must be non-negative")

    directory = args.run_directory.resolve()
    manifest_path = directory / "run-manifest.json"
    if not manifest_path.is_file():
        raise SystemExit(f"missing run manifest: {manifest_path}")
    manifest = _read_json(manifest_path)
    latency = manifest.get("latency_ms") or {}
    questions = int(manifest.get("question_count") or latency.get("queries") or 0)
    qa_records, trace_count = _artifacts(directory)
    completed = min(len(qa_records), trace_count)
    firewall_count = sum(_is_firewall(record) for record in qa_records)
    question_metrics = {
        str(item.get("question_id")): item
        for item in manifest.get("questions", [])
        if isinstance(item, dict)
    }
    valid_insufficient_count = sum(
        item.get("status") == "valid_insufficient_evidence"
        for item in question_metrics.values()
    )
    unanswered_count = sum(
        _is_unanswered(record)
        and question_metrics.get(str(record.get("question_id")), {}).get("status")
        != "valid_insufficient_evidence"
        for record in qa_records
        if not _is_firewall(record)
    )
    answered_count = (
        len(qa_records) - firewall_count - valid_insufficient_count
        - unanswered_count
    )
    measured_latencies = [
        int(record["latency_ms"])
        for record in qa_records
        if (
            not _is_firewall(record)
            and isinstance(record.get("latency_ms"), (int, float))
            and record["latency_ms"] > 0
        )
    ]
    if measured_latencies:
        latency = {
            "min": min(measured_latencies),
            "mean": statistics.fmean(measured_latencies),
            "p50": _percentile(measured_latencies, 0.50),
            "p95": _percentile(measured_latencies, 0.95),
            "p99": _percentile(measured_latencies, 0.99),
            "max": max(measured_latencies),
        }

    structural = manifest.get("structural_outcome_check") or {}
    completion = manifest.get("completion") or {}
    structural_passed = structural.get(
        "passed", completion.get("structural_passed", completed)
    )
    structural_total = structural.get(
        "total", completion.get("structural_total", questions)
    )

    validation_path = directory / "validation-report.json"
    if validation_path.is_file():
        validation = _read_json(validation_path)
        validation_errors = validation.get("error_count", 0)
        validation_warnings = validation.get("warning_count", 0)
        validation_text = (
            f"{'PASS' if validation_errors == 0 and validation_warnings == 0 else 'FAIL'} "
            f"— {validation_errors} errors, {validation_warnings} warnings"
        )
    else:
        validation_text = "not run"

    nodes, edges = _database_counts(manifest)
    database_text = (
        f"{nodes:,} nodes and {edges:,} directed edges"
        if nodes is not None and edges is not None
        else "counts unavailable"
    )

    model = manifest.get("model") or {}
    model_id = model.get("model_id") or manifest.get("planner", {}).get("model_id")
    temperature = model.get("temperature_requested")
    model_text = str(model_id or "deterministic/no model")
    if temperature is not None:
        model_text += f", temperature {temperature:g}"

    usage = manifest.get("token_usage") or {}
    input_tokens = usage.get("input_tokens")
    output_tokens = usage.get("output_tokens")
    total_tokens = usage.get("total_tokens")
    requests = usage.get("requests")
    if isinstance(input_tokens, int) and isinstance(output_tokens, int):
        total_cost = (
            input_tokens / 1_000_000 * args.input_cost_per_million
            + output_tokens / 1_000_000 * args.output_cost_per_million
        )
        average_cost = total_cost / questions if questions else None
        cost_basis = (
            f"${args.input_cost_per_million:g}/M input, "
            f"${args.output_cost_per_million:g}/M output"
        )
    else:
        total_cost = None
        average_cost = None
        cost_basis = "token totals unavailable"

    # Load ground truth and calculate node matching metrics
    repo_root = directory.parent.parent
    dataset = manifest.get("dataset", "PrimeKG")
    ground_truth = _load_ground_truth(repo_root, dataset)
    node_metrics = _node_matching_metrics(manifest.get("questions", []), ground_truth)

    print("Vanguard run report")
    print("===================\n")
    print("Outcome")
    print("-------")
    print(f"- Outcomes recorded: {len(qa_records)}/{questions}")
    print(f"- Answered: {answered_count}")
    print(f"- Valid insufficient evidence: {valid_insufficient_count}")
    print(f"- Firewall blocked: {firewall_count}")
    print(f"- Unanswered: {unanswered_count}")
    print(f"- Structural checks: {structural_passed}/{structural_total}")
    print(f"- Validation: {validation_text}")
    
    if node_metrics.get("total_questions_with_ground_truth", 0) > 0:
        print("\nNode Matching (vs. ground truth)")
        print("--------------------------------")
        exact = node_metrics.get("exact_match_rate")
        prec = node_metrics.get("mean_precision")
        recall = node_metrics.get("mean_recall")
        total_gt = node_metrics.get("total_questions_with_ground_truth", 0)
        full_cov = node_metrics.get("full_coverage_count", 0)
        incomplete_count = total_gt - full_cov
        print(f"- Questions with ground truth: {total_gt}")
        print(f"- Full coverage (100% recall): {full_cov}/{total_gt}")
        print(f"- Incomplete coverage: {incomplete_count}/{total_gt}")
        print(f"- Exact matches: {node_metrics.get('exact_matches')}")
        print(f"- Exact match rate: {exact:.2%}" if exact is not None else "- Exact match rate: not available")
        print(f"- Mean precision: {prec:.2%}" if prec is not None else "- Mean precision: not available")
        print(f"- Mean recall: {recall:.2%}" if recall is not None else "- Mean recall: not available")
        
        # Show questions with < 100% recall (only in verbose mode)
        incomplete = [pq for pq in node_metrics.get("per_question", []) if pq["recall"] < 1.0]
        if args.verbose:
            print("\n  Per-question node matching:")
            for pq in sorted(node_metrics.get("per_question", []), key=lambda x: x["number"]):
                match_str = "✓" if pq["exact_match"] else "✗"
                print(f"    Q{pq['number']:3d} {match_str}: expected {pq['expected_count']:5d}, got {pq['returned_count']:5d}, recall {pq['recall']:6.1%}")
        elif incomplete:
            print(f"\n  {len(incomplete)} questions with incomplete coverage. Use --verbose to see all details.")
    
    print("\nPerformance")
    print("-----------")
    print(f"- Concurrency: {manifest.get('concurrency', latency.get('concurrency', 1))}")
    print(f"- Mean latency (excluding firewall): {_seconds(latency.get('mean'))}")
    print(f"- Minimum latency (excluding firewall): {_seconds(latency.get('min'))}")
    print(f"- p50: {_seconds(latency.get('p50'))}")
    print(f"- p95: {_seconds(latency.get('p95'))}")
    print(f"- p99: {_seconds(latency.get('p99'))}")
    print(f"- Maximum latency (excluding firewall): {_seconds(latency.get('max'))}")
    wall_seconds = manifest.get("wall_seconds")
    if isinstance(wall_seconds, (int, float)):
        print(f"- Total wall time: {wall_seconds:.2f} seconds")
    print("\nModel usage and cost")
    print("--------------------")
    print(f"- Model: {model_text}")
    print(f"- Model requests: {requests if requests is not None else 'not recorded'}")
    print(f"- Input tokens: {input_tokens:,}" if isinstance(input_tokens, int) else "- Input tokens: not recorded")
    print(f"- Output tokens: {output_tokens:,}" if isinstance(output_tokens, int) else "- Output tokens: not recorded")
    print(f"- Total tokens: {total_tokens:,}" if isinstance(total_tokens, int) else "- Total tokens: not recorded")
    print(
        f"- Model cost total: ${total_cost:.8f}"
        if isinstance(total_cost, (int, float))
        else "- Model cost total: not recorded"
    )
    print(
        f"- Model cost per question: ${average_cost:.8f}"
        if isinstance(average_cost, (int, float))
        else "- Model cost per question: not recorded"
    )
    print(f"- Cost basis: {cost_basis}")
    print("\nEnvironment")
    print("-----------")
    print(f"- Database: {database_text}")
    print("\nNote: completion and structural checks are not correctness scores; "
          "Cotiviti owns the withheld answer key.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
