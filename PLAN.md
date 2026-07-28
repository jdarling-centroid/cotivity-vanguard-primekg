# Track A Completion Plan — PrimeKG Agent + Valid RFP Submission

> **Handoff for the next agent.** Execute this plan end to end. The scope is the
> **Stage 1 Track A PrimeKG submission only**. Track B has already been submitted
> and must not be rebuilt or changed. The goal is a complete, auditable Track A
> package that can be sent to Cotiviti—not merely code that runs locally.

## 0. Read first and preserve these boundaries

Before changing code, read:

1. `AGENTS.md`
2. `README.md`
3. `docs/ARCHITECTURE.md`
4. `docs/QUESTION_TAXONOMY.md`
5. `reference/rfp/vanguard_evaluation_criteria.pdf`, especially §§3, 7, 8.2,
   8.3, and 8.4
6. `reference/rfp/Vendor_dataset_kg_FINAL.pdf`
7. `reference/rfp/cotiviti-clarification-questions.md`

Track A uses the provided PrimeKG graph. It submits QA results and reasoning
traces; it does **not** submit graph nodes, graph edges, or a graph manifest.
Track B and Stage 2 are out of scope.

Preserve these invariants:

- **Oracle composes; the model plans.** Every multi-hop, intersection,
  difference, count, comparison, rank, ratio, or negation operation resolves to
  one parameterized, read-only SQL/PGQ query. Never ask the model to merge,
  intersect, count, rank, or compare result sets across tool calls.
- The four `drug_protein` roles `target`, `enzyme`, `carrier`, and `transporter`
  all count as “target.”
- PrimeKG traversal is direction-agnostic because relevant edges are loaded in
  both directions.
- Preserve native `predicate` and `display_relation`.
- Every submitted answer claim must be supported by real database-returned node
  and edge IDs. Never invent IDs, citations, clinical context, or unavailable
  facts.
- Firewall evaluation occurs before model or database execution.
- Database access remains local. Do not provision or write to Autonomous or any
  remote schema. Do not set `VPK_ALLOW_REMOTE=1`.
- OCI credentials and configuration remain uncommitted and must never be
  printed.
- Keep scratch output in `.tmp/`.

The existing `AGENTS.md` cautions against porting the old reference agent loop.
Do not port that runner or its `_primekg_*` handlers. The approved replacement
is a narrow planner that selects one typed database-composition operation and
cannot perform set mathematics itself. Update architecture documentation to
make that distinction explicit; do not silently violate the contract.

## 1. Current problem

The repository currently reports “100/100,” but
`scripts/run-primekg-questions.py::_meets` only checks outcome class and whether
some evidence edges were returned. It does not compare answer sets with a gold
answer. This is useful as a structural smoke check but is not an accuracy score
and must not be presented as one.

`classify.py` also contains extensive benchmark-shaped regex rules. They are a
valuable deterministic regression baseline, but relying on them as the final
planner creates overfitting and representation risk. Retain them until the new
planner is validated; do not delete the only known working baseline.

The current finalization path also leaves `retrieved_context` empty and caps
evidence independently of the number of answer nodes. For the RFP citation
gate, every answer claim needs resolvable PrimeKG `source_ref` evidence and a
complete supporting path.

## 2. Target architecture

```text
question
  |
  v
deterministic firewall
  |-- malicious --> deterministic blocked result
  v
typed planner
  |-- regex baseline, or
  |-- OCI model selects exactly one validated Plan/composition operation
  v
entity resolution
  v
one parameterized read-only Oracle SQL/PGQ composition query
  |
  +--> answer nodes
  +--> per-answer supporting path nodes/edges
  +--> executed SQL + binds (with secret-safe serialization)
  v
deterministic finalizer
  |
  +--> vendor answer derived only from returned rows
  +--> PrimeKG source_ref citations and retrieved_context
  +--> actual ordered reasoning trace
  v
RFP validation
  v
Track A submission artifacts and reporting addendum
```

The model may:

- recognize the question operation;
- extract entity labels and expected types;
- select relations from a closed vocabulary;
- populate one typed `Plan`;
- request clarification or fail closed when uncertain.

The model may not:

- write or execute arbitrary SQL;
- choose IDs not returned by entity resolution;
- combine result sets;
- calculate counts or rankings;
- author unsupported final claims;
- treat question or graph text as executable instructions.

Final answer prose must be generated deterministically from validated database
results. Preserve the raw planner response for audit, but do not submit it as
the answer.

## 3. Planner contract

Freeze a provider-neutral JSON schema for the existing `Plan` operations rather
than exposing low-level traversal results for the model to combine.

