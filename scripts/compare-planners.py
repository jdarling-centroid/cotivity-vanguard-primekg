#!/usr/bin/env python3
"""Compare regex and agent Track A runs without claiming correctness.

The comparison reports plan, disposition, and normalized answer-node-set
changes.  A divergence is a review item; this tool does not decide which
planner is correct.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load_run(path: Path) -> dict[str, dict[str, Any]]:
    manifest_path = path / "run-manifest.json" if path.is_dir() else path
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    questions = manifest.get("questions")
    if not isinstance(questions, list):
        raise SystemExit(f"{manifest_path}: missing questions array")
    result: dict[str, dict[str, Any]] = {}
    for item in questions:
        question_id = item.get("question_id")
        if not isinstance(question_id, str) or question_id in result:
            raise SystemExit(f"{manifest_path}: invalid or duplicate question_id {question_id!r}")
        result[question_id] = item
    return result


def _answer_nodes(item: dict[str, Any]) -> list[str]:
    value = item.get("answer_node_ids")
    if isinstance(value, list):
        return sorted({str(v) for v in value})
    # Backward-compatible manifests may not have answer_node_ids.  Do not
    # substitute all graph nodes, because those include intermediate nodes.
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("regex_run", type=Path)
    parser.add_argument("agent_run", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    regex = _load_run(args.regex_run)
    agent = _load_run(args.agent_run)
    ids = sorted(set(regex) | set(agent))
    divergences: list[dict[str, Any]] = []
    matches = 0
    for question_id in ids:
        left = regex.get(question_id)
        right = agent.get(question_id)
        reasons: list[str] = []
        if left is None or right is None:
            reasons.append("missing_question")
        else:
            if left.get("plan") != right.get("plan"):
                reasons.append("validated_plan")
            if left.get("status") != right.get("status"):
                reasons.append("disposition")
            if _answer_nodes(left) != _answer_nodes(right):
                reasons.append("answer_node_set")
            if bool(left.get("truncated")) != bool(right.get("truncated")):
                reasons.append("truncation")
        if reasons:
            divergences.append(
                {
                    "question_id": question_id,
                    "reasons": reasons,
                    "regex": None if left is None else {
                        "status": left.get("status"),
                        "plan": left.get("plan"),
                        "answer_node_ids": _answer_nodes(left),
                        "truncated": left.get("truncated"),
                    },
                    "agent": None if right is None else {
                        "status": right.get("status"),
                        "plan": right.get("plan"),
                        "answer_node_ids": _answer_nodes(right),
                        "truncated": right.get("truncated"),
                    },
                    "disposition": "requires_review",
                }
            )
        else:
            matches += 1

    report = {
        "comparison_type": "regression_review_not_accuracy",
        "question_count_union": len(ids),
        "exact_matches": matches,
        "divergence_count": len(divergences),
        "divergences": divergences,
    }
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8", newline="\n")
    print(text, end="")
    return 3 if divergences else 0


if __name__ == "__main__":
    raise SystemExit(main())
