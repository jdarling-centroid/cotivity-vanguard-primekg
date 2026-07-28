# Decisions

Confirmed with the user on 2026-07-27, before Milestone 0 (originally PLAN.md §14,
since removed — the plan is implemented; see `docs/ARCHITECTURE.md`).

1. **Load scope — subset first.** Load the ~13 question-relevant relations
   (~4M edges) for fast M2–M6 iteration; load the full 8.1M-edge graph before M7.
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
