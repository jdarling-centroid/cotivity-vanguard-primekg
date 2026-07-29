# Stage 1 Track B completion plan

## Required package

- Provenance-complete graph nodes, edges, and manifest (§8.1).
- QA results for all 60 issued questions, including five firewall questions
  (§8.2). The evaluation-criteria prose says 57 while the supplied question set
  contains 60; the implementation preserves all supplied records.
- One reasoning trace per answer (§8.3).
- Metrics, operations, methodology, and clarification reports (§8.4/§7).
- Human-readable review Markdown generated from the authoritative artifacts.

## Acceptance gates

- Zero schema violations and dangling edge endpoints.
- 100% node and edge `doc_id` provenance.
- All 609 source documents represented; orphan-node rate reported.
- Exact issued question IDs/text and one-to-one QA/trace references.
- Citations resolve to submitted documents, nodes, edges, and spans.
- Firewall executes before retrieval/model calls.
- Query latency p50/p95/p99, ingestion throughput, hardware, concurrency,
  model configuration, and cost basis recorded.
- No answer correctness, multi-hop accuracy, or citation-quality score is
  self-claimed; Cotiviti scores those against its withheld key.
