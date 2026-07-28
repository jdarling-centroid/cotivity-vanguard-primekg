# PrimeKG dataset placement

Place the provided PrimeKG `kg.csv` at:

```text
data/datasets/primekg/kg.csv
```

The source dataset is intentionally not packaged here. The loader computes a
source fingerprint, records the bidirectional load format in `pk_load_journal`,
and materializes deterministic forward and reverse edge records while
preserving native `predicate` and `display_relation` values.
