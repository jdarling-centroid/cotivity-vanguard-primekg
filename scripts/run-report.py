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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_directory", type=Path)
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
    unanswered_count = sum(
        _is_unanswered(record) for record in qa_records if not _is_firewall(record)
    )
    answered_count = len(qa_records) - firewall_count - unanswered_count
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

    print("Vanguard run report")
    print("===================\n")
    print("Outcome")
    print("-------")
    print(f"- Outcomes recorded: {len(qa_records)}/{questions}")
    print(f"- Answered: {answered_count}")
    print(f"- Firewall blocked: {firewall_count}")
    print(f"- Unanswered: {unanswered_count}")
    print(f"- Structural checks: {structural_passed}/{structural_total}")
    print(f"- Validation: {validation_text}")
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
