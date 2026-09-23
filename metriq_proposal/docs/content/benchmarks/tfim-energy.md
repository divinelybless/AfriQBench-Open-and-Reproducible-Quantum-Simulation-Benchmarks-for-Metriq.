# TFIM Energy

**Proposed application-oriented benchmark for Metriq-Gym**

The TFIM Energy benchmark evaluates how accurately a quantum execution stack estimates the energy of a fixed four-qubit transverse-field Ising model workload.

## Hamiltonian

The benchmark uses the open-chain Hamiltonian

[
H=-J\sum_{i=0}^{2} Z_iZ_{i+1}-h\sum_{i=0}^{3}X_i,
]

with

[
J=h=1.
]

## State preparation

The workload uses a fixed, reproducible two-layer variational ansatz.

The circuit starts from

[
|+\rangle^{\otimes 4}
]

and applies two layers consisting of:

1. one (R_y) rotation per qubit; and
2. a nearest-neighbour CNOT chain.

The fixed parameter vector is:

```text
[
  0.292792927,
 -0.0000282104047,
 -0.100168525,
 -0.100168480,
 -0.292808429,
 -0.518628570,
 -0.562315096,
 -0.518620523
]
```

For the ideal statevector this produces an energy close to the exact four-site ground state.

## Measurement workload

The Hamiltonian contains seven Pauli terms:

```text
Z0Z1
Z1Z2
Z2Z3
X0
X1
X2
X3
```

One circuit is submitted per term.

- (ZZ) terms are measured in the computational basis.
- (X) terms are rotated with a Hadamard before measurement.
- Every term receives the same configured shot count.

The seven circuits are submitted as one batch where the provider supports batching.

## Reference values

The implementation computes its references directly from the benchmark definition:

- exact ground-state energy from exact diagonalization of the 16-by-16 Hamiltonian;
- ideal variational energy from Qiskit statevector evaluation of the fixed ansatz.

The expected development values are approximately:

| Quantity | Value |
|---|---:|
| Exact ground-state energy | -4.7587704831 |
| Ideal variational energy | -4.7575478600 |
| Intrinsic ansatz energy error | 0.0012226231 |

## Metrics

### Measured energy

[
E_{meas}=\sum_k c_k\langle P_k\rangle.
]

Each Pauli product has outcomes (pm1), so for (N_k) effective shots,

[
\sigma_k=
\sqrt{\frac{1-\langle P_k\rangle^2}{N_k}}.
]

Assuming independently sampled Hamiltonian terms, the propagated energy uncertainty is

[
\sigma_E=
\sqrt{\sum_k c_k^2\sigma_k^2}.
]

### Execution energy error

[
\epsilon_{exec}
=
|E_{meas}-E_{ideal\,ansatz}|.
]

This isolates execution effects from the ansatz's intrinsic approximation error.

### Application energy error

[
\epsilon_{app}
=
|E_{meas}-E_{ground}|.
]

This is the end-to-end application-level error.

### Relative application error

[
r_{app}
=
\frac{\epsilon_{app}}{|E_{ground}|}.
]

### Proposed normalized score

The proposed scalar Metriq score is

[
S=\max(0,\min(1,1-r_{app})).
]

This gives a dimensionless quantity in ([0,1]), with larger values indicating a more accurate end-to-end energy estimate.

The score definition should be considered part of the upstream design discussion. The raw energy and both error metrics remain available independently of the scalar score.

## Why separate execution and application errors?

A measured energy can differ from the exact ground-state energy for at least two reasons:

1. the fixed ansatz is not exactly the ground state; and
2. the execution stack introduces sampling, noise, compilation, and hardware error.

Reporting both quantities prevents the ansatz approximation from being incorrectly attributed to the hardware.

## Error mitigation

The canonical TFIM Energy benchmark is **unmitigated**.

Mitiq zero-noise extrapolation is an optional companion experiment in AfriQBench and should not silently modify the raw benchmark score. This keeps hardware/provider comparisons interpretable.

## Configuration

Example:

```json
{
  "benchmark_name": "TFIM Energy",
  "num_qubits": 4,
  "coupling_j": 1.0,
  "field_h": 1.0,
  "shots": 8192
}
```

## Intended upstream command

After registration in Metriq-Gym:

```bash
mgym job dispatch metriq_gym/schemas/examples/tfim_energy.example.json \
  --provider local --device aer_simulator

mgym job poll latest
```

The same configuration can then be used with supported hardware providers.

## Scope of the MVP

The first contribution deliberately fixes:

- (N=4);
- (J=1);
- (h=1);
- the ansatz architecture; and
- the ansatz parameters.

This keeps the benchmark definition stable across providers. Later versions can add scale points or additional Hamiltonians only after the initial workload is validated upstream.
