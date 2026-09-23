# AfriQBench Notebooks

## Implemented

1. **`01_exact_tfim_reference.ipynb`**  
   Exact diagonalization, ground-state energy, transverse magnetization, nearest-neighbour correlation, and reference-data generation.

2. **`02_ideal_quantum_benchmark.ipynb`**  
   Reproducible two-layer TFIM variational circuit, exact statevector evaluation, finite-shot Qiskit Aer measurement, uncertainty estimation, and raw circuit-resource metrics.

3. **`03_noisy_simulation.ipynb`**  
   Controlled single-qubit, two-qubit, and readout noise; finite-shot uncertainty; noise sweeps; term-level diagnostics; and structured noisy benchmark outputs.

4. **`04_cross_backend_comparison.ipynb`**  
   Side-by-side comparison of ideal Aer, controlled synthetic noise, and device-derived Aer noise from a cached IBM fake backend. Includes post-transpilation resource metrics and software-version capture.

## Planned

5. `05_mitiq_error_mitigation.ipynb`  
   Companion analysis comparing raw, mitigated, and exact results.

## Installation

For Notebook 01:

```bash
python -m pip install -e ".[notebook]"
```

For quantum notebooks:

```bash
python -m pip install -e ".[quantum,notebook]"
```
