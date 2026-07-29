#!/usr/bin/env python3
"""Generate human-readable Track A or Track B review Markdown."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def _artifact(directory: Path, pattern: str) -> Path:
    matches = sorted(directory.glob(pattern))
    if len(matches) != 1:
        raise SystemExit(
            f"expected exactly one {pattern!r} in {directory}, found {len(matches)}"
        )
    return matches[0]


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise SystemExit(f"{path}:{number}: expected a JSON object")
            records.append(value)
    return records


def _question_parts(question_id: str) -> tuple[str, int]:
    match = re.fullmatch(r"Q-(KG|MH)-(\d{3})", question_id)
    if not match:
        raise SystemExit(f"invalid Stage 1 question_id: {question_id!r}")
    return match.group(1), int(match.group(2))


def _question_number(question_id: str) -> int:
    return _question_parts(question_id)[1]


def _json_block(value: Any) -> list[str]:
    return ["```json", json.dumps(value, indent=2, sort_keys=True), "```"]


def _render_step(index: int, step: dict[str, Any]) -> list[str]:
    operation = str(step.get("operation", "unknown"))
    lines = [f"### {index}. `{operation}`", ""]
    if operation == "firewall_check":
        lines.append(
            f"Status: **{step.get('status', 'unknown')}**; executed before planner: "
            f"`{step.get('executed_before_planner')}`."
        )
    elif operation == "planner_selection":
        lines.append(
            f"Planner: `{step.get('planner')}` / `{step.get('provider')}` / "
            f"`{step.get('model_id')}`; prompt `{step.get('prompt_version')}`; "
            f"validated operation `{step.get('validated_operation')}`; "
            f"attempts `{step.get('attempts')}`; deterministic fallback "
            f"`{step.get('deterministic_fallback_used', False)}`."
        )
    elif operation == "entity_lookup":
        lines += [
            f"Input `{step.get('input')}` resolved to `{step.get('node_id')}` "
            f"({step.get('node_type')}) using `{step.get('resolution_method')}` "
            f"with score `{step.get('resolution_score')}`."
        ]
    elif operation == "database_composition":
        lines += [
            f"Composition: `{step.get('composition')}`; read-only: "
            f"`{step.get('read_only')}`; authoritative query count: "
            f"`{step.get('authoritative_query_count')}`; returned answer nodes: "
            f"`{step.get('answer_node_count')}`; truncated: `{step.get('truncated')}`.",
            "",
            "#### Executed SQL",
            "",
            "```sql",
            str(step.get("query", "")),
            "```",
            "",
            "#### Safe binds",
            "",
            *_json_block(step.get("binds", {})),
        ]
    elif operation == "support_path":
        predicates = list(step.get("predicates", []))
        displays = list(step.get("display_relations", []))
        relations = [
            f"{predicate} / {displays[i] if i < len(displays) else ''}"
            for i, predicate in enumerate(predicates)
        ]
        lines += [
            f"Answer node: `{step.get('answer_node_id')}`",
            "",
            f"- Nodes: {' → '.join(f'`{value}`' for value in step.get('path_nodes', []))}",
            f"- Edges: {' → '.join(f'`{value}`' for value in step.get('path_edges', []))}",
            f"- Relations: {' → '.join(f'`{value}`' for value in relations)}",
            f"- Semantics: {step.get('semantics')}",
        ]
    else:
        details = {key: value for key, value in step.items() if key != "step"}
        lines += _json_block(details)
    return lines + [""]


def _question_metrics(
    qa: dict[str, Any],
    manifest: dict[str, Any] | None,
) -> dict[str, Any]:
    manifest = manifest or {}
    question_id = str(qa["question_id"])
    questions = manifest.get("questions", [])
    question = next(
        (
            item for item in questions
            if isinstance(item, dict) and str(item.get("question_id")) == question_id
        ),
        {},
    )
    usage = question.get("token_usage")
    exact_usage = isinstance(usage, dict)
    if qa.get("answer_type") == "firewall_block":
        usage = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "requests": 0,
        }
        exact_usage = True
    if not exact_usage:
        usage = {}
    return {
        "latency_ms": qa.get("latency_ms"),
        "status": question.get("status", qa.get("answer_type")),
        "structural_outcome_check": question.get("structural_outcome_check"),
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "total_tokens": usage.get("total_tokens"),
        "model_requests": usage.get("requests"),
        "model_cost_usd": (
            0.0
            if qa.get("answer_type") == "firewall_block"
            else question.get("model_cost_usd")
        ),
        "per_question_usage_exact": exact_usage,
    }


def render_review(
    qa: dict[str, Any],
    trace: dict[str, Any],
    manifest: dict[str, Any] | None = None,
) -> str:
    question_id = str(qa["question_id"])
    key, number = _question_parts(question_id)
    title = "PrimeKG" if key == "KG" else "MultiHop RAG"
    supported_by = trace.get("answer_supported_by", [])
    metrics = _question_metrics(qa, manifest)
    execution_facts = [
        f"- disposition/status: `{metrics['status']}`",
        f"- elapsed time: `{metrics['latency_ms']} ms`",
    ]
    if metrics["structural_outcome_check"] is not None:
        execution_facts.insert(
            1,
            f"- structural outcome check: `{metrics['structural_outcome_check']}` "
            "(shape/evidence check only; not answer accuracy)",
        )
    if metrics["per_question_usage_exact"]:
        execution_facts.extend([
            f"- model requests: `{metrics['model_requests']}`",
            f"- input tokens: `{metrics['input_tokens']}`",
            f"- output tokens: `{metrics['output_tokens']}`",
            f"- total tokens: `{metrics['total_tokens']}`",
            f"- measured model cost: `{metrics['model_cost_usd']} USD`",
        ])
    lines = [
        f"# {title} - Q{number}",
        "",
        f"**Question ID:** `{question_id}`",
        "",
        f"**Question:** {qa.get('question', '')}",
        "",
        f"- category: `{qa.get('category')}`",
        f"- answer type: `{qa.get('answer_type')}`",
        f"- confidence: `{qa.get('confidence')}`",
        f"- confidence basis: `{qa.get('confidence_basis')}`",
        f"- latency: `{qa.get('latency_ms')} ms`",
        f"- truncated: `{qa.get('truncated')}`",
        f"- reasoning trace: `{qa.get('reasoning_trace_ref')}`",
        "",
        "## Question execution facts",
        "",
        *execution_facts,
        "",
        "## Answer",
        "",
        str(qa.get("vendor_answer", "")),
        "",
        "## Answer support",
        "",
        *(f"- `{reference}`" for reference in supported_by),
        "",
        "## Reasoning and evidence path",
        "",
    ]
    for index, step in enumerate(trace.get("steps", []), 1):
        lines.extend(_render_step(index, step))
    lines += [
        "## Graph elements used",
        "",
        "### Nodes",
        "",
        *(f"- `{node_id}`" for node_id in qa.get("graph_nodes_used", [])),
        "",
        "### Edges",
        "",
        *(f"- `{edge_id}`" for edge_id in qa.get("graph_edges_used", [])),
        "",
        "## Citations",
        "",
        *_json_block(qa.get("citations", [])),
        "",
        "## Retrieved context",
        "",
        *_json_block(qa.get("retrieved_context", [])),
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "submission_dir",
        type=Path,
        help="directory containing one QA JSONL and one reasoning-trace JSON",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="review output directory (default: <submission_dir>/reviews)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="replace existing review Markdown files",
    )
    args = parser.parse_args()

    source = args.submission_dir.resolve()
    qa_path = _artifact(source, "vendor_*_stage1_qa-results_v*.jsonl")
    trace_path = _artifact(source, "vendor_*_stage1_reasoning-traces_v*.json")
    qa_records = _load_jsonl(qa_path)
    traces = json.loads(trace_path.read_text(encoding="utf-8"))
    if not isinstance(traces, list) or not all(isinstance(item, dict) for item in traces):
        raise SystemExit(f"{trace_path}: expected a JSON array of objects")
    manifest_path = source / "run-manifest.json"
    manifest = (
        json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest_path.exists()
        else {}
    )

    qa_by_id = {str(item.get("question_id")): item for item in qa_records}
    trace_by_id = {str(item.get("question_id")): item for item in traces}
    if len(qa_by_id) != len(qa_records):
        raise SystemExit("QA results contain duplicate question IDs")
    if len(trace_by_id) != len(traces):
        raise SystemExit("reasoning traces contain duplicate question IDs")
    if qa_by_id.keys() != trace_by_id.keys():
        missing_traces = sorted(qa_by_id.keys() - trace_by_id.keys())
        missing_qa = sorted(trace_by_id.keys() - qa_by_id.keys())
        raise SystemExit(
            f"QA/trace question IDs differ; missing traces={missing_traces}, "
            f"missing QA={missing_qa}"
        )

    output = (args.out or source / "reviews").resolve()
    output.mkdir(parents=True, exist_ok=True)
    written = 0
    for question_id in sorted(qa_by_id, key=_question_number):
        key, number = _question_parts(question_id)
        title = "PrimeKG" if key == "KG" else "MultiHop RAG"
        destination = output / f"{title} - Q{number}.md"
        if destination.exists() and not args.overwrite:
            raise SystemExit(
                f"refusing to overwrite {destination}; pass --overwrite to replace reviews"
            )
        destination.write_text(
            render_review(qa_by_id[question_id], trace_by_id[question_id], manifest),
            encoding="utf-8",
            newline="\n",
        )
        written += 1

    print(f"generated {written} review files in {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
