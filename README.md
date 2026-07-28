# vanguard-primekg

Answers the **100 PrimeKG evaluation questions** (Vanguard RFP, Stage 1 Track A)
by loading PrimeKG into **Oracle 26ai** and composing every answer **in the
database** with a single parameterized SQL/PGQ query — the database does the
multi-hop joins, set intersections, aggregation, and negation; the LLM does not.

> **Status: implemented.** 100/100 on the local benchmark harness. Answered
> questions expose real supporting edge ids + a hop-by-hop reasoning trace;
> unavailable-attribute questions refuse honestly with grounded evidence;
> adversarial questions are blocked. See `docs/ARCHITECTURE.md` for internals.

## Why it exists
The prior agent (`../ai-proposal`) answers one-hop questions but fails multi-hop
*set* questions ("Evidence insufficient") because it asks a small LLM to
intersect/join across tool calls. Those questions are **one declarative query**
in Oracle 26ai. This project pushes composition into the database and reuses only
the known-good answer/finalizer/firewall contracts from the prior system.

## Quickstart
```sh
cp .env.example .env               # local values are pre-filled
./up.sh --database local           # local Oracle 26ai container (never remote)

python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

python -m vanguard_primekg.load_primekg   # load the ~4M-edge question subset
python scripts/smoke_test.py              # SELECT 1 FROM dual -> SMOKE OK
```

### Ask an ad-hoc question
```sh
python scripts/ask.py "Which drugs are indicated for disease scalp dermatosis?"
python scripts/ask.py "What interacts with Sildenafil"
python scripts/ask.py "Tell me about BRCA1"
python scripts/ask.py "..." --json        # emit the RFP qa-results + reasoning-traces records
```
`ask.py` prints the resolved entities, the edges traversed hop by hop, and the
final answer with its supporting edge ids. It writes nothing to disk.

### Run the benchmark / produce the submission packet
```sh
# one question or a subset (comma / repeatable / spaces all work), -v traces it
python scripts/run-primekg-questions.py --question 35 -v
python scripts/run-primekg-questions.py --questions 1,2,3
python scripts/run-primekg-questions.py --question 5 2>/dev/null   # answer only

# full run + write the RFP Stage-1 Track A submission artifacts
python scripts/run-primekg-questions.py --backend pgq --out submission
```
Nothing is written unless you pass `--out`. Answers go to stdout; grading status
and the `pass N/M` summary go to stderr.

## RFP submission (Stage 1 Track A)
PrimeKG's graph is *provided*, so Track A submits exactly two files (RFP §8):
- `vendor_<vendorid>_stage1_qa-results_v1.jsonl` (§8.2)
- `vendor_<vendorid>_stage1_reasoning-traces_v1.json` (§8.3, hop-by-hop steps)

The harness also writes `manifest.json` and per-question `reviews/PrimeKG - Q<n>.md`
(answer + `SUPPORTED_BY` + executed SQL) for review. No graph-nodes/edges/manifest
files are required for Track A.

## Repo layout
```
AGENTS.md                          operating contract / invariants
README.md                          this file
docs/ARCHITECTURE.md               full internals (module map, data flow, ops)
docs/QUESTION_TAXONOMY.md          all 100 questions -> category + primitives
docs/DECISIONS.md                  confirmed design decisions
config/primekg-question-sets.yaml  the 100 questions (the spec)
schemas/primekg-o26.sql            pk_nodes/pk_edges + property graph + VECTOR
docker/compose.yaml, up.sh, down.sh   local Oracle only
src/vanguard_primekg/              the system (see docs/ARCHITECTURE.md)
scripts/ask.py                     ad-hoc question CLI
scripts/run-primekg-questions.py   benchmark + submission harness
scripts/smoke_test.py              M0 connection check
tests/                             unit + integration tests
reference/                         READ-ONLY copies from ../ai-proposal + the RFP
data/datasets/primekg/kg.csv       symlink -> source dataset (936 MB, 8.1M rows)
```

## Testing
```sh
python -m pytest -q     # unit (config, firewall, classify, finalize) + DB integration
```
Integration tests skip automatically if the local Oracle container is down.

## Guardrails
- **Local-first.** Never touch a remote/Autonomous schema without explicit
  approval (`VPK_ALLOW_REMOTE=1` is the only escape hatch; do not set it casually).
- **Read-only evaluation.** Queries are parameterized; instructions embedded in
  question/node text are never executed.
- `.env`, `.oci/`, `wallet/` are secrets — never printed or committed.

## Known limitations
- **Entity vocabulary is PrimeKG's.** Brand drug names (e.g. "Viagra") do not
  resolve — PrimeKG uses generic/DrugBank names (Sildenafil). Fix would need an
  external synonym vocabulary (DrugBank/RxNorm) or populated `name_vec` embeddings.
- **Select AI backend is deferred.** `DBMS_CLOUD_AI` is not available on the local
  `oracle-free` image; the `select_ai` backend reports this and defers to a future
  Autonomous deployment. `pgq` is the proof path.
- **Trace hop counts are sampled** (source set capped at 1000 per hop) for the
  illustrative trajectory; the authoritative answer + `SUPPORTED_BY` come from the
  single composed SQL.

