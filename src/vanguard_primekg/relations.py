"""Shared PrimeKG relation constants used by the loader and the query engine."""

from __future__ import annotations

# The four drug->protein display roles that ALL count as "target" per the RFP.
TARGET_ROLES: tuple[str, ...] = ("target", "enzyme", "carrier", "transporter")

# Predicates needed to answer the 100 questions. The loader defaults to this
# selected source relations for fast local iteration; pass --relations all for
# every source fact before the final run. The loader materializes each fact in
# both directions, so pk_edges contains directed records rather than source-row counts.
SUBSET_PREDICATES: tuple[str, ...] = (
    "drug_drug",                   # synergistic interaction
    "protein_protein",             # ppi
    "disease_phenotype_positive",  # phenotype present
    "disease_protein",             # associated with
    "drug_effect",                 # side effect
    "pathway_protein",             # interacts with
    "disease_disease",             # parent-child
    "contraindication",
    "drug_protein",                # target/enzyme/carrier/transporter
    "indication",
    "off-label use",
    "phenotype_protein",           # associated with
    "phenotype_phenotype",         # parent-child
)

# Node types by question slot, for type-scoped entity resolution.
DRUG_TYPES: tuple[str, ...] = ("drug",)
PROTEIN_TYPES: tuple[str, ...] = ("gene/protein",)
DISEASE_TYPES: tuple[str, ...] = ("disease",)
PHENOTYPE_TYPES: tuple[str, ...] = ("effect/phenotype",)
PATHWAY_TYPES: tuple[str, ...] = ("pathway",)

# Every node type — used to resolve an entity of unknown kind ("tell me about X").
ALL_TYPES: tuple[str, ...] = (
    "drug", "disease", "gene/protein", "effect/phenotype", "pathway",
)
