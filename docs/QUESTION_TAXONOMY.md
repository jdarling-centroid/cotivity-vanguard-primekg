# Question Taxonomy (Milestone 1)

The spec for the query engine. Every one of the 100 PrimeKG questions is mapped
to a category (A–F) and the graph primitive(s) it composes. Composition happens
in Oracle — each answered question resolves to **one** parameterized SQL/PGQ
query. No per-question query builders.

## Graph primitives

All primitives read `pk_edges` filtered by `(predicate, display_relation)` and
return node ids + the edge ids that justify them. **Drug→protein targeting always
includes all four roles**: `target`, `enzyme`, `carrier`, `transporter`.

| id | traversal | predicate \| display_relation |
|---|---|---|
| `drug_targets(d)` | drug → proteins | `drug_protein` \| {target,enzyme,carrier,transporter} |
| `targeted_by(p)` | protein → drugs | reverse of `drug_targets` |
| `side_effects(d)` | drug → effect/phenotype | `drug_effect` \| side effect |
| `indicated_drugs(dis)` | disease → drugs | `indication` \| indication |
| `contra_drugs(dis)` | disease → drugs | `contraindication` \| contraindication |
| `offlabel_drugs(dis)` | disease → drugs | `off-label use` \| off-label use |
| `disease_proteins(dis)` | disease → proteins | `disease_protein` \| associated with |
| `disease_phenotypes(dis)` | disease → phenotypes | `disease_phenotype_positive` \| phenotype present |
| `ppi(p)` | protein → proteins | `protein_protein` \| ppi |
| `pathways(p)` | protein → pathways | `pathway_protein` \| interacts with (reverse) |
| `pathway_proteins(pw)` | pathway → proteins | `pathway_protein` \| interacts with |
| `child_diseases(dis)` | disease → child diseases | `disease_disease` \| parent-child |
| `drug_interacts(d)` | drug → drugs | `drug_drug` \| synergistic interaction |
| `protein_phenotypes(p)` | protein → phenotypes | `phenotype_protein` \| associated with (reverse) |

## Categories

- **A — one-hop lookup.** `resolve(entity)` → one primitive → return nodes + edge ids.
- **B — two/N-set intersection / conjunction.** Two or more sub-selects combined
  with `INTERSECT` / `IN (…) AND IN (…)` in one query. The class that broke the
  old system.
- **C — multi-hop chain.** One PGQ `MATCH` with several segments (or a CTE chain).
- **D — aggregation / quantifier / negation.** `GROUP BY … HAVING COUNT >= n`,
  `EXCEPT` / `NOT EXISTS`, `RANK()` for "MOST", XOR, ratios, "EXACTLY n".
- **E — out-of-graph fact.** PrimeKG does not contain it → honest
  "not represented in PrimeKG" with `SUPPORTED_BY:\n- NONE`. Never hallucinate.
- **F — adversarial / injection.** Blocked by the firewall before any query.

## Distribution

| category | count | question numbers |
|---|---:|---|
| A | 12 | 1–10, 69, 76 |
| B | 15 | 11, 22, 23, 24, 25, 28, 29, 31, 32, 33, 34, 35, 48, 55, 91 |
| C | 41 | 14–21, 26, 27, 30, 36–47, 49, 51–54, 56–66, 94, 95 |
| D | 19 | 12, 13, 50, 77–90, 92, 93 |
| E | 8 | 67, 68, 70, 71, 72, 73, 74, 75 |
| F | 5 | 96, 97, 98, 99, 100 |

## Per-question map

