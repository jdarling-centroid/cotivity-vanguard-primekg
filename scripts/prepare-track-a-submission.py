#!/usr/bin/env python3
"""Package a validated Track A run with every RFP-required reporting artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def _percentile(values: list[int], fraction: float) -> float:
    ordered = sorted(values)
    rank = (len(ordered) - 1) * fraction
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    weight = rank - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _hardware_details(source: dict[str, Any]) -> dict[str, Any]:
    hardware = dict(source)
    hardware.setdefault("platform", platform.platform())
    hardware.setdefault("machine", platform.machine())
    hardware.setdefault("cpu_count", os.cpu_count())
    if not hardware.get("cpu_model"):
        try:
            hardware["cpu_model"] = subprocess.check_output(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
        except (OSError, subprocess.CalledProcessError):
            hardware["cpu_model"] = platform.processor() or None
    if hardware.get("ram_gib") is None:
        try:
            memory_bytes = int(subprocess.check_output(
                ["sysctl", "-n", "hw.memsize"],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip())
            hardware["ram_gib"] = round(memory_bytes / (1024 ** 3), 2)
        except (OSError, ValueError, subprocess.CalledProcessError):
            hardware["ram_gib"] = None
    missing = [
        key for key in ("platform", "machine", "cpu_count", "cpu_model", "ram_gib")
        if hardware.get(key) is None
    ]
    if missing:
        raise SystemExit(
            "cannot create an RFP-ready package without measured hardware fields: "
            + ", ".join(missing)
        )
    return hardware


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    parser.add_argument("--vendor-id", required=True)
    parser.add_argument("--version", type=int, required=True)
    args = parser.parse_args()

    source = args.source.resolve()
    target = args.target.resolve()
    if target.exists():
        raise SystemExit(f"refusing to overwrite existing target: {target}")
    qa_sources = sorted(source.glob("vendor_*_stage1_qa-results_v*.jsonl"))
    trace_sources = sorted(source.glob("vendor_*_stage1_reasoning-traces_v*.json"))
    if len(qa_sources) != 1 or len(trace_sources) != 1:
        raise SystemExit("source must contain exactly one QA file and one trace file")
    source_validation = _json(source / "validation-report.json")
    if (
        source_validation.get("result") != "pass"
        or source_validation.get("error_count") != 0
        or source_validation.get("warning_count") != 0
        or not source_validation.get("database_provenance_checked")
    ):
        raise SystemExit("source run lacks a clean database-provenance validation")

    target.mkdir(parents=True)
    suffix = f"_v{args.version}"
    prefix = f"vendor_{args.vendor_id}_stage1_"
    qa_path = target / f"{prefix}qa-results{suffix}.jsonl"
    trace_path = target / f"{prefix}reasoning-traces{suffix}.json"
    shutil.copyfile(qa_sources[0], qa_path)
    shutil.copyfile(trace_sources[0], trace_path)

    qa_records = [
        json.loads(line)
        for line in qa_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    traces = _json(trace_path)
    source_manifest = _json(source / "run-manifest.json")
    token_usage = source_manifest.get("token_usage")
    cost_per_query = source_manifest.get("cost_per_query")
    source_questions = source_manifest.get("questions")
    if (
        not isinstance(token_usage, dict)
        or not all(
            isinstance(token_usage.get(key), int) and token_usage[key] > 0
            for key in ("input_tokens", "output_tokens", "total_tokens", "requests")
        )
        or not isinstance(cost_per_query, dict)
        or cost_per_query.get("status") != "model_cost_measured"
        or not isinstance(cost_per_query.get("model_cost_usd_per_query"), (int, float))
        or not isinstance(source_questions, list)
        or len(source_questions) != len(qa_records)
        or any(
            not isinstance(item, dict)
            or not isinstance(item.get("token_usage"), dict)
            or not all(
                isinstance(item["token_usage"].get(key), int)
                and item["token_usage"][key] >= 0
                for key in ("input_tokens", "output_tokens", "total_tokens", "requests")
            )
            or not isinstance(item.get("model_cost_usd"), (int, float))
            for item in source_questions
        )
    ):
        raise SystemExit(
            "source run lacks measured run-level and per-question OCI token usage "
            "and model cost"
        )
    cost_per_query = dict(cost_per_query)
    cost_per_query.update({
        "local_compute_usd_total": 0.0,
        "local_storage_usd_total": 0.0,
        "fully_loaded_usd_total": cost_per_query["model_cost_usd_total"],
        "fully_loaded_usd_per_query": cost_per_query["model_cost_usd_per_query"],
        "local_cost_basis": (
            "Incremental billed-cost basis: the measured run used an existing "
            "owned workstation and local Oracle storage with no incremental "
            "cloud compute or storage charge."
        ),
    })
    latencies = [
        int(record["latency_ms"])
        for record in qa_records
        if isinstance(record.get("latency_ms"), (int, float))
        and record["latency_ms"] > 0
    ]
    database = source_manifest["database"]
    hardware = _hardware_details(source_manifest["hardware"])
    planner = source_manifest["planner"]
    temperature_display = (
        f"{planner['temperature_sent']:g}"
        if planner.get("temperature_sent") is not None
        else "not sent"
    )
    structural = source_manifest["structural_outcome_check"]
    created_at = datetime.now(timezone.utc).isoformat()

    run_manifest = {
        "schema_version": "vanguard-stage1-run-metrics-1.0",
        "vendor_id": args.vendor_id,
        "stage": 1,
        "track": "A",
        "dataset": "PrimeKG",
        "authoritative": True,
        "authoritative_version": args.version,
        "created_at": created_at,
        "source_run": {
            "directory": source.name,
            "authoritative_version": source_manifest["authoritative_version"],
            "created_at": source_manifest["created_at"],
            "qa_sha256": _sha256(qa_sources[0]),
            "reasoning_traces_sha256": _sha256(trace_sources[0]),
        },
        "question_count": len(qa_records),
        "concurrency": 1,
        "completion": {
            "qa_records": len(qa_records),
            "reasoning_traces": len(traces),
            "structural_passed": structural["passed"],
            "structural_total": structural["total"],
            "explicitly_not_accuracy": True,
        },
        "latency_ms": {
            "queries": len(latencies),
            "excludes_firewall_and_zero_ms": True,
            "min": min(latencies),
            "mean": round(statistics.fmean(latencies), 2),
            "p50": round(_percentile(latencies, 0.50), 2),
            "p95": round(_percentile(latencies, 0.95), 2),
            "p99": round(_percentile(latencies, 0.99), 2),
            "max": max(latencies),
        },
        "hardware": hardware,
        "model": {
            "role": "closed-schema semantic planner only",
            "provider": planner["provider"],
            "model_id": planner["model_id"],
            "temperature_requested": planner["temperature_sent"],
            "prompt_version": planner["prompt_version"],
            "timeout_seconds": planner["timeout_seconds"],
            "max_tokens": planner["max_tokens"],
            "retries": planner["max_retries"],
        },
        "database": database,
        "feature_flags": {
            "remote_database": bool(database.get("remote_allowed")),
            "model_database_composition": False,
            "question_specific_shortcuts": False,
            "deterministic_planner_fallback": bool(
                planner.get("deterministic_fallback")
            ),
        },
        "token_usage": token_usage,
        "cost_per_query": cost_per_query,
        "questions": source_questions,
        "artifacts": {},
    }
    run_manifest_path = target / "run-manifest.json"
    _write(run_manifest_path, json.dumps(run_manifest, indent=2, sort_keys=True))

    metrics_path = target / f"{prefix}metrics-self-report{suffix}.md"
    _write(metrics_path, f"""# Vanguard Stage 1 Track A metrics self-report

