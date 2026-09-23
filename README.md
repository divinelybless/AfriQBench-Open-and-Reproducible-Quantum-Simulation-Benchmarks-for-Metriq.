# AfriQBench

**Open and Reproducible Quantum Simulation Benchmarks for the Metriq Ecosystem**

AfriQBench is an open-source project for building reproducible, application-oriented quantum simulation benchmarks, beginning with the **transverse-field Ising model (TFIM)**.

The project is designed to **complement and contribute to Unitary Foundation's Metriq ecosystem**, rather than create a competing benchmarking platform.

## Motivation

Quantum processors are increasingly accessible through cloud platforms, but meaningful cross-platform comparison remains difficult. Experiments often differ in:

- problem instances and parameter choices;
- circuit construction and compilation;
- observables and measurement procedures;
- noise assumptions;
- reporting conventions; and
- accuracy and resource metrics.

AfriQBench addresses this by defining small, reproducible scientific workloads with transparent classical reference solutions and standardized quantum benchmarking metrics.

## Initial Benchmark

The first benchmark family is based on the transverse-field Ising model

```text
H = -J Σ_i Z_i Z_(i+1) - h Σ_i X_i
```

For small systems, exact diagonalization provides reference values against which quantum executions can be compared.

Initial scientific outputs include:

- ground-state energy;
- magnetization;
- selected correlation functions; and
- observable-level error.

Initial resource metrics include:

- number of qubits;
- transpiled circuit depth;
- two-qubit gate count;
- number of shots; and
- execution metadata where supported.

## Project Pipeline

```text
Benchmark configuration
        ↓
TFIM problem instance
        ↓
Exact classical reference
        ↓
Quantum circuit + measurement specification
        ↓
Metriq-compatible execution
        ↓
Simulator / noisy simulator / accessible QPU
        ↓
Scientific accuracy + resource metrics
        ↓
Structured reproducible benchmark record
        ↓
Metriq-compatible contribution
```

## MVP Deliverables

The first development phase targets:

- deterministic TFIM benchmark configurations;
- exact classical reference solver;
- reproducible circuit and measurement specifications;
- scientific accuracy metrics;
- circuit-resource metrics;
- ideal and noisy simulator validation;
- accessible-hardware results where available;
- automated tests and continuous integration;
- tutorial notebooks;
- a Mitiq-based error-mitigation companion analysis; and
- an upstream benchmark proposal, issue, or pull request for the Metriq ecosystem.

## Why TFIM?

The TFIM is a useful first workload because it is:

1. scientifically meaningful;
2. scalable with system size;
3. exactly solvable for small benchmark instances;
4. sensitive to circuit depth and noise;
5. naturally expressed through experimentally measurable observables; and
6. suitable for studying both quantum accuracy and computational resource requirements.

## Relationship to Metriq

AfriQBench is not intended to replace Metriq.

The goal is to contribute a well-specified Hamiltonian-simulation workload, reproducible configurations, validated reference values, and benchmark results that can fit into the existing Metriq benchmarking workflow.

Metriq-specific interfaces will be implemented against the current upstream `metriq-gym` API rather than introducing an incompatible local abstraction.

## Error Mitigation

Error mitigation will be treated as a **companion analysis**, not part of the canonical baseline benchmark score.

A tutorial will compare:

```text
raw estimate → mitigated estimate → exact reference
```

using open-source tooling such as Mitiq while also reporting the additional execution cost.

## Five-Month MVP Roadmap

| Month | Milestone |
|---|---|
| 1 | Benchmark specification, reference solver, community alignment |
| 2 | Circuit-generation and measurement prototype |
| 3 | Noisy simulation and Metriq-compatible execution/results pathway |
| 4 | Accessible-hardware runs and Mitiq mitigation notebook |
| 5 | Documentation, public benchmark data, upstream contribution, community validation |

## Repository Structure

```text
AfriQBench/
├── configs/
├── docs/
├── notebooks/
├── src/afriqbench/
│   ├── models/
│   ├── reference/
│   └── metrics.py
├── tests/
└── .github/workflows/
```

## Quick Start

```bash
python -m pip install -e ".[dev]"
pytest
```

Example:

```python
from afriqbench.models.tfim import tfim_hamiltonian
from afriqbench.reference.exact import ground_state

H = tfim_hamiltonian(n_qubits=3, J=1.0, h=0.8, periodic=False)
energy, state = ground_state(H)

print("Ground-state energy:", energy)
```

## Project Status

AfriQBench is currently at the **application-stage MVP**. Four executable benchmark layers are implemented: (1) exact TFIM classical references, (2) ideal finite-shot Qiskit/Aer execution, (3) controlled noisy-Aer sensitivity analysis, and (4) cross-backend comparison using ideal Aer, controlled noise, and device-derived Aer noise from cached IBM fake-backend snapshots. The device-derived pathway mirrors the public local-simulation mechanism used by current Metriq-Gym.

## Open Source

Software is released under the MIT License. Benchmark datasets produced by the project will be released under an appropriate open-data license.

## Project Lead

**Dorcas Attuabea Addo**  
University of Education, Winneba, Ghana

## Vision

AfriQBench aims to help researchers move from simply accessing quantum hardware to producing transparent, reproducible, application-level evidence about how quantum systems perform on scientifically meaningful workloads.

It also seeks to widen participation in global quantum open-source infrastructure by enabling contributions through benchmark design, classical validation, simulation, testing, documentation, reproducibility, and data analysis.
