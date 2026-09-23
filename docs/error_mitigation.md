# Mitiq Error Mitigation

AfriQBench treats error mitigation as a **companion analysis**, not as part of the canonical raw benchmark score.

## Method

Notebook 05 uses zero-noise extrapolation (ZNE) with Mitiq.

The default MVP protocol is:

- global unitary folding;
- noise scale factors `[1.0, 2.0, 3.0]`;
- linear extrapolation to the zero-noise limit;
- the same TFIM state, Hamiltonian, shot budget, and base noise model used by the unmitigated benchmark.

The workflow is intentionally two-stage:

```text
base circuit
    ↓
Mitiq noise-scaled circuits
    ↓
execute every scaled circuit
    ↓
energies at λ = 1, 2, 3
    ↓
linear zero-noise extrapolation
    ↓
mitigated energy
```

Using Mitiq's two-stage API keeps the scaled circuits and intermediate measurements visible.

## Why linear extrapolation?

Higher-order Richardson extrapolation can be useful, but finite-shot data can make higher-order fits unstable. The MVP therefore starts with a linear model as a transparent baseline. The extrapolation method can later become a benchmark parameter rather than silently changing the canonical workflow.

## Success metric

AfriQBench does not assume that mitigation improves a result.

For exact reference energy (E_{exact}), raw energy (E_{raw}), and mitigated energy (E_{mit}),

[
\epsilon_{raw}=|E_{raw}-E_{exact}|,
]

[
\epsilon_{mit}=|E_{mit}-E_{exact}|.
]

The improvement factor is

[
G = \frac{\epsilon_{raw}}{\epsilon_{mit}}.
]

Interpretation:

- (G>1): mitigation improved the estimate;
- (G=1): no change;
- (G<1): mitigation made the estimate worse.

This avoids presenting ZNE as automatically beneficial.

## Cost accounting

For the open (N=4) TFIM,

- 3 nearest-neighbour (ZZ) terms;
- 4 transverse (X) terms;
- 7 Hamiltonian terms total.

At 20,000 shots per term, one unmitigated energy estimate uses

[
7 \times 20,000 = 140,000
]

shots.

With three ZNE scale factors, the measurement budget becomes

[
3 \times 140,000 = 420,000
]

shots, before accounting for the extra gates introduced by folding.

AfriQBench therefore reports both:

- shot-overhead factor; and
- logical-operation-overhead factor.

## Uncertainty

The extrapolation fit error produced by a linear factory is not the same as the full physical uncertainty of the mitigated result. Sampling uncertainty, extrapolation-model error, calibration drift, and model mismatch can all contribute.

The repository therefore labels fit diagnostics explicitly rather than interpreting them as a complete error bar.

## Environment

The current Mitiq 1.1 series supports Python 3.11–3.12. The AfriQBench mitigation CI job therefore runs on Python 3.12, independently of the broader core package support.
