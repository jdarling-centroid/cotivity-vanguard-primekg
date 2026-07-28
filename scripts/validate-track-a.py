#!/usr/bin/env python3
"""Validate Stage 1 Track A artifacts and PrimeKG evidence provenance.

Structural and internal provenance checks run offline.  ``--verify-db`` adds
local Oracle checks that every cited source_ref exists and every support edge
matches its path endpoints, predicate, and display relation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml

from vanguard_primekg.submission import validate_vendor_id

QA_REQUIRED = {
    "question_id", "category", "question", "vendor_answer", "answer_type",
    "confidence", "retrieved_context", "citations", "graph_nodes_used",
    "graph_edges_used", "reasoning_trace_ref", "latency_ms",
}
TRACE_REQUIRED = {"trace_id", "question_id", "steps", "final_answer", "answer_supported_by"}
NAME_RE = re.compile(
    r"^vendor_([A-Za-z0-9][A-Za-z0-9_-]{0,63})_stage1_"
    r"(qa-results|reasoning-traces)_v([1-9][0-9]*)\.(jsonl|json)$"
)
READ_ONLY_RE = re.compile(r"^\s*(WITH|SELECT)\b", re.I)
WRITE_SQL_RE = re.compile(r"\b(INSERT|UPDATE|DELETE|MERGE|DROP|ALTER|CREATE|TRUNCATE|GRANT|REVOKE|CALL|EXECUTE)\b", re.I)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_jsonl(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        for line_number, line in enumerate(handle, 1):
            if "\r" in line:
                errors.append(f"{path.name}:{line_number}: non-Unix line ending")
            if not line.strip():
                errors.append(f"{path.name}:{line_number}: blank JSONL line")
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"{path.name}:{line_number}: invalid JSON: {exc}")
                continue
            if not isinstance(item, dict):
                errors.append(f"{path.name}:{line_number}: record is not an object")
                continue
            records.append(item)
    return records


def _load_questions(path: Path) -> dict[str, str]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    questions: dict[str, str] = {}
    for section in data.get("sections", []):
        for item in section.get("questions", []):
            question_id = f"Q-KG-{int(item['number']):03d}"
            questions[question_id] = item["question"]
    return questions


def _unique_strings(value: Any, label: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        errors.append(f"{label}: must be an array of strings")
        return []
    if len(value) != len(set(value)):
        errors.append(f"{label}: contains duplicates")
    return value


def _ref_map(items: Any, label: str, errors: list[str]) -> dict[str, dict[str, Any]]:
    if not isinstance(items, list):
        errors.append(f"{label}: must be an array")
        return {}
    result: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"{label}[{index}]: must be an object")
            continue
        ref = item.get("source_ref")
        source_type = item.get("source_type")
        if not isinstance(ref, str) or not ref:
            errors.append(f"{label}[{index}]: missing source_ref")
            continue
        if source_type not in {"primekg_node", "primekg_edge"}:
            errors.append(f"{label}[{index}]: invalid source_type {source_type!r}")
        if ref in result:
            errors.append(f"{label}: duplicate source_ref {ref}")
        result[ref] = item
    return result


def _find_artifacts(directory: Path) -> tuple[Path, Path, str, int]:
    qa: list[tuple[Path, re.Match[str]]] = []
    traces: list[tuple[Path, re.Match[str]]] = []
    for path in directory.iterdir():
        if not path.is_file():
            continue
        match = NAME_RE.match(path.name)
        if not match:
            continue
        (qa if match.group(2) == "qa-results" else traces).append((path, match))
    if len(qa) != 1 or len(traces) != 1:
        raise SystemExit(
            f"expected exactly one qa-results and one reasoning-traces artifact; "
            f"found {len(qa)} and {len(traces)}"
        )
    qa_path, qa_match = qa[0]
    trace_path, trace_match = traces[0]
    if qa_match.group(1) != trace_match.group(1) or qa_match.group(3) != trace_match.group(3):
        raise SystemExit("artifact vendor IDs or versions do not match")
    if qa_match.group(4) != "jsonl" or trace_match.group(4) != "json":
        raise SystemExit("artifact extensions do not match the RFP convention")
    return qa_path, trace_path, qa_match.group(1), int(qa_match.group(3))


def _collect_support_paths(trace: dict[str, Any], errors: list[str]) -> list[dict[str, Any]]:
    steps = trace.get("steps")
    if not isinstance(steps, list):
        return []
    paths: list[dict[str, Any]] = []
    expected_step = 1
    for step in steps:
        if not isinstance(step, dict):
            errors.append(f"{trace.get('trace_id')}: trace step is not an object")
            continue
        if step.get("step") != expected_step:
            errors.append(f"{trace.get('trace_id')}: steps are not consecutively ordered")
        expected_step += 1
        if step.get("operation") == "support_path":
            paths.append(step)
    return paths


def _chunked(values: list[str], size: int = 500) -> Iterable[list[str]]:
    for index in range(0, len(values), size):
        yield values[index:index + size]


def _verify_database(
    node_refs: set[str],
    edge_claims: dict[str, set[tuple[str, str, str, str]]],
    errors: list[str],
) -> None:
    from vanguard_primekg.db import connect

    with connect() as conn:
        node_found: set[str] = set()
        edge_found: dict[str, tuple[str, str, str, str]] = {}
        with conn.cursor() as cursor:
            for chunk in _chunked(sorted(node_refs)):
                binds = {f"n{i}": value for i, value in enumerate(chunk)}
                in_list = ",".join(f":{key}" for key in binds)
                cursor.execute(f"SELECT node_id FROM pk_nodes WHERE node_id IN ({in_list})", binds)
                node_found.update(str(row[0]) for row in cursor.fetchall())
            for chunk in _chunked(sorted(edge_claims)):
                binds = {f"e{i}": value for i, value in enumerate(chunk)}
                in_list = ",".join(f":{key}" for key in binds)
                cursor.execute(
                    "SELECT edge_id, source_node_id, target_node_id, predicate, display_relation "
                    f"FROM pk_edges WHERE edge_id IN ({in_list})",
                    binds,
                )
                for row in cursor.fetchall():
                    edge_found[str(row[0])] = tuple(str(value) for value in row[1:5])
        for node_id in sorted(node_refs - node_found):
            errors.append(f"database: missing cited node {node_id}")
        for edge_id, claims in edge_claims.items():
            actual = edge_found.get(edge_id)
            if actual is None:
                errors.append(f"database: missing cited edge {edge_id}")
            elif actual not in claims:
                errors.append(
                    f"database: edge {edge_id} actual endpoints/predicate/display {actual!r} "
                    f"do not match claimed path {sorted(claims)!r}"
                )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("submission_directory", type=Path)
    parser.add_argument("--questions", type=Path)
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--verify-db", action="store_true")
    parser.add_argument("--no-write-reports", action="store_true")
    args = parser.parse_args(argv)

    directory = args.submission_directory.resolve()
    qa_path, trace_path, vendor_id, version = _find_artifacts(directory)
    errors: list[str] = []
    try:
        normalized_vendor = validate_vendor_id(vendor_id)
        if normalized_vendor != vendor_id:
            errors.append("artifact vendor ID must use normalized lowercase form")
    except ValueError as exc:
        errors.append(f"invalid artifact vendor ID: {exc}")
    warnings: list[str] = []
    qa_records = _load_jsonl(qa_path, errors)
    trace_bytes = trace_path.read_bytes()
    if b"\r" in trace_bytes:
        errors.append(f"{trace_path.name}: non-Unix line ending")
    try:
        traces = json.loads(trace_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append(f"{trace_path.name}: invalid UTF-8 JSON: {exc}")
        traces = []
    if not isinstance(traces, list):
        errors.append(f"{trace_path.name}: top level must be an array")
        traces = []

    expected_count = len(qa_records) if args.allow_partial else 100
    if len(qa_records) != expected_count:
        errors.append(f"qa record count {len(qa_records)} != {expected_count}")
    if len(traces) != expected_count:
        errors.append(f"trace count {len(traces)} != {expected_count}")

    default_questions = Path(__file__).resolve().parents[1] / "config" / "primekg-question-sets.yaml"
    question_map = _load_questions(args.questions or default_questions)
    qa_by_id: dict[str, dict[str, Any]] = {}
    trace_by_id: dict[str, dict[str, Any]] = {}
    all_node_refs: set[str] = set()
    edge_claims: dict[str, set[tuple[str, str, str, str]]] = {}

    for index, record in enumerate(qa_records):
        prefix = f"qa[{index}]"
        missing = QA_REQUIRED - set(record)
        if missing:
            errors.append(f"{prefix}: missing fields {sorted(missing)}")
        question_id = record.get("question_id")
        if not isinstance(question_id, str):
            errors.append(f"{prefix}: invalid question_id")
            continue
        if not isinstance(record.get("category"), str) or not record.get("category"):
            errors.append(f"{question_id}: category must be non-empty text")
        if not isinstance(record.get("answer_type"), str) or not record.get("answer_type"):
            errors.append(f"{question_id}: answer_type must be non-empty text")
        if not isinstance(record.get("reasoning_trace_ref"), str):
            errors.append(f"{question_id}: reasoning_trace_ref must be text")
        if question_id in qa_by_id:
            errors.append(f"duplicate QA question_id {question_id}")
        qa_by_id[question_id] = record
        expected_text = question_map.get(question_id)
        if expected_text is None:
            errors.append(f"{question_id}: not in supplied question set")
        elif record.get("question") != expected_text:
            errors.append(f"{question_id}: question text does not exactly match supplied set")
        if not isinstance(record.get("vendor_answer"), str) or not record.get("vendor_answer"):
            errors.append(f"{question_id}: vendor_answer must be non-empty text")
        confidence = record.get("confidence")
        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not 0 <= confidence <= 1:
            errors.append(f"{question_id}: confidence must be numeric in [0,1]")
        if not isinstance(record.get("latency_ms"), int) or record.get("latency_ms", -1) < 0:
            errors.append(f"{question_id}: latency_ms must be a non-negative integer")
        citations = _ref_map(record.get("citations"), f"{question_id}.citations", errors)
        contexts = _ref_map(record.get("retrieved_context"), f"{question_id}.retrieved_context", errors)
        if set(citations) != set(contexts):
            errors.append(f"{question_id}: citation and retrieved_context source_ref sets differ")
        nodes = _unique_strings(record.get("graph_nodes_used"), f"{question_id}.graph_nodes_used", errors)
        edges = _unique_strings(record.get("graph_edges_used"), f"{question_id}.graph_edges_used", errors)
        all_node_refs.update(nodes)
        if not set(nodes).issubset(citations):
            errors.append(f"{question_id}: graph_nodes_used contains uncited refs")
        if not set(edges).issubset(citations):
            errors.append(f"{question_id}: graph_edges_used contains uncited refs")
        for ref in nodes:
            if not ref.startswith("pk_n_"):
                errors.append(f"{question_id}: malformed PrimeKG node source_ref {ref}")
            if citations.get(ref, {}).get("source_type") != "primekg_node":
                errors.append(f"{question_id}: node {ref} is not typed primekg_node")
        for ref in edges:
            if not ref.startswith("pk_e_"):
                errors.append(f"{question_id}: malformed PrimeKG edge source_ref {ref}")
            if citations.get(ref, {}).get("source_type") != "primekg_edge":
                errors.append(f"{question_id}: edge {ref} is not typed primekg_edge")

    for index, trace in enumerate(traces):
        prefix = f"trace[{index}]"
        if not isinstance(trace, dict):
            errors.append(f"{prefix}: must be an object")
            continue
        missing = TRACE_REQUIRED - set(trace)
        if missing:
            errors.append(f"{prefix}: missing fields {sorted(missing)}")
        trace_id = trace.get("trace_id")
        question_id = trace.get("question_id")
        if not isinstance(trace_id, str) or not isinstance(question_id, str):
            errors.append(f"{prefix}: invalid trace_id/question_id")
            continue
        if trace_id in trace_by_id:
            errors.append(f"duplicate trace_id {trace_id}")
        trace_by_id[trace_id] = trace
        qa = qa_by_id.get(question_id)
        if qa is None:
            errors.append(f"{trace_id}: no matching QA record")
            continue
        if qa.get("reasoning_trace_ref") != trace_id:
            errors.append(f"{question_id}: reasoning_trace_ref does not resolve one-to-one")
        if trace.get("final_answer") != qa.get("vendor_answer"):
            errors.append(f"{question_id}: trace final_answer differs from vendor_answer")
        steps = trace.get("steps")
        operations = [step.get("operation") for step in steps if isinstance(step, dict)] if isinstance(steps, list) else []
        if "context_check" not in operations and "security_block" not in operations:
            errors.append(f"{question_id}: missing context_check step")
        if "security_block" not in operations and "planner_selection" not in operations:
            errors.append(f"{question_id}: missing planner_selection step")
        for context_step in [
            step for step in (steps if isinstance(steps, list) else [])
            if isinstance(step, dict) and step.get("operation") == "context_check"
        ]:
            if context_step.get("source") != "PrimeKG" or context_step.get("clinical_context_available") is not False:
                errors.append(f"{question_id}: invalid PrimeKG context availability declaration")
            if not isinstance(context_step.get("reason"), str) or "does not encode patient-level" not in context_step.get("reason", ""):
                errors.append(f"{question_id}: context_check reason is missing or unsupported")
        if operations and operations[0] not in {"firewall_check", "security_block"}:
            errors.append(f"{question_id}: first operation is not firewall disposition")
        if "security_block" in operations:
            block = next(step for step in steps if isinstance(step, dict) and step.get("operation") == "security_block")
            if block.get("planner_executed") is not False or block.get("database_executed") is not False:
                errors.append(f"{question_id}: block does not prove pre-model/pre-database execution")
            if qa.get("citations") or qa.get("graph_nodes_used") or qa.get("graph_edges_used"):
                errors.append(f"{question_id}: firewall block must not carry graph evidence")
        for step in steps if isinstance(steps, list) else []:
            if not isinstance(step, dict) or step.get("operation") != "database_composition":
                continue
            query = step.get("query")
            if query is not None:
                if not isinstance(query, str) or not READ_ONLY_RE.search(query) or WRITE_SQL_RE.search(query):
                    errors.append(f"{question_id}: database query is not demonstrably read-only")
            if step.get("authoritative_query_count") != 1:
                errors.append(f"{question_id}: authoritative_query_count must be 1")
            binds = step.get("binds", {})
            if not isinstance(binds, dict):
                errors.append(f"{question_id}: database binds must be an object")
            else:
                for key, value in binds.items():
                    if any(marker in str(key).lower() for marker in ("password", "secret", "token", "key", "credential")) and value != "[REDACTED]":
                        errors.append(f"{question_id}: sensitive bind {key!r} is not redacted")
        paths = _collect_support_paths(trace, errors)
        qa_nodes = set(qa.get("graph_nodes_used") or [])
        qa_edges = set(qa.get("graph_edges_used") or [])
        answer_nodes: set[str] = set()
        for path_index, path in enumerate(paths):
            answer_node = path.get("answer_node_id")
            path_nodes = path.get("path_nodes")
            path_edges = path.get("path_edges")
            predicates = path.get("predicates")
            displays = path.get("display_relations")
            label = f"{question_id}.support_path[{path_index}]"
            if not isinstance(answer_node, str):
                errors.append(f"{label}: missing answer_node_id")
                continue
            answer_nodes.add(answer_node)
            if not all(isinstance(value, list) for value in (path_nodes, path_edges, predicates, displays)):
                errors.append(f"{label}: path fields must be arrays")
                continue
            if not path_nodes or path_nodes[-1] != answer_node:
                errors.append(f"{label}: answer_node_id is not final path node")
            if len(path_edges) != len(path_nodes) - 1:
                errors.append(f"{label}: edge count does not equal node count minus one")
            if len(predicates) != len(path_edges) or len(displays) != len(path_edges):
                errors.append(f"{label}: predicate/display counts do not equal edge count")
            if not set(path_nodes).issubset(qa_nodes) or not set(path_edges).issubset(qa_edges):
                errors.append(f"{label}: path refs are not fully represented in QA graph fields")
            all_node_refs.update(str(value) for value in path_nodes)
            for i, edge_id in enumerate(path_edges):
                if i + 1 >= len(path_nodes) or i >= len(predicates) or i >= len(displays):
                    continue
                claim = (str(path_nodes[i]), str(path_nodes[i + 1]), str(predicates[i]), str(displays[i]))
                edge_claims.setdefault(str(edge_id), set()).add(claim)
        if paths and not answer_nodes:
            errors.append(f"{question_id}: no answer nodes extracted from support paths")
        if paths and not set(trace.get("answer_supported_by") or []).issubset(qa_edges | qa_nodes):
            errors.append(f"{question_id}: answer_supported_by contains refs outside QA evidence")
        planner_operation = next(
            (
                step.get("validated_operation")
                for step in (steps if isinstance(steps, list) else [])
                if isinstance(step, dict) and step.get("operation") == "planner_selection"
            ),
            None,
        )
        if not paths and qa_edges and "insufficient_data" not in operations and planner_operation != "describe":
            errors.append(f"{question_id}: asserted graph edges but no complete support_path")

    if set(qa_by_id) != {trace.get("question_id") for trace in traces if isinstance(trace, dict)}:
        errors.append("QA and trace question_id sets differ")
    if not args.allow_partial and set(qa_by_id) != set(question_map):
        errors.append("artifact question IDs do not exactly match all 100 supplied questions")

    if args.verify_db:
        try:
            _verify_database(all_node_refs, edge_claims, errors)
        except Exception as exc:
            errors.append(f"database verification failed: {type(exc).__name__}: {exc}")
    else:
        warnings.append("local database provenance verification was not requested")

    # Scan artifact bytes for key material, not for ordinary question words.
    dangerous = (b"-----BEGIN PRIVATE KEY-----", b"-----BEGIN RSA PRIVATE KEY-----")
    for path in (qa_path, trace_path):
        payload = path.read_bytes()
        if any(marker in payload for marker in dangerous):
            errors.append(f"{path.name}: contains private key material")

    report = {
        "scope": "Stage 1 Track A PrimeKG only",
        "validator": "validate-track-a.py",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "vendor_id": vendor_id,
        "authoritative_version": version,
        "qa_records": len(qa_records),
        "reasoning_traces": len(traces),
        "database_provenance_checked": args.verify_db,
        "result": "pass" if not errors else "fail",
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }
    if not args.no_write_reports:
        (directory / "validation-report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
        )
        checksum = {
            "scope": "internal delivery QA; not a Track A graph manifest",
            "created_at": report["created_at"],
            "vendor_id": vendor_id,
            "authoritative_version": version,
            "validator_result": report["result"],
            "record_counts": {"qa": len(qa_records), "traces": len(traces)},
            "artifacts": [
                {"name": path.name, "size": path.stat().st_size, "sha256": _sha256(path)}
                for path in (qa_path, trace_path)
            ],
            "configuration_fingerprint": hashlib.sha256(
                json.dumps(
                    {
                        "vendor_id": vendor_id,
                        "version": version,
                        "question_ids": sorted(qa_by_id),
                        "database_provenance_checked": args.verify_db,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest(),
        }
        (directory / "checksum-report.json").write_text(
            json.dumps(checksum, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
        )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
