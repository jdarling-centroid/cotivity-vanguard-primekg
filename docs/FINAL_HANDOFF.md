# Track A implementation handoff

**Date:** 2026-07-28  
**Scope:** Cotiviti Stage 1 Track A PrimeKG only  
**Track B:** Not rebuilt or modified  
**Completion status:** **Implementation package complete; authoritative Track A submission not produced**

## Executive status

The repository now contains the closed-schema planner, evidence-complete query result contract, deterministic answer and trace finalization, versioned submission writer, planner comparison utility, Track A validator, compliance documentation, and offline test coverage required to prepare a valid Track A run.

The final submission acceptance gates cannot be closed in this execution environment because it does not contain a runnable local Oracle instance, the PrimeKG `kg.csv` dataset, the `python-oracledb` driver, OCI credentials and an approved model ID, or the actual Cotiviti vendor ID. No authoritative 100-question artifacts were generated, and no Cotiviti correctness, multi-hop accuracy, or citation-quality score is claimed.

## Implemented

### Closed planner contract

- Added `schemas/planner-plan.schema.json` with a closed operation and relation vocabulary, typed slots and legs, bounded chain depth and thresholds, unknown-property rejection, and rejection of SQL/URL/file-path-like entity labels.
- Added provider-neutral planner modules under `src/vanguard_primekg/agent/`.
- Retained the deterministic regex planner as a selectable regression baseline.
- Added an OCI chat adapter that exposes only text completion to the planner. It does not expose SQL, graph tools, or the old reference runner.
- Added bounded planner settings: timeout 1–300 seconds, maximum tokens 64–4096, retries 0–3, and optional OCI temperature 0–1.
- Added bounded retry and fail-closed behavior for transport errors, invalid JSON, and schema-invalid plans.
- Serialized the user question as untrusted JSON data rather than executable prompt instructions.

### Oracle composition and evidence

- Extended `QueryResult` with answer nodes, answer-scoped `SupportPath` records, exact SQL, safe bind metadata, truncation, and execution errors.
- Updated every supported composition operation to return answer nodes and complete witness paths from the same authoritative read-only SQL statement:
  - expansion and direct-edge lookup;
  - intersection and multi-leg intersection;
  - difference and multi-leg difference;
  - symmetric difference;
  - count threshold and count comparison;
  - bridge count;
  - ratio qualification;
  - ranking.
- Preserved native PrimeKG `predicate` and `display_relation` values in returned evidence.
- Removed sampled traversal evidence from production finalization.
- Enforced fail-closed finalization: a returned node is not stated in the answer unless it has complete returned support.
- Retained resolved input-node provenance for valid empty result sets while recording the authoritative SQL that established the empty set.
- Added one-query adjacent evidence for describe and unavailable-attribute responses.

### Bidirectional PrimeKG load

- Updated the loader to materialize each non-self-loop PrimeKG fact in both directions using deterministic edge IDs.
- Preserved the original predicate and display relation on both directed records.
- Added load format marker `bidirectional-v2` to the load-journal key. A prior one-direction load therefore cannot be mistaken for the final required load.
- Removed the broken absolute-path dataset symlink and replaced it with a dataset placement README.

### Deterministic answer and trace generation

- Answers, citations, retrieved context, graph references, support references, and trace steps are generated only from validated planner output, entity resolution, and database-returned records.
- Added concise, ordered operation traces for:
  1. firewall disposition;
  2. planner selection and validated operation;
  3. entity resolution;
  4. authoritative SQL composition and safe binds;
  5. returned support paths and operation semantics;
  6. PrimeKG context availability;
  7. deterministic finalization.
- Added the required honest PrimeKG clinical-context declaration without fabricating patient-level negation, temporality, uncertainty, or experiencer.
- Firewall blocks record that planner and database execution did not occur.
- Confidence is documented as deterministic execution/disposition confidence, not correctness probability.

### Submission and validation tooling

- Added validated vendor-ID and versioned file naming.
- Submission files are created exclusively and cannot overwrite a prior version.
- Added `scripts/compare-planners.py` to compare validated plans, dispositions, normalized answer-node sets, and truncation. Divergences are review items, not accuracy judgments.
- Added `scripts/validate-track-a.py` for:
  - required §8.2 and §8.3 fields;
  - exact question IDs and text;
  - one-to-one QA/trace references;
  - citation/context consistency;
  - complete path structure;
  - read-only single-query composition records;
  - firewall ordering;
  - secret-safe binds;
  - optional local database provenance validation of nodes, edges, endpoints, predicates, and display relations;
  - validation and SHA-256 checksum reports.
- Renamed the old “pass” concept to `structural_outcome_check` and explicitly labels it as not accuracy.
- Added run manifest fields for latency percentiles, concurrency, host hardware, planner configuration, database snapshot, artifact hashes, and cost-basis status.

### Documentation and hygiene

- Updated `README.md`, `AGENTS.md`, and `docs/ARCHITECTURE.md` to define the narrow typed planner rather than the old tool-calling runner.
- Added `docs/TRACK_A_COMPLIANCE.md` and `docs/TRACK_A_REPORTING_ADDENDUM.md`.
- Updated the clarification log without inventing a Cotiviti response.
- Moved legacy generated artifacts, prior hardcoded-vendor outputs, local `.env`, and transcript files containing old local credentials into excluded `.tmp/` scratch storage.
- Removed hardcoded local database passwords from runtime defaults and Docker Compose; `.env` values are now explicitly required.

