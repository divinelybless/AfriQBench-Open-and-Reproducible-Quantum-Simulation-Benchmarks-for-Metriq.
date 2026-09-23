"""Controlled Qiskit Aer noise models for AfriQBench."""

from __future__ import annotations

from typing import Any

from afriqbench.quantum.qiskit_tfim import estimate_tfim_energy_backend


def build_controlled_noise_model(
    single_qubit_error: float = 0.001,
    two_qubit_error: float = 0.01,
    readout_error: float = 0.01,
):
    """Build a transparent synthetic noise model for TFIM benchmarking.

    The model contains:
    - depolarizing noise on H and RY gates;
    - depolarizing noise on CX gates; and
    - symmetric independent readout error on every measured qubit.

    This is a controlled benchmark model, not a calibrated hardware model.
    """
    try:
        from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error
    except ImportError as exc:
        raise ImportError(
            "Controlled noisy simulation requires qiskit-aer. "
            "Install with: pip install -e \".[quantum]\""
        ) from exc

    for name, value in {
        "single_qubit_error": single_qubit_error,
        "two_qubit_error": two_qubit_error,
        "readout_error": readout_error,
    }.items():
        if not 0.0 <= float(value) < 1.0:
            raise ValueError(f"{name} must satisfy 0 <= value < 1")

    noise_model = NoiseModel()

    if single_qubit_error > 0:
        one_qubit = depolarizing_error(float(single_qubit_error), 1)
        noise_model.add_all_qubit_quantum_error(one_qubit, ["h", "ry"])

    if two_qubit_error > 0:
        two_qubit = depolarizing_error(float(two_qubit_error), 2)
        noise_model.add_all_qubit_quantum_error(two_qubit, ["cx"])

    if readout_error > 0:
        p = float(readout_error)
        readout = ReadoutError([[1.0 - p, p], [p, 1.0 - p]])
        noise_model.add_all_qubit_readout_error(readout)

    return noise_model


def estimate_tfim_energy_noisy_aer(
    circuit,
    n_qubits: int,
    J: float = 1.0,
    h: float = 1.0,
    periodic: bool = False,
    shots: int = 20_000,
    seed: int = 12345,
    single_qubit_error: float = 0.001,
    two_qubit_error: float = 0.01,
    readout_error: float = 0.01,
) -> dict[str, Any]:
    """Estimate the TFIM energy under the controlled Aer noise model."""
    try:
        from qiskit_aer import AerSimulator
    except ImportError as exc:
        raise ImportError(
            "Controlled noisy simulation requires qiskit-aer. "
            "Install with: pip install -e \".[quantum]\""
        ) from exc

    noise_model = build_controlled_noise_model(
        single_qubit_error=single_qubit_error,
        two_qubit_error=two_qubit_error,
        readout_error=readout_error,
    )
    backend = AerSimulator(noise_model=noise_model)

    result = estimate_tfim_energy_backend(
        circuit=circuit,
        backend=backend,
        n_qubits=n_qubits,
        J=J,
        h=h,
        periodic=periodic,
        shots=shots,
        seed=seed,
        optimization_level=0,
    )

    result["backend"] = "aer_simulator_controlled_noise"
    result["noise_model"] = {
        "type": "synthetic_controlled",
        "single_qubit_depolarizing": float(single_qubit_error),
        "two_qubit_depolarizing": float(two_qubit_error),
        "symmetric_readout": float(readout_error),
    }
    return result
