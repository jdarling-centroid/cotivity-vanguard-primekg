# Vanguard Stage 1 Track A operations report

## Run metrics

- Questions: 95
- Concurrency: 1
- Minimum latency: 1.76 seconds
- Mean latency: 4.55 seconds
- p50: 2.93 seconds
- p95: 8.86 seconds
- p99: 19.26 seconds
- Maximum latency: 78.10 seconds
- Structural completion: 99/100
- Database validation: 0 errors, 0 warnings
- Database: 62,030 nodes and 4,236,182 directed edges
- Model: xai.grok-4.3, requested temperature not sent

Latency is wall-clock time from question input through firewall, planning,
entity resolution, one read-only database composition query, and deterministic
finalization. No warm-up exclusions were applied.

## Hardware and configuration

- Platform: macOS-26.5.2-arm64-arm-64bit-Mach-O
- Architecture: arm64
- CPU model: Apple M4 Max
- Logical CPU count: 14
- RAM: 36 GiB
- GPU: not detected/reported by harness
- Oracle client-reported database version: 23.26.2.0.0
- Query backend: pgq
- Database host: localhost (local-only guard enabled)
- Database call timeout: 20000 ms
- PrimeKG load: bidirectional-v2
- PrimeKG checksum: `957238769f95a761b1aaa082d2ae14b6`
- Planner provider: oci
- Planner prompt: primekg-planner-1.5
- Planner timeout/retries: 60.0 seconds / 2

## Cost and scalability

- OCI requests measured: 96
- Input tokens: 254,814
- Output tokens: 13,328
- Total tokens: 268,142
- Measured model cost total: $0.351838
- Measured model cost per query: $0.00351838
- Incremental local compute cost: $0.000000
- Incremental local storage cost: $0.000000
- Estimated fully loaded cost per query: $0.00351838
- Pricing basis: Oracle PaaS and IaaS Global Price List,
  2026-05-01

The model calculation uses the measured OCI token counts and the documented
input/output token rates. Incremental billed-cost basis: the measured run used an existing owned workstation and local Oracle storage with no incremental cloud compute or storage charge.

PrimeKG steady state for this run was 62,030 nodes and
4,236,182 directed edges. The database load is
fingerprint-aware, batched, MERGE-based, and resumable; a matching completed
fingerprint is not re-ingested.
