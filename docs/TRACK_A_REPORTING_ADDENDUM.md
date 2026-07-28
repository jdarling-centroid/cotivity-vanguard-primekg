# Stage 1 Track A reporting addendum

> Complete this document from the authoritative final run. Do not replace
> unmeasured values with estimates presented as measurements.

## Submission identity

- Scope: Stage 1 Track A PrimeKG only
- Track B modified: No
- Vendor ID: `<actual vendor ID>`
- Authoritative artifact version: `<n>`
- Run UTC timestamp: `<from run-manifest.json>`
- QA record count: `<must be 100>`
- Reasoning trace count: `<must be 100>`
- Final validator result: `<must be pass with zero errors and DB verification>`

## Query operations

| Metric | Final measured value |
|---|---:|
| Questions measured | `<100>` |
| Concurrency | `<run value>` |
| Query latency p50 | `<run-manifest value> ms` |
| Query latency p95 | `<run-manifest value> ms` |
| Query latency p99 | `<run-manifest value> ms` |
| Mean latency | `<run-manifest value> ms` |

Latency covers the full per-question path measured by the harness: firewall,
planning, entity resolution, authoritative database query, and deterministic
finalization. Report any model warm-up, database cache warm-up, retries, or
excluded failed attempts separately.

## Hardware and database configuration

- Host/machine or cloud shape: `<record exact value>`
- CPU/vCPU: `<record exact value>`
- RAM: `<record exact value>`
- GPU: `<none or exact model/count>`
- Operating system/container host: `<record exact value>`
- Oracle image and exact database version: `<record exact value>`
- Database backend: `pgq`
- Database call timeout: `20,000 ms`, unless changed and documented
- PrimeKG load scope/record counts/fingerprint: `<record from load manifest>`
- Database location: local only

## Planner configuration

### Regex regression run

- Planner: deterministic regex baseline
- Version: source/configuration fingerprint `<record>`
- Purpose: structural and regression comparison only

### Agent authoritative candidate

- Provider: OCI
- Model ID/version: `<exact approved endpoint/model>`
- Prompt version: `primekg-planner-1.0`, unless incremented
- Maximum tokens: `<exact final value>`
- Timeout/retry policy: `<exact final values>`
- Temperature or determinism parameter: `<record only if actually accepted and sent>`
- Planner response schema: `planner-plan-1.0`
- Agent/regex divergence count: `<from comparison report>`
- Disposition summary: `<reviewed result for every divergence>`

## Fully loaded cost per query

Report the actual basis used for the final run:

| Component | Cost basis | Run cost |
|---|---|---:|
| OCI model/API | `<token/request pricing and measured usage>` | `<USD>` |
| Compute | `<shape hourly rate × measured duration>` | `<USD>` |
| Storage/database | `<allocated/storage basis>` | `<USD>` |
| Other metered services | `<basis or none>` | `<USD>` |
| Total |  | `<USD>` |
| Fully loaded cost per query | `total / 100` | `<USD>` |

Do not report a cost value until the final provider, model usage, compute shape,
and duration are known. State any excluded labor or one-time engineering costs.

## Methodology summary

1. The deterministic firewall evaluates the question before any model or
   database execution.
2. The typed planner recognizes the operation, extracts entity labels/types,
   and selects relations from a closed vocabulary. It cannot write SQL or IDs.
3. Local entity resolution returns real PrimeKG node IDs.
4. Oracle composes traversal, set, count, comparison, rank, ratio, and negation
   semantics in one parameterized read-only query.
5. The same query returns answer nodes and answer-scoped supporting paths.
6. Deterministic code creates answer prose, source_ref citations, retrieved
   context, and operation traces only from returned rows.
7. Question/graph text is isolated as data and is never treated as executable
   instruction content.
8. The final validator checks structure, cross-references, support paths,
   read-only composition, firewall order, and local database provenance.

## Known limitations

- Cotiviti's withheld key is required to score correctness, multi-hop accuracy,
  and citation quality. No official value is self-reported.
- Entity names are limited to PrimeKG and configured resolver vocabularies.
- PrimeKG does not provide patient-level clinical context for graph facts.
- Aggregate/rank/ratio/negation qualification is established by the recorded
  authoritative SQL plus returned witness paths; representative records require
  final human review.
- Any unavailable OCI setting, timeout, or transport failure fails closed.

## Clarification treatment

- PrimeKG provenance uses node/edge/record `source_ref` values rather than page
  and span, as stated in the RFP.
- No Cotiviti response was found for the separate question about preferred
  source_ref syntax; native local IDs are used.
- No Cotiviti response was found for how to represent absent patient-level
  clinical-context attributes in PrimeKG traces. The explicit unavailable
  context check is a documented assumption.
