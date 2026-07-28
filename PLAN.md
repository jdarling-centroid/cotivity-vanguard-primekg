# Migration Plan — Regex Prototype → OCI AI Agent

> **For the next agent.** This repo currently answers the 100 PrimeKG questions
> with a **hard-coded regex classifier** (`classify.py`) that maps each benchmark
> question's *wording* to a query plan, plus a self-graded "100/100" metric that
> only checks "did we return edges," not correctness. **Both are unacceptable in
> an RFP response** (misrepresentation risk) and must be removed. Replace the
> classifier with the OCI Generative AI agent so the system *reasons* to the
> answer instead of pattern-matching known questions.

---

## 1. What must change and what must not

**Retain as the validation oracle (do NOT delete yet):**
- `src/vanguard_primekg/classify.py` — the regex intent layer. It hard-codes the
  100 questions' answer *paths*, so it is the **known-good baseline**: for each of
  the 100 it tells you which tools/primitives the correct answer uses. Keep it
  wired behind a `--planner regex` switch and use it to validate the agent. Only
  after the agent matches it on all 100 do you **deprecate** it — move it to
  `reference/` (or `classify_legacy.py`) for reference, do not lose it.

**Remove (fake metric only):**
- The self-graded pass metric in `scripts/run-primekg-questions.py`
  (`_meets` / "pass N/M"). It only checks "did we return edges," not correctness.
  Replace it with a real diff against the regex baseline + independent gold
  (§6). Do not report a self-graded number as accuracy.

**Keep (legitimate, reusable):**
- `query_engine/engine.py` — the general graph-composition primitives
  (expand / intersect / count / difference / rank / bridge / ratio, etc.). These
  do the set math **in one SQL query each**. They become the agent's **tools**.
- `resolve.py` (entity resolution), `firewall.py` (adversarial blocking),
  `finalize.py` + `_vendor/finalizer.py` (RFP §8.2/§8.3 output), the schema,
  loader, `db.py`/`config.py`, `walk_hops`/`trace.py` (for the trace).
- `reference/agent/llm.py` — the OCI `ChatModel` abstraction (`ModelTurn`,
  `ToolCall`, `make_chat_model`). Reuse it to talk to OCI.

**Invariants that do NOT change:**
- **The database composes; the agent orchestrates.** The agent decides *which*
  graph operation to run; each operation is one parameterized DB query that does
  the join/intersection/count. The agent must **never** intersect/count/join sets
  in its own text (that is the exact failure of `reference/agent/runner.py` —
  study it as the cautionary example, do not copy its `_primekg_*` handlers).
- All four `drug_protein` roles = "target" (target/enzyme/carrier/transporter).
- PrimeKG is undirected; traversal is `source_node_id IN S` + predicate.
- Every answered fact is grounded in **real node/edge ids returned by the DB**.
  The agent never invents ids and never answers a fact PrimeKG lacks — it refuses
  honestly (grounded `insufficient_data`).
- Firewall runs before the agent. Local-first; no remote without approval.

---

## 2. Target architecture

```
question
  │
  ▼ firewall.verdict()                       → blocked (adversarial)
  ▼ AGENT LOOP  (OCI Generative AI, xai.grok-4.3 via .oci/config)
  │    system prompt = graph vocabulary + tool catalog + "DB composes, you don't"
  │    repeat:
  │      model → ToolCall(s)  →  execute against DB  →  tool result (nodes+edges)
  │    until model emits final answer
  ▼ finalize.*  (real answer prose + SUPPORTED_BY from the tools' real edge ids)
  ▼ §8.2 qa-results  +  §8.3 reasoning-traces  (built from the ACTUAL tool trajectory)
```

The agent is the reasoning brain. The tools are thin wrappers over the existing
engine primitives — **each tool call is one DB query**, so composition stays in
Oracle and the agent only plans/sequences and phrases the grounded result.

---

## 3. OCI wiring

- Provider `oci_generative_ai`, model `xai.grok-4.3`, region from `.oci/config`
  (same as `../ai-proposal`; see `config/agent-worker/config.yaml` there and the
  commented `MC_MODELS__ORCHESTRATOR__*` block in `.env.example`).
- Reuse `reference/agent/llm.py::make_chat_model` (it already builds an OCI
  `ChatModel` from provider/model/region/config-file). If it needs the sibling's
  `..config`, vendor a minimal `ModelConfig` into `src/vanguard_primekg/_vendor/`.
- Auth: `.oci/config` + key (gitignored). Add `MC_MODELS__ORCHESTRATOR__PROVIDER`,
  `__MODEL_ID`, `__REGION`, `__CONFIG_FILE` to `.env`. Temperature **0** for
  determinism; validate/retry on malformed tool calls.
- Local dev without OCI creds: keep a deterministic `StubChatModel`
  (`reference/agent/llm.py` has one) so tests run offline.

---

## 4. Tool catalog (the agent's only way to touch the graph)

Expose the engine primitives as tools with JSON schemas (mirror
`reference/agent/tools.py::configured_tool_schemas`). Each returns
`{nodes:[{id,name,type}], edges:[edge_id], sql}` from **one** DB query so set math
never leaves the database:

