# Vanguard Stage 1 Track A metrics self-report

Authoritative submission version: 9

This report follows RFP §8.4. Cotiviti retains the answer key; answer
correctness, multi-hop accuracy, and citation quality are not self-scored.

| Domain | Metric | Result | Configuration/basis |
|---|---|---:|---|
| Retrieval and reasoning | Answer and citation quality | Not self-reported | Cotiviti-scored against the withheld key |
| Reported NFRs | Queries measured | 95 | Full issued Track A question set |
| Reported NFRs | Query latency p50 | 2718.00 ms | Wall clock, question input through finalized answer |
| Reported NFRs | Query latency p95 | 9823.40 ms | Same run/configuration |
| Reported NFRs | Query latency p99 | 22969.58 ms | Same run/configuration |
| Reported NFRs | Mean query latency | 4571.56 ms | Same run/configuration |
| Reported NFRs | Input tokens | 252,137 | Measured OCI response usage over 95 requests |
| Reported NFRs | Output tokens | 13,450 | Measured OCI response usage |
| Reported NFRs | Fully loaded cost per query | $0.00348796 | Measured model usage plus $0 incremental local compute/storage; see operations report |

Graph-construction and ingestion metrics do not apply to Track A because
PrimeKG is provided by Cotiviti. Structural completion was
100/100; this is not an accuracy score.
