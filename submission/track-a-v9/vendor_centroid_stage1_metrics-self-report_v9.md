# Vanguard Stage 1 Track A metrics self-report

Authoritative submission version: 9

This report follows RFP §8.4. Cotiviti retains the answer key; answer
correctness, multi-hop accuracy, and citation quality are not self-scored.

| Domain | Metric | Result | Configuration/basis |
|---|---|---:|---|
| Retrieval and reasoning | Answer and citation quality | Not self-reported | Cotiviti-scored against the withheld key |
| Reported NFRs | Queries measured | 95 | Full issued Track A question set |
| Reported NFRs | Query latency p50 | 2933.00 ms | Wall clock, question input through finalized answer |
| Reported NFRs | Query latency p95 | 8855.20 ms | Same run/configuration |
| Reported NFRs | Query latency p99 | 19261.82 ms | Same run/configuration |
| Reported NFRs | Mean query latency | 4547.12 ms | Same run/configuration |
| Reported NFRs | Input tokens | 254,814 | Measured OCI response usage over 96 requests |
| Reported NFRs | Output tokens | 13,328 | Measured OCI response usage |
| Reported NFRs | Fully loaded cost per query | $0.00351838 | Measured model usage plus $0 incremental local compute/storage; see operations report |

Graph-construction and ingestion metrics do not apply to Track A because
PrimeKG is provided by Cotiviti. Structural completion was
99/100; this is not an accuracy score.
