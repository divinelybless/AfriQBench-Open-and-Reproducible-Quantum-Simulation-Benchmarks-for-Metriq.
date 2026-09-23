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

5. **`05_mitiq_error_mitigation.ipynb`**  
   Mitiq zero-noise extrapolation with visible scale-factor data, explicit success/failure assessment, fit diagnostics, shot overhead, and logical-circuit overhead. Device-derived ZNE is included as an optional extension.

## Installation

For Notebook 01:

```bash
python -m pip install -e ".[notebook]"
```

For Notebooks 02–04:

```bash
python -m pip install -e ".[quantum,notebook]"
```

For Notebook 05, use Python 3.11 or 3.12 (Python 3.12 recommended):

```bash
python -m pip install -e ".[quantum,mitigation,notebook]"
```
