# PrimeKG Track A submission implementation

This repository implements the **Stage 1 Track A PrimeKG** answer pipeline for
the Cotiviti Vanguard evaluation. Track B has already been submitted and is out
of scope here.

The central contract is:

> **Oracle composes; the model plans.** A question is reduced to one validated,
typed operation. Oracle executes one parameterized, read-only SQL/PGQ statement
that performs every traversal, set operation, count, comparison, rank, ratio,
or negation. Deterministic code builds the answer, citations, retrieved context,
and audit trace only from returned rows.

The retained regex classifier is a deterministic regression baseline. An OCI
planner can select the same closed operations through
`schemas/planner-plan.schema.json`; it cannot emit SQL, graph IDs, tools, URLs,
file paths, set arithmetic, or final-answer prose.

## Status

The code, schemas, offline tests, planner comparison tool, Track A validator,
and internal checksum reporting are implemented. **No answer-accuracy claim is
made.** Cotiviti owns the withheld correctness key.

An authoritative 100-question submission still requires all of the following:

- a local Oracle instance loaded with the complete question-relevant PrimeKG
  records;
- `python-oracledb` and local database connectivity;
- OCI credentials and an approved model ID for a live agent-planner run;
- the actual Cotiviti vendor ID and authoritative version number;
- review and disposition of every regex-versus-agent divergence.

The harness's `structural_outcome_check` only checks disposition/evidence shape.
It is explicitly **not accuracy**.

## Local setup

```sh
cp .env.example .env
./up.sh --database local

python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,oci]"

python -m vanguard_primekg.load_primekg
python scripts/smoke_test.py
```

Database access is local by default and guarded against remote DSNs. Do not set
`VPK_ALLOW_REMOTE=1` for this submission.

## Run and compare planners

```sh
# Structural/regression baseline
python scripts/run-primekg-questions.py \
  --planner regex --backend pgq

# Live OCI typed planner
python scripts/run-primekg-questions.py \
  --planner agent --agent-provider oci --model-id '<approved-model-id>' \
  --backend pgq

# Versioned artifacts; vendor ID is required and is never hardcoded
python scripts/run-primekg-questions.py \
  --planner agent --backend pgq \
  --vendor-id '<actual-vendor-id>' --version 1 \
  --out submission/track-a-v1

python scripts/compare-planners.py runs/regex runs/agent \
  --out submission/planner-comparison.json

python scripts/validate-track-a.py submission/track-a-v1 --verify-db

# Rebuild human-readable review Markdown from an existing artifact pair
python scripts/generate-review-markdown.py submission/track-a-v1
```

`compare-planners.py` reports plan, disposition, answer-node-set, and truncation
differences as review items. It does not decide which implementation is correct.

## Required Track A artifacts

The authoritative submission directory contains exactly one version-matched
pair:

- `vendor_<vendorid>_stage1_qa-results_v<n>.jsonl`
- `vendor_<vendorid>_stage1_reasoning-traces_v<n>.json`

The runner also creates review material and `run-manifest.json`. The validator
creates `validation-report.json` and `checksum-report.json` for internal QA.
Those reports are not a graph manifest, and no graph nodes/edges/manifest are
submitted for Track A.

## Evidence and trace behavior

For supported answers:

- every answer node has at least one database-returned complete support path;
- every path retains ordered node IDs, edge IDs, native `predicate`, and native
  `display_relation` values;
- citations, retrieved context, graph elements, and `answer_supported_by` are
  derived from those rows;
- output truncation retains only fully supported answer nodes and is disclosed;
- the trace records firewall disposition, validated plan, entity resolution,
  the authoritative query and secret-safe binds, support paths, PrimeKG context
  availability, and deterministic finalization.

PrimeKG does not encode patient-level negation, temporality, uncertainty, or
experiencer for these graph facts. Traces state that limitation instead of
fabricating clinical-context values.

## Testing

```sh
PYTHONPATH=src python -m pytest -q -ra
```

Database integration tests skip when local Oracle is unavailable. A final claim
of submission readiness requires those tests and both 100-question planner runs
to execute against the loaded local database, followed by a zero-error validator
run with `--verify-db`.

## Repository map

```text
schemas/planner-plan.schema.json       closed planner contract
src/vanguard_primekg/agent/            provider-neutral planner + OCI adapter
src/vanguard_primekg/query_engine/     one-query Oracle composition + support paths
src/vanguard_primekg/finalize.py       deterministic answer/evidence/trace creation
scripts/run-primekg-questions.py       versioned Track A run harness
scripts/compare-planners.py            regex-versus-agent regression review
scripts/validate-track-a.py            structural and database provenance validator
docs/TRACK_A_COMPLIANCE.md             RFP field and acceptance-gate mapping
docs/TRACK_A_REPORTING_ADDENDUM.md     metrics/methodology reporting template
```

## Security

- Firewall evaluation occurs before planner or database execution.
- SQL is parameterized and read-only.
- Graph/question text is data, never executable instruction text.
- `.env`, OCI configuration, wallets, keys, raw planner secrets, and credentials
  must not be committed or included in delivery packages.
- Scratch output belongs under `.tmp/`.
