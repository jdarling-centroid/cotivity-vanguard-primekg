"""Orchestration: firewall -> classify -> execute -> finalize (one question).

With ``verbose``/``trace`` it also builds the real hop-by-hop trajectory (the
edges followed, level by level) — shown on stdout and embedded as the RFP §8.3
reasoning-trace steps.
"""

from __future__ import annotations

import time

from . import finalize, firewall
from ._vendor.models import SessionResult
from .classify import Plan, classify
from .trace import build_trace


def _print_header(number: int, text: str) -> None:
    if number:
        print(f"\n──────── Q{number} ────────")
    print(f"Q: {text}")


def _unresolved_message(label: str) -> str:
    return (
        f"Could not find '{label}' in PrimeKG. PrimeKG uses generic/DrugBank drug "
        f"names (e.g. Sildenafil, not Viagra), MONDO disease names, and gene "
        f"symbols — try the generic or standard name."
    )


def solve(
    number: int,
    text: str,
    backend,
    *,
    verbose: bool = False,
    trace: bool = False,
) -> SessionResult:
    started = time.monotonic()

    verdict = firewall.verdict(text)
    if verdict.malicious:
        if verbose:
            _print_header(number, text)
            print(f"  firewall: BLOCKED ({verdict.reason})")
        return finalize.blocked(number, text, verdict.reason)

    plan = classify(text)
    if verbose:
        _print_header(number, text)
        print(f"  plan: {plan.op}")

    if plan.op == "out_of_graph":
        if verbose:
            print("  outcome: out-of-graph (not represented in PrimeKG)")
        return finalize.refused(
            number, text, "out_of_graph", plan.answer_type, plan.refusal or ""
        )

    if plan.op == "insufficient_data":
        hit = backend.resolver.resolve(*plan.slots[0])
        latency = int((time.monotonic() - started) * 1000)
        if hit is None:
            if verbose:
                print(f"  outcome: insufficient_data ({plan.missing}); entity unresolved")
            return finalize.refused(
                number, text, "insufficient_data", plan.answer_type,
                f"PrimeKG does not represent {plan.missing}.", latency_ms=latency,
            )
        name, _ntype, summary, edge_ids = backend.engine.node_evidence(hit.node_id)
        if verbose:
            print(f"  entity_lookup  -> {name} [{hit.node_id}]")
            print(f"  outcome: insufficient_data ({plan.missing}); grounded on "
                  f"{len(edge_ids)} evidence edge(s)")
        return finalize.insufficient(
            number, text, plan.missing or "this attribute", name, hit.node_id,
            summary, edge_ids, latency_ms=latency,
        )

    if plan.op == "insufficient":
        if verbose:
            print("  outcome: unmatched -> insufficient (honest refusal)")
        return finalize.refused(
            number, text, "insufficient", plan.answer_type, "Evidence is insufficient."
        )

    if plan.op == "describe":
        hit = backend.resolver.resolve(*plan.slots[0])
        latency = int((time.monotonic() - started) * 1000)
        if hit is None:
            if verbose:
                print("  entity unresolved")
            return finalize.refused(
                number, text, "describe", plan.answer_type,
                _unresolved_message(plan.slots[0][0]), latency_ms=latency,
            )
        name, ntype, summary, edge_ids = backend.engine.node_evidence(hit.node_id)
        if verbose:
            print(f"  entity_lookup  -> {name} [{hit.node_id}] ({ntype})")
            print(f"  summarize: {len(edge_ids)} evidence edge(s) across {len(summary)} relation(s)")
        session = finalize.describe(
            number, text, name, ntype, hit.node_id, summary, edge_ids, latency_ms=latency
        )
        if verbose:
            print(f"  ANSWER: {session.answer.answer}")
        return session

    trajectory_steps = None
    if verbose or trace:
        lines, trajectory_steps, _ = build_trace(plan, backend)
        if verbose:
            for line in lines:
                print(f"  {line}")

    result = backend.execute(plan)
    latency = int((time.monotonic() - started) * 1000)

    if result is None:
        if verbose:
            print("  outcome: a slot did not resolve -> not found in PrimeKG")
        label = plan.slots[0][0] if plan.slots else "the entity"
        return finalize.refused(
            number, text, plan.op, plan.answer_type, _unresolved_message(label),
            latency_ms=latency,
        )

    session = finalize.answered(
        number, text, plan.op, plan.answer_type, result,
        noun=plan.noun, single_entity=plan.single_entity, latency_ms=latency,
        trace_steps=(trajectory_steps if trace else None),
    )
    if verbose:
        print(f"  ANSWER: {session.answer.answer}")
        print(f"  supported_by: {', '.join(session.answer_supported_by)}")
    return session