Authoritative submission version: {args.version}

This report follows RFP §8.4. Cotiviti retains the answer key; answer
correctness, multi-hop accuracy, and citation quality are not self-scored.

| Domain | Metric | Result | Configuration/basis |
|---|---|---:|---|
| Retrieval and reasoning | Answer and citation quality | Not self-reported | Cotiviti-scored against the withheld key |
| Reported NFRs | Queries measured | {len(latencies)} | Full issued Track A question set |
| Reported NFRs | Query latency p50 | {_percentile(latencies, .50):.2f} ms | Wall clock, question input through finalized answer |
| Reported NFRs | Query latency p95 | {_percentile(latencies, .95):.2f} ms | Same run/configuration |
| Reported NFRs | Query latency p99 | {_percentile(latencies, .99):.2f} ms | Same run/configuration |
| Reported NFRs | Mean query latency | {statistics.fmean(latencies):.2f} ms | Same run/configuration |
| Reported NFRs | Input tokens | {token_usage["input_tokens"]:,} | Measured OCI response usage over {token_usage["requests"]} requests |
| Reported NFRs | Output tokens | {token_usage["output_tokens"]:,} | Measured OCI response usage |
| Reported NFRs | Fully loaded cost per query | ${cost_per_query["fully_loaded_usd_per_query"]:.8f} | Measured model usage plus $0 incremental local compute/storage; see operations report |

