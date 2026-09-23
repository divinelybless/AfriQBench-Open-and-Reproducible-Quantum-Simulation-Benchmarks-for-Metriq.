"""Mitiq zero-noise extrapolation utilities for AfriQBench."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from afriqbench.quantum.qiskit_tfim import circuit_resource_metrics


def _require_mitiq():
    try:
        from mitiq.zne import combine_results, construct_circuits
        from mitiq.zne.inference import LinearFactory
        from mitiq.zne.scaling import fold_global
    except ImportError as exc:
        raise ImportError(
            "Mitiq mitigation support requires the optional 'mitigation' dependencies. "
            "Use Python 3.11 or 3.12 and install with: "
            "pip install -e \".[quantum,mitigation]\""
        ) from exc

    return construct_circuits, combine_results, LinearFactory, fold_global


def construct_global_zne_circuits(
    circuit,
    scale_factors: Sequence[float] = (1.0, 2.0, 3.0),
):
    """Construct globally folded circuits using Mitiq.

    The input circuit is returned in the same frontend type when supported by
    Mitiq. AfriQBench uses bound Qiskit circuits for the TFIM benchmark.
    """
    construct_circuits, _, _, fold_global = _require_mitiq()

    factors = [float(value) for value in scale_factors]
    if len(factors) < 2:
        raise ValueError("ZNE requires at least two noise scale factors")
    if factors[0] != 1.0:
        raise ValueError("The first ZNE scale factor must be 1.0")
    if any(value < 1.0 for value in factors):
        raise ValueError("All ZNE scale factors must be >= 1.0")
    if factors != sorted(factors):
        raise ValueError("ZNE scale factors must be sorted in ascending order")

    return construct_circuits(
        circuit=circuit,
        scale_factors=factors,
        scale_method=fold_global,
    )


def _linear_extrapolate(
    scale_factors: Sequence[float],
    values: Sequence[float],
) -> tuple[float, float | None, list[float] | None]:
    """Apply Mitiq's LinearFactory and return diagnostics."""
    _, combine_results, LinearFactory, _ = _require_mitiq()

    factors = [float(value) for value in scale_factors]
    energies = [float(value) for value in values]

    factory = LinearFactory(scale_factors=factors)
    mitigated = float(
        combine_results(
            factors,
            energies,
            LinearFactory.extrapolate,
        )
    )

    # Populate a factory as well so fit diagnostics are available.
    for scale_factor, energy in zip(factors, energies, strict=True):
        factory.push({"scale_factor": scale_factor}, energy)

    factory_result = float(factory.reduce())

    # Both paths use the same LinearFactory implementation. Keep a sanity
    # check rather than silently returning inconsistent extrapolations.
    if abs(factory_result - mitigated) > 1e-10:
        raise RuntimeError("Inconsistent Mitiq linear-extrapolation results")

    try:
        fit_error: float | None = float(factory.get_zero_noise_limit_error())
    except ValueError:
        fit_error = None

    try:
        parameters: list[float] | None = [
            float(value) for value in factory.get_optimal_parameters()
        ]
    except ValueError:
        parameters = None

    return mitigated, fit_error, parameters


def mitigation_quality(
    unmitigated_energy: float,
    mitigated_energy: float,
    exact_energy: float,
) -> dict[str, Any]:
    """Compare unmitigated and mitigated estimates against an exact reference."""
    raw_error = abs(float(unmitigated_energy) - float(exact_energy))
    mitigated_error = abs(float(mitigated_energy) - float(exact_energy))

    if mitigated_error > 0.0:
        improvement_factor = raw_error / mitigated_error
    elif raw_error > 0.0:
        improvement_factor = float("inf")
    else:
        improvement_factor = 1.0

    return {
        "unmitigated_absolute_error": float(raw_error),
        "mitigated_absolute_error": float(mitigated_error),
        "absolute_error_reduction": float(raw_error - mitigated_error),
        "improvement_factor": float(improvement_factor),
        "mitigation_success": bool(mitigated_error < raw_error),
    }


def zne_cost_summary(
    scaled_circuits: Sequence[Any],
    n_qubits: int,
    shots_per_term: int,
    periodic: bool = False,
) -> dict[str, Any]:
    """Summarize shot and logical-circuit overhead for a ZNE experiment."""
    if shots_per_term < 1:
        raise ValueError("shots_per_term must be positive")
    if not scaled_circuits:
        raise ValueError("scaled_circuits must not be empty")

    zz_terms = n_qubits if periodic and n_qubits > 2 else n_qubits - 1
    hamiltonian_terms = zz_terms + n_qubits

    resources = [circuit_resource_metrics(circuit) for circuit in scaled_circuits]
    baseline_size = max(resources[0]["size"], 1)

    baseline_shots = hamiltonian_terms * int(shots_per_term)
    zne_shots = baseline_shots * len(scaled_circuits)

    return {
        "hamiltonian_term_count": int(hamiltonian_terms),
        "number_of_scale_factors": int(len(scaled_circuits)),
        "baseline_total_shots": int(baseline_shots),
        "zne_total_shots": int(zne_shots),
        "shot_overhead_factor": float(zne_shots / baseline_shots),
        "scaled_circuit_resources": resources,
        "logical_operation_overhead_factor": float(
            sum(item["size"] for item in resources) / baseline_size
        ),
    }


def run_zne_energy_experiment(
    circuit,
    executor: Callable[[Any], float],
    *,
    exact_energy: float | None = None,
    scale_factors: Sequence[float] = (1.0, 2.0, 3.0),
    n_qubits: int | None = None,
    shots_per_term: int | None = None,
    periodic: bool = False,
) -> dict[str, Any]:
    """Run transparent two-stage Mitiq ZNE for a scalar energy executor.

    The executor must accept a circuit and return one scalar Hamiltonian-energy
    estimate. For AfriQBench, the executor normally wraps the existing
    controlled-noise or device-derived TFIM finite-shot estimators.
    """
    factors = [float(value) for value in scale_factors]
    scaled_circuits = construct_global_zne_circuits(circuit, factors)

    energies = [float(executor(scaled)) for scaled in scaled_circuits]
    mitigated, fit_error, fit_parameters = _linear_extrapolate(factors, energies)

    result: dict[str, Any] = {
        "method": "Mitiq ZNE",
        "scaling_method": "global_unitary_folding",
        "extrapolation_method": "linear",
        "scale_factors": factors,
        "scaled_energies": energies,
        "unmitigated_energy": float(energies[0]),
        "mitigated_energy": float(mitigated),
        "fit_error": fit_error,
        "fit_parameters": fit_parameters,
    }

    if exact_energy is not None:
        result["quality"] = mitigation_quality(
            unmitigated_energy=energies[0],
            mitigated_energy=mitigated,
            exact_energy=float(exact_energy),
        )

    if n_qubits is not None and shots_per_term is not None:
        result["cost"] = zne_cost_summary(
            scaled_circuits=scaled_circuits,
            n_qubits=int(n_qubits),
            shots_per_term=int(shots_per_term),
            periodic=periodic,
        )

    return result
