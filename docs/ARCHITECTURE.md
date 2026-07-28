# Architecture

How vanguard-primekg works, end to end. Read `README.md` first for how to run it,
`AGENTS.md` for the invariants, and `docs/QUESTION_TAXONOMY.md` for the per-question
category map. This document is the map for picking the project back up.

## 1. Thesis & data flow

Every question resolves to **one parameterized SQL/PGQ query** executed by Oracle
26ai. The database does all composition (joins, `INTERSECT`, `GROUP BY … HAVING`,
`EXCEPT`, `RANK`); the LLM is not in the answer path at all.

```
question text
   │
   ▼  firewall.verdict()            ── adversarial → blocked (Category F)
   ▼  classify()                    ── question → Plan (op + slots + relation steps)
   │      ├─ out_of_graph           → honest refusal (no such data kind)
   │      ├─ insufficient_data      → grounded refusal (entity's real edges)
   │      ├─ describe               → summarize an entity's edges
   │      └─ answerable op          ↓
   ▼  PgqBackend.execute(plan)      ── resolve slots → build ONE SQL → run it
   │      (resolve.py + query_engine/engine.py)
   ▼  trace.build_trace(plan)       ── optional hop-by-hop trajectory (RFP §8.3)
   ▼  finalize.*                    ── SessionResult (answer prose + SUPPORTED_BY)
   ▼  _vendor/finalizer.qa_record / trace_record   ── RFP §8.2 / §8.3 records
```

## 2. Data model — `schemas/primekg-o26.sql`

- **`pk_nodes`** `(node_id PK, node_index, node_type, name, source, code,
  name_norm, name_vec VECTOR(384))`. One row per distinct PrimeKG index;
  `node_id = pk_n_<index>`. `name_norm` is the lowercased/space-collapsed name
  (indexed for resolution). `name_vec` exists but is unpopulated by default.
- **`pk_edges`** `(edge_id PK, source_node_id, target_node_id, predicate,
  display_relation)`. Native predicate + display_relation preserved (never
  collapsed). `edge_id = pk_e_<x>_<y>_<sha1(predicate,display)[:8]>`.
- Indexes on `(predicate, display_relation, source_node_id)` and `(… ,
  target_node_id)`; `pk_nodes(node_type, name_norm)` and `(name_norm)`.
- **Property graph `primekg`** over the two tables (SQL/PGQ `GRAPH_TABLE … MATCH`
  works, verified). The engine mostly uses plain SQL over `pk_edges` (cleaner for
  `INTERSECT`/`GROUP BY`), which is equally "in the database".
- **`pk_load_journal`** — one row per completed load, keyed by source fingerprint
  + relation subset, so a re-run is a no-op.

**Critical fact: PrimeKG is undirected.** Every edge is stored in *both*
directions (symmetric counts). So a hop is always `source_node_id IN S` filtered
by predicate — direction-agnostic. `disease_disease`/`phenotype_phenotype`
parent-child are also bidirectional, so "children of X" = all hierarchy
neighbours (direction does not encode parent vs child; best the data supports).

**Loaded subset (~4.24M edges, 62,030 nodes):** the 13 question-relevant
predicates (drug_drug, protein_protein, disease_phenotype_positive,
disease_protein, drug_effect, pathway_protein, disease_disease, contraindication,
drug_protein, indication, off-label use, phenotype_protein, phenotype_phenotype).
`--relations all` loads the full 8.1M graph (only these 13 matter for the 100 Qs).

## 3. Loader — `load_primekg.py`

Streams `kg.csv` once; accumulates distinct nodes in memory (~62k) and MERGE-es
edges in batches (idempotent — a re-run never double-inserts). Content
fingerprint = sha256(size + head + tail). Flags: `--relations subset|all|<list>`,
`--limit`, `--vectors` (embed names via `all-MiniLM-L6-v2`, optional extra),
`--force`. Column widths were widened after a long drug `code` (144 chars) hit
ORA-12899; values are defensively truncated.

## 4. Entity resolution — `resolve.py`

