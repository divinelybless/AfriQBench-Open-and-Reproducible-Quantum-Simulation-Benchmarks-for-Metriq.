# Controlled Noise Model

Notebook 03 introduces the first noise-aware AfriQBench execution path.

## Purpose

The initial noisy benchmark deliberately uses a **synthetic controlled noise model** instead of a vendor-calibrated device model. This makes the relationship between noise strength and application-level error transparent.

The model includes three components:

1. single-qubit depolarizing error applied to `H` and `RY`;
2. two-qubit depolarizing error applied to `CX`; and
3. symmetric independent readout error.

The canonical parameter sweep is stored in `configs/noise_sweep.yaml`.

## Why separate this from device-derived noise?

A controlled model answers a different question from a hardware snapshot.

- **Controlled noise:** how does benchmark accuracy respond when specified error channels are increased?
- **Device-derived noise:** how does the benchmark behave under the calibration/noise characteristics of a particular device?

AfriQBench treats these as separate experiment classes so results remain interpretable.

## Metriq alignment

Current `metriq-gym` local execution uses Qiskit Aer and can also run local noise models based on IBM device data or cached fake backends. AfriQBench's controlled model therefore uses the same underlying Aer simulation family while keeping the first noise study provider-independent.

A later execution layer can map the benchmark to Metriq's local-device workflow and compare controlled synthetic noise with device-derived noise snapshots.

## Statistical uncertainty vs noise-induced bias

Finite-shot estimates contain sampling uncertainty even in an ideal simulator. The noisy benchmark therefore records:

- estimated energy;
- propagated finite-shot standard error;
- error relative to the exact classical reference; and
- the explicit noise configuration.

The reported shot uncertainty should not be interpreted as the full uncertainty caused by the noise model. Noise can introduce systematic bias in addition to sampling variance.