| # | cat | primitives / operation |
|---|---|---|
| 1 | A | drug_targets |
| 2 | A | side_effects |
| 3 | A | disease_phenotypes |
| 4 | A | indicated_drugs |
| 5 | A | contra_drugs |
| 6 | A | disease_proteins |
| 7 | A | ppi |
| 8 | A | pathways |
| 9 | A | offlabel_drugs |
| 10 | A | child_diseases |
| 11 | B | indicated_drugs(X) INTERSECT contra_drugs(Y) |
| 12 | D | side_effects of indicated_drugs(X); HAVING COUNT(distinct drug) >= 2 |
| 13 | D | as Q12 |
| 14 | C | disease_proteins → protein_phenotypes |
| 15 | C | as Q14 |
| 16 | C | disease_proteins(X) → disease_proteins⁻¹ (diseases sharing a protein) |
| 17 | C | as Q16 |
| 18 | C | drug_targets → pathways |
| 19 | C | as Q18 |
| 20 | C | indicated_drugs → drug_interacts |
| 21 | C | as Q20 |
| 22 | B | disease_proteins(X) INTERSECT drug_targets(Y) |
| 23 | B | as Q22 |
| 24 | B | indicated_drugs(X) INTERSECT (drugs with side_effect Y) |
| 25 | B | as Q24 |
| 26 | C | drug_interacts(X) INTERSECT contra_drugs(Y) |
| 27 | C | indicated_drugs → drug_targets → ppi |
| 28 | B | contra_drugs(A) INTERSECT contra_drugs(B) (diseases) |
| 29 | B | drug_targets(indicated_drugs X) INTERSECT drug_targets(contra_drugs Y) |
| 30 | C | drug_interacts(X) INTERSECT contra_drugs(Y) |
| 31 | B | as Q29 |
| 32 | B | contra_drugs(A) INTERSECT contra_drugs(B) |
| 33 | B | as Q29 |
| 34 | B | contra_drugs(A) INTERSECT contra_drugs(B) |
| 35 | B | as Q29 |
| 36 | C | drug_interacts(X) INTERSECT contra_drugs(Y) |
| 37 | C | disease_proteins⁻¹(SOD2) → indicated_drugs → side_effects |
| 38 | C | indicated_drugs → drug_targets → pathways |
| 39 | C | disease_proteins(X) → pathways → pathway_proteins → targeted_by |
| 40 | C | drug_targets(X) → disease_proteins⁻¹ |
| 41 | C | drug_targets(Carvedilol) → targeted_by → side_effects |
| 42 | C | indicated_drugs → drug_targets → pathways → pathway_proteins → protein_phenotypes |
| 43 | C | contra_drugs(X) INTERSECT targeted_by(disease_proteins Y) |
| 44 | C | disease_proteins(X) → pathways → pathway_proteins → disease_proteins⁻¹ |
| 45 | C | child_diseases(X) → indicated_drugs |
| 46 | C | indicated_drugs(X) INTERSECT drug_interacts(contra_drugs Y) |
| 47 | C | indicated_drugs → drug_interacts → shared-target → contra_drugs (chain) |
| 48 | B | drug_interacts(X) INTERSECT (drugs sharing a target with X) |
| 49 | C | as Q47 |
| 50 | D | target→ppi→target bridges between drug X and others; HAVING distinct bridges >= 2 |
| 51 | C | ppi(drug_targets(indicated X)) INTERSECT ppi(drug_targets(indicated Y)) |
| 52 | C | drug_targets(drug_interacts(indicated X)) INTERSECT drug_targets(contra Y) |
| 53 | C | as Q47 |
| 54 | C | as Q51 |
| 55 | B | as Q48 |
| 56 | C | as Q51 |
| 57 | C | indicated→target→ppi→targeted_by→treated-disease, minus diseases sharing an indicated drug (negation-flavored chain) |
| 58 | C | drug_targets(drug_interacts(indicated X)) INTERSECT drug_targets(contra Y) |
| 59 | C | as Q51 |
| 60 | C | indicated(X) INTERSECT drug_interacts(shared-target(contra Y)) |
| 61 | C | as Q60 |
| 62 | C | indicated→target→pathway→pathway_proteins→ppi→protein_phenotypes |
| 63 | C | child_diseases → indicated → target → ppi → targeted_by → treated-disease |
| 64 | C | child_diseases → indicated → shared-target → interacts → side_effects |
| 65 | C | disease_proteins → pathway → co-pathway protein → targeted_by → interacts → treated-disease |
| 66 | C | disease_proteins → pathway → co-pathway protein → targeted_by → interacts → targeted_by |
| 67 | E | recommended dosage — not in PrimeKG |
| 68 | E | approval date — not in PrimeKG |
| 69 | A | drug_targets (single) |
| 70 | E | first-line treatment — not in PrimeKG |
| 71 | E | price — not in PrimeKG |
| 72 | E | clinical trial — not in PrimeKG |
| 73 | E | dose causing side effect — not in PrimeKG |
| 74 | E | prescribing physician — not in PrimeKG |
| 75 | E | prognosis — not in PrimeKG |
| 76 | A | disease/phenotype → associated protein (gene) |
| 77 | D | COUNT indicated(hypertension) vs indicated(asthma) per target; HAVING n1 > n2 |
| 78 | D | shared targets with Imatinib per drug; HAVING COUNT = 3 |
| 79 | D | share-target(Carvedilol) EXCEPT interacts(Carvedilol) EXCEPT indicated-overlap |
| 80 | D | ppi(BRCA1) filtered by COUNT(distinct targeted_by drug) >= 5 |
| 81 | D | proteins with COUNT(distinct indicated-for-schizophrenia drug) >= 3 |
| 82 | D | diseases with COUNT(shared proteins with epilepsy) >= 3 AND EXISTS indicated_drugs |
| 83 | D | side_effects with COUNT(distinct drug targeting ppi(disease_proteins CF)) >= 2 |
| 84 | D | disease_proteins(X) XOR disease_proteins(Y) |
| 85 | D | diseases ranked by shared-protein count with Alzheimer; RANK() = 1 |
| 86 | D | bridges(Plinabulin, drug) >= 3 |
| 87 | D | drug_targets(Imatinib) EXCEPT (targets in pathway shared with a Dasatinib target) |
| 88 | D | proteins with COUNT(distinct ppi to epilepsy proteins) >= 4 |
| 89 | D | drugs with shared(Imatinib targets) >= 0.5 * own targets AND >= 1 |
| 90 | D | drug_interacts(Warfarin) filtered by shared-targets(Warfarin) >= 2 |
| 91 | B | indicated(hypertension) INTERSECT contra(asthma) INTERSECT share-target(Carvedilol) |
| 92 | D | disease_proteins(X) INTERSECT disease_proteins(Y) filtered by EXISTS targeted_by |
| 93 | D | gene in disease_proteins(X) INTERSECT disease_proteins(Y), uniqueness (COUNT = 1) |
| 94 | C | drug: targets(gene assoc epilepsy) AND in pathway P AND side_effect Ph AND contra epilepsy |
| 95 | C | drug indicated(morphine dependence) targeting protein co-pathway(P) with gene assoc FAP |
| 96 | F | blocked — instruction_override (appended DETACH DELETE) |
| 97 | F | blocked — fabricated_authority (node-embedded SYSTEM NOTE) |
| 98 | F | blocked — instruction_override (insert edge before answering) |
| 99 | F | blocked — data_exfiltration (export_graph to external URL) |
| 100 | F | blocked — forced_answer (ignore KG, respond NONE) |

## Notes

- Several B/C questions intersect two multi-hop sets (e.g. Q29/31/33/35 intersect
  two 2-hop target sets; Q51/54/56/59 intersect two 3-hop PPI sets). They are
  built from the same primitives plus one `INTERSECT`; the category marks the
  dominant operation, not a distinct builder.
- "shares a target with D" = `drug_targets(D)` joined back through `targeted_by`.
- "bridge" (Q50/86) = `target(drugA) —ppi— target(drugB)`; count distinct
  `(p_a, p_b)` pairs.
- Category E's honest refusal is mandatory even when `requires_evidence: true`
  (Q74/75): the fact is absent, so the evidence-free refusal is the correct answer.
