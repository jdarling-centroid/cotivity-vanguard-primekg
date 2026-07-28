"""Firewall -> closed planner -> entity resolution -> one DB composition -> finalizer."""

from __future__ import annotations

import time
from dataclasses import asdict, is_dataclass
from typing import Any

from . import finalize, firewall
from ._vendor.models import SessionResult
from .agent.planner import RegexPlanner, plan_to_payload


def _print_header(number: int, text: str) -> None:
    if number:
        print(f"\n-------- Q{number} --------")
    print(f"Q: {text}")


def _unresolved_message(label: str) -> str:
    return (
        f"Could not find '{label}' in PrimeKG. PrimeKG uses generic/DrugBank drug "
        "names, MONDO disease names, and gene symbols; use the generic or standard name."
    )


def _audit_dict(audit: Any, *, planner_name: str, plan: Any) -> dict[str, Any]:
    if audit is None:
        payload: dict[str, Any] = {}
    elif is_dataclass(audit):
        payload = asdict(audit)
    elif isinstance(audit, dict):
        payload = dict(audit)
    else:
        payload = {"detail": str(audit)}
    payload["planner"] = planner_name
    payload["validated_plan"] = plan_to_payload(plan)
    return payload


def _resolution_records(plan, resolved: list) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for (label, _types), hit in zip(plan.slots, resolved, strict=True):
        records.append(
            {
                "input": label,
                "node_id": hit.node_id,
                "name": hit.name,
                "node_type": hit.node_type,
                "method": hit.method,
                "score": hit.score,
            }
        )
    return records


def solve(
    number: int,
    text: str,
    backend,
    *,
    planner=None,
    verbose: bool = False,
    trace: bool = False,
) -> SessionResult:
    del trace  # traces are always built from actual execution records now
    started = time.monotonic()

    verdict = firewall.verdict(text)
    if verdict.malicious:
        latency = int((time.monotonic() - started) * 1000)
        if verbose:
            _print_header(number, text)
            print(f"  firewall: BLOCKED ({verdict.reason})")
        return finalize.blocked(number, text, verdict.reason, latency_ms=latency)

    planner = planner or RegexPlanner()
    plan, planner_result = planner.plan(text)
    planner_audit = _audit_dict(planner_result, planner_name=planner.name, plan=plan)
    if verbose:
        _print_header(number, text)
        print(f"  planner: {planner.name}")
        print(f"  plan: {plan.op}")

    if plan.op == "out_of_graph":
        latency = int((time.monotonic() - started) * 1000)
        return finalize.refused(
            number,
            text,
            "out_of_graph",
            plan.answer_type,
            plan.refusal or "This request cannot be represented in PrimeKG.",
            latency_ms=latency,
            planner_audit=planner_audit,
        )

    if plan.op == "insufficient":
        latency = int((time.monotonic() - started) * 1000)
        return finalize.refused(
            number,
            text,
            "insufficient",
            plan.answer_type,
            plan.refusal or "Evidence is insufficient.",
            latency_ms=latency,
            planner_audit=planner_audit,
        )

    resolved = backend.resolve_plan(plan)
    latency = int((time.monotonic() - started) * 1000)
    if resolved is None:
        label = plan.slots[0][0] if plan.slots else "the entity"
        return finalize.refused(
            number,
            text,
            plan.op,
            plan.answer_type,
            _unresolved_message(label),
            latency_ms=latency,
            planner_audit=planner_audit,
        )
    resolution_records = _resolution_records(plan, resolved)

    if plan.op == "insufficient_data":
        hit = resolved[0]
        evidence = backend.engine.node_evidence(hit.node_id)
        latency = int((time.monotonic() - started) * 1000)
        return finalize.insufficient(
            number,
            text,
            plan.missing or "this attribute",
            evidence.name,
            hit.node_id,
            evidence.node_type,
            evidence.summary,
            evidence.edges,
            latency_ms=latency,
            planner_audit=planner_audit,
            resolution=resolution_records[0],
            query=evidence.sql,
            binds=evidence.binds,
        )

    if plan.op == "describe":
        hit = resolved[0]
        evidence = backend.engine.node_evidence(hit.node_id)
        latency = int((time.monotonic() - started) * 1000)
        return finalize.describe(
            number,
            text,
            evidence.name,
            evidence.node_type,
            hit.node_id,
            evidence.summary,
            evidence.edges,
            latency_ms=latency,
            planner_audit=planner_audit,
            resolution=resolution_records[0],
            query=evidence.sql,
            binds=evidence.binds,
        )

    result = backend.execute(plan, resolved=resolved)
    latency = int((time.monotonic() - started) * 1000)
    if result is None:
        return finalize.refused(
            number,
            text,
            plan.op,
            plan.answer_type,
            "The validated operation could not be executed safely.",
            latency_ms=latency,
            planner_audit=planner_audit,
        )

    session = finalize.answered(
        number,
        text,
        plan.op,
        plan.answer_type,
        result,
        noun=plan.noun,
        single_entity=plan.single_entity,
        latency_ms=latency,
        planner_audit=planner_audit,
        resolved_entities=resolution_records,
    )
    if verbose:
        print(f"  ANSWER: {session.answer.answer}")
        print(f"  support refs: {', '.join(session.answer_supported_by)}")
    return session
