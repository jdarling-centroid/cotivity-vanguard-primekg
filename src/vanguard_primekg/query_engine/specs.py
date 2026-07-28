"""Named relation specs. PrimeKG is undirected (every edge stored both ways), so
a hop is always source->target filtered by predicate (+ optional display roles).
"""

from __future__ import annotations

from dataclasses import dataclass

from ..relations import TARGET_ROLES


@dataclass(frozen=True)
class RelSpec:
    predicate: str
    displays: tuple[str, ...] | None = None  # None = any display_relation


TARGETS = RelSpec("drug_protein", TARGET_ROLES)   # drug <-> protein (all 4 roles)
SIDE_EFFECT = RelSpec("drug_effect", ("side effect",))
INDICATION = RelSpec("indication")
CONTRA = RelSpec("contraindication")
OFFLABEL = RelSpec("off-label use")
DIS_PROTEIN = RelSpec("disease_protein")          # disease <-> protein
DIS_PHENO = RelSpec("disease_phenotype_positive") # disease <-> phenotype
PPI = RelSpec("protein_protein", ("ppi",))
PATHWAY = RelSpec("pathway_protein")              # pathway <-> protein
DIS_HIER = RelSpec("disease_disease")             # parent-child (undirected)
PHENO_HIER = RelSpec("phenotype_phenotype")
INTERACTS = RelSpec("drug_drug")                  # synergistic interaction
PHENO_PROTEIN = RelSpec("phenotype_protein")

# Closed planner vocabulary.  The model selects these stable identifiers; it
# never supplies raw predicates or display-relation strings.
RELATION_BY_ID: dict[str, RelSpec] = {
    "targets": TARGETS,
    "side_effect": SIDE_EFFECT,
    "indication": INDICATION,
    "contraindication": CONTRA,
    "off_label": OFFLABEL,
    "disease_protein": DIS_PROTEIN,
    "disease_phenotype": DIS_PHENO,
    "protein_interaction": PPI,
    "pathway_protein": PATHWAY,
    "disease_hierarchy": DIS_HIER,
    "phenotype_hierarchy": PHENO_HIER,
    "drug_interaction": INTERACTS,
    "phenotype_protein": PHENO_PROTEIN,
}


def relation_id(spec: RelSpec) -> str:
    """Return the stable planner identifier for a relation specification."""
    for identifier, candidate in RELATION_BY_ID.items():
        if candidate == spec:
            return identifier
    raise ValueError(f"relation is not in the closed planner vocabulary: {spec!r}")
