# Track A compliance and acceptance mapping

## Scope freeze

- Stage 1 Track A PrimeKG only.
- Track B is already submitted and is not regenerated or modified.
- Track A submits QA results and reasoning traces, not graph files.
- Local database only; no Autonomous or remote schema writes.

## RFP §8.2 field producers

| Required field | Producer | Validation |
|---|---|---|
| `question_id` | deterministic `Q-KG-<number>` mapping | unique; exact supplied set |
| `category` | validated plan operation/disposition | required string |
| `question` | supplied YAML question text | exact byte-for-text comparison |
| `vendor_answer` | deterministic finalizer from returned rows | non-empty; equals trace final answer |
| `answer_type` | validated plan | required string |
| `confidence` | deterministic execution disposition | numeric `[0,1]`; basis in added field |
| `retrieved_context` | returned path/adjacent evidence | source_ref/type/snippet; matches citations |
| `citations` | returned path/adjacent evidence | PrimeKG source_ref; no page/span invention |
| `graph_nodes_used` | ordered support paths/adjacent evidence | cited; optionally resolved against `pk_nodes` |
| `graph_edges_used` | ordered support paths/adjacent evidence | cited; endpoints/predicate/display verified |
| `reasoning_trace_ref` | `T-` form of question ID | exactly one trace |
| `latency_ms` | full per-question wall-clock execution | non-negative integer |

Added fields:

- `truncated`: true only when the qualified output exceeded the retained,
  fully-supported answer limit;
- `confidence_basis`: documents deterministic confidence semantics.

## RFP §8.3 trace producers

| Trace content | Producer |
|---|---|
| firewall disposition | deterministic firewall, before planner/database |
| planner selection | planner audit with provider/model/prompt/validated plan |
| entity lookup | local resolver result and method |
| composition | actual SQL, safe binds, query count, answer count, truncation |
| support semantics | database-returned ordered paths and operation semantics |
| context availability | explicit PrimeKG context check; no fabricated values |
| final answer | same deterministic answer as §8.2 |
| `answer_supported_by` | returned evidence references |

Traces contain operation records and evidence, not private chain-of-thought.

## Confidence semantics

Confidence is not an answer-correctness probability.

- `1.0`: deterministic allowed outcome with returned support, grounded
  unavailable-attribute evidence, or deterministic firewall disposition.
- `0.5`: deterministic empty result without an execution error.
- `0.0`: execution error, unresolved/out-of-graph disposition, or planner
  fail-closed disposition.

The exact basis is written to `confidence_basis`. These values are not
calibrated against Cotiviti's withheld answer key.

## Evidence coverage and truncation

- Every asserted answer node has at least one complete returned support path.
- All path nodes/edges are represented in QA graph fields and citations.
- Every citation has matching retrieved context.
- Every cited edge must resolve locally and match path endpoints, predicate,
  and display relation.
- Set/count/rank/ratio/negation qualification is performed by the single
  authoritative SQL query.
- When the answer cap applies, unsupported or overflow nodes are omitted and the
  answer explicitly says the result is truncated.

## PrimeKG clinical-context treatment

PrimeKG is biomedical and graph-native, but the supplied graph relationships do
not encode patient-level negation, temporality, uncertainty, or experiencer.
Each applicable trace records:

```json
{
  "operation": "context_check",
  "source": "PrimeKG",
  "clinical_context_available": false,
  "reason": "PrimeKG is a graph-native biomedical source and does not encode patient-level negation, temporality, uncertainty, or experiencer for this fact."
}
```

No Cotiviti response overriding this treatment is present in the repository.
The clarification log therefore records it as a documented assumption.

## Validation gates

A deliverable is authoritative only after all are true:

- exactly 100 supplied questions and 100 unique one-to-one traces;
- all required fields and exact question text;
- complete support for every asserted answer node;
- local database verification for every cited node/edge and path claim;
- one-query composition for all compound operations;
- no model-authored IDs, SQL, set arithmetic, or claims;
- adversarial inputs blocked before planner/database execution;
- grounded unavailable-attribute handling;
- zero validator errors;
- planner divergences reviewed and dispositioned;
- p50/p95/p99, hardware, model, database configuration, concurrency, and cost
  basis reported;
- actual vendor ID/version used and prior versions preserved;
- no secret or OCI key/config value in code, logs, or artifacts.

Structural harness outcomes, regex agreement, and same-author fixtures are not
reported as official answer accuracy.
