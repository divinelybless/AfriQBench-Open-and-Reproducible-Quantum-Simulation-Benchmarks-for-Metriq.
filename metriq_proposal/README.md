# Metriq-Gym Upstream Proposal Bundle

This directory mirrors the file layout required for a proposed **TFIM Energy** contribution to `unitaryfoundation/metriq-gym`.

It was prepared against the current Metriq-Gym contribution pattern:

- `Benchmark`, `BenchmarkData`, and `BenchmarkResult` classes;
- JSON Schema configuration;
- editable example configuration;
- `JobType` / `SCHEMA_MAPPING` registration;
- benchmark/data/result registry entries;
- local-simulator resource estimation;
- unit tests; and
- benchmark documentation.

## Bundle contents

```text
metriq_proposal/
├── README.md
├── INTEGRATION_PATCH.md
├── UPSTREAM_PROPOSAL.md
├── metriq_gym/
│   ├── benchmarks/
│   │   └── tfim_energy.py
│   └── schemas/
│       ├── tfim_energy.schema.json
│       └── examples/
│           └── tfim_energy.example.json
├── tests/
│   └── unit/
│       └── benchmarks/
│           └── test_tfim_energy.py
└── docs/
    └── content/
        └── benchmarks/
            └── tfim-energy.md
```

## Design decision

The MVP is intentionally fixed at four qubits. This avoids adding variational optimization to the benchmark runtime and ensures every provider receives the same state-preparation and measurement workload.

The canonical benchmark is also unmitigated. Mitiq ZNE remains a companion AfriQBench analysis rather than changing the raw Metriq result.

## Next upstream step

The recommended sequence is:

1. open a Metriq-Gym discussion/issue using `UPSTREAM_PROPOSAL.md`;
2. incorporate maintainer feedback on naming and score semantics;
3. apply the bundle on a fork/branch of Metriq-Gym;
4. run the local `mgym job estimate/dispatch/poll` workflow;
5. run the full Metriq-Gym tests and linters;
6. open a focused pull request.
