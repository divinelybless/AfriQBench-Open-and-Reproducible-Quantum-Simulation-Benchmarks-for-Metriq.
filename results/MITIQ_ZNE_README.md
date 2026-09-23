# Mitiq ZNE Run Outputs

Notebook `05_mitiq_error_mitigation.ipynb` generates run-specific files rather than committing invented mitigation results.

Expected outputs:

- `mitiq_zne_controlled_n4_h1_run.csv` — scale factor versus measured energy and circuit resources;
- `mitiq_zne_controlled_n4_h1_run.json` — full mitigation summary, fit diagnostics, cost, and quality metrics;
- optionally, a device-derived ZNE record if the user enables the cached fake-backend experiment.

The deterministic references remain:

- exact ground-state energy: **-4.7587704831**;
- variational statevector energy: **-4.7575478600**.

The notebook reports whether Mitiq ZNE actually improves the noisy result and how much additional execution cost was required.
