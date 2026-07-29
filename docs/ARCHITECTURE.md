# Stage 1 architecture

Track A and Track B share the local-only Oracle, security, stable-ID,
provenance, and no-overwrite requirements, but use isolated graph schemas and
submission directories. Sections 1-10 below describe Track A.

## 1. End-to-end flow

```text
question
  |
  v
deterministic firewall
  |-- malicious --> deterministic blocked record; no model/database call
  v
typed planner
  |-- regex baseline
  |-- OCI model selects exactly one validated closed-schema Plan
  v
entity resolution to local PrimeKG IDs
  v
one parameterized read-only Oracle SQL/PGQ composition query
  |-- answer nodes
  |-- per-answer ordered support paths
  |-- native predicates and display relations
  |-- executed SQL and safe bind metadata
  v
deterministic finalizer
  |-- vendor answer from returned rows only
  |-- source_ref citations and retrieved_context
  |-- actual operation trace; no private chain-of-thought
  v
Track A validator and internal checksum report
```

The model performs semantic parsing only. It never receives a tool loop that
allows independent retrieval calls to be combined. Set mathematics and
aggregation remain inside Oracle.

## 2. Planner contract

`schemas/planner-plan.schema.json` is the provider-neutral contract. It:

- enumerates all operations and relation identifiers;
- types and bounds slots, legs, steps, comparison operators, and thresholds;
- rejects unknown properties;
- limits strings, chain depth, and leg count;
- excludes SQL-like labels, URLs, and file paths;
- supports explicit `insufficient_data`, `out_of_graph`, and fail-closed
  `insufficient` outcomes.

`src/vanguard_primekg/agent/planner.py` provides:

- `RegexPlanner`: retained regression baseline around `classify.py`;
- `AgentPlanner`: validates model JSON, applies semantic bounds, retries bounded
  transport/malformed responses, and fails closed;
- `StubPlannerModel`: offline fixtures for tests;
- `plan_to_payload`: stable plan serialization for audit and comparison.

`agent/oci_llm.py` adapts only OCI chat completion. Temperature is sent only
when explicitly configured; documentation must not claim deterministic
settings the selected endpoint does not accept or honor.

## 3. Relation vocabulary

The model selects stable identifiers from `query_engine/specs.py`, not raw graph
predicates. The mapping preserves PrimeKG predicates and display relations.
`targets` includes all four `drug_protein` display roles: `target`, `enzyme`,
`carrier`, and `transporter`.

## 4. Entity resolution

The planner supplies labels and expected node types. `Resolver` maps them to
local `pk_nodes` records through deterministic normalization and supported
fallbacks. Only returned IDs enter the query. Resolution method and score are
recorded in the trace.

An unresolved entity fails safely and produces no invented ID. An unavailable
attribute such as dosage resolves the entity, queries real adjacent PrimeKG
records once, cites those records, and states that the requested attribute is
not represented.

## 5. Oracle composition

`query_engine/engine.py` implements reusable operations:

- expansion and direct-edge lookup;
- two-way and N-way intersection;
- difference and multi-difference;
- count thresholds and count comparison;
- symmetric difference;
- rank-top;
- shared-target ratio;
- target/PPI/target bridge thresholds;
- adjacent evidence for describe/refusal records.

Every executable answer operation returns a `QueryResult` containing answer
nodes, one or more `SupportPath` records per retained answer, SQL, safe binds,
truncation state, and any execution error. A support path contains ordered node
IDs, ordered edge IDs, native predicates, native display relations, and query
semantics. Oracle constructs answer sets and support rows in the same statement.

The engine caps returned answers. It drops any answer node without returned
support and marks truncation when the qualified set exceeds the output limit.
The answer text then states that the list is truncated.

## 6. Deterministic finalization

`finalize.py` never calls a model. For supported results it:

1. retains only answer nodes represented by support paths;
2. creates answer prose from returned names;
3. creates PrimeKG `source_ref` citations and matching retrieved context;
4. records all path graph nodes and edges;
5. records the authoritative query and secret-safe binds;
6. emits ordered support-path steps;
7. adds the PrimeKG clinical-context availability statement;
8. records deterministic finalization.

Confidence is a deterministic execution disposition, not a calibrated
probability of correctness. `confidence_basis` documents the semantics.

## 7. Reasoning traces

Traces are auditable execution records, not hidden chain-of-thought. A normal
trace includes:

1. firewall disposition;
2. planner/provider/model/prompt version and validated operation;
3. entity lookup IDs/types/methods;
4. one authoritative read-only composition query and binds;
5. ordered support path(s) and set/count/rank semantics;
6. `context_check` stating that PrimeKG does not encode patient-level negation,
   temporality, uncertainty, or experiencer for the fact;
7. deterministic finalization.

A firewall trace proves that neither planner nor database executed. A truly
unresolved/out-of-graph disposition may have no graph evidence.

## 8. Submission serialization

`_vendor/finalizer.py` writes exact, versioned Track A filenames using a
validated caller-provided vendor ID. Files open in exclusive-create mode and use
UTF-8 with Unix line endings. Each QA record references exactly one trace.

No graph artifacts are produced for Track A. `run-manifest.json`, review files,
`validation-report.json`, and `checksum-report.json` are internal QA/supporting
report material.

## 9. Validation layers

`scripts/validate-track-a.py` checks:

- filename/vendor/version agreement;
- JSON/JSONL shape, required fields, counts, unique IDs, exact question text,
  and one-to-one trace references;
- citation/retrieved-context agreement;
- full support-path lengths and representation in graph fields;
- read-only query evidence and one-query semantics;
- firewall pre-execution disposition;
- clinical-context availability step;
- optional local database existence and edge endpoint/predicate/display checks;
- key-material leakage;
- checksums and configuration fingerprint.

`scripts/compare-planners.py` compares normalized plans, dispositions,
answer-node sets, and truncation. Its output is a regression review, never an
accuracy score.

## 10. Runtime boundary and known limits

The final run must use a local, fully loaded Oracle database. Remote execution is
blocked unless explicitly overridden, which is prohibited for this Track A
handoff. The repository can run offline unit tests without the Oracle driver,
but that mode cannot establish database provenance or submission readiness.

The query layer emits a qualifying support path per answer while aggregate,
rank, ratio, and negation qualification is established by the authoritative SQL
itself. The final review should sample those operations and verify that the SQL
semantics and witness paths jointly support the submitted claim.

## 11. Track B extension

Track B builds a graph from the public MultiHopRAG corpus. The deterministic
builder emits the RFP §8.1 nodes, edges, and manifest triplet. Node types include
Document, TextBlock, Source, Person, Category, and cross-document Entity;
relations include document metadata, containment, and entity mentions.

All graph elements carry source `doc_id` provenance. Text blocks and entity
mentions also carry character spans. Clinical-context fields are omitted
because MultiHopRAG is non-clinical.

The graph loads idempotently into separate `mh_*` Oracle tables. Retrieval uses
one parameterized, read-only Oracle query to rank TextBlock nodes and returns
the Document-to-TextBlock graph edge with each passage. Track B answers must
cite only returned passages and record ordered graph/evidence steps.