## Verification results

### Offline test suite

Command:

```sh
PYTHONPATH=src python -m pytest -q -ra
```

Result:

- Exit code: `0`
- Collected: `69`
- Passed: `51`
- Skipped: `18`
- Failed: `0`
- Runtime: `4.68 seconds` wall clock
- All 18 skips are local Oracle integration cases and explicitly report `local Oracle not available`.

Test coverage includes schema validation, all benign regex-plan round trips through the closed planner schema, malformed planner output, OCI adapter request behavior, bounded settings, firewall-before-planner/database order, all composition SQL contracts through a fake Oracle cursor, evidence-complete finalization, empty-answer provenance, bidirectional loading, version/no-overwrite behavior, planner comparison, and Track A artifact validation.

### Compilation

Command:

```sh
python -m compileall -q src scripts tests
```

Result: exit code `0`.

### Offline validator fixture

Command:

```sh
PYTHONPATH=src python scripts/validate-track-a.py .tmp/fixture-submission --allow-partial
```

Result:

- Exit code: `0`
- QA records: `1`
- Traces: `1`
- Errors: `0`
- Warnings: `1` (`local database provenance verification was not requested`)

This is a structural fixture only. It is not a Track A submission and does not establish database provenance or correctness.

### Planner comparison fixture

Command:

```sh
PYTHONPATH=src python scripts/compare-planners.py \
  .tmp/compare-fixture/regex .tmp/compare-fixture/agent
```

Result:

- Exit code: `0`
- Questions compared: `1`
- Exact matches: `1`
- Divergences: `0`

This validates comparison behavior only. No real 100-question regex-versus-agent comparison was possible.

## Required commands that could not complete

### Regex 100-question run

```sh
PYTHONPATH=src python scripts/run-primekg-questions.py --planner regex --backend pgq
```

- Exit code: `1`
- Blocking error: `python-oracledb is not installed; database operations are unavailable`.

### Agent 100-question run

```sh
PYTHONPATH=src python scripts/run-primekg-questions.py --planner agent --backend pgq
```

- Exit code: `1`
- Blocking error: `agent planner requires --model-id or VPK_PLANNER_MODEL_ID`.
- OCI credentials and an approved final model were also not available.

### Local database startup

- `docker` command discovery exit code: `1`.
- The PrimeKG source dataset was not present.
- Therefore the bidirectional loader, Oracle version/count snapshot, real integration tests, final 100-question runs, real planner comparison, and `validate-track-a.py --verify-db` could not run.

## Planner divergences

No real planner divergences were measured because neither authoritative 100-question database-backed run could execute. Divergence count is therefore **not available**, not zero. The final delivery process must investigate and disposition every real plan, answer-set, disposition, or truncation divergence before selecting the agent run as authoritative.

## Final model and database configuration

### Model

- Live provider/model used: **none**
- OCI live calls made: **none**
- Offline adapters used: deterministic regex planner, fixture planner model, and fake OCI SDK objects in unit tests
- Prompt schema/version prepared: `planner-plan-1.0` / `primekg-planner-1.0`
- Temperature claim: **none**; the adapter sends temperature only when explicitly configured and the final run must document whether the selected endpoint accepted it

### Database

- Live Oracle used: **none**
- Database version/image measured: **not available**
- PrimeKG node/edge counts: **not available**
- Database provenance validation: **not performed**
- Intended configuration: local Oracle only, PGQ backend, 20,000 ms call timeout, bidirectional-v2 directed edge load

## Acceptance-gate disposition

The following implementation-level gates are covered by code and offline tests:

- Track A-only architecture and no Track B regeneration.
- Closed typed planner; no model SQL, graph IDs, set arithmetic, or final claims.
- Firewall before planner/database.
- Parameterized read-only composition contracts.
- Answer-scoped support paths and deterministic evidence finalization.
- Versioned no-overwrite output.
- Structural, cross-reference, evidence, security, and optional DB provenance validation.
- Honest non-accuracy reporting and clinical-context treatment.

The following final-run gates remain open:

- all Oracle integration tests passing against the final loaded database;
- exactly 100 real QA records and 100 real traces;
- real citation/path resolution against local `pk_nodes` and `pk_edges`;
- real regex and OCI-agent runs and reviewed divergence disposition;
- approved OCI provider/model/configuration record;
- measured p50/p95/p99, database/hardware configuration, and fully loaded cost per query;
- actual vendor ID and authoritative version;
- zero-error final validator with `--verify-db`;
- final human sample review;
- authoritative submission checksums.

## Authoritative artifact paths

**None.** No artifact in this delivery should be sent to Cotiviti as the final Track A answer package.

Expected final paths after the missing environment and identifiers are supplied are:

```text
submission/track-a-v<n>/vendor_<actual-vendor-id>_stage1_qa-results_v<n>.jsonl
submission/track-a-v<n>/vendor_<actual-vendor-id>_stage1_reasoning-traces_v<n>.json
submission/track-a-v<n>/validation-report.json
submission/track-a-v<n>/checksum-report.json
submission/track-a-v<n>/run-manifest.json
```

The authoritative pair must be identified only after a complete local database run and a zero-error validator result with database provenance enabled.
