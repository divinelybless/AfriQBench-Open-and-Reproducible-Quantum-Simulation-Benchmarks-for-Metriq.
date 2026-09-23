# Exact TFIM Reference Results

This directory contains reproducible classical reference results for the first AfriQBench workload.

## Dataset

`tfim_n4_reference.csv` contains exact-diagonalization results for:

- system size: **N = 4 qubits**;
- coupling: **J = 1**;
- transverse field: **h/J = 0.00 to 2.00** in steps of 0.05;
- boundary condition: **open**.

Columns include:

- exact ground-state energy;
- energy per site;
- site-averaged transverse magnetization;
- mean nearest-neighbour `ZZ` correlation.

## Reference spot checks

| h/J | Ground-state energy | <X> | mean <ZZ> |
|---:|---:|---:|---:|
| 0.5 | -3.4270340889 | 0.4601264023 | 0.8355937615 |
| 1.0 | -4.7587704831 | 0.8100954855 | 0.5061295137 |
| 1.5 | -6.5038915571 | 0.9150270221 | 0.3379098082 |

These values are also used to provide regression checks for the reference implementation.

## Interpretation

For this finite four-site open chain, increasing the transverse field strengthens alignment in the X direction while reducing nearest-neighbour Z-order. The repository deliberately treats these as **finite-size benchmark trends**, not as a direct estimate of the thermodynamic-limit critical point.

The accompanying notebook `notebooks/01_exact_tfim_reference.ipynb` regenerates the dataset and produces separate plots for energy, transverse magnetization, and nearest-neighbour correlation.
