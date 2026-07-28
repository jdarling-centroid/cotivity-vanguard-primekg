"""Hop-by-hop trace of how an answer was reached.

Turns a classified Plan into (1) a human-readable trajectory for `ask`/--verbose
and (2) RFP §8.3 reasoning-trace steps (entity_lookup, edge_traversal with real
edge ids and from/to node names, then the set/aggregate composition). This is
the actual graph traversal behind the single-SQL answer.
"""

from __future__ import annotations

from .classify import Plan
from .query_engine import specs as S


def _disp(displays) -> str:
    return "/".join(displays) if displays else "*"


class _Trace:
    def __init__(self) -> None:
        self.lines: list[str] = []
        self.steps: list[dict] = []
        self._n = 0

    def step(self, **fields) -> None:
        self._n += 1
        self.steps.append({"step": self._n, **fields})

    def lookup(self, label: str, hit) -> None:
        if hit is None:
            self.lines.append(f"entity_lookup  {label!r} -> UNRESOLVED")
            self.step(operation="entity_lookup", input=label, node_id=None)
            return
        self.lines.append(
            f"entity_lookup  {label!r} -> {hit.name} [{hit.node_id}] ({hit.node_type})"
        )
        self.step(
            operation="entity_lookup",
            input=label,
            node_id=hit.node_id,
            node_type=hit.node_type,
            evidence={"source_ref": hit.node_id},
        )

    def hops(self, engine, base_id: str, chain, *, tag: str | None = None) -> list[str]:
        if tag:
            self.lines.append(tag)
        final, hops = engine.walk_hops([base_id], list(chain))
        for h in hops:
            d = _disp(h["displays"])
            self.lines.append(
                f"  traverse {h['predicate']}[{d}]: {h['from_count']} -> {h['to_count']} node(s)"
            )
            for edge_id, frm, to in h["samples"][:3]:
                self.lines.append(f"      {frm} --{d}--> {to}   ({edge_id})")
            self.step(
                operation="edge_traversal",
                predicate=h["predicate"],
                display_relation=(d if h["displays"] else None),
                from_count=h["from_count"],
                to_count=h["to_count"],
                examples=[{"edge_id": e, "from": f, "to": t} for e, f, t in h["samples"]],
            )
        return final

    def compose(self, operation: str, detail: str, count: int | None = None) -> None:
        suffix = f" -> {count} node(s)" if count is not None else ""
        self.lines.append(f"{operation}: {detail}{suffix}")
        self.step(operation=operation, detail=detail, **({"result_count": count} if count is not None else {}))


def build_trace(plan: Plan, backend) -> tuple[list[str], list[dict], list]:
    """Return (human_lines, rfp_steps, resolved_entities)."""
    t = _Trace()
    resolved = []
    for label, types in plan.slots:
        hit = backend.resolver.resolve(label, types)
        resolved.append(hit)
        t.lookup(label, hit)
    if any(r is None for r in resolved):
        return t.lines, t.steps, resolved

    engine = backend.engine
    op = plan.op

    if op == "expand":
        t.hops(engine, resolved[0].node_id, plan.steps)
    elif op == "neighbors":
        hit = resolved[0]
        spec = S.INTERACTS if hit.node_type == "drug" else S.PPI
        t.hops(engine, hit.node_id, [spec])
    elif op == "edge_between":
        spec = plan.steps[0]
        t.lines.append(
            f"check_edge  {resolved[0].name} --{spec.predicate}[{_disp(spec.displays)}]--> {resolved[1].name}"
        )
        t.step(
            operation="edge_traversal",
            predicate=spec.predicate,
            display_relation=_disp(spec.displays),
            **{"from": resolved[0].node_id, "to": resolved[1].node_id},
        )
    elif op in ("intersect", "difference", "intersect_many", "difference_many"):
        finals = []
        for i, (slot_idx, chain) in enumerate(plan.legs):
            finals.append(set(t.hops(engine, resolved[slot_idx].node_id, chain, tag=f"leg {i + 1}:")))
        if op in ("intersect", "intersect_many"):
            res = set.intersection(*finals) if finals else set()
            t.compose("set_intersection", "keep nodes reached by ALL legs (AND)", len(res))
        elif op == "difference":
            res = finals[0] - finals[1]
            t.compose("set_difference", "leg 1 nodes NOT in leg 2", len(res))
        else:
            res = finals[0] - set().union(*finals[1:])
            t.compose("set_difference", "leg 1 nodes NOT in any later leg", len(res))
    elif op == "count":
        t.hops(engine, resolved[0].node_id, plan.steps)
        t.compose(
            "aggregate",
            f"group by hop-{plan.group_level} node; keep COUNT(distinct hop-"
            f"{plan.distinct_level}) {plan.cmp} {plan.n}",
        )
    elif op == "count_compare":
        for i, (slot_idx, chain) in enumerate(plan.legs):
            t.hops(engine, resolved[slot_idx].node_id, chain, tag=f"leg {i + 1}:")
        t.compose("aggregate", f"keep nodes where count(leg1) {plan.cmp} count(leg2)")
    elif op == "ratio":
        t.hops(engine, resolved[0].node_id, [S.TARGETS])
        t.compose("aggregate", "keep drugs with shared_targets * 2 >= total_targets (>= half)")
    elif op == "bridge":
        t.hops(engine, resolved[0].node_id, [S.TARGETS, S.PPI, S.TARGETS])
        t.compose("aggregate", f"keep drugs with >= {plan.n} distinct target->PPI->target bridges")
    elif op == "rank":
        t.hops(engine, resolved[0].node_id, plan.steps)
        t.compose("rank", "keep peers sharing the MOST nodes (rank = 1)")
    elif op == "xor":
        finals = [set(t.hops(engine, resolved[i].node_id, chain, tag=f"leg {j + 1}:"))
                  for j, (i, chain) in enumerate(plan.legs)]
        res = finals[0].symmetric_difference(finals[1])
        t.compose("set_symmetric_difference", "nodes in exactly one leg (XOR)", len(res))

    return t.lines, t.steps, resolved
