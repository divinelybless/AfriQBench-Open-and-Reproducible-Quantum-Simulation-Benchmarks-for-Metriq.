# AfriQBench Technical Architecture

```mermaid
flowchart LR
    A[Benchmark configuration] --> B[TFIM instance generator]
    B --> C[Exact classical reference]
    B --> D[Quantum circuit and measurement specification]
    D --> E[Metriq-compatible execution adapter]
    E --> F[Ideal simulator]
    E --> G[Noisy simulator]
    E --> H[Accessible QPU]
    C --> I[Reference observables]
    F --> J[Structured results]
    G --> J
    H --> J
    I --> K[Scientific accuracy metrics]
    J --> K
    J --> L[Resource metrics]
    K --> M[Validated benchmark record]
    L --> M
    M --> N[Metriq-compatible dataset or upstream contribution]
    J --> O[Mitiq companion analysis]
```

## Design principles

### 1. Separate benchmark definition from execution

The scientific workload should be specified independently from the provider used to execute it.

### 2. Keep classical references transparent

Small TFIM instances are validated with exact diagonalization so benchmark accuracy is interpretable.

### 3. Separate canonical benchmarking from mitigation

Error mitigation can be studied in companion analyses without changing the definition of the baseline benchmark.

### 4. Prefer upstream compatibility

Metriq-specific execution and result interfaces should follow the current upstream `metriq-gym` conventions wherever practical.

### 5. Report both scientific and computational performance

Application-level error alone is not sufficient. AfriQBench also records circuit and execution resources.

## Code layout

The source tree follows the benchmark pipeline:

1. `models` defines the TFIM Hamiltonian.
2. `reference` computes the exact ground state.
3. `observables` and `metrics` turn that state into the score.
4. `quantum/qiskit_tfim.py` builds the fixed circuit.
5. `quantum/noise.py`, `cross_backend.py`, and `mitigation.py` add the simulator studies.
6. `quantum/hardware/` checks the same circuit locally, then submits it to IBM.

Notebooks `01` through `06` follow that same order. `metriq_proposal/` keeps the upstream file layout required by Metriq-Gym.