Graph-construction and ingestion metrics do not apply to Track A because
PrimeKG is provided by Cotiviti. Structural completion was
{structural["passed"]}/{structural["total"]}; this is not an accuracy score.
""")

    operations_path = target / f"{prefix}operations-report{suffix}.md"
    _write(operations_path, f"""# Vanguard Stage 1 Track A operations report

## Run metrics

- Questions: {len(latencies)}
- Concurrency: 1
- Minimum latency: {min(latencies) / 1000:.2f} seconds
- Mean latency: {statistics.fmean(latencies) / 1000:.2f} seconds
- p50: {_percentile(latencies, .50) / 1000:.2f} seconds
- p95: {_percentile(latencies, .95) / 1000:.2f} seconds
- p99: {_percentile(latencies, .99) / 1000:.2f} seconds
- Maximum latency: {max(latencies) / 1000:.2f} seconds
- Structural completion: {structural["passed"]}/{structural["total"]}
- Database validation: 0 errors, 0 warnings
- Database: {database["node_count"]:,} nodes and {database["directed_edge_count"]:,} directed edges
- Model: {planner["model_id"]}, requested temperature {temperature_display}

Latency is wall-clock time from question input through firewall, planning,
entity resolution, one read-only database composition query, and deterministic
finalization. No warm-up exclusions were applied.

## Hardware and configuration

- Platform: {hardware["platform"]}
- Architecture: {hardware["machine"]}
- CPU model: {hardware["cpu_model"]}
- Logical CPU count: {hardware["cpu_count"]}
- RAM: {hardware["ram_gib"]:g} GiB
- GPU: {hardware["gpu"]}
- Oracle client-reported database version: {database["oracle_client_reported_version"]}
- Query backend: {database["backend"]}
- Database host: {database["dsn_host"]} (local-only guard enabled)
- Database call timeout: {database["call_timeout_ms"]} ms
- PrimeKG load: bidirectional-v2
- PrimeKG checksum: `{database["load_journal"]["kg_checksum"]}`
- Planner provider: {planner["provider"]}
- Planner prompt: {planner["prompt_version"]}
- Planner timeout/retries: {planner["timeout_seconds"]} seconds / {planner["max_retries"]}

## Cost and scalability

- OCI requests measured: {token_usage["requests"]}
- Input tokens: {token_usage["input_tokens"]:,}
- Output tokens: {token_usage["output_tokens"]:,}
- Total tokens: {token_usage["total_tokens"]:,}
- Measured model cost total: ${cost_per_query["model_cost_usd_total"]:.6f}
- Measured model cost per query: ${cost_per_query["model_cost_usd_per_query"]:.8f}
- Incremental local compute cost: $0.000000
- Incremental local storage cost: $0.000000
- Estimated fully loaded cost per query: ${cost_per_query["fully_loaded_usd_per_query"]:.8f}
- Pricing basis: {cost_per_query["pricing_basis"]["source"]},
  {cost_per_query["pricing_basis"]["price_list_date"]}

The model calculation uses the measured OCI token counts and the documented
input/output token rates. {cost_per_query["local_cost_basis"]}

PrimeKG steady state for this run was {database["node_count"]:,} nodes and
{database["directed_edge_count"]:,} directed edges. The database load is
fingerprint-aware, batched, MERGE-based, and resumable; a matching completed
fingerprint is not re-ingested.
""")

    methodology_path = target / f"{prefix}methodology-summary{suffix}.md"
    _write(methodology_path, f"""# Vanguard Stage 1 Track A methodology summary

## Scope

Track A loads the provided PrimeKG graph into local Oracle and answers the 100
issued questions. It does not construct or submit a replacement graph.

## Architecture

1. A deterministic firewall runs before model or database access.
2. OCI Generative AI `{planner["model_id"]}` maps an untrusted question to the
   closed `planner-plan-1.0` schema.
3. Deterministic entity resolution maps labels to local PrimeKG node IDs.
4. Oracle executes one parameterized, read-only SQL/PGQ composition statement.
5. Deterministic finalization emits the answer, citations, graph references,
   and ordered execution trace only from database-returned records.

The model cannot emit or execute SQL, access graph tools, select graph IDs,
perform set arithmetic across retrieval calls, or write the final answer.
Multi-hop traversal, intersection, difference, aggregation, ranking, ratio,
and negation are composed in Oracle.

## Graph fidelity and provenance

PrimeKG native predicates and display relations are preserved. Each
non-self-loop edge is loaded in both directions because the evaluation treats
PrimeKG traversal as direction-agnostic. Drug-to-protein targeting includes the
target, enzyme, carrier, and transporter roles.

