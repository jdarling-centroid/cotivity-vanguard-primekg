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