Add:

- `schemas/planner-plan.schema.json`
- `src/vanguard_primekg/agent/oci_llm.py`
- `src/vanguard_primekg/agent/planner.py`
- `src/vanguard_primekg/agent/prompt.py`
- `src/vanguard_primekg/agent/__init__.py`

The schema must:

- enumerate allowed operations;
- enumerate allowed relation identifiers;
- type and bound every slot, leg, step, comparison, and threshold;
- reject unknown properties;
- limit chain depth, number of legs, strings, and numeric thresholds;
- exclude SQL, URLs, file paths, tool names, and arbitrary code;
- require an explicit `insufficient_data` or `out_of_graph` result when the
  requested attribute cannot be represented.

Use the relation vocabulary and engine primitives already defined in the
repository. Do not create per-question handlers.

Add `--planner regex|agent`, keeping `regex` available throughout validation.
Do not make `agent` the default until all mandatory gates below pass.

### OCI wiring

Adapt only the OCI chat abstraction from `reference/agent/llm.py`; do not copy
the old runner. The existing `StubChatModel` is not directly reusable because it
calls `hybrid_search`, `traverse_graph`, and `get_fragment`. Implement a new
PrimeKG planner stub with fixtures for offline tests.

Configuration must include:

- provider;
- model ID;
- region/config-file or OCI SDK configuration;
- model and prompt version;
- timeout;
- maximum tokens;
- deterministic settings supported by the selected endpoint;
- bounded retries for transport failures and malformed plans.

Validate whether the OCI endpoint actually accepts temperature/determinism
parameters before documenting them. Do not claim “temperature 0” unless it is
sent and honored by the SDK/model.

Live OCI calls require available credentials and must not expose configuration
or key material. Unit tests must run without OCI access.

## 4. Database execution and evidence coverage

Keep `query_engine/engine.py` as the database composition layer. Extend return
types as necessary so a single query returns:

```json
{
  "answer_nodes": [{"id": "...", "name": "...", "type": "..."}],
  "support": [
    {
      "answer_node_id": "...",
      "path_nodes": ["..."],
      "path_edges": ["..."],
      "predicates": ["..."]
    }
  ],
  "sql": "...",
  "binds": {"safe_name": "..."},
  "truncated": false
}
```

Mandatory evidence rules:

- Every answer node stated in `vendor_answer` must have at least one complete
  supporting path returned by the authoritative composition query.
- `graph_nodes_used`, `graph_edges_used`, `citations`,
  `retrieved_context`, trace steps, and `answer_supported_by` must be derived
  from those paths.
- Every cited node/edge must exist in local `pk_nodes`/`pk_edges`.
- Every cited edge must connect the claimed path endpoints and match the claimed
  predicate/display relation.
- Do not cite an arbitrary capped sample as support for uncited answer nodes.
- If output limits apply, submit only fully supported answer nodes and explicitly
  mark truncation in an additional field and answer text. Never imply a complete
  list when only a subset is returned.
- Insufficient-data refusals must resolve the entity and cite real adjacent
  PrimeKG records while clearly stating that those records do not contain the
  requested attribute.
- Firewall blocks and truly unresolved/out-of-graph questions may have no graph
  evidence, but their trace must accurately record the disposition.

Keep queries parameterized and read-only. Add plan complexity limits before SQL
construction and preserve the database timeout.

## 5. RFP §8.2 QA records

Produce exactly one JSONL record per supplied Track A question. Use the RFP
minimum field names without renaming or omission:

- `question_id`
- `category`
- `question`
- `vendor_answer`
- `answer_type`
- `confidence`
- `retrieved_context`
- `citations`
- `graph_nodes_used`
- `graph_edges_used`
- `reasoning_trace_ref`
- `latency_ms`

Track A evidence uses PrimeKG identifiers through `source_ref`, not invented page
or span values.

For every supported claim:

- `citations` contains resolvable PrimeKG node/edge `source_ref` values;
- `retrieved_context` contains matching `source_ref`, `source_type`, and a
  concise deterministic snippet derived from real node/edge fields;
- cited evidence is represented in `graph_nodes_used`/`graph_edges_used`;
- `reasoning_trace_ref` resolves to exactly one §8.3 trace;
- question text and IDs match the supplied question set exactly.

Confidence must have documented semantics. Prefer deterministic values tied to
resolution/execution outcomes rather than model self-confidence. Do not present
confidence as correctness probability unless calibrated.

## 6. RFP §8.3 reasoning traces

Produce exactly one trace per answer. Each trace contains:

