# Agent operating contract — PrimeKG Track A

Read `README.md`, `docs/ARCHITECTURE.md`, `docs/TRACK_A_COMPLIANCE.md`, and the
RFP documents under `reference/rfp/` before changing behavior.

## Scope boundary

This repository is for **Stage 1 Track A PrimeKG only**. Track B has already
been submitted and must not be rebuilt or modified. Track A submits Q&A results
and reasoning traces; it does not submit graph nodes, graph edges, or a graph
manifest.

## Non-negotiable architecture

- **Oracle composes; the model plans.** Each multi-hop, intersection,
  difference, count, comparison, rank, ratio, or negation request executes as
  one parameterized, read-only database composition query.
- The model selects one closed-schema `Plan`. It may not write SQL, choose graph
  IDs, combine result sets, calculate counts/ranks, or author final claims.
- Keep the regex classifier as a selectable deterministic baseline until the
  agent planner passes every mandatory gate.
- Do not port `reference/agent/runner.py` or its `_primekg_*` handlers. That
  orchestration pattern is a cautionary reference, not the approved agent.
- The four `drug_protein` roles `target`, `enzyme`, `carrier`, and `transporter`
  all count as target.
- PrimeKG traversal is direction-agnostic because relevant edges are loaded in
  both directions.
- Preserve native `predicate` and `display_relation` values.

## Evidence and finalization

- Every asserted answer node must have a complete support path returned by the
  authoritative composition query.
- Derive `citations`, `retrieved_context`, `graph_nodes_used`,
  `graph_edges_used`, trace paths, and `answer_supported_by` from returned rows.
- Every cited source reference must resolve locally; each edge must match the
  claimed endpoints, predicate, and display relation.
- Do not support an uncited answer with an arbitrary evidence sample.
- When limited, emit only fully supported answer nodes and disclose truncation.
- Final prose is deterministic. Preserve raw planner output only in internal
  audit material, never as the submitted answer.
- Do not fabricate patient-level clinical context. Record PrimeKG context
  availability explicitly.

## Security and operations

- Evaluate the deterministic firewall before planner or database execution.
- Keep database access local. Do not set `VPK_ALLOW_REMOTE=1`.
- Never print, commit, or package OCI configuration, key material, wallets, or
  credentials.
- Keep scratch output in `.tmp/`.
- Do not overwrite an existing submission version.

## Honest validation

- Never call the structural outcome harness an accuracy score.
- Cotiviti owns answer correctness, multi-hop accuracy, and citation-quality
  scoring against the withheld key.
- Planner differences require review; neither implementation is presumed gold.
- Same-author expected values are regression fixtures, not independent truth.

## Definition of done

Do not declare Track A complete until the final local database run produces
exactly 100 QA records and 100 one-to-one traces, all integration tests run,
every planner divergence is dispositioned, `validate-track-a.py --verify-db`
returns zero errors, metrics/configuration/cost basis are documented, the actual
vendor ID/version are used, and checksum reporting identifies the authoritative
files. Disclose every skip or unavailable external dependency.
