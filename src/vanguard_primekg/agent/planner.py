"""Provider-neutral, closed-schema PrimeKG planner.

The model can select one typed composition operation.  It cannot emit SQL,
choose graph IDs, perform set mathematics, or author the final answer.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol

from jsonschema import Draft202012Validator

from ..classify import Plan, classify
from ..query_engine import specs as S
from .prompt import load_schema, system_prompt, user_prompt


class PlanValidationError(ValueError):
    """Raised when a model response cannot be converted to a safe Plan."""


class PlannerModel(Protocol):
    def complete(self, *, system: str, user: str, max_tokens: int, timeout: float) -> str: ...


@dataclass(frozen=True)
class PlannerAudit:
    provider: str
    model_id: str
    prompt_version: str
    raw_response: str | None
    attempts: int
    elapsed_ms: int
    error: str | None = None


class RegexPlanner:
    name = "regex"

    def plan(self, question: str) -> tuple[Plan, PlannerAudit]:
        started = time.monotonic()
        return classify(question), PlannerAudit(
            provider="deterministic",
            model_id="regex-baseline",
            prompt_version="classify.py",
            raw_response=None,
            attempts=1,
            elapsed_ms=int((time.monotonic() - started) * 1000),
        )


class StubPlannerModel:
    """Offline fixture model used by unit tests; no retrieval or tools exist."""

    def __init__(self, fixtures: Mapping[str, Mapping[str, Any] | str]) -> None:
        self._fixtures = dict(fixtures)

    def complete(self, *, system: str, user: str, max_tokens: int, timeout: float) -> str:
        del system, max_tokens, timeout
        payload = json.loads(user.split("\n", 1)[-1])
        question = payload["untrusted_question"]
        value = self._fixtures.get(question)
        if value is None:
            raise RuntimeError(f"no planner fixture for question: {question}")
        return value if isinstance(value, str) else json.dumps(value)


class AgentPlanner:
    name = "agent"

    def __init__(
        self,
        model: PlannerModel,
        *,
        repo_root: Path,
        provider: str,
        model_id: str,
        prompt_version: str = "primekg-planner-1.5",
        timeout: float = 60.0,
        max_tokens: int = 1800,
        retries: int = 2,
    ) -> None:
        if not 1.0 <= timeout <= 300.0:
            raise ValueError("planner timeout must be between 1 and 300 seconds")
        if not 64 <= max_tokens <= 4096:
            raise ValueError("planner max_tokens must be between 64 and 4096")
        if not 0 <= retries <= 3:
            raise ValueError("planner retries must be between 0 and 3")
        self._model = model
        self._schema = load_schema(repo_root)
        self._validator = Draft202012Validator(self._schema)
        self._system = system_prompt(self._schema)
        self._provider = provider
        self._model_id = model_id
        self._prompt_version = prompt_version
        self._timeout = timeout
        self._max_tokens = max_tokens
        self._retries = retries

    @property
    def usage(self) -> dict[str, int] | None:
        value = getattr(self._model, "usage", None)
        return value if isinstance(value, dict) else None

    def plan(self, question: str) -> tuple[Plan, PlannerAudit]:
        started = time.monotonic()
        raw: str | None = None
        error: str | None = None
        for attempt in range(1, self._retries + 2):
            try:
                prompt = user_prompt(question)
                if error is not None:
                    prompt += (
                        "\nThe previous response was invalid: "
                        + error[:600]
                        + "\nReturn a corrected JSON object only."
                    )
                raw = self._model.complete(
                    system=self._system,
                    user=prompt,
                    max_tokens=self._max_tokens,
                    timeout=self._timeout,
                )
                payload = _extract_json(raw)
                plan = _payload_to_plan(payload, self._validator, question=question)
                return plan, PlannerAudit(
                    provider=self._provider,
                    model_id=self._model_id,
                    prompt_version=self._prompt_version,
                    raw_response=raw,
                    attempts=attempt,
                    elapsed_ms=int((time.monotonic() - started) * 1000),
                )
            except Exception as exc:  # bounded retry; final result fails closed
                error = f"{type(exc).__name__}: {exc}"
        return Plan(
            op="insufficient",
            answer_type="short_text",
            refusal="The planner could not produce a valid closed-schema plan.",
        ), PlannerAudit(
            provider=self._provider,
            model_id=self._model_id,
            prompt_version=self._prompt_version,
            raw_response=raw,
            attempts=self._retries + 1,
            elapsed_ms=int((time.monotonic() - started) * 1000),
            error=error,
        )


def _extract_json(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        text = text.rsplit("```", 1)[0]
    value = json.loads(text)
    if not isinstance(value, dict):
        raise PlanValidationError("planner response must be one JSON object")
    return value


def _payload_to_plan(
    payload: dict[str, Any],
    validator: Draft202012Validator,
    *,
    question: str = "",
) -> Plan:
    # Some provider endpoints serialize unused optional fields as JSON null even
    # when explicitly instructed to omit them.  Treat null optional values as
    # omission; required fields and non-null values still face full validation.
    payload = dict(payload)
    for field in (
        "exclude_slot", "group_level", "distinct_level", "cmp", "n",
        "member_leg", "require_edge", "single_entity", "refusal", "missing",
    ):
        if payload.get(field, object()) is None:
            payload.pop(field)
    errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.path))
    if errors:
        detail = "; ".join(error.message for error in errors[:5])
        raise PlanValidationError(detail)

    slots = [(s["label"], tuple(s["expected_types"])) for s in payload["slots"]]
    steps = [S.RELATION_BY_ID[name] for name in payload["steps"]]
    legs = [
        (leg["slot"], [S.RELATION_BY_ID[name] for name in leg["steps"]])
        for leg in payload["legs"]
    ]
    member = payload.get("member_leg")
    member_leg = None if member is None else (
        member["slot"], [S.RELATION_BY_ID[name] for name in member["steps"]]
    )
    required = payload.get("require_edge")
    plan = Plan(
        op=payload["op"],
        slots=slots,
        steps=steps,
        legs=legs,
        final_type=tuple(payload["final_types"]),
        exclude_slot=payload.get("exclude_slot"),
        group_level=payload.get("group_level", 0),
        distinct_level=payload.get("distinct_level", 0),
        cmp=payload.get("cmp", ">="),
        n=payload.get("n", 0),
        member_leg=member_leg,
        require_edge=None if required is None else S.RELATION_BY_ID[required],
        noun=payload["noun"],
        answer_type=payload["answer_type"],
        single_entity=payload.get("single_entity", False),
        refusal=payload.get("refusal"),
        missing=payload.get("missing"),
    )
    _semantic_validate(plan, question=question)
    return plan


def _semantic_validate(plan: Plan, *, question: str = "") -> None:
    slot_count = len(plan.slots)
    for index, _ in plan.legs:
        if index >= slot_count:
            raise PlanValidationError("leg references a missing slot")
    if plan.exclude_slot is not None and plan.exclude_slot >= slot_count:
        raise PlanValidationError("exclude_slot references a missing slot")
    if plan.member_leg is not None and plan.member_leg[0] >= slot_count:
        raise PlanValidationError("member_leg references a missing slot")
    executable = {
        "expand", "neighbors", "edge_between", "intersect", "intersect_many",
        "difference", "difference_many", "count", "count_compare", "bridge",
        "ratio", "xor", "rank", "describe", "insufficient_data",
    }
    if plan.op in executable and not plan.slots:
        raise PlanValidationError(f"{plan.op} requires at least one slot")
    if plan.op in {"expand", "count", "rank", "edge_between"} and not plan.steps:
        raise PlanValidationError(f"{plan.op} requires steps")
    if plan.op == "neighbors" and (plan.steps or plan.legs):
        raise PlanValidationError("neighbors requires empty steps and legs")
    if plan.op in {"expand", "count", "rank", "edge_between"} and plan.legs:
        raise PlanValidationError(f"{plan.op} requires empty legs")
    if plan.op in {"intersect", "difference", "count_compare", "xor"} and len(plan.legs) != 2:
        raise PlanValidationError(f"{plan.op} requires exactly two legs")
    if plan.op in {"intersect_many", "difference_many"} and len(plan.legs) < 2:
        raise PlanValidationError(f"{plan.op} requires at least two legs")
    if plan.op == "count" and max(plan.group_level, plan.distinct_level) > len(plan.steps):
        raise PlanValidationError("count levels exceed chain depth")

    # Reject semantically incomplete plans so bounded retries can repair them.
    # These checks use reusable relation language, never question IDs/entities.
    q = question.casefold()
    all_steps = list(plan.steps)
    for _slot, leg_steps in plan.legs:
        all_steps.extend(leg_steps)
    if plan.member_leg is not None:
        all_steps.extend(plan.member_leg[1])
    relation_ids = [S.relation_id(spec) for spec in all_steps]
    biomedical_terms = (
        "drug", "protein", "gene", "disease", "phenotype", "pathway",
        "target", "interact", "indicat", "contraindicat", "side effect",
    )
    if plan.op == "out_of_graph" and any(term in q for term in biomedical_terms):
        raise PlanValidationError(
            "biomedical PrimeKG relation questions are not out_of_graph"
        )
    if "share an associated protein" in q or "share a protein" in q:
        if relation_ids.count("disease_protein") < 2:
            raise PlanValidationError(
                "sharing an associated protein requires disease_protein twice"
            )
        if plan.exclude_slot is None:
            raise PlanValidationError(
                "sharing with the starting disease requires exclude_slot"
            )
    if "share a target" in q or "shares a target" in q:
        if relation_ids.count("targets") < 2:
            raise PlanValidationError("sharing a target requires targets twice")
    if "pathway" in q and "pathway_protein" not in relation_ids:
        raise PlanValidationError(
            "a question involving a pathway requires pathway_protein"
        )
    pathway_bridge_phrases = (
        "protein in a pathway",
        "proteins in a pathway",
        "same pathway",
        "through a pathway",
        "pathway with a protein",
        "pathway targeted by",
    )
    if any(phrase in q for phrase in pathway_bridge_phrases):
        if relation_ids.count("pathway_protein") < 2:
            raise PlanValidationError(
                "a protein-to-protein pathway bridge requires pathway_protein twice"
            )
    if "target->ppi->target bridge" in q:
        if plan.op != "bridge":
            raise PlanValidationError(
                "target->PPI->target bridge thresholds require the bridge operation"
            )
    if "first-line treatment" in q:
        if plan.op != "expand" or "indication" not in relation_ids:
            raise PlanValidationError(
                "first-line treatment is answered from represented indication edges"
            )
    if q.startswith("what dose of ") and " causes " in q:
        if (
            plan.op != "edge_between"
            or "side_effect" not in relation_ids
            or slot_count != 2
        ):
            raise PlanValidationError(
                "dose-causes-effect questions require the represented drug/side-effect edge"
            )
    if "gene mutation causes" in q:
        if plan.op != "expand" or "phenotype_protein" not in relation_ids:
            raise PlanValidationError(
                "gene-mutation/phenotype questions require phenotype_protein"
            )
    if "among drugs that interact with" in q and "at least" in q and "target" in q:
        if (
            plan.op != "count"
            or relation_ids.count("targets") < 2
            or plan.member_leg is None
            or "drug_interaction"
            not in [S.relation_id(spec) for spec in plan.member_leg[1]]
        ):
            raise PlanValidationError(
                "shared-target thresholds within interacting drugs require count with "
                "two target traversals and a drug_interaction member leg"
            )
    if "ppi partners" in q and "targeted by at least" in q and "distinct drug" in q:
        if (
            plan.op != "count"
            or relation_ids[:2] != ["protein_interaction", "targets"]
            or plan.group_level != 1
            or plan.distinct_level != 2
        ):
            raise PlanValidationError(
                "counting distinct drugs per PPI partner requires group_level 1 "
                "and distinct_level 2"
            )
    if "at least half" in q and "target" in q and "shared" in q:
        if plan.op != "ratio":
            raise PlanValidationError(
                "an at-least-half shared-target threshold requires the ratio operation"
            )
    if "indicated for" in q and "pathway" in q and "targets a protein" in q:
        if (
            plan.op != "intersect"
            or "indication" not in relation_ids
            or "pathway_protein" not in relation_ids
            or "targets" not in relation_ids
        ):
            raise PlanValidationError(
                "indication plus pathway-target constraints require an intersection"
            )
    if "excluding diseases sharing an indicated drug" in q:
        if plan.op not in {"difference", "difference_many"} or len(plan.legs) < 2:
            raise PlanValidationError(
                "an explicit disease-sharing exclusion requires a difference operation"
            )
    if "share at least one target with" in q and slot_count >= 2:
        drug_slots = [
            index for index, (_label, types) in enumerate(plan.slots)
            if "drug" in types
        ]
        if not drug_slots or plan.exclude_slot != drug_slots[-1]:
            raise PlanValidationError(
                "the named anchor drug must be excluded from shared-target answers"
            )
    named_pathway = re.search(r"""shares\s+the\s+['"](.+?)['"]\s+pathway""", q)
    if named_pathway:
        label = named_pathway.group(1).casefold()
        pathway_slots = [
            slot_label.casefold()
            for slot_label, types in plan.slots
            if "pathway" in types
        ]
        if label not in pathway_slots:
            raise PlanValidationError(
                "an explicitly named quoted pathway must be used as the pathway slot"
            )


def plan_to_payload(plan: Plan) -> dict[str, Any]:
    """Serialize a deterministic Plan for comparison/audit fixtures."""
    return {
        "schema_version": "planner-plan-1.0",
        "op": plan.op,
        "slots": [
            {"label": label, "expected_types": list(types)} for label, types in plan.slots
        ],
        "steps": [S.relation_id(spec) for spec in plan.steps],
        "legs": [
            {"slot": index, "steps": [S.relation_id(spec) for spec in steps]}
            for index, steps in plan.legs
        ],
        "final_types": list(plan.final_type),
        "exclude_slot": plan.exclude_slot,
        "group_level": plan.group_level,
        "distinct_level": plan.distinct_level,
        "cmp": plan.cmp,
        "n": plan.n,
        "member_leg": None if plan.member_leg is None else {
            "slot": plan.member_leg[0],
            "steps": [S.relation_id(spec) for spec in plan.member_leg[1]],
        },
        "require_edge": None if plan.require_edge is None else S.relation_id(plan.require_edge),
        "noun": plan.noun,
        "answer_type": plan.answer_type,
        "single_entity": plan.single_entity,
        "refusal": plan.refusal,
        "missing": plan.missing,
    }