| tool | backed by | purpose |
|---|---|---|
| `resolve_entity(label, type?)` | `resolve.py` | label → node id(s); returns candidates + method; agent disambiguates, never invents ids |
| `neighbors(node_id, relation, roles?)` | `engine.expand` (1 hop) | one-hop traversal (targets, side effects, indications, PPI, …) |
| `chain(base_id, [relations])` | `engine.expand` | multi-hop chain, set-collapsed, in one query |
| `intersect(legA, legB, …)` | `engine.intersect`/`intersect_many` | "both … and …" in one query |
| `difference(legA, minus…)` | `engine.difference`/`difference_many` | negation/"NOT" |
| `count_filter(base, steps, group, distinct, op, n)` | `engine.count_threshold` | "at least/exactly n …" |
| `compare_counts`, `rank_top`, `bridge_count`, `ratio_shared`, `xor` | same-named engine methods | quantified/aggregate/ranking questions |
| `describe(node_id)` | `engine.node_evidence` | what PrimeKG records about an entity (also grounds refusals) |

Give the model, in the system prompt: the **relation vocabulary** (the 13
predicates + the 4 target roles), the **undirected-graph** fact, and the rule
**"to combine sets, call one composition tool — never merge results yourself."**
Provide 5–8 *general* few-shot examples (varied phrasings mapped to tool calls),
explicitly **not** the benchmark's exact sentences.

---

## 5. Reasoning trace (§8.3) — from the real trajectory

Build `reasoning-traces.json` from the **agent's actual tool calls**, not a
reconstructed walk: `resolve_entity` → `entity_lookup` step; each graph tool →
`edge_traversal`/composition step with the real edge ids it returned;
`final_answer` + `answer_supported_by` from the last grounded result. This is a
genuine, gradeable trajectory (a wrong path is now visible), which is the point
of §8.3.

---

## 6. Honest correctness (replace the fake metric)

There is **no** self-declared pass rate. Two oracles:
1. **Regex baseline (bootstrap regression oracle).** Run the retained regex
   planner over the 100 and record its tool/answer path per question. The agent
   must reproduce the same answer set (and cite existing edges) for each. Any
   divergence is a real diff to investigate — this is how you validate the agent
   before deprecating the regex. It is same-author, so it is a regression oracle,
   not proof of truth.
2. **Independent gold (truth).** For truth, author a **separate** reference answer
   per question (hand-written SQL or a reviewed spec, authored independently of
   both the agent and the regex) and spot-check by hand. Report answer
   correctness, multi-hop accuracy, citation validity, adversarial block rate,
   latency — and state clearly the final grade is Cotiviti's **withheld** key.
3. Never mark a question "pass" just because edges were returned.

---

## 7. Migration steps (phased, each ends test-green)

- **P0 — Freeze the primitive API.** Confirm the engine methods are the stable
  tool surface; write `schemas/tool-catalog.json` (tool names + arg schemas).
- **P1 — OCI ChatModel.** Vendor/adapt `make_chat_model`; smoke-test a live OCI
  call and the offline `StubChatModel`.
- **P2 — Agent runner.** New `src/vanguard_primekg/agent/runner.py`: firewall →
  tool loop → grounded answer. Tools wrap the engine primitives. **No** per-
  question handlers. Reuse `Recorder` to capture the trajectory.
- **P3 — Wire finalize.** §8.2/§8.3 built from the agent's trajectory + real ids.
- **P4 — Validate against the regex baseline.** Both planners run the 100 behind
  a `--planner agent|regex` switch; diff their answer sets question-by-question
  (§6.1) until the agent matches on all 100 and passes the independent gold
  spot-check (§6.2). Keep the regex planner wired throughout this phase.
- **P5 — Deprecate the regex classifier** (only now): move it to `reference/`
  (or `classify_legacy.py`) for reference; make the agent the default planner.
  Remove the `_meets` fake metric; keep the diff/gold scorer.
- **P6 — (approval-gated)** full 8.1M load, Select AI comparison, remote/
  Autonomous.

---

## 8. Files

**Add:** `src/vanguard_primekg/agent/{runner.py,tools.py,oci_llm.py}`,
`schemas/tool-catalog.json`, `tests/gold/*.json` (independent ground truth),
`scripts/score.py` (diff vs regex baseline + gold).
**Change:** `solver.py` (add agent path behind `--planner agent|regex`), `ask.py`
+ harness (planner switch, replace `_meets` with the diff/gold scorer),
`finalize.py` (trace from trajectory), `.env`/`config.py` (OCI creds).
**Deprecate only after validation (P5):** `classify.py` → `reference/` /
`classify_legacy.py` (retain for reference; do not delete).

---

## 9. Pitfalls (do not repeat)

- **LLM set-math across tool calls** — the reason `reference/agent/runner.py`
  failed. Force composition into single-query tools; the agent picks the tool.
- **Hallucinated entity/edge ids** — ids come only from tool results; validate
  every id the agent cites against what the DB returned.
- **Overfit few-shots** — keep examples general and few; never paste benchmark
  sentences.
- **Non-determinism** — temperature 0, validate tool JSON, bounded retries,
  fail closed to an honest refusal (never a guess).
- **Firewall bypass** — run `firewall.verdict` before the agent; never let the
  agent execute instructions embedded in question/node text.

---

## 10. Definition of done

The OCI agent answers arbitrary PrimeKG questions by orchestrating the general
DB-composition tools; there is **no** question-specific code; every answer is
grounded in DB-returned ids with a real hop-by-hop §8.3 trace; correctness is
measured against an **independent** ground truth (not a self-graded proxy);
adversarial questions are blocked; unavailable facts are refused honestly. Only
then discuss remote/Autonomous + Select AI.
