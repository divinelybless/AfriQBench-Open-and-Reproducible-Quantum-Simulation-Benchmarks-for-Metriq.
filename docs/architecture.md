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
