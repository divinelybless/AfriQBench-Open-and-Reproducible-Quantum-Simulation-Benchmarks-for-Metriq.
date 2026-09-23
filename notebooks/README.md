# AfriQBench Notebooks

## Implemented

1. **`01_exact_tfim_reference.ipynb`**  
   Exact diagonalization, ground-state energy, transverse magnetization, nearest-neighbour correlation, and reference-data generation.

2. **`02_ideal_quantum_benchmark.ipynb`**  
   Reproducible two-layer TFIM variational circuit, exact statevector evaluation, finite-shot Qiskit Aer measurement, uncertainty estimation, and raw circuit-resource metrics.

## Planned

3. `03_noisy_simulation.ipynb`  
   Noise-aware execution and observable error analysis.

4. `04_cross_backend_comparison.ipynb`  
   Reproducible comparison across supported execution targets.

5. `05_mitiq_error_mitigation.ipynb`  
   Companion analysis comparing raw, mitigated, and exact results.

## Installation

For Notebook 01:

```bash
python -m pip install -e ".[notebook]"
```

For Notebook 02 and later quantum notebooks:

```bash
python -m pip install -e ".[quantum,notebook]"
```
