# Cross-Backend Comparison

Notebook 04 compares the same AfriQBench TFIM workload across three local execution classes:

1. **Ideal Aer** — finite-shot sampling with no device noise.
2. **Controlled synthetic noise** — transparent depolarizing + readout error.
3. **Device-derived Aer** — a cached IBM fake-backend snapshot converted with `AerSimulator.from_backend(...)`.

## Why this matters

A useful application benchmark should distinguish between several sources of discrepancy:

```text
exact-reference error
        +
variational approximation
        +
finite-shot sampling
        +
noise / hardware effects
        +
compilation / topology effects
```

The same state-preparation ansatz, Hamiltonian, shot budget, and seed conventions are retained across execution targets.

## Device-derived backend choice

The default MVP target is `fake_manila`, a compact five-qubit cached backend. This is large enough for the four-qubit TFIM benchmark while avoiding an unnecessarily large simulated device.

Aliases such as `manila`, `ibm_manila`, and `ibm-manila` are normalized to `fake_manila`.

## Relationship to Metriq-Gym

Current Metriq-Gym local execution uses Qiskit Aer. For IBM-style local noise simulation, its provider loads cached backends from `qiskit_ibm_runtime.fake_provider.FakeProviderForBackendV2` and creates an Aer simulator with `AerSimulator.from_backend(backend)`.

AfriQBench intentionally mirrors that public mechanism. This does **not** yet make AfriQBench a native Metriq benchmark, but it removes a major execution-model mismatch before upstream integration.

## Resource reporting

The cross-backend layer records both:

- raw logical circuit metrics; and
- post-transpilation metrics for the device-derived target.

This is important because topology, basis gates, routing, and optimization can change depth and two-qubit gate counts even when the logical workload is identical.

## Reproducibility

The canonical comparison configuration is stored in:

`configs/cross_backend.yaml`

Run-generated records should include software versions before publication or upload to an upstream benchmark-data repository.
