"""Run Track A questions and optionally write versioned submission artifacts.

The reported harness result is a structural outcome check only.  Cotiviti owns
the withheld correctness key; this script never labels its own result accuracy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import statistics
import sys
from contextlib import nullcontext
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from vanguard_primekg._vendor.finalizer import Finalizer
from vanguard_primekg._vendor.models import SessionResult
from vanguard_primekg.agent import AgentPlanner, RegexPlanner, StubPlannerModel
from vanguard_primekg.agent.oci_llm import OCIPlannerConfig, OCIPlannerModel
from vanguard_primekg.agent.prompt import PROMPT_VERSION
from vanguard_primekg.backends import PgqBackend, SelectAiBackend, SelectAiUnavailable
from vanguard_primekg.config import load_settings
from vanguard_primekg.db import connect
from vanguard_primekg.question_selection import parse_numbers
from vanguard_primekg.solver import solve
from vanguard_primekg.submission import validate_vendor_id


def _status(result: SessionResult) -> str:
    if result.answer.answer == "Won't do that":
        return "blocked"
    if any(step.get("operation") == "insufficient_data" for step in result.steps):
        return "insufficient_with_evidence" if result.retrieved_context else "insufficient_no_evidence"
    if result.graph_edges_used and result.retrieved_context:
        return "answered_with_evidence"
    if result.answer_supported_by == ["NONE"] and not result.graph_nodes_used:
        return "refused"
    return "answered_no_evidence"


def structural_outcome_check(meta: dict[str, Any], status: str) -> bool:
    """Smoke-check disposition/evidence shape; this is not answer accuracy."""
    expected = meta.get("expected_outcome", "answered")
    if expected == "blocked":
        return status == "blocked"
    if expected == "insufficient_data":
        return status == "insufficient_with_evidence"
    return status == "answered_with_evidence"


def _review_md(number: int, text: str, meta: dict, result: SessionResult, status: str) -> str:
    query_step = next(
        (step for step in result.steps if step.get("operation") == "database_composition"),
        {},
    )
    lines = [
        f"# PrimeKG - Q{number}",
        "",
        f"**Question:** {text}",
        "",
        f"- expected outcome class: {meta.get('expected_outcome')}",
        f"- structural status: {status}",
        f"- planner: {result.audit.get('planner', {}).get('planner', 'unknown')}",
        f"- confidence basis: {result.confidence_basis}",
        f"- truncated: {result.truncated}",
        "",
        "## Answer",
        "",
        result.answer.answer,
        "",
        "## Answer support",
        "",
        *(f"- {ref}" for ref in result.answer_supported_by),
        "",
    ]
    if query_step.get("query"):
        lines += ["## Executed read-only query", "", "```sql", query_step["query"], "```", ""]
    lines += [
        "## Planner audit",
        "",
        "```json",
        json.dumps(result.audit.get("planner", {}), indent=2, sort_keys=True),
        "```",
        "",
    ]
    return "\n".join(lines)


def _percentile(values: list[int], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = (len(ordered) - 1) * percentile
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    weight = rank - lower
    return round(ordered[lower] * (1 - weight) + ordered[upper] * weight, 2)


def _memory_gib() -> float | None:
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal:"):
                return round(int(line.split()[1]) / 1024 / 1024, 2)
    except OSError:
        pass
    return None


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _database_snapshot(conn) -> dict[str, Any]:
    """Collect non-secret configuration and load identity for the run manifest."""
    snapshot: dict[str, Any] = {
        "oracle_client_reported_version": getattr(conn, "version", None),
        "node_count": None,
        "directed_edge_count": None,
        "load_journal": None,
    }
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM pk_nodes")
            snapshot["node_count"] = int(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM pk_edges")
            snapshot["directed_edge_count"] = int(cursor.fetchone()[0])
            cursor.execute(
                "SELECT kg_checksum, relations, nodes_loaded, edges_loaded, status, "
                "TO_CHAR(updated_at, 'YYYY-MM-DD\"T\"HH24:MI:SS.FF6') "
                "FROM pk_load_journal ORDER BY id DESC FETCH FIRST 1 ROW ONLY"
            )
            row = cursor.fetchone()
            if row:
                snapshot["load_journal"] = {
                    "kg_checksum": row[0],
                    "relations": row[1],
                    "nodes_loaded": int(row[2]) if row[2] is not None else None,
                    "directed_edges_loaded": int(row[3]) if row[3] is not None else None,
                    "status": row[4],
                    "updated_at": row[5],
                }
    except Exception as exc:
        snapshot["metadata_error"] = f"{type(exc).__name__}: {str(exc).splitlines()[0]}"
    return snapshot


def _planner(args: argparse.Namespace, repo_root: Path):
    if args.planner == "regex":
        return RegexPlanner()
    if args.agent_provider == "stub":
        if not args.planner_fixtures:
            raise SystemExit("--planner-fixtures is required for --agent-provider stub")
        fixtures = json.loads(args.planner_fixtures.read_text(encoding="utf-8"))
        model = StubPlannerModel(fixtures)
        model_id = "offline-fixture-stub"
    else:
        model_id = args.model_id or os.environ.get("VPK_PLANNER_MODEL_ID")
        if not model_id:
            raise SystemExit("agent planner requires --model-id or VPK_PLANNER_MODEL_ID")
        config = OCIPlannerConfig(
            model_id=model_id,
            region=args.oci_region or os.environ.get("OCI_REGION"),
            config_file=args.oci_config_file,
            profile=args.oci_profile,
            compartment_id=os.environ.get("OCI_COMPARTMENT_ID"),
            timeout=args.planner_timeout,
            max_tokens=args.planner_max_tokens,
            temperature=args.temperature,
        )
        model = OCIPlannerModel(config)
    return AgentPlanner(
        model,
        repo_root=repo_root,
        provider=args.agent_provider,
        model_id=model_id,
        prompt_version=args.prompt_version,
        timeout=args.planner_timeout,
        max_tokens=args.planner_max_tokens,
        retries=args.planner_retries,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", choices=["pgq", "select_ai"], default="pgq")
    parser.add_argument("--planner", choices=["regex", "agent"], default="regex")
    parser.add_argument("--agent-provider", choices=["oci", "stub"], default="oci")
    parser.add_argument("--model-id")
    parser.add_argument("--oci-region")
    parser.add_argument("--oci-config-file")
    parser.add_argument("--oci-profile", default="DEFAULT")
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--prompt-version", default=PROMPT_VERSION)
    parser.add_argument("--planner-timeout", type=float, default=60.0)
    parser.add_argument("--planner-max-tokens", type=int, default=1800)
    parser.add_argument("--planner-retries", type=int, default=2)
    parser.add_argument("--planner-fixtures", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--vendor-id", help="Required with --out; actual Cotiviti vendor identifier.")
    parser.add_argument("--version", type=int, default=1)
    parser.add_argument("--input", type=Path)
    parser.add_argument(
        "--question", "--questions",
        dest="numbers", action="append", default=[],
    )
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args(argv)

    settings = load_settings()
    questions_path = args.input or settings.repo_root / "config" / "primekg-question-sets.yaml"
    if args.out is not None:
        if not args.vendor_id:
            raise SystemExit("--vendor-id is required when writing submission artifacts")
        args.vendor_id = validate_vendor_id(args.vendor_id)
        if args.version < 1:
            raise SystemExit("--version must be >= 1")
        args.out.mkdir(parents=True, exist_ok=True)
        reviews_dir = args.out / "reviews"
        reviews_dir.mkdir(exist_ok=True)
    else:
        reviews_dir = None

    data = yaml.safe_load(questions_path.read_text(encoding="utf-8"))
    questions = data["sections"][0]["questions"]
    wanted = parse_numbers(args.numbers)
    if wanted:
        questions = [question for question in questions if question["number"] in wanted]
        if not questions:
            raise SystemExit("no matching questions")

    planner = _planner(args, settings.repo_root)
    structural_passes = 0
    manifest_questions: list[dict[str, Any]] = []
    results: list[SessionResult] = []
    finalizer = (
        Finalizer(args.out, vendor_id=args.vendor_id, version=args.version)
        if args.out is not None
        else nullcontext(None)
    )

    with connect() as conn, finalizer as fin:
        conn.call_timeout = 20000
        if args.backend == "select_ai":
            try:
                backend = SelectAiBackend(conn)
            except SelectAiUnavailable as exc:
                print(f"select_ai unavailable: {exc}", file=sys.stderr)
                return 2
        else:
            backend = PgqBackend(conn)
        database_snapshot = _database_snapshot(conn)
        for question in questions:
            number = question["number"]
            text = question["question"]
            meta = question["metadata"]
            result = solve(number, text, backend, planner=planner, verbose=args.verbose)
            results.append(result)
            if fin is not None:
                fin.write(result)
            status = _status(result)
            structural_ok = structural_outcome_check(meta, status)
            structural_passes += int(structural_ok)
            print(f"Q{number}: {result.answer.answer}")
            print(
                f"  [{status}; structural outcome {'ok' if structural_ok else 'mismatch'}]",
                file=sys.stderr,
            )
            if reviews_dir is not None:
                (reviews_dir / f"PrimeKG - Q{number}.md").write_text(
                    _review_md(number, text, meta, result, status),
                    encoding="utf-8",
                    newline="\n",
                )
            answer_node_ids = sorted({
                str(step["answer_node_id"])
                for step in result.steps
                if step.get("operation") == "support_path" and step.get("answer_node_id")
            })
            manifest_questions.append(
                {
                    "number": number,
                    "question_id": result.question.question_id,
                    "expected_outcome": meta.get("expected_outcome"),
                    "status": status,
                    "structural_outcome_check": structural_ok,
                    "plan": result.audit.get("planner", {}).get("validated_plan"),
                    "planner_audit": result.audit.get("planner", {}),
                    "answer_node_ids": answer_node_ids,
                    "answer_node_count": len(answer_node_ids),
                    "support_edge_count": len(result.graph_edges_used),
                    "retrieved_context_count": len(result.retrieved_context),
                    "latency_ms": result.latency_ms,
                    "truncated": result.truncated,
                }
            )

    latencies = [result.latency_ms for result in results]
    print(
        f"backend={args.backend} planner={args.planner} structural outcome "
        f"{structural_passes}/{len(questions)} (not accuracy)",
        file=sys.stderr,
    )
    if args.out is not None:
        artifact_paths = [fin.results_path, fin.traces_path]
        token_usage = getattr(planner, "usage", None)
        input_rate = 1.25
        output_rate = 2.50
        model_cost = None
        if token_usage:
            model_cost = round(
                token_usage["input_tokens"] / 1_000_000 * input_rate
                + token_usage["output_tokens"] / 1_000_000 * output_rate,
                6,
            )
        manifest = {
            "run_label": os.environ.get("VPK_RUN_LABEL"),
            "scope": "Stage 1 Track A PrimeKG only",
            "track_b_modified": False,
            "authoritative_version": args.version,
            "vendor_id": args.vendor_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "question_count": len(questions),
            "structural_outcome_check": {
                "passed": structural_passes,
                "total": len(questions),
                "explicitly_not_accuracy": True,
            },
            "latency_ms": {
                "queries": len(latencies),
                "concurrency": 1,
                "p50": _percentile(latencies, 0.50),
                "p95": _percentile(latencies, 0.95),
                "p99": _percentile(latencies, 0.99),
                "mean": round(statistics.fmean(latencies), 2) if latencies else 0,
            },
            "hardware": {
                "platform": platform.platform(),
                "machine": platform.machine(),
                "cpu_count": os.cpu_count(),
                "ram_gib": _memory_gib(),
                "gpu": "not detected/reported by harness",
            },
            "planner": {
                "mode": args.planner,
                "provider": (
                    results[0].audit.get("planner", {}).get("provider")
                    if results else (args.agent_provider if args.planner == "agent" else "deterministic")
                ),
                "model_id": (
                    results[0].audit.get("planner", {}).get("model_id")
                    if results else (args.model_id if args.planner == "agent" else "regex-baseline")
                ),
                "temperature_sent": args.temperature if args.planner == "agent" else None,
                "prompt_version": (
                    results[0].audit.get("planner", {}).get("prompt_version")
                    if results else (args.prompt_version if args.planner == "agent" else "classify.py")
                ),
                "timeout_seconds": args.planner_timeout if args.planner == "agent" else None,
                "max_tokens": args.planner_max_tokens if args.planner == "agent" else None,
                "max_retries": args.planner_retries if args.planner == "agent" else None,
            },
            "token_usage": token_usage,
            "database": {
                "backend": args.backend,
                "dsn_host": settings.database.host,
                "call_timeout_ms": 20000,
                "remote_allowed": os.environ.get("VPK_ALLOW_REMOTE") == "1",
                **database_snapshot,
            },
            "cost_per_query": {
                "status": "model_cost_measured" if model_cost is not None else "not_applicable",
                "model_cost_usd_total": model_cost,
                "model_cost_usd_per_query": (
                    round(model_cost / len(questions), 8)
                    if model_cost is not None and questions else None
                ),
                "pricing_basis": {
                    "input_usd_per_million_tokens": input_rate,
                    "output_usd_per_million_tokens": output_rate,
                    "price_list_date": "2026-05-01",
                    "source": "Oracle PaaS and IaaS Global Price List",
                },
                "scope_note": "Model API cost; local hardware/storage cost is reported separately.",
            },
            "artifacts": [
                {
                    "name": path.name,
                    "size": path.stat().st_size,
                    "sha256": _file_sha256(path),
                }
                for path in artifact_paths
            ],
            "questions": manifest_questions,
        }
        (args.out / "run-manifest.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8", newline="\n"
        )
        print(f"artifacts: {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
