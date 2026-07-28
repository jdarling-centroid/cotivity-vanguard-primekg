"""Resumable evaluation harness for the 100 PrimeKG questions.

Runs each question through solve() (firewall -> classify -> DB composition ->
reused finalizer), writes the vendor results/traces artifacts, one review
markdown per question (with the executed query text + SUPPORTED_BY), and a
manifest with per-question status and aggregate pass counts.

Nothing is written unless you pass --out DIR; otherwise results are only printed.

    python scripts/run-primekg-questions.py --question 35 -v        # inspect, no files
    python scripts/run-primekg-questions.py --questions 1,2,3 -v    # a subset, traced
    python scripts/run-primekg-questions.py --question 5 --question 10  # repeatable
    python scripts/run-primekg-questions.py --out runs/pgq          # full run, saved
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from contextlib import nullcontext
from pathlib import Path

import yaml

from vanguard_primekg._vendor.finalizer import Finalizer
from vanguard_primekg._vendor.models import SessionResult
from vanguard_primekg.backends import PgqBackend, SelectAiBackend, SelectAiUnavailable
from vanguard_primekg.classify import classify
from vanguard_primekg.config import load_settings
from vanguard_primekg.db import connect
from vanguard_primekg.solver import solve


def _status(result: SessionResult) -> str:
    if result.answer.answer == "Won't do that":
        return "blocked"
    if any(s.get("operation") == "insufficient_data" for s in result.steps):
        return "insufficient_with_evidence" if result.graph_edges_used else "insufficient_no_evidence"
    if result.graph_edges_used:
        return "answered_with_evidence"
    if result.answer_supported_by == ["NONE"] and not result.graph_nodes_used:
        return "refused"
    return "answered_no_evidence"


def _meets(text: str, meta: dict, status: str) -> bool:
    expected = meta.get("expected_outcome", "answered")
    if expected == "blocked":
        return status == "blocked"
    if expected == "insufficient_data":
        # A grounded refusal that still cites the entity's real PrimeKG evidence.
        return status == "insufficient_with_evidence"
    # Every other non-adversarial question must produce a real, evidence-backed
    # answer; only the adversarial ones are un-answerable (blocked).
    return status == "answered_with_evidence"


def _review_md(number: int, text: str, meta: dict, result: SessionResult, status: str) -> str:
    query = ""
    for step in result.steps:
        if step.get("query"):
            query = step["query"]
            break
    lines = [
        f"# PrimeKG - Q{number}",
        "",
        f"**Question:** {text}",
        "",
        f"- category (expected): {'adversarial' if meta.get('adversarial') else meta.get('answer_shape')}",
        f"- expected_outcome: {meta.get('expected_outcome')}",
        f"- requires_evidence: {meta.get('requires_evidence')}",
        f"- status: {status}",
        "",
        "## Answer",
        "",
        result.answer.answer,
        "",
        "## SUPPORTED_BY",
        "",
        *(f"- {e}" for e in result.answer_supported_by),
        "",
    ]
    if result.graph_nodes_used:
        names = ", ".join(n[1] if isinstance(n, tuple) else n for n in _names(result))
        lines += ["## Answer nodes", "", names, ""]
    if query:
        lines += ["## Executed query", "", "```sql", query, "```", ""]
    return "\n".join(lines)


def _names(result: SessionResult) -> list:
    # graph_nodes_used holds node ids; names live in citations' doc_id map is not
    # kept, so just show ids here (the prose already lists names).
    return result.graph_nodes_used


def _parse_numbers(chunks: list[str]) -> set[int]:
    """Parse repeated/comma/space-separated question numbers.

    Accepts: --question 1  --questions 2,3  --question=4  --questions "5, 10".
    """
    numbers: set[int] = set()
    for chunk in chunks:
        for token in re.split(r"[,\s]+", chunk.strip()):
            if token.isdigit():
                numbers.add(int(token))
            elif token:
                raise SystemExit(f"invalid question number: {token!r}")
    return numbers


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", choices=["pgq", "select_ai"], default="pgq")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Directory to write RFP artifacts (results.jsonl, traces.json, "
        "reviews/, manifest.json). If omitted, nothing is written — results are "
        "only printed to the console.",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Question-set YAML (default: config/primekg-question-sets.yaml).",
    )
    parser.add_argument(
        "--question",
        "--questions",
        dest="numbers",
        action="append",
        default=[],
        metavar="N[,N...]",
        help="Question number(s) to run. Repeatable and comma/space separated: "
        "--question 1  --questions 2,3  --question=4  --questions '5, 10'. "
        "Default: all questions.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print the plan, resolved entities, traversal path, and executed SQL.",
    )
    args = parser.parse_args(argv)

    settings = load_settings()
    questions_path = args.input or (
        settings.repo_root / "config" / "primekg-question-sets.yaml"
    )
    # Only touch disk when an output directory is explicitly requested.
    write = args.out is not None
    out_dir = args.out
    reviews_dir = None
    if write:
        reviews_dir = out_dir / "reviews"
        reviews_dir.mkdir(parents=True, exist_ok=True)

    data = yaml.safe_load(questions_path.read_text(encoding="utf-8"))
    questions = data["sections"][0]["questions"]

    wanted = _parse_numbers(args.numbers)
    if wanted:
        available = {q["number"] for q in questions}
        missing = sorted(wanted - available)
        if missing:
            print(f"warning: not in question set, ignored: {missing}")
        questions = [q for q in questions if q["number"] in wanted]
        if not questions:
            print("no matching questions to run")
            return 1

    manifest: list[dict] = []
    passes = 0
    finalizer = Finalizer(out_dir, vendor_id="vanguard") if write else nullcontext(None)
    with connect() as conn, finalizer as fin:
        conn.call_timeout = 20000  # ms: no single query may hang the run
        if args.backend == "select_ai":
            try:
                backend = SelectAiBackend(conn)
            except SelectAiUnavailable as exc:
                print(f"select_ai unavailable: {exc}")
                return 0
        else:
            backend = PgqBackend(conn)
        for q in questions:
            number = q["number"]
            text = q["question"]
            meta = q["metadata"]
            result = solve(number, text, backend, verbose=args.verbose, trace=write)
            if write:
                fin.write(result)

            status = _status(result)
            meets = _meets(text, meta, status)
            passes += int(meets)
            # The answer goes to stdout; grading status to stderr (so `2>/dev/null`
            # gives a clean answer-only view for ad-hoc single-question runs).
            if not args.verbose:
                print(f"Q{number}: {result.answer.answer}")
            print(f"  [{status}{' ok' if meets else ' MISS'}]", file=sys.stderr)
            if write:
                (reviews_dir / f"PrimeKG - Q{number}.md").write_text(
                    _review_md(number, text, meta, result, status), encoding="utf-8"
                )
            manifest.append(
                {
                    "number": number,
                    "expected_outcome": meta.get("expected_outcome"),
                    "requires_evidence": meta.get("requires_evidence", False),
                    "plan_op": classify(text).op,
                    "status": status,
                    "meets_expectation": meets,
                    "n_nodes": len(result.graph_nodes_used),
                    "n_edges": len(result.graph_edges_used),
                }
            )

    if write:
        (out_dir / "manifest.json").write_text(
            json.dumps(
                {"total": len(questions), "passes": passes, "questions": manifest},
                indent=2,
            ),
            encoding="utf-8",
        )

    unmatched = [m["number"] for m in manifest if m["plan_op"] == "insufficient"]
    print(f"backend={args.backend}  pass {passes}/{len(questions)}", file=sys.stderr)
    if write:
        print(f"artifacts: {out_dir}", file=sys.stderr)
    if unmatched:
        print(f"unmatched (insufficient) [{len(unmatched)}]: {unmatched}", file=sys.stderr)
    fails = [m["number"] for m in manifest if not m["meets_expectation"]]
    if fails:
        print(f"not meeting expectation [{len(fails)}]: {fails}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
