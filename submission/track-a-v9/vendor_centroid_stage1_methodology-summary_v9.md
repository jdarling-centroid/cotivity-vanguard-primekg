# Vanguard Stage 1 Track A methodology summary

## Scope

Track A loads the provided PrimeKG graph into local Oracle and answers the 100
issued questions. It does not construct or submit a replacement graph.

## Architecture

1. A deterministic firewall runs before model or database access.
2. OCI Generative AI `xai.grok-4.3` maps an untrusted question to the
   closed `planner-plan-1.0` schema.
3. Deterministic entity resolution maps labels to local PrimeKG node IDs.
4. Oracle executes one parameterized, read-only SQL/PGQ composition statement.
5. Deterministic finalization emits the answer, citations, graph references,
   and ordered execution trace only from database-returned records.

The model cannot emit or execute SQL, access graph tools, select graph IDs,
perform set arithmetic across retrieval calls, or write the final answer.
Multi-hop traversal, intersection, difference, aggregation, ranking, ratio,
and negation are composed in Oracle.

## Graph fidelity and provenance

PrimeKG native predicates and display relations are preserved. Each
non-self-loop edge is loaded in both directions because the evaluation treats
PrimeKG traversal as direction-agnostic. Drug-to-protein targeting includes the
target, enzyme, carrier, and transporter roles.

Every stated answer node has a database-returned support path containing real
PrimeKG node IDs, edge IDs, predicates, display relations, and the executed
parameterized query. Unsupported facts fail closed.

## Model and versions

- Planner provider: oci
- Planner model: xai.grok-4.3
- Requested temperature: not sent
- Prompt version: primekg-planner-1.5
- Planner schema: planner-plan-1.0
- Oracle client-reported database version: 23.26.2.0.0
- PrimeKG load format: bidirectional-v2
- PrimeKG dataset fingerprint: `957238769f95a761b1aaa082d2ae14b6`

## Isolation of untrusted text

Track A is graph-native and does not ingest external document instructions.
Question and node text are nevertheless treated as untrusted data. Questions
are JSON-serialized into the planner prompt, planner output must validate
against a closed schema, and the firewall precedes both planner and database
execution. The evaluation path never executes instructions contained in
question or graph text.

## Known limitations

PrimeKG does not encode patient-level negation, temporality, uncertainty, or
experiencer. The traces state this limitation rather than inventing clinical
context. Cotiviti retains the correctness key, so no answer-accuracy claim is
self-reported.
