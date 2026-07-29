# Vanguard Stage 1 Track A metrics self-report

Authoritative submission version: 7

This report follows RFP §8.4. Cotiviti retains the answer key; answer
correctness, multi-hop accuracy, and citation quality are not self-scored.

| Domain | Metric | Result | Configuration/basis |
|---|---|---:|---|
| Retrieval and reasoning | Answer and citation quality | Not self-reported | Cotiviti-scored against the withheld key |
| Reported NFRs | Queries measured | 95 | Full issued Track A question set |
| Reported NFRs | Query latency p50 | 2718.00 ms | Wall clock, question input through finalized answer |
| Reported NFRs | Query latency p95 | 9579.30 ms | Same run/configuration |
| Reported NFRs | Query latency p99 | 19391.52 ms | Same run/configuration |
| Reported NFRs | Mean query latency | 4313.12 ms | Same run/configuration |
| Reported NFRs | Cost per query | Not available | OCI response lacked billing usage; no billing export was queried |

Graph-construction and ingestion metrics do not apply to Track A because
PrimeKG is provided by Cotiviti. Structural completion was
100/100; this is not an accuracy score.
