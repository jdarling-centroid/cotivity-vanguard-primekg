# Decisions

Confirmed with the user on 2026-07-27, before Milestone 0 (originally PLAN.md §14,
since removed — the plan is implemented; see `docs/ARCHITECTURE.md`).

1. **Load scope — subset first.** Load the ~13 question-relevant relations
   for fast M2–M6 iteration; load all source facts before M7. The current loader
   materializes each non-self-loop fact in both directions, so database edge
   counts are directed records and are not directly comparable to source-row counts.
   The loader exposes `--relations` to select the subset. Document the exact
   subset loaded.
2. **Vendoring — copy, do not `pip install -e ../ai-proposal`.** The reused
   reference-agent modules are copied into `src/vanguard_primekg/_vendor/` (added
   at the milestone that first needs them) for true greenfield isolation. Their
   sibling imports (`..logging`, `..config`, `..errors`, `..submission`) are
   repointed at this package's minimal equivalents (`logging.py` already exists;
   others added when the module is vendored). We do **not** port
   `runner.py`'s `_primekg_*` handler chain or its LLM tool-orchestration loop.
3. **Embedder — local `all-MiniLM-L6-v2` (384-dim)** via `sentence-transformers`
   (optional `embed` extra). Entity resolution is lexical-first with vector
   similarity as fallback.
4. **Oracle image — `gvenzl/oracle-free:23-slim` (Oracle 23ai Free).** Provides
   SQL/PGQ + VECTOR. Host port 1522 → container 1521, service `FREEPDB1`. Select
   AI (`DBMS_CLOUD_AI`) availability on Free is verified during M0; if absent
   locally, the `select_ai` backend is deferred to the M7 comparison / remote.
5. **Target pass rate — ≥ 90/100 overall**, with hard sub-gates: 100% Category F
   (all adversarial blocked), 100% Category A, and 0 hallucinated facts on
   Category E.

## Track A completion decisions — 2026-07-28

6. **Track A only.** Track B is already submitted and is not rebuilt or altered.
7. **No self-scored accuracy.** The prior `100/100` result is reclassified as a
   structural outcome smoke check. Cotiviti's withheld key determines official
   correctness, multi-hop accuracy, and citation quality.
8. **Typed planner boundary.** Retain the regex classifier as a regression
   baseline. The OCI planner may select one closed-schema `Plan`; it may not
   write SQL, choose graph IDs, combine results, calculate aggregates, or author
   submitted claims.
9. **Evidence-complete finalization.** Answers, citations, context, graph fields,
   and traces are generated only from database-returned support paths. Native
   predicates and display relations are preserved.
10. **PrimeKG clinical context.** Record patient-level clinical-context fields as
    unavailable with an explicit reason; never fabricate them.
11. **Submission identity.** Require the actual vendor ID and version at runtime,
    open artifacts exclusively, and never overwrite an earlier submission.
12. **Definition of done revised.** Offline unit success is not submission
    completion. The final gate requires a loaded local Oracle run, all 100
    records/traces, reviewed planner divergences, and zero validator errors with
    database provenance enabled.
