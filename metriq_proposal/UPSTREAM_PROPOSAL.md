# Proposed Metriq-Gym Benchmark: TFIM Energy

## Summary

AfriQBench proposes a small application-oriented Hamiltonian benchmark for Metriq-Gym based on a fixed four-qubit transverse-field Ising model (TFIM) workload.

The benchmark would add a scientifically meaningful observable-estimation task to Metriq-Gym while remaining small enough to run on local simulators and current hardware providers.

## Motivation

Many quantum benchmarks emphasize circuit fidelity, randomized circuits, algorithm success probability, or abstract gate-level performance. A Hamiltonian-energy benchmark adds a complementary application-level question:

> How accurately does an execution stack reproduce a physically meaningful many-body observable for a completely specified workload?

The proposed MVP intentionally avoids runtime variational optimization. It uses a fixed four-qubit ansatz and measures a fixed seven-term Hamiltonian. This keeps the workload reproducible and provider-comparable.

## Proposed benchmark contract

- Name: **TFIM Energy**
- Qubits: **4**
- Boundary condition: **open**
- Hamiltonian: (H=-\sum Z_iZ_{i+1}-\sum X_i)
- Ansatz: fixed two-layer RY/CX circuit
- Circuits per run: **7**
- Shots: configurable per Hamiltonian term
- Canonical result: **unmitigated**
- Optional mitigation: outside the core benchmark

## Proposed metrics

1. measured energy with propagated shot uncertainty;
2. execution energy error relative to the ideal fixed ansatz;
3. application energy error relative to the exact ground state;
4. relative application error;
5. proposed normalized energy-accuracy score.

## Why the two reference energies?

The ideal fixed ansatz is close to, but not exactly equal to, the ground state. Reporting both reference points distinguishes algorithmic approximation from execution error.

## Questions for maintainers

Before opening a full upstream PR, feedback would be especially useful on:

1. **Benchmark naming:** Is `TFIM Energy` appropriate within the current `JobType` naming convention?
2. **Scalar score:** Should the normalized application-energy accuracy be the benchmark `score`, or should the first version expose metrics without a scalar score?
3. **Reference scope:** Is a fixed (N=4, J=h=1) workload preferred for the first contribution, or should the schema expose multiple canonical system sizes?
4. **Batch structure:** Is one seven-circuit batch the preferred dispatch structure for cross-provider portability?
5. **Future scale points:** Would a later suite benefit from canonical (N=4,6,8) scale points once state-preparation definitions are established?

## Existing implementation work

The AfriQBench repository already contains:

- exact classical TFIM references;
- an ideal Qiskit/Aer benchmark;
- controlled noisy simulation;
- device-derived fake-backend simulation;
- cross-backend comparison;
- Mitiq ZNE companion analysis; and
- this Metriq-Gym-shaped benchmark/schema proposal.

The upstream contribution would therefore start from tested project code rather than from an unimplemented concept.
