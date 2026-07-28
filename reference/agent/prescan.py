"""Standalone ``mc-prescan`` command: scan one query with the security firewall.

Runs the dual-model prescan (Orinth + MiniCPM) against the local Ollama server
using the configured firewall prompt and prints a single JSON verdict. It exits 0
after a successful scan (whether or not the query is malicious) and exits 1 —
with a fail-closed ``malicious`` verdict — if it cannot reach the firewall
models or otherwise crashes.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from ..config import load_config
from ..errors import SecurityError
from ..logging import get_logger
from .llm import (
    ChatModel,
    deterministic_security_verdict,
    get_security_prescan_prompt,
    make_chat_model,
)

log = get_logger("agent.prescan")


def _parse_verdict(content: str | None) -> dict[str, Any]:
    """Parse a ``{"malicious": ..., "reason": ...}`` object, tolerating prose."""
    text = (content or "").strip()
    if not text:
        return {}
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            return {}
        try:
            parsed = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return {}
    return parsed if isinstance(parsed, dict) else {}


def _security_verdict(model: ChatModel, question: str) -> tuple[bool, str | None]:
    """Ask one firewall model whether a query is malicious.

    A transport error raises :class:`SecurityError`: a firewall we cannot reach
    must block the query (fail-closed), never wave it through.
    """
    messages = [
        {"role": "system", "content": get_security_prescan_prompt()},
        {"role": "user", "content": question},
    ]
    try:
        turn = model.respond(messages, [])
    except Exception as exc:  # fail-closed: a firewall outage blocks the query
        log.warning("firewall.prescan_error", error=str(exc))
        raise SecurityError(load_config().security.offline_reason) from exc
    payload = _parse_verdict(turn.content)
    malicious = payload.get("malicious")
    reason = payload.get("reason")
    if not isinstance(malicious, bool) or not (
        reason is None or isinstance(reason, str)
    ):
        raise SecurityError("Firewall returned an invalid verdict")
    return malicious, reason


def scan(question: str, *, dry_run: bool = False) -> dict[str, Any]:
    """Run the firewall prescan and return ``{"malicious": ..., "reason": ...}``.

    Raises :class:`SecurityError` if a firewall model cannot be reached, so the
    caller can distinguish a clean verdict from a firewall outage (fail-closed).
    """
    deterministic = deterministic_security_verdict(question)
    if deterministic["malicious"]:
        return deterministic
    if dry_run:
        models = [make_chat_model("stub", dry_run=True)]
    else:
        model_names = load_config().security.prescan_models
        if not model_names:
            raise SecurityError("Firewall has no prescan models configured")
        models = [make_chat_model(name) for name in model_names]
    for model in models:
        malicious, reason = _security_verdict(model, question)
        if malicious:
            return {"malicious": True, "reason": reason}
    return {"malicious": False, "reason": None}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scan a single query with the clinical security firewall."
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="Query to scan (read from stdin when omitted)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Use the offline stub firewall model (no Ollama required)",
    )
    args = parser.parse_args()

    query = args.query if args.query is not None else sys.stdin.read()
    query = query.strip()
    if not query:
        print(json.dumps({"malicious": False, "reason": None}))
        sys.exit(0)

    try:
        verdict = scan(query, dry_run=args.dry_run)
    except SecurityError as exc:  # fail-closed: cannot reach the firewall
        print(json.dumps({"malicious": True, "reason": str(exc)}))
        sys.exit(1)
    except Exception as exc:  # fail-closed on any unexpected crash
        print(json.dumps({"malicious": True, "reason": f"prescan error: {exc}"}))
        sys.exit(1)

    print(json.dumps(verdict))
    sys.exit(0)


if __name__ == "__main__":
    main()
