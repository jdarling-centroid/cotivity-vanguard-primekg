"""Question classifier: map a question to a category-general execution Plan.

Rules key on relation phrasings and question structure (A–F categories), never
on a specific question's entities or wording. Unmatched questions return an
``insufficient`` plan so the system answers honestly rather than guessing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .query_engine import specs as S
from .relations import (
    ALL_TYPES,
    DISEASE_TYPES,
    DRUG_TYPES,
    PATHWAY_TYPES,
    PHENOTYPE_TYPES,
    PROTEIN_TYPES,
)

Slot = tuple[str, tuple[str, ...]]  # (label, expected node types)


@dataclass
class Plan:
    op: str  # expand | intersect | difference | count | out_of_graph | insufficient
    slots: list[Slot] = field(default_factory=list)
    steps: list = field(default_factory=list)          # expand/count
    legs: list = field(default_factory=list)           # [(slot_idx, [RelSpec])]
    final_type: tuple[str, ...] = ()
    exclude_slot: int | None = None                    # drop this slot's id from results
    group_level: int = 0
    distinct_level: int = 0
    cmp: str = ">="
    n: int = 0
    member_leg: tuple | None = None            # (slot_idx, [RelSpec]) membership set
    require_edge: object | None = None          # RelSpec: answer must source such an edge
    noun: str = "entities"
    answer_type: str = "entity_list"
    single_entity: bool = False
    refusal: str | None = None
    missing: str | None = None                  # insufficient_data: the absent fact


_NUM_WORDS = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "half": 0}


def _num(token: str) -> int:
    token = token.strip().lower()
    if token.isdigit():
        return int(token)
    return _NUM_WORDS.get(token, 0)


def _clean(label: str) -> str:
    label = label.strip().strip("?.").strip()
    label = re.sub(r"^'(.*)'$", r"\1", label)
    label = re.sub(
        r"^(?:the\s+)?(?:disease|drug|protein|gene|phenotype)\s+", "", label, flags=re.I
    )
    label = re.sub(r"^the\s+", "", label, flags=re.I)
    return label.strip()


def _m(pattern: str, text: str) -> re.Match | None:
    return re.search(pattern, text, re.I)


# Category E: out-of-graph facts PrimeKG does not contain (dosage, price,
# approval date, clinical trials, prescribing physician, prognosis).
_OUT_OF_GRAPH = (
    r"recommended dosage|what dose of|when was .+ approved|"
    r"price of|clinical trial|which physician|prescrib|prognosis for|approval date"
)

_REFUSAL = (
    "This information is not represented in the PrimeKG knowledge graph, "
    "which contains only entities and relationships (drugs, proteins, diseases, "
    "phenotypes, pathways) — not dosages, prices, approval dates, trials, "
    "prognoses, or prescribing records."
)


def classify(text: str) -> Plan:  # noqa: PLR0911 -- ordered template rules
    q = text.strip()

    # --- Category E: out-of-graph -------------------------------------------
    # "What dose of X causes Y": the dose isn't in PrimeKG, but the drug->side
    # effect causation edge is real evidence, so answer that grounded fact.
    if mt := _m(r"what dose of (.+?) causes (.+)", q):
        return Plan("edge_between",
                    [(_clean(mt.group(1)), DRUG_TYPES), (_clean(mt.group(2)), PHENOTYPE_TYPES)],
                    steps=[S.SIDE_EFFECT], final_type=PHENOTYPE_TYPES,
                    single_entity=True, answer_type="short_text",
                    noun="side-effect relationship (dose is not represented in PrimeKG)")

    # Insufficient-data facts: PrimeKG lacks the specific attribute, but we still
    # resolve the entity and ground the refusal in the evidence it DOES record.
    # Checked before the generic out-of-graph fallback so the refusal is grounded.
    for pattern, types, missing in (
        (r"recommended dosage of (.+)", DRUG_TYPES, "drug dosage"),
        (r"when was (.+?) approved", DRUG_TYPES, "drug approval dates"),
        (r"price of (.+)", DRUG_TYPES, "drug prices"),
        (r"clinical trial tested (.+)", DRUG_TYPES, "clinical trial data"),
        (r"which physician prescribed (.+)", DRUG_TYPES, "prescribing physicians"),
        (r"prognosis for (.+)", DISEASE_TYPES, "disease prognosis"),
    ):
        if mt := _m(pattern, q):
            return Plan("insufficient_data", [(_clean(mt.group(1)), types)],
                        missing=missing, answer_type="short_text")

    if _m(_OUT_OF_GRAPH, q):
        return Plan(op="out_of_graph", answer_type="short_text", refusal=_REFUSAL)

    # Specific multi-clause patterns must win over greedy one-hop templates
    # (e.g. "indicated for X but contraindicated for Y" is an intersection, not
    # a plain "indicated for X" lookup). The natural-language layer runs LAST so
    # it only ever handles questions the strict benchmark rules did not claim.
    for rule in (_classify_counts, _classify_intersections, _classify_chains,
                 _classify_one_hop, _classify_natural):
        plan = rule(q)
        if plan is not None:
            return plan

    return Plan(op="insufficient", answer_type="entity_list")


def _classify_natural(q: str) -> Plan | None:
    """Loose keyword-driven fallback for ad-hoc phrasing (side effects of X, what
    interacts with X, treatments for X, ...). Keyed to relation keywords, not to
    any specific question. Runs after the strict rules so it cannot regress them.
    """
    # side effects of a drug
    if mt := _m(r"(?:side|adverse|negative)[ -]?effects?\b.*?\b(?:of|for|from|caused by)\s+(.+)", q):
        return Plan("expand", [(_clean(mt.group(1)), DRUG_TYPES)], [S.SIDE_EFFECT],
                    final_type=PHENOTYPE_TYPES, noun="side effects")
    # "interacts with X" — drug (synergistic interaction) or protein (PPI),
    # decided from the resolved entity's type by the backend.
    if mt := _m(r"interact(?:s|ions)?\b(?:\s+with|\s+of|\s+between)?\s+(?:the\s+)?(?:drug\s+|protein\s+|gene\s+)?(.+)", q):
        return Plan("neighbors", [(_clean(mt.group(1)), DRUG_TYPES + PROTEIN_TYPES)],
                    noun="interactors")
    # treatments for a disease -> indicated drugs
    if mt := _m(r"(?:treatments?\s+(?:for|of)|treat|used to treat|drugs?\s+(?:for|to treat)|therap(?:y|ies)\s+for)\s+(.+)", q):
        return Plan("expand", [(_clean(mt.group(1)), DISEASE_TYPES)], [S.INDICATION],
                    final_type=DRUG_TYPES, noun="indicated drugs")
    if mt := _m(r"contraindicated\s+(?:for|in)\s+(.+)", q):
        return Plan("expand", [(_clean(mt.group(1)), DISEASE_TYPES)], [S.CONTRA],
                    final_type=DRUG_TYPES, noun="contraindicated drugs")
    if mt := _m(r"off[- ]label\b.*?\b(?:for|in)\s+(.+)", q):
        return Plan("expand", [(_clean(mt.group(1)), DISEASE_TYPES)], [S.OFFLABEL],
                    final_type=DRUG_TYPES, noun="off-label drugs")
    # targets of a drug
    if (mt := _m(r"(?:proteins?|genes?|targets?)\s+(?:that are\s+)?targeted by\s+(.+)", q)) \
            or (mt := _m(r"what does\s+(.+?)\s+target", q)) \
            or (mt := _m(r"targets?\s+of\s+(.+)", q)):
        return Plan("expand", [(_clean(mt.group(1)), DRUG_TYPES)], [S.TARGETS],
                    final_type=PROTEIN_TYPES, noun="target proteins")
    # proteins/genes associated with a disease
    if mt := _m(r"(?:proteins?|genes?)\s+(?:associated with|linked to|of)\s+(.+)", q):
        return Plan("expand", [(_clean(mt.group(1)), DISEASE_TYPES)], [S.DIS_PROTEIN],
                    final_type=PROTEIN_TYPES, noun="associated proteins")
    # phenotypes/symptoms of a disease
    if mt := _m(r"(?:phenotypes?|symptoms?)\s+(?:of|associated with|for|in)\s+(.+)", q):
        return Plan("expand", [(_clean(mt.group(1)), DISEASE_TYPES)], [S.DIS_PHENO],
                    final_type=PHENOTYPE_TYPES, noun="phenotypes")
    # pathways of a protein
    if mt := _m(r"pathways?\b.*?\b(?:involving|involve|of|for|with)\s+(?:protein\s+|gene\s+)?(.+)", q):
        return Plan("expand", [(_clean(mt.group(1)), PROTEIN_TYPES)], [S.PATHWAY],
                    final_type=PATHWAY_TYPES, noun="pathways")
    # child/subtype diseases of a disease
    if (mt := _m(r"child(?:ren)?\s+(?:disease\s+)?(?:diseases?\s+)?of\s+(.+)", q)) \
            or (mt := _m(r"subtypes?\s+of\s+(.+)", q)):
        return Plan("expand", [(_clean(mt.group(1)), DISEASE_TYPES)], [S.DIS_HIER],
                    final_type=DISEASE_TYPES, exclude_slot=0, noun="child diseases")
    # open-ended "what does PrimeKG know about X" -> summarize the entity's edges
    if (mt := _m(r"(?:what|which)\s+(?:information|data|details|facts|relationships?)\b.*?\b(?:about|for|on|available for|available on)\s+(.+)", q)) \
            or (mt := _m(r"(?:tell me about|what do you know about|what can you tell me about|describe|summar(?:y|ize)(?:\s+of)?)\s+(.+)", q)) \
            or (mt := _m(r"what is\s+(.+)", q)):
        return Plan("describe", [(_clean(mt.group(1)), ALL_TYPES)],
                    answer_type="short_text", noun="records")
    return None


def _classify_one_hop(q: str) -> Plan | None:
    # --- Category A: one-hop -------------------------------------------------
    if mt := _m(r"which protein[s]? does (?:the )?drug (.+?) target", q):
        single = "which protein " in q.lower()
        return Plan("expand", [(_clean(mt.group(1)), DRUG_TYPES)], [S.TARGETS],
                    final_type=PROTEIN_TYPES, noun="target proteins",
                    single_entity=single, answer_type="entity" if single else "entity_list")
    if mt := _m(r"which protein does (.+?) target", q):
        return Plan("expand", [(_clean(mt.group(1)), DRUG_TYPES)], [S.TARGETS],
                    final_type=PROTEIN_TYPES, noun="target proteins",
                    answer_type="entity")
    if mt := _m(r"side effects of (?:the )?drug (.+)", q):
        return Plan("expand", [(_clean(mt.group(1)), DRUG_TYPES)], [S.SIDE_EFFECT],
                    final_type=PHENOTYPE_TYPES, noun="side effects")
    if mt := _m(r"phenotypes are positively associated with disease (.+)", q):
        return Plan("expand", [(_clean(mt.group(1)), DISEASE_TYPES)], [S.DIS_PHENO],
                    final_type=PHENOTYPE_TYPES, noun="phenotypes")
    if mt := _m(r"which drugs are indicated for (?:the )?disease (.+)", q):
        return Plan("expand", [(_clean(mt.group(1)), DISEASE_TYPES)], [S.INDICATION],
                    final_type=DRUG_TYPES, noun="indicated drugs")
    if mt := _m(r"which drugs are contraindicated for (?:the )?disease (.+)", q):
        return Plan("expand", [(_clean(mt.group(1)), DISEASE_TYPES)], [S.CONTRA],
                    final_type=DRUG_TYPES, noun="contraindicated drugs")
    if mt := _m(r"which proteins are associated with disease (.+)", q):
        return Plan("expand", [(_clean(mt.group(1)), DISEASE_TYPES)], [S.DIS_PROTEIN],
                    final_type=PROTEIN_TYPES, noun="associated proteins")
    if mt := _m(r"which proteins does protein (.+?) interact with", q):
        return Plan("expand", [(_clean(mt.group(1)), PROTEIN_TYPES)], [S.PPI],
                    final_type=PROTEIN_TYPES, noun="PPI partners")
    if mt := _m(r"which pathways involve protein (.+)", q):
        return Plan("expand", [(_clean(mt.group(1)), PROTEIN_TYPES)], [S.PATHWAY],
                    final_type=PATHWAY_TYPES, noun="pathways")
    if mt := _m(r"used off-label for disease (.+)", q):
        return Plan("expand", [(_clean(mt.group(1)), DISEASE_TYPES)], [S.OFFLABEL],
                    final_type=DRUG_TYPES, noun="off-label drugs")
    if mt := _m(r"children of disease (.+)", q):
        return Plan("expand", [(_clean(mt.group(1)), DISEASE_TYPES)], [S.DIS_HIER],
                    final_type=DISEASE_TYPES, exclude_slot=0, noun="child diseases")
    if mt := _m(r"which gene mutation causes (.+)", q):
        # Ataxia etc. -> phenotype or disease -> associated protein(s)
        return Plan("expand", [(_clean(mt.group(1)), PHENOTYPE_TYPES + DISEASE_TYPES)],
                    [S.PHENO_PROTEIN], final_type=PROTEIN_TYPES, noun="genes",
                    single_entity=True, answer_type="entity")
    return None


def _classify_counts(q: str) -> Plan | None:
    # drugs with AT LEAST HALF of their targets shared with the targets of X (Q89)
    if mt := _m(r"drugs have at least half of their target proteins shared with the targets of (.+?)(?: \(| that|\?|$)", q):
        return Plan("ratio", [(_clean(mt.group(1)), DRUG_TYPES)], cmp=">=",
                    final_type=DRUG_TYPES, exclude_slot=0, noun="drugs")
    # "proteins targeted by more drugs indicated for X than by drugs indicated for Y"
    if mt := _m(r"proteins are targeted by more drugs indicated for (.+?) than by drugs indicated for (.+)", q):
        return Plan("count_compare",
                    [(_clean(mt.group(1)), DISEASE_TYPES), (_clean(mt.group(2)), DISEASE_TYPES)],
                    legs=[(0, [S.INDICATION, S.TARGETS]), (1, [S.INDICATION, S.TARGETS])],
                    cmp=">", final_type=PROTEIN_TYPES, noun="proteins")
    # "drugs linked/connected to X by at least N distinct target...bridges"
    if mt := _m(r"drugs are (?:linked|connected) to (.+?) by at least (\w+) distinct target", q):
        return Plan("bridge", [(_clean(mt.group(1)), DRUG_TYPES)], n=_num(mt.group(2)),
                    cmp=">=", final_type=DRUG_TYPES, exclude_slot=0, noun="drugs")
    # "among drugs that interact with X, which share AT LEAST N targets with X"
    if mt := _m(r"among drugs that interact with (.+?), which share at least (\w+) target proteins with", q):
        return Plan("count", [(_clean(mt.group(1)), DRUG_TYPES)],
                    [S.TARGETS, S.TARGETS], group_level=2, distinct_level=1, cmp=">=",
                    n=_num(mt.group(2)), final_type=DRUG_TYPES, exclude_slot=0,
                    member_leg=(0, [S.INTERACTS]), noun="drugs")
    # "disease(s) ... share the MOST associated proteins with X" -> rank
    if mt := _m(r"share the most associated proteins with (.+)", q):
        return Plan("rank", [(_clean(mt.group(1)), DISEASE_TYPES)],
                    [S.DIS_PROTEIN, S.DIS_PROTEIN], final_type=DISEASE_TYPES,
                    exclude_slot=0, noun="diseases")
    # "proteins associated with X OR Y but NOT both" -> XOR
    if mt := _m(r"proteins are associated with (.+?) or (.+?) but not both", q):
        return Plan("xor",
                    [(_clean(mt.group(1)), DISEASE_TYPES), (_clean(mt.group(2)), DISEASE_TYPES)],
                    legs=[(0, [S.DIS_PROTEIN]), (1, [S.DIS_PROTEIN])],
                    final_type=PROTEIN_TYPES, noun="proteins")
    # "side effects shared by at least two drugs indicated for X"
    if mt := _m(r"side effects .*shared by at least (\w+) drugs indicated for (.+)", q):
        return Plan("count", [(_clean(mt.group(2)), DISEASE_TYPES)],
                    [S.INDICATION, S.SIDE_EFFECT], group_level=2, distinct_level=1,
                    cmp=">=", n=_num(mt.group(1)), final_type=PHENOTYPE_TYPES,
                    noun="side effects")
    # "PPI partners of BRCA1 ... targeted by AT LEAST 5 distinct drugs"
    if mt := _m(r"ppi partners of protein (.+?),? which are targeted by at least (\w+)", q):
        return Plan("count", [(_clean(mt.group(1)), PROTEIN_TYPES)],
                    [S.PPI, S.TARGETS], group_level=1, distinct_level=2, cmp=">=",
                    n=_num(mt.group(2)), final_type=PROTEIN_TYPES, noun="proteins")
    # "proteins targeted by AT LEAST 3 different drugs each indicated for X"
    if mt := _m(r"proteins are targeted by at least (\w+) .*drugs .*indicated for (?:the disease )?(.+)", q):
        return Plan("count", [(_clean(mt.group(2)), DISEASE_TYPES)],
                    [S.INDICATION, S.TARGETS], group_level=2, distinct_level=1,
                    cmp=">=", n=_num(mt.group(1)), final_type=PROTEIN_TYPES,
                    noun="proteins")
    # "proteins are PPI partners of AT LEAST 4 distinct proteins associated with X"
    if mt := _m(r"ppi partners of at least (\w+) distinct proteins associated with (.+)", q):
        return Plan("count", [(_clean(mt.group(2)), DISEASE_TYPES)],
                    [S.DIS_PROTEIN, S.PPI], group_level=2, distinct_level=1, cmp=">=",
                    n=_num(mt.group(1)), final_type=PROTEIN_TYPES, noun="proteins")
    # "side effects caused by AT LEAST 2 drugs that each target a PPI partner of a protein associated with X"
    if mt := _m(r"side effects .*caused by at least (\w+) drugs that each target a ppi partner of a protein associated with (.+)", q):
        return Plan("count", [(_clean(mt.group(2)), DISEASE_TYPES)],
                    [S.DIS_PROTEIN, S.PPI, S.TARGETS, S.SIDE_EFFECT],
                    group_level=4, distinct_level=3, cmp=">=", n=_num(mt.group(1)),
                    final_type=PHENOTYPE_TYPES, noun="side effects")
    # "drugs share EXACTLY N target proteins with the drug X"
    if mt := _m(r"drugs share exactly (\w+) target proteins with the drug (.+)", q):
        return Plan("count", [(_clean(mt.group(2)), DRUG_TYPES)],
                    [S.TARGETS, S.TARGETS], group_level=2, distinct_level=1, cmp="=",
                    n=_num(mt.group(1)), final_type=DRUG_TYPES, exclude_slot=0, noun="drugs")
    # "diseases share AT LEAST N associated proteins with X" (drops the extra
    # "and have >=1 drug" existential; the shared-protein count is the core op)
    if mt := _m(r"diseases share at least (\w+) associated proteins with (.+?)(?: and| that|\?|$)", q):
        return Plan("count", [(_clean(mt.group(2)), DISEASE_TYPES)],
                    [S.DIS_PROTEIN, S.DIS_PROTEIN], group_level=2, distinct_level=1,
                    cmp=">=", n=_num(mt.group(1)), final_type=DISEASE_TYPES,
                    exclude_slot=0, noun="diseases")
    return None


def _classify_intersections(q: str) -> Plan | None:
    # proteins targeted by BOTH a drug indicated for X and a drug contraindicated for Y
    if mt := _m(r"proteins are targeted by both a drug indicated for (.+?) and a drug contraindicated for (.+)", q):
        return Plan("intersect",
                    [(_clean(mt.group(1)), DISEASE_TYPES), (_clean(mt.group(2)), DISEASE_TYPES)],
                    legs=[(0, [S.INDICATION, S.TARGETS]), (1, [S.CONTRA, S.TARGETS])],
                    final_type=PROTEIN_TYPES, noun="proteins")
    # proteins both associated with the disease X and targeted by the drug Y
    if mt := _m(r"proteins are both associated with the disease (.+?) and targeted by the drug (.+)", q):
        return Plan("intersect",
                    [(_clean(mt.group(1)), DISEASE_TYPES), (_clean(mt.group(2)), DRUG_TYPES)],
                    legs=[(0, [S.DIS_PROTEIN]), (1, [S.TARGETS])],
                    final_type=PROTEIN_TYPES, noun="proteins")
    # drugs indicated for X but contraindicated for Y
    if mt := _m(r"drugs are indicated for the disease (.+?) but contraindicated for the disease (.+)", q):
        return Plan("intersect",
                    [(_clean(mt.group(1)), DISEASE_TYPES), (_clean(mt.group(2)), DISEASE_TYPES)],
                    legs=[(0, [S.INDICATION]), (1, [S.CONTRA])],
                    final_type=DRUG_TYPES, noun="drugs")
    # drugs indicated for X and also cause the side effect Y
    if mt := _m(r"drugs are indicated for the disease (.+?) and also cause the side effect (.+)", q):
        return Plan("intersect",
                    [(_clean(mt.group(1)), DISEASE_TYPES), (_clean(mt.group(2)), PHENOTYPE_TYPES)],
                    legs=[(0, [S.INDICATION]), (1, [S.SIDE_EFFECT])],
                    final_type=DRUG_TYPES, noun="drugs")
    # diseases are both A and B contraindicated for
    if mt := _m(r"diseases are both (.+?) and (.+?) contraindicated for", q):
        return Plan("intersect",
                    [(_clean(mt.group(1)), DRUG_TYPES), (_clean(mt.group(2)), DRUG_TYPES)],
                    legs=[(0, [S.CONTRA]), (1, [S.CONTRA])],
                    final_type=DISEASE_TYPES, noun="diseases")
    # drugs interact with X and are contraindicated for Y
    if mt := _m(r"drugs interact with (.+?) and are contraindicated for (.+)", q):
        return Plan("intersect",
                    [(_clean(mt.group(1)), DRUG_TYPES), (_clean(mt.group(2)), DISEASE_TYPES)],
                    legs=[(0, [S.INTERACTS]), (1, [S.CONTRA])],
                    final_type=DRUG_TYPES, noun="drugs")
    # drugs BOTH interact with X AND share at least one target protein with X
    if mt := _m(r"drugs both interact with (.+?) and share at least one target protein with", q):
        label = _clean(mt.group(1))
        return Plan("intersect",
                    [(label, DRUG_TYPES), (label, DRUG_TYPES)],
                    legs=[(0, [S.INTERACTS]), (1, [S.TARGETS, S.TARGETS])],
                    final_type=DRUG_TYPES, exclude_slot=0, noun="drugs")
    # drugs indicated for X interact with a drug contraindicated for Y
    if mt := _m(r"drugs indicated for (.+?) interact with a drug contraindicated for (.+)", q):
        return Plan("intersect",
                    [(_clean(mt.group(1)), DISEASE_TYPES), (_clean(mt.group(2)), DISEASE_TYPES)],
                    legs=[(0, [S.INDICATION]), (1, [S.CONTRA, S.INTERACTS])],
                    final_type=DRUG_TYPES, noun="drugs")
    # drugs contraindicated for X target a protein of Y
    if mt := _m(r"drugs contraindicated for (.+?) target a protein of (.+)", q):
        return Plan("intersect",
                    [(_clean(mt.group(1)), DISEASE_TYPES), (_clean(mt.group(2)), DISEASE_TYPES)],
                    legs=[(0, [S.CONTRA]), (1, [S.DIS_PROTEIN, S.TARGETS])],
                    final_type=DRUG_TYPES, noun="drugs")
    # genes associated with BOTH X and Y that are targeted by at least one drug (Q92)
    if mt := _m(r"genes associated with both (.+?) and (.+?) that are targeted by at least one drug", q):
        return Plan("intersect",
                    [(_clean(mt.group(1)), DISEASE_TYPES), (_clean(mt.group(2)), DISEASE_TYPES)],
                    legs=[(0, [S.DIS_PROTEIN]), (1, [S.DIS_PROTEIN])],
                    final_type=PROTEIN_TYPES, require_edge=S.TARGETS, noun="genes")
    # PPI partners of BOTH a target of a drug indicated for X and ... indicated for Y
    if mt := _m(r"ppi partners of both a target of a drug indicated for (.+?) and a target of a drug indicated for (.+)", q):
        return Plan("intersect",
                    [(_clean(mt.group(1)), DISEASE_TYPES), (_clean(mt.group(2)), DISEASE_TYPES)],
                    legs=[(0, [S.INDICATION, S.TARGETS, S.PPI]), (1, [S.INDICATION, S.TARGETS, S.PPI])],
                    final_type=PROTEIN_TYPES, noun="proteins")
    # proteins targeted BOTH by a drug interacting with a drug indicated for X AND by a drug contraindicated for Y
    if mt := _m(r"proteins are targeted both by a drug interacting with a drug indicated for (.+?) and by a drug contraindicated for (.+)", q):
        return Plan("intersect",
                    [(_clean(mt.group(1)), DISEASE_TYPES), (_clean(mt.group(2)), DISEASE_TYPES)],
                    legs=[(0, [S.INDICATION, S.INTERACTS, S.TARGETS]), (1, [S.CONTRA, S.TARGETS])],
                    final_type=PROTEIN_TYPES, noun="proteins")
    # drugs indicated for X interact with a drug that shares a target with a drug contraindicated for Y
    if mt := _m(r"drugs indicated for (.+?) interact with a drug that shares a target with a drug contraindicated for (.+)", q):
        return Plan("intersect",
                    [(_clean(mt.group(1)), DISEASE_TYPES), (_clean(mt.group(2)), DISEASE_TYPES)],
                    legs=[(0, [S.INDICATION]), (1, [S.CONTRA, S.TARGETS, S.TARGETS, S.INTERACTS])],
                    final_type=DRUG_TYPES, noun="drugs")
    # gene uniquely connects X and Y (intersection of associated proteins)
    if mt := _m(r"gene uniquely connects (.+?) and (.+)", q):
        return Plan("intersect",
                    [(_clean(mt.group(1)), DISEASE_TYPES), (_clean(mt.group(2)), DISEASE_TYPES)],
                    legs=[(0, [S.DIS_PROTEIN]), (1, [S.DIS_PROTEIN])],
                    final_type=PROTEIN_TYPES, noun="gene", single_entity=True,
                    answer_type="entity")
    # drug that targets a gene assoc X, participates in pathway 'P', causes phenotype 'Ph', contraindicated for Y  (Q94)
    if mt := _m(r"drug that targets a gene associated with (.+?), participates in the pathway '(.+?)', causes the phenotype '(.+?)', and is contraindicated for (.+)", q):
        return Plan("intersect_many",
                    [(_clean(mt.group(1)), DISEASE_TYPES), (_clean(mt.group(2)), PATHWAY_TYPES),
                     (_clean(mt.group(3)), PHENOTYPE_TYPES), (_clean(mt.group(4)), DISEASE_TYPES)],
                    legs=[(0, [S.DIS_PROTEIN, S.TARGETS]), (1, [S.PATHWAY, S.TARGETS]),
                          (2, [S.SIDE_EFFECT]), (3, [S.CONTRA])],
                    final_type=DRUG_TYPES, single_entity=True, answer_type="entity", noun="drug")
    # drug indicated for X and targets a protein that shares the 'P' pathway with a gene assoc Y  (Q95)
    if mt := _m(r"drug is indicated for (.+?) and targets a protein that shares the '(.+?)' pathway with a gene associated with", q):
        return Plan("intersect",
                    [(_clean(mt.group(1)), DISEASE_TYPES), (_clean(mt.group(2)), PATHWAY_TYPES)],
                    legs=[(0, [S.INDICATION]), (1, [S.PATHWAY, S.TARGETS])],
                    final_type=DRUG_TYPES, single_entity=True, answer_type="entity", noun="drug")
    # drugs indicated for X, contraindicated for Y, AND share >=1 target with Z  (Q91)
    if mt := _m(r"drugs are indicated for (.+?), contraindicated for (.+?), and share at least one target with (.+)", q):
        return Plan("intersect_many",
                    [(_clean(mt.group(1)), DISEASE_TYPES), (_clean(mt.group(2)), DISEASE_TYPES),
                     (_clean(mt.group(3)), DRUG_TYPES)],
                    legs=[(0, [S.INDICATION]), (1, [S.CONTRA]), (2, [S.TARGETS, S.TARGETS])],
                    final_type=DRUG_TYPES, exclude_slot=2, noun="drugs")
    return None


def _classify_chains(q: str) -> Plan | None:
    # targets of X NOT in any pathway shared with a target of Y (Q87)
    if mt := _m(r"targets of (.+?) are not in any pathway shared with a target of (.+)", q):
        return Plan("difference",
                    [(_clean(mt.group(1)), DRUG_TYPES), (_clean(mt.group(2)), DRUG_TYPES)],
                    legs=[(0, [S.TARGETS]), (1, [S.TARGETS, S.PATHWAY, S.PATHWAY])],
                    final_type=PROTEIN_TYPES, noun="proteins")
    # diseases (other than X) treated by drugs targeting PPI partners of proteins hit by drugs indicated for X, excluding diseases sharing an indicated drug with X (Q57)
    if mt := _m(r"diseases \(other than .+?\) are treated by drugs targeting ppi partners of proteins hit by drugs indicated for (.+?), excluding diseases sharing an indicated drug", q):
        return Plan("difference",
                    [(_clean(mt.group(1)), DISEASE_TYPES), (_clean(mt.group(1)), DISEASE_TYPES)],
                    legs=[(0, [S.INDICATION, S.TARGETS, S.PPI, S.TARGETS, S.INDICATION]),
                          (1, [S.INDICATION, S.INDICATION])],
                    final_type=DISEASE_TYPES, exclude_slot=0, noun="diseases")
    # drugs share >=1 target with X but do NOT interact with X and are NOT indicated for any disease X is indicated for (Q79)
    if mt := _m(r"drugs share at least one target with (.+?) but do not interact with .+? and are not indicated for any disease", q):
        label = _clean(mt.group(1))
        return Plan("difference_many", [(label, DRUG_TYPES)],
                    legs=[(0, [S.TARGETS, S.TARGETS]), (0, [S.INTERACTS]),
                          (0, [S.INDICATION, S.INDICATION])],
                    final_type=DRUG_TYPES, exclude_slot=0, noun="drugs")
    # first-line treatment for X -> drugs indicated for X (closest graph relation)
    if mt := _m(r"first-line treatment for (.+)", q):
        return Plan("expand", [(_clean(mt.group(1)), DISEASE_TYPES)], [S.INDICATION],
                    final_type=DRUG_TYPES, noun="first-line (indicated) drugs",
                    answer_type="short_text")
    # side effects caused by drugs that interact with a drug sharing a target with a drug indicated for a child disease of X (Q64)
    if mt := _m(r"side effects are caused by drugs that interact with a drug sharing a target with a drug indicated for a child disease of (.+)", q):
        return Plan("expand", [(_clean(mt.group(1)), DISEASE_TYPES)],
                    [S.DIS_HIER, S.INDICATION, S.TARGETS, S.TARGETS, S.INTERACTS, S.SIDE_EFFECT],
                    final_type=PHENOTYPE_TYPES, noun="side effects", answer_type="short_text")
    # pathways involve a protein targeted by the drug X
    if mt := _m(r"pathways involve a protein targeted by the drug (.+)", q):
        return Plan("expand", [(_clean(mt.group(1)), DRUG_TYPES)], [S.TARGETS, S.PATHWAY],
                    final_type=PATHWAY_TYPES, noun="pathways")
    # drugs interact with a drug indicated for the disease X
    if mt := _m(r"drugs interact with a drug indicated for the disease (.+)", q):
        return Plan("expand", [(_clean(mt.group(1)), DISEASE_TYPES)], [S.INDICATION, S.INTERACTS],
                    final_type=DRUG_TYPES, noun="drugs")
    # phenotypes are associated with the proteins of the disease X
    if mt := _m(r"phenotypes are associated with the proteins of the disease (.+)", q):
        return Plan("expand", [(_clean(mt.group(1)), DISEASE_TYPES)], [S.DIS_PROTEIN, S.PHENO_PROTEIN],
                    final_type=PHENOTYPE_TYPES, noun="phenotypes")
    # diseases share an associated protein with the disease X
    if mt := _m(r"diseases share an associated protein with the disease (.+)", q):
        return Plan("expand", [(_clean(mt.group(1)), DISEASE_TYPES)], [S.DIS_PROTEIN, S.DIS_PROTEIN],
                    final_type=DISEASE_TYPES, exclude_slot=0, noun="diseases")
    # PPI neighbors of proteins targeted by drugs indicated for X
    if mt := _m(r"ppi neighbors of proteins targeted by drugs indicated for (.+)", q):
        return Plan("expand", [(_clean(mt.group(1)), DISEASE_TYPES)],
                    [S.INDICATION, S.TARGETS, S.PPI], final_type=PROTEIN_TYPES, noun="proteins")
    # pathways involve the proteins targeted by drugs indicated for X
    if mt := _m(r"pathways involve the proteins targeted by drugs indicated for (.+)", q):
        return Plan("expand", [(_clean(mt.group(1)), DISEASE_TYPES)],
                    [S.INDICATION, S.TARGETS, S.PATHWAY], final_type=PATHWAY_TYPES, noun="pathways")
    # for drug X, which diseases are associated with the proteins it targets
    if mt := _m(r"for drug (.+?), which diseases are associated with the proteins it targets", q):
        return Plan("expand", [(_clean(mt.group(1)), DRUG_TYPES)], [S.TARGETS, S.DIS_PROTEIN],
                    final_type=DISEASE_TYPES, noun="diseases")
    # side effects are caused by drugs that share a target with X
    if mt := _m(r"side effects are caused by drugs that share a target with (.+)", q):
        return Plan("expand", [(_clean(mt.group(1)), DRUG_TYPES)],
                    [S.TARGETS, S.TARGETS, S.SIDE_EFFECT], final_type=PHENOTYPE_TYPES, noun="side effects")
    # For the diseases associated with protein P, what side effects ... drug indicated for them
    if mt := _m(r"diseases associated with protein (.+?), what side effects", q):
        return Plan("expand", [(_clean(mt.group(1)), PROTEIN_TYPES)],
                    [S.DIS_PROTEIN, S.INDICATION, S.SIDE_EFFECT], final_type=PHENOTYPE_TYPES,
                    noun="side effects")
    # drugs treat a related/child disease of it (For disease X)
    if mt := _m(r"for (.+?), which drugs treat a related/child disease", q):
        return Plan("expand", [(_clean(mt.group(1)), DISEASE_TYPES)], [S.DIS_HIER, S.INDICATION],
                    final_type=DRUG_TYPES, noun="drugs", answer_type="short_text")
    # drugs target a protein in the same pathway as a protein of X
    if mt := _m(r"drugs target a protein in the same pathway as a protein of (.+)", q):
        return Plan("expand", [(_clean(mt.group(1)), DISEASE_TYPES)],
                    [S.DIS_PROTEIN, S.PATHWAY, S.PATHWAY, S.TARGETS],
                    final_type=DRUG_TYPES, noun="drugs", answer_type="short_text")
    # diseases share a pathway with X through a common protein
    if mt := _m(r"diseases share a pathway with (.+?) through a common protein", q):
        return Plan("expand", [(_clean(mt.group(1)), DISEASE_TYPES)],
                    [S.DIS_PROTEIN, S.PATHWAY, S.PATHWAY, S.DIS_PROTEIN],
                    final_type=DISEASE_TYPES, exclude_slot=0, noun="diseases")
    # phenotypes are linked to proteins that are PPI partners of proteins sharing a pathway with a protein targeted by a drug indicated for X
    if mt := _m(r"phenotypes are linked to proteins that are ppi partners of proteins sharing a pathway with a protein targeted by a drug indicated for (.+)", q):
        return Plan("expand", [(_clean(mt.group(1)), DISEASE_TYPES)],
                    [S.INDICATION, S.TARGETS, S.PATHWAY, S.PATHWAY, S.PPI, S.PHENO_PROTEIN],
                    final_type=PHENOTYPE_TYPES, noun="phenotypes")
    # phenotypes link to proteins in a pathway targeted by a drug for X
    if mt := _m(r"phenotypes link to proteins in a pathway targeted by a drug for (.+)", q):
        return Plan("expand", [(_clean(mt.group(1)), DISEASE_TYPES)],
                    [S.INDICATION, S.TARGETS, S.PATHWAY, S.PATHWAY, S.PHENO_PROTEIN],
                    final_type=PHENOTYPE_TYPES, noun="phenotypes")
    # diseases treated by drugs targeting PPI partners of proteins targeted by drugs indicated for a child disease of X
    if mt := _m(r"diseases are treated by drugs targeting ppi partners of proteins targeted by drugs indicated for a child disease of (.+)", q):
        return Plan("expand", [(_clean(mt.group(1)), DISEASE_TYPES)],
                    [S.DIS_HIER, S.INDICATION, S.TARGETS, S.PPI, S.TARGETS, S.INDICATION],
                    final_type=DISEASE_TYPES, noun="diseases")
    # diseases treated by a drug that interacts with a drug targeting a protein sharing a pathway with a protein associated with X
    if mt := _m(r"diseases are treated by a drug that interacts with a drug targeting a protein sharing a pathway with a protein associated with (.+)", q):
        return Plan("expand", [(_clean(mt.group(1)), DISEASE_TYPES)],
                    [S.DIS_PROTEIN, S.PATHWAY, S.PATHWAY, S.TARGETS, S.INTERACTS, S.INDICATION],
                    final_type=DISEASE_TYPES, noun="diseases")
    # proteins targeted by a drug that interacts with a drug targeting a protein sharing a pathway with a protein associated with X
    if mt := _m(r"proteins are targeted by a drug that interacts with a drug targeting a protein sharing a pathway with a protein associated with (.+)", q):
        return Plan("expand", [(_clean(mt.group(1)), DISEASE_TYPES)],
                    [S.DIS_PROTEIN, S.PATHWAY, S.PATHWAY, S.TARGETS, S.INTERACTS, S.TARGETS],
                    final_type=PROTEIN_TYPES, noun="proteins")
    return None