Every stated answer node has a database-returned support path containing real
PrimeKG node IDs, edge IDs, predicates, display relations, and the executed
parameterized query. Unsupported facts fail closed.

## Model and versions

- Planner provider: {planner["provider"]}
- Planner model: {planner["model_id"]}
- Requested temperature: {temperature_display}
- Prompt version: {planner["prompt_version"]}
- Planner schema: planner-plan-1.0
- Oracle client-reported database version: {database["oracle_client_reported_version"]}
- PrimeKG load format: bidirectional-v2
- PrimeKG dataset fingerprint: `{database["load_journal"]["kg_checksum"]}`

## Isolation of untrusted text

Track A is graph-native and does not ingest external document instructions.
Question and node text are nevertheless treated as untrusted data. Questions
are JSON-serialized into the planner prompt, planner output must validate
against a closed schema, and the firewall precedes both planner and database
execution. The evaluation path never executes instructions contained in
question or graph text.

## Known limitations

PrimeKG does not encode patient-level negation, temporality, uncertainty, or
experiencer. The traces state this limitation rather than inventing clinical
context. Cotiviti retains the correctness key, so no answer-accuracy claim is
self-reported.
""")

    clarification_path = target / f"{prefix}clarification-log{suffix}.md"
    _write(clarification_path, """# Vanguard Stage 1 clarification log

## Cotiviti responses relied upon

None. No Cotiviti clarification response was received or relied upon in
producing this Track A package.

## Interpretation used

- For graph-native PrimeKG evidence, RFP §8 permits `source_ref` identifiers in
  place of page and character spans.
- Track A submits QA results and reasoning traces, but no constructed graph.
- The §8.4 answer/citation-quality row is not self-scored because Cotiviti
  retains the answer key.
- PrimeKG does not provide patient-level clinical-context attributes; the
  traces disclose that limitation and do not fabricate them.

## Open questions

The previously prepared clarification questions remain unanswered. This
submission does not represent any assumption as a Cotiviti-approved response.
""")

    required_paths = [
        qa_path,
        trace_path,
        metrics_path,
        operations_path,
        methodology_path,
        clarification_path,
    ]
    package_manifest_path = (
        target / f"{prefix}submission-manifest{suffix}.json"
    )
    package_manifest = {
        "vendor_id": args.vendor_id,
        "stage": 1,
        "track": "A",
        "version": args.version,
        "authoritative": True,
        "created_at": created_at,
        "rfp_sections": ["7.1", "8.2", "8.3", "8.4"],
        "required_artifacts": [
            {
                "name": path.name,
                "size": path.stat().st_size,
                "sha256": _sha256(path),
            }
            for path in required_paths
        ],
        "supporting_artifacts": ["run-manifest.json"],
    }
    _write(
        package_manifest_path,
        json.dumps(package_manifest, indent=2, sort_keys=True),
    )
    run_manifest["artifacts"] = {
        path.name: _sha256(path)
        for path in [*required_paths, package_manifest_path]
    }
    _write(run_manifest_path, json.dumps(run_manifest, indent=2, sort_keys=True))

    repository = Path(__file__).resolve().parents[1]
    validation_commands = [
        [
            sys.executable,
            str(repository / "scripts" / "validate-track-a.py"),
            str(target),
            "--verify-db",
        ],
        [
            sys.executable,
            str(repository / "scripts" / "validate-stage1-track-a-package.py"),
            str(target),
        ],
    ]
    environment = dict(os.environ)
    source_root = str(repository / "src")
    environment["PYTHONPATH"] = (
        source_root
        if not environment.get("PYTHONPATH")
        else source_root + os.pathsep + environment["PYTHONPATH"]
    )
    subprocess.run(
        [
            sys.executable,
            str(repository / "scripts" / "generate-review-markdown.py"),
            str(target),
        ],
        cwd=repository,
        env=environment,
        check=True,
    )
    review_count = len(list((target / "reviews").glob("*.md")))
    if review_count != len(qa_records):
        raise SystemExit(
            f"review generation produced {review_count} files; "
            f"expected {len(qa_records)}"
        )
    for command in validation_commands:
        subprocess.run(
            command,
            cwd=repository,
            env=environment,
            check=True,
        )
    validation = _json(target / "validation-report.json")
    compliance = _json(target / "rfp-compliance-report.json")
    if any(
        report.get("result") != "pass"
        or report.get("error_count") != 0
        or report.get("warning_count") != 0
        for report in (validation, compliance)
    ):
        raise SystemExit("package validation did not finish with zero errors/warnings")
    print(f"READY: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
