"""Ask PrimeKG a single question and get the answer + how it got there.

    python scripts/ask.py "Which drugs are indicated for disease scalp dermatosis?"
    python scripts/ask.py "..." --json     # emit the RFP qa-results / reasoning-traces records

Shows the hop-by-hop reasoning (entity lookups and the edges traversed) and the
final answer with its supporting edge ids. Writes nothing to disk.
"""

from __future__ import annotations

import argparse
import json
import sys

from vanguard_primekg._vendor.finalizer import qa_record, trace_record
from vanguard_primekg.backends import PgqBackend
from vanguard_primekg.db import connect
from vanguard_primekg.solver import solve


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ask PrimeKG a question.")
    parser.add_argument("question", nargs="+", help="The question (quote it).")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the RFP qa-results (8.2) and reasoning-traces (8.3) records.",
    )
    args = parser.parse_args(argv)
    question = " ".join(args.question).strip()

    with connect() as conn:
        conn.call_timeout = 30000
        backend = PgqBackend(conn)
        # verbose prints the trajectory unless we're emitting JSON.
        session = solve(0, question, backend, verbose=not args.json, trace=True)

    if args.json:
        print(
            json.dumps(
                {"qa_result": qa_record(session), "reasoning_trace": trace_record(session)},
                indent=2,
            )
        )
    else:
        print()  # blank line after the trajectory
    return 0


if __name__ == "__main__":
    sys.exit(main())
