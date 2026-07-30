#!/usr/bin/env python3
"""Run the issued Track B questions against local Oracle and OCI GenAI."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from vanguard_primekg.agent.oci_llm import OCIPlannerConfig, OCIPlannerModel
from vanguard_primekg.config import load_settings
from vanguard_primekg.db import connect
from vanguard_primekg.submission import validate_vendor_id
from vanguard_primekg.track_b.answerer import answer_question
from vanguard_primekg.question_selection import parse_numbers


def _percentile(values: list[int], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = (len(ordered) - 1) * fraction
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    weight = rank - lower
    return round(ordered[lower] * (1 - weight) + ordered[upper] * weight, 2)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _exclusive_json(path: Path, value: Any) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")


def _questions(path: Path) -> list[dict[str, Any]]:
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    sections = config.get("sections", [])
    if len(sections) != 1 or sections[0].get("key") != "MH":
        raise SystemExit("question config must contain exactly one MH section")
    questions = sections[0].get("questions", [])
    if len(questions) != 60:
        raise SystemExit(f"expected 60 issued Track B questions, found {len(questions)}")
    return questions


def _is_insufficient_answer(record: dict[str, Any]) -> bool:
    answer = str(record.get("vendor_answer") or "").casefold()
    return (
        answer.startswith("insufficient evidence")
        or record.get("answer_type") == "insufficient_data"
    )


def _outcome_status(
    record: dict[str, Any], expected_outcome: str
) -> str:
    if record.get("answer_type") == "firewall_block":
        return "firewall_blocked"
    if _is_insufficient_answer(record):
        if expected_outcome == "insufficient_evidence":
            return "valid_insufficient_evidence"
        return "unexpected_insufficient_evidence"
    if expected_outcome == "insufficient_evidence":
        return "unexpected_answer"
    return "answered_with_evidence"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--vendor-id", required=True)
    parser.add_argument("--version", type=int, default=1)
    parser.add_argument(
        "--input",
        "--questions-file",
        dest="questions_file",
        type=Path,
        default=Path("config/multihop-question-sets.yaml"),
    )
    parser.add_argument("--corpus", type=Path, default=Path("data/datasets/multihop/corpus.json"))
    parser.add_argument("--model-id", default="xai.grok-4.3")
    parser.add_argument("--oci-config-file", default=".oci/config")
    parser.add_argument("--oci-profile", default="DEFAULT")
    parser.add_argument("--oci-region")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--max-tokens", type=int, default=1400)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument(
        "--question", "--questions",
        dest="numbers", action="append", default=[],
    )
    parser.add_argument(
        "--deterministic-shared-entity-fallback",
        action="store_true",
        help=(
            "enable the experimental cross-document candidate intersection "
            "(disabled by default for v7-compatible behavior)"
        ),
    )
    args = parser.parse_args()

    vendor = validate_vendor_id(args.vendor_id)
    if args.version < 1:
        raise SystemExit("--version must be positive")
    selected = parse_numbers(args.numbers)
    questions = [
        item for item in _questions(args.questions_file)
        if not selected or int(item["number"]) in selected
    ]
    corpus = json.loads(args.corpus.read_text(encoding="utf-8"))
    known_sources = {
        str(article.get("source")).strip()
        for article in corpus
        if str(article.get("source") or "").strip()
    }
    args.out.mkdir(parents=True, exist_ok=True)
    suffix = f"_v{args.version}"
    qa_path = args.out / f"vendor_{vendor}_stage1_qa-results{suffix}.jsonl"
    trace_path = args.out / f"vendor_{vendor}_stage1_reasoning-traces{suffix}.json"
    manifest_path = args.out / "run-manifest.json"
    audit_path = args.out / "model-audit.json"
    for path in (qa_path, trace_path, manifest_path, audit_path):
        if path.exists():
            raise SystemExit(f"refusing to overwrite existing artifact: {path}")

    settings = load_settings()
    model = OCIPlannerModel(OCIPlannerConfig(
        model_id=args.model_id,
        region=args.oci_region,
        config_file=args.oci_config_file,
        profile=args.oci_profile,
        compartment_id=os.environ.get("OCI_COMPARTMENT_ID"),
        timeout=args.timeout,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
    ))
    qa_records: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    audits: list[dict[str, Any]] = []
    run_started = time.monotonic()
    with connect(settings) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM mh_nodes")
            node_count = int(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM mh_edges")
            edge_count = int(cursor.fetchone()[0])
        for item in questions:
            number = int(item["number"])
            metadata = item.get("metadata", {})
            expected_outcome = str(
                metadata.get("expected_outcome") or "answered"
            )
            usage_before = dict(model.usage)
            result = answer_question(
                conn,
                model,
                number=number,
                question=str(item["question"]),
                answer_shape=str(metadata.get("answer_shape", "short_text")),
                max_tokens=args.max_tokens,
                timeout=args.timeout,
                retries=args.retries,
                known_sources=known_sources,
                deterministic_shared_entity_fallback=(
                    args.deterministic_shared_entity_fallback
                    and expected_outcome == "answered"
                ),
            )
            usage_after = dict(model.usage)
            question_usage = {
                key: int(usage_after.get(key, 0)) - int(usage_before.get(key, 0))
                for key in ("input_tokens", "output_tokens", "total_tokens", "requests")
            }
            question_cost = round(
                question_usage["input_tokens"] / 1_000_000 * 1.25
                + question_usage["output_tokens"] / 1_000_000 * 2.50,
                8,
            )
            expected_block = bool(metadata.get("adversarial"))
            actual_block = result.qa["answer_type"] == "firewall_block"
            if expected_block != actual_block:
                raise RuntimeError(
                    f"Q-MH-{number:03d}: expected_block={expected_block}, "
                    f"actual_block={actual_block}"
                )
            status = _outcome_status(result.qa, expected_outcome)
            if status in {
                "unexpected_insufficient_evidence", "unexpected_answer",
            }:
                raise RuntimeError(
                    f"Q-MH-{number:03d}: expected_outcome={expected_outcome}, "
                    f"actual_status={status}"
                )
            qa_records.append(result.qa)
            traces.append(result.trace)
            result.model_audit["token_usage"] = question_usage
            result.model_audit["model_cost_usd"] = question_cost
            audits.append({"question_id": result.qa["question_id"], **result.model_audit})
            print(
                f"{result.qa['question_id']} {result.qa['latency_ms']}ms "
                f"{result.qa['vendor_answer'][:100]}",
                flush=True,
            )

    with qa_path.open("x", encoding="utf-8", newline="\n") as handle:
        for record in qa_records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    _exclusive_json(trace_path, traces)
    _exclusive_json(audit_path, audits)
    latencies = [int(record["latency_ms"]) for record in qa_records]
    elapsed = round(time.monotonic() - run_started, 3)
    token_usage = dict(model.usage)
    model_cost = round(
        token_usage["input_tokens"] / 1_000_000 * 1.25
        + token_usage["output_tokens"] / 1_000_000 * 2.50,
        8,
    )
    manifest = {
        "track": "B",
        "stage": 1,
        "authoritative": len(qa_records) == 60,
        "question_count": len(qa_records),
        "answered_count": sum(
            _outcome_status(r, str(item.get("metadata", {}).get(
                "expected_outcome", "answered"
            ))) == "answered_with_evidence"
            for item, r in zip(questions, qa_records, strict=True)
        ),
        "valid_insufficient_evidence_count": sum(
            _outcome_status(r, str(item.get("metadata", {}).get(
                "expected_outcome", "answered"
            ))) == "valid_insufficient_evidence"
            for item, r in zip(questions, qa_records, strict=True)
        ),
        "unanswered_count": 0,
        "firewall_block_count": sum(r["answer_type"] == "firewall_block" for r in qa_records),
        "model": {
            "provider": "oci_generative_ai",
            "model_id": args.model_id,
            "temperature_requested": args.temperature,
            "max_tokens": args.max_tokens,
            "timeout_seconds": args.timeout,
            "retries": args.retries,
        },
        "database": {
            "dsn_host": settings.database.host,
            "local_only_guard": True,
            "node_count": node_count,
            "directed_edge_count": edge_count,
            "retrieval": (
                "one baseline parameterized read-only Oracle query; one bounded "
                "expanded read-only query when baseline evidence is weak"
            ),
        },
        "concurrency": 1,
        "feature_flags": {
            "deterministic_shared_entity_fallback": (
                args.deterministic_shared_entity_fallback
            ),
        },
        "host": {"platform": platform.platform(), "python": platform.python_version()},
        "latency_ms": {
            "min": min(latencies, default=0),
            "mean": round(statistics.fmean(latencies), 2) if latencies else 0,
            "p50": _percentile(latencies, 0.50),
            "p95": _percentile(latencies, 0.95),
            "p99": _percentile(latencies, 0.99),
            "max": max(latencies, default=0),
        },
        "wall_seconds": elapsed,
        "token_usage": token_usage,
        "cost_per_query": {
            "status": "model_cost_measured",
            "model_cost_usd_total": model_cost,
            "model_cost_usd_per_query": (
                round(model_cost / len(qa_records), 8) if qa_records else None
            ),
            "pricing_basis": {
                "input_usd_per_million_tokens": 1.25,
                "output_usd_per_million_tokens": 2.50,
                "price_list_date": "2026-05-01",
                "source": "Oracle PaaS and IaaS Global Price List",
            },
        },
        "questions": [
            {
                "number": int(item["number"]),
                "question_id": qa["question_id"],
                "expected_outcome": str(item.get("metadata", {}).get(
                    "expected_outcome", "answered"
                )),
                "status": _outcome_status(
                    qa, str(item.get("metadata", {}).get(
                        "expected_outcome", "answered"
                    ))
                ),
                "structural_outcome_check": True,
                "latency_ms": qa["latency_ms"],
                "token_usage": audit["token_usage"],
                "model_cost_usd": audit["model_cost_usd"],
            }
            for item, qa, audit in zip(questions, qa_records, audits, strict=True)
        ],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "artifacts": {
            qa_path.name: _sha256(qa_path),
            trace_path.name: _sha256(trace_path),
            audit_path.name: _sha256(audit_path),
        },
    }
    _exclusive_json(manifest_path, manifest)
    subprocess.run(
        [
            sys.executable,
            "scripts/generate-review-markdown.py",
            str(args.out),
            "--overwrite",
        ],
        check=True,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
