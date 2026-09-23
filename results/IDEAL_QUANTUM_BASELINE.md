# Ideal Quantum Baseline

`ideal_quantum_n4_h1_baseline.json` records the deterministic statevector regression baseline used by Notebook 02.

For the open four-qubit TFIM with (J=h=1):

- exact ground-state energy: **-4.7587704831**;
- two-layer variational energy: **-4.7575478600**;
- absolute energy error: **0.0012226231**;
- relative energy error: **0.00025692**;
- fidelity to the exact ground state: **0.99976369**.

This deterministic result is intentionally kept separate from finite-shot Aer estimates. Shot-based results have statistical uncertainty and depend on the number of shots and random seed.

The raw state-preparation circuit contains six CNOT gates. Provider-specific transpilation can change depth and gate counts, so hardware-facing results should report metrics after transpilation as well.