`Resolver.resolve(name, types)` tries, in order:
1. exact `name_norm` match, type-scoped (with variants: strip/append `(disease)`);
2. exact match, any type;
3. **space-insensitive** match (`REPLACE(name_norm,' ','')`) — fixes `]METHANOL`;
4. guarded **prefix** LIKE, type-scoped;
5. **fuzzy token** — most distinctive token (plural-stripped) `LIKE '%tok%'`,
   type-scoped (e.g. "tourettes ticks" → "Tourette syndrome").
Plus: **radiolabeled-tracer → parent** — a name with an isotope prefix
(`(1,2,6,7-3H)Testosterone`, explicit isotope tokens `3H/14C/35S/…`) resolves to
its parent compound (`Testosterone`), which is where PrimeKG holds the
pharmacology (AR target, SHBG carrier). Stereo descriptors like `(2S)-` are never
stripped.

## 5. Firewall — `firewall.py`

`verdict(question) -> Verdict(malicious, reason)`. Deterministic (no LLM/service),
ported from the reference agent's `deterministic_security_verdict`, plus a rule
for node-embedded fabricated authority. Blocks the 5 adversarial questions
(instruction override, mutation, exfiltration, forced answer, fabricated
authority) with **0 false positives** on the other 95.

## 6. Classifier — `classify.py`

`classify(text) -> Plan`. Order (first match wins):
1. `edge_between` for "what dose of X causes Y" (dose absent, but the causation
   edge is real evidence).
2. `insufficient_data` for genuinely-absent attributes (dosage, approval date,
   price, clinical trial, physician, prognosis) — resolves the entity so the
   refusal is grounded.
3. `out_of_graph` fallback.
4. **Strict benchmark rules** (`_classify_counts`, `_classify_intersections`,
   `_classify_chains`, `_classify_one_hop`) — keyed to the 100 questions'
   phrasings and relation structure. These produce 100/100.
5. **Natural-language layer** (`_classify_natural`) — loose keyword-driven
   fallback for ad-hoc phrasing (side effects of X, what interacts with X,
   treatments for X, describe X, …). Runs LAST so it cannot regress the benchmark.
6. else `insufficient` (honest refusal).

A `Plan` carries: `op`, `slots` (label + expected node types), `steps`
(relation chain for expand/count), `legs` (per-leg chains for set ops),
`final_type`, `exclude_slot`, count/compare params, `member_leg`, `require_edge`,
`missing` (for insufficient_data), `noun`, `single_entity`.

## 7. Query engine — `query_engine/engine.py`

Relation specs in `query_engine/specs.py` (`RelSpec(predicate, displays)`);
`TARGETS` includes all four drug_protein roles. Each method builds **one** SQL
statement (CTE chain), set-collapsed per hop (no path explosion), and returns
answer nodes + real evidence edge ids (capped at 25). A 20s `call_timeout` turns
a pathological query into an honest empty result rather than a hang.

| method | question shape |
|---|---|
| `expand(base, steps)` | one-hop + multi-hop chains (A, C); `require_edge` = "…that have such an edge" |
| `intersect(legA, legB)` | two-set AND (B); `require_edge` supported |
| `intersect_many(legs)` | N-way AND (Q91/94) |
| `difference(legA, legB)` | A NOT B (Q87) |
| `difference_many(legA, minus)` | A minus several sets (Q79) |
| `symmetric_difference` | XOR (Q84) |
| `rank_top(base, 2 steps)` | "share the MOST …" (Q85) |
| `count_threshold(...)` | "AT LEAST/EXACTLY n …" with anchor-pair counting; `member_of` filter (Q90) |
| `count_compare(legA, legB)` | "more X than Y" (Q77) |
| `bridge_count(base, n)` | target→PPI→target bridge counting (Q50/86) |
| `ratio_shared(base)` | "≥ half of targets shared" (Q89) |
| `edge_between(a, b, spec)` | does a specific edge exist (Q73) |
| `node_evidence(node_id)` | an entity's per-relation summary + sample edges (describe / insufficient_data) |
| `walk_hops(base, steps)` | tracing only — per-hop edges + node counts (source IN-list capped 1000) |

