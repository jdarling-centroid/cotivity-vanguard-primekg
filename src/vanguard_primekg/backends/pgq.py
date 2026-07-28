"""pgq backend: resolve a Plan's slots and execute it via the SQL/PGQ engine."""

from __future__ import annotations

import oracledb

from ..classify import Plan
from ..query_engine import QueryEngine, QueryResult, specs as S
from ..relations import DRUG_TYPES, PROTEIN_TYPES
from ..resolve import Resolver


class PgqBackend:
    name = "pgq"

    def __init__(self, conn: oracledb.Connection) -> None:
        self.resolver = Resolver(conn)
        self.engine = QueryEngine(conn)

    def execute(self, plan: Plan) -> QueryResult | None:
        resolved = []
        for label, types in plan.slots:
            hit = self.resolver.resolve(label, types)
            if hit is None:
                return None
            resolved.append(hit)

        exclude: tuple[str, ...] = ()
        if plan.exclude_slot is not None:
            exclude = (resolved[plan.exclude_slot].node_id,)
        final_type = plan.final_type or None

        if plan.op == "expand":
            return self.engine.expand(
                [resolved[0].node_id], plan.steps, final_type=final_type,
                exclude_ids=exclude, require_edge=plan.require_edge,
            )
        if plan.op == "neighbors":
            hit = resolved[0]
            if hit.node_type in DRUG_TYPES:
                return self.engine.expand(
                    [hit.node_id], [S.INTERACTS], final_type=DRUG_TYPES,
                    exclude_ids=(hit.node_id,),
                )
            if hit.node_type in PROTEIN_TYPES:
                return self.engine.expand([hit.node_id], [S.PPI], final_type=PROTEIN_TYPES)
            return None
        if plan.op == "edge_between":
            return self.engine.edge_between(
                resolved[0].node_id, resolved[1].node_id, plan.steps[0]
            )
        if plan.op in ("intersect", "difference"):
            legs = [([resolved[i].node_id], steps) for i, steps in plan.legs]
            if plan.op == "intersect":
                return self.engine.intersect(
                    legs[0], legs[1], final_type=final_type, exclude_ids=exclude,
                    require_edge=plan.require_edge,
                )
            return self.engine.difference(legs[0], legs[1], final_type=final_type, exclude_ids=exclude)
        if plan.op == "difference_many":
            legs = [([resolved[i].node_id], steps) for i, steps in plan.legs]
            return self.engine.difference_many(
                legs[0], legs[1:], final_type=final_type, exclude_ids=exclude
            )
        if plan.op == "count_compare":
            legs = [([resolved[i].node_id], steps) for i, steps in plan.legs]
            return self.engine.count_compare(
                legs[0], legs[1], cmp=plan.cmp, final_type=final_type
            )
        if plan.op == "bridge":
            return self.engine.bridge_count(
                [resolved[0].node_id], n=plan.n, op=plan.cmp,
                final_type=final_type, exclude_ids=exclude,
            )
        if plan.op == "ratio":
            return self.engine.ratio_shared(
                [resolved[0].node_id], numerator=1, denominator=2,
                final_type=final_type, exclude_ids=exclude,
            )
        if plan.op == "intersect_many":
            legs = [([resolved[i].node_id], steps) for i, steps in plan.legs]
            return self.engine.intersect_many(legs, final_type=final_type, exclude_ids=exclude)
        if plan.op == "xor":
            legs = [([resolved[i].node_id], steps) for i, steps in plan.legs]
            return self.engine.symmetric_difference(legs[0], legs[1], final_type=final_type)
        if plan.op == "rank":
            return self.engine.rank_top(
                [resolved[0].node_id], plan.steps, final_type=final_type, exclude_ids=exclude
            )
        if plan.op == "count":
            member_of = None
            if plan.member_leg is not None:
                idx, steps = plan.member_leg
                member_of = ([resolved[idx].node_id], steps)
            return self.engine.count_threshold(
                [resolved[0].node_id],
                plan.steps,
                group_level=plan.group_level,
                distinct_level=plan.distinct_level,
                op=plan.cmp,
                n=plan.n,
                final_type=final_type,
                exclude_ids=exclude,
                member_of=member_of,
            )
        return None
