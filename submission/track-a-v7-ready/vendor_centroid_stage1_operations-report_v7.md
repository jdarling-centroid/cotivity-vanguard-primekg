# Vanguard Stage 1 Track A operations report

## Run metrics

- Questions: 95
- Concurrency: 1
- Minimum latency: 1.54 seconds
- Mean latency: 4.31 seconds
- p50: 2.72 seconds
- p95: 9.58 seconds
- p99: 19.39 seconds
- Maximum latency: 75.55 seconds
- Structural completion: 100/100
- Database validation: 0 errors, 0 warnings
- Database: 62,030 nodes and 4,236,182 directed edges
- Model: xai.grok-4.3, requested temperature 0

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
- Planner timeout/retries: 300.0 seconds / 2

## Cost and scalability

Fully loaded cost per query is not reported because the OCI runtime response did
not provide billable usage and no billing export was queried. The run used local
Oracle storage/compute and OCI Generative AI only for closed-schema planning.
No unsupported cost estimate is presented.

PrimeKG steady state for this run was 62,030 nodes and
4,236,182 directed edges. The database load is
fingerprint-aware, batched, MERGE-based, and resumable; a matching completed
fingerprint is not re-ingested.