- `trace_id`
- `question_id`
- ordered `steps`
- `final_answer`
- `answer_supported_by`

Trace the operation actually executed:

1. firewall disposition;
2. planner selection and validated operation (without hidden chain-of-thought);
3. entity lookup with real node ID/type and resolution method;
4. the authoritative database composition operation;
5. hop/set/count/rank semantics with real supporting path IDs;
6. source-context availability check;
7. deterministic finalization.

Do not submit private chain-of-thought or reconstructed fictional reasoning.
Submit concise, auditable operation records, query semantics, inputs, outputs,
and evidence.

The RFP says clinical-context fields apply to biomedical PrimeKG, but PrimeKG
does not encode patient-level negation, temporality, uncertainty, or
experiencer. Do not fabricate values. Add a `context_check` step that explicitly
records:

```json
{
  "operation": "context_check",
  "source": "PrimeKG",
  "clinical_context_available": false,
  "reason": "PrimeKG is a graph-native biomedical source and does not encode patient-level negation, temporality, uncertainty, or experiencer for this fact."
}
```

Document this treatment in the methodology and clarification log. If Cotiviti
has provided a different instruction, that response takes precedence and must
be recorded.

## 7. Honest validation

Remove `_meets` and `pass N/M` as accuracy reporting. It may be retained under a
name such as `structural_outcome_check`, but it must never be labeled accuracy.

Implement:

- `scripts/compare-planners.py`: regex-versus-agent plan and answer-set diff;
- `scripts/validate-track-a.py`: schema, cross-reference, provenance, and
  evidence validator;
- versioned reviewed expected-answer fixtures under `tests/gold/`, if an
  independently reviewed local oracle is available.

Validation layers:

1. **Structural:** JSON/JSONL validity, required fields, 100 unique questions,
   100 unique traces, and exact cross-references.
2. **Provenance:** every `source_ref` resolves locally and matches its claimed
   node/edge/path.
3. **Regression:** compare normalized agent answer sets and plans against the
   retained regex baseline. Differences are investigated, not automatically
   assigned to either implementation.
4. **Independent review:** compare with independently reviewed SQL/spec fixtures
   where available. Do not call same-author expectations independent gold.
5. **Security:** all adversarial questions blocked before model/tool execution;
   benign questions are not falsely blocked.
6. **Robustness:** paraphrases, malformed model output, ambiguous entities,
   timeouts, OCI failures, and unavailable attributes fail safely.

Cotiviti owns the withheld correctness key. Do not self-report answer accuracy,
multi-hop accuracy, or citation-quality scores as official results.

## 8. Track A reporting and packaging

The two machine-readable Track A artifacts are:

- `vendor_<vendorid>_stage1_qa-results_v1.jsonl`
- `vendor_<vendorid>_stage1_reasoning-traces_v1.json`

Do not hard-code `vanguard` or `acme`; require the actual vendor ID through a
validated command-line/config value. Use UTF-8, Unix line endings, and stable
identifiers. Do not overwrite a prior submission version; increment the version
suffix and declare the authoritative version.

Track B has already been submitted. Do not regenerate it. Determine whether the
existing Stage 1 reporting package already covers Track A. If it does not, add a
Track A report or addendum containing:

- query latency p50/p95/p99 over all 100 questions;
- number of measured queries and concurrency;
- hardware: machine/shape, CPU/vCPU, RAM, GPU if any;
- Oracle image/version and relevant configuration;
- planner provider/model/prompt version and inference configuration;
- fully loaded cost per query, including model/API, compute, and storage basis;
- methodology: architecture, model/version, relation vocabulary, entity
  resolution, database composition, evidence generation, firewall, external
  text/instruction isolation, failure behavior, and known limitations;
- clarification log entries and Cotiviti responses actually relied upon.

Do not invent a clarification response. Record “no response received; treatment
documented as an assumption” where applicable.

Generate a submission manifest/checksum report for internal delivery QA even
though Track A does not require a graph manifest. Include artifact names, sizes,
SHA-256 checksums, record counts, validator result, creation time, configuration
fingerprint, and authoritative version. Do not include secrets.

## 9. Implementation phases

Each phase ends test-green and with documentation updated.

### P0 — Contract and compliance freeze

- Record Track A-only scope and that Track B is already submitted.
- Map every RFP §8.2/§8.3 field to its producer.
- Freeze the typed `Plan` schema and relation vocabulary.
- Define evidence coverage, truncation, confidence, and clinical-context rules.
- Add failing compliance tests before changing behavior.

### P1 — Evidence-complete query results