## 8. Hop-by-hop trace — `trace.py`

`build_trace(plan, backend) -> (human_lines, rfp_steps, resolved)` walks the plan
level by level via `walk_hops`, producing:
- human-readable lines for `ask`/`-v` (entity lookups, `from --rel--> to (edge_id)`
  per hop, set/aggregate composition);
- RFP §8.3 steps: `entity_lookup`, `edge_traversal` (with `predicate`,
  `from`/`to` examples, set sizes), then a set-op / aggregate / rank step.

The single composed SQL is authoritative for the answer + `SUPPORTED_BY`; the walk
is the illustrative trajectory (hop counts are sampled where sets exceed 1000).

## 9. Finalize + RFP mapping — `finalize.py`, `_vendor/`

`finalize.*` build a reused `SessionResult` (`_vendor/models.py`, verbatim):
- `answered(...)` — entity-list/entity answer + `SUPPORTED_BY` edges; `trace_steps`
  embeds the §8.3 trajectory.
- `insufficient(...)` — grounded refusal (attribute absent) citing the entity's
  real edges as evidence.
- `describe(...)` — positive summary of everything PrimeKG records for an entity.
- `refused(...)` — honest evidence-free refusal (out_of_graph / unresolved).
- `blocked(...)` — firewall block ("Won't do that").

`_vendor/finalizer.py` (copied from `../ai-proposal`, then adapted): writes the
RFP filenames `vendor_<id>_stage1_qa-results_v1.jsonl` (§8.2) and
`…_reasoning-traces_v1.json` (§8.3); `trace_record` emits our clean trajectory
directly (no LLM-path pruning). Citations carry `doc_id="primekg"` + `source_ref`
= the node/edge id (Track A cites via `source_ref`, not page/span).

## 10. Backends — `backends/`

- `pgq.py` (`PgqBackend`) — resolves a Plan's slots and dispatches to the engine.
  The proof path.
- `select_ai.py` (`SelectAiBackend`) — faithful scaffold; refuses on the local
  image because `DBMS_CLOUD_AI` is absent. Deferred to a future Autonomous DB.

## 11. Entrypoints

- `scripts/ask.py "question"` — ad-hoc; prints trajectory + answer; `--json`
  emits the qa-results + reasoning-traces records. Writes nothing.
- `scripts/run-primekg-questions.py` — benchmark/submission harness.
  `--question/--questions N[,N]` (repeatable), `--verbose`, `--input FILE`,
  `--backend pgq|select_ai`, `--out DIR` (writes only when given).
- `scripts/smoke_test.py` — `SELECT 1 FROM dual` (M0 gate).

## 12. Runtime & config

`config.py` loads `.env`; host DSN defaults to `localhost:${ORACLE_PORT}/FREEPDB1`.
`db.py` guards against non-local DSNs unless `VPK_ALLOW_REMOTE=1`. Local Oracle is
`gvenzl/oracle-free:23-slim` (reports "Oracle AI Database 26ai Free 23.26.2.0.0";
VECTOR + SQL/PGQ available). `up.sh --database local` / `down.sh [--purge]`.

## 13. Status

- **Done:** schema + loader (subset), resolver, firewall, classifier (benchmark +
  natural language), full query engine, hop-by-hop tracer, finalize + RFP §8.2/§8.3
  output, ask + harness, tests. **100/100** on the benchmark
  (89 answered-with-evidence, 6 grounded insufficient_data, 5 blocked).
- **Deferred (need approval):** full 8.1M load for a submission run; the Select AI
  comparison; any remote/Autonomous deployment.

## 14. Known limitations / future work

- **Vocabulary:** brand names (Viagra) don't resolve — PrimeKG uses generic names.
  Add a DrugBank/RxNorm synonym table, or populate `name_vec` (`--vectors`) for
  semantic matching.
- **Trace sampling:** wide hops are sampled at 1000 source ids; switch to a temp
  table join if exact per-hop counts are required.
- **`retrieved_context`** in qa-results is currently empty (citations +
  `graph_*_used` carry the provenance); could be populated with `source_ref`
  pointers for maximal §8.2 completeness.