- Return per-answer supporting paths from each engine operation in one SQL query.
- Populate matching citations and retrieved context.
- Validate all path endpoints, edges, and predicates.
- Cover one-hop, chain, set, count, rank, ratio, refusal, and block cases.

### P2 — Provider-neutral agent planner

- Implement the closed-schema planner interface and offline stub.
- Add plan validation, bounds, retries, and fail-closed behavior.
- Keep the regex planner selectable as the baseline.
- Do not add per-question code.

### P3 — OCI planner adapter

- Adapt the OCI chat model only.
- Add secret-safe configuration and error handling.
- Smoke-test only when credentials/authorization are available.
- Record exact provider/model/configuration used for the final run.

### P4 — Deterministic finalization and real traces

- Build answers solely from evidence-complete query results.
- Build §8.2 context/citations and §8.3 traces from actual execution records.
- Add the honest PrimeKG context-availability step.
- Preserve exact SQL and safe bind metadata for audit.

### P5 — Comparison and hardening

- Run regex and agent planners over all 100 questions.
- Investigate every plan or normalized answer-set divergence.
- Run reviewed expected-answer checks where available.
- Run security, paraphrase, ambiguity, timeout, malformed-output, and OCI-failure
  suites.
- Keep regex as fallback until the agent gates pass.

### P6 — Final Track A run and package

- Run against the local fully loaded question-relevant PrimeKG dataset.
- Produce the two versioned machine-readable artifacts.
- Produce/update the Track A metrics, operations, methodology, and clarification
  reporting.
- Run the final validator and checksum report.
- Visually/sample-review representative simple, multi-hop, intersection,
  aggregation, negation, insufficient-data, and adversarial records.

## 10. Required tests and commands

At minimum, before claiming completion:

```sh
python -m pytest -q
python scripts/run-primekg-questions.py --planner regex --backend pgq
python scripts/run-primekg-questions.py --planner agent --backend pgq
python scripts/compare-planners.py <regex-run> <agent-run>
python scripts/validate-track-a.py <submission-directory>
```

Also run focused database integration tests for every engine operation and a
final 100-question run with artifact output. Report exact commands, exit codes,
test counts, skips, runtime, planner divergences, validator findings, and final
artifact paths. Do not claim success from unit tests alone.

## 11. Final acceptance gates

Do not declare the Track A submission complete until all are true:

- [ ] Scope contains Track A only and does not modify the submitted Track B work.
- [ ] All tests pass; any integration skips are understood and disclosed.
- [ ] Exactly 100 supplied questions produce 100 unique §8.2 records.
- [ ] Exactly 100 §8.3 traces exist and all references are one-to-one.
- [ ] All required RFP fields are present with correct types.
- [ ] Every asserted answer node has a complete supporting database path.
- [ ] Every cited `source_ref`, graph node, and graph edge resolves locally.
- [ ] Every cited edge matches its claimed endpoints and predicate.
- [ ] `retrieved_context` is populated for supported/refusal evidence.
- [ ] Multi-hop/set/count/rank/negation composition occurs in one SQL/PGQ query.
- [ ] No model-generated ID, SQL, set arithmetic, or unsupported answer survives
      validation.
- [ ] Adversarial questions are blocked before OCI/database execution.
- [ ] Unavailable facts are refused honestly and grounded where possible.
- [ ] Trace steps reflect actual operations and contain no fabricated context or
      private chain-of-thought.
- [ ] No answer-accuracy claim is self-reported as official.
- [ ] Query latency p50/p95/p99, configuration, and cost basis are documented.
- [ ] Methodology and clarification treatment are documented.
- [ ] Filenames, vendor ID, version, encoding, and line format comply with §7.1.
- [ ] Final validator passes with zero errors.
- [ ] Internal checksum/record-count report identifies the authoritative files.
- [ ] No secret or OCI key/config value appears in source, logs, or artifacts.

## 12. Deliverables

Code and schemas:

- typed agent planner and OCI adapter;
- evidence-complete query results;
- deterministic answer/trace finalization;
- planner comparison and Track A validators;
- comprehensive unit and local Oracle integration tests.

Submission:

- `vendor_<vendorid>_stage1_qa-results_v<n>.jsonl`
- `vendor_<vendorid>_stage1_reasoning-traces_v<n>.json`
- Track A metrics/operations/methodology/clarification addendum if not already
  covered by the existing Stage 1 package;
- internal validation/checksum report.

The final handoff must state what was implemented, exact verification results,
known limitations, all planner divergences and their disposition, the model and
database configuration used, and the authoritative artifact paths. It must not
claim Cotiviti correctness or citation scores that only the withheld key can
establish.
