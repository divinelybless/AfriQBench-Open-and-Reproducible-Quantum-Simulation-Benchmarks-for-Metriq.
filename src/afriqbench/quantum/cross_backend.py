"""Cross-backend execution helpers for AfriQBench.

This module intentionally mirrors the public local-device mechanism used by
metriq-gym: cached IBM fake backends from qiskit-ibm-runtime are converted to
Qiskit Aer simulators using AerSimulator.from_backend(...).
"""

from __future__ import annotations

from typing import Any

from afriqbench.quantum.qiskit_tfim import (
    circuit_resource_metrics,
    estimate_tfim_energy_aer,
    estimate_tfim_energy_backend,
)


def _backend_name(backend) -> str:
    name = getattr(backend, "name", None)
    if callable(name):
        name = name()
    if not isinstance(name, str):
        raise TypeError("Backend does not expose a string name")
    return name


def normalize_fake_device_id(device_id: str) -> str:
    """Normalize IBM/fake backend aliases to the cached fake-backend form."""
    normalized = device_id.strip().lower().replace("-", "_")

    if normalized.startswith("fake_"):
        return normalized
    if normalized.startswith("ibm_"):
        return f"fake_{normalized.removeprefix('ibm_')}"
    return f"fake_{normalized}"


def available_fake_backend_names() -> list[str]:
    """Return cached fake backend names provided by qiskit-ibm-runtime."""
    try:
        from qiskit_ibm_runtime.fake_provider import FakeProviderForBackendV2
    except ImportError as exc:
        raise ImportError(
            "Device-derived local noise requires qiskit-ibm-runtime. "
            "Install with: pip install -e \".[quantum]\""
        ) from exc

    names = []
    for backend in FakeProviderForBackendV2().backends():
        try:
            names.append(_backend_name(backend).lower().replace("-", "_"))
        except TypeError:
            continue
    return sorted(set(names))


def load_fake_backend(device_id: str = "fake_manila"):
    """Load a cached fake backend by normalized alias.

    Examples accepted:
        fake_manila
        ibm_manila
        ibm-manila
        manila
    """
    try:
        from qiskit_ibm_runtime.fake_provider import FakeProviderForBackendV2
    except ImportError as exc:
        raise ImportError(
            "Device-derived local noise requires qiskit-ibm-runtime. "
            "Install with: pip install -e \".[quantum]\""
        ) from exc

    target = normalize_fake_device_id(device_id)

    for backend in FakeProviderForBackendV2().backends():
        try:
            name = _backend_name(backend).lower().replace("-", "_")
        except TypeError:
            continue

        if name == target:
            return backend

    available = available_fake_backend_names()
    preview = ", ".join(available[:12])
    raise ValueError(
        f"Unknown cached fake backend '{device_id}' (normalized to '{target}'). "
        f"Examples available in this installation: {preview}"
    )


def make_device_derived_aer_backend(device_id: str = "fake_manila"):
    """Create an Aer simulator from a cached fake IBM backend snapshot."""
    try:
        from qiskit_aer import AerSimulator
    except ImportError as exc:
        raise ImportError(
            "Device-derived local noise requires qiskit-aer. "
            "Install with: pip install -e \".[quantum]\""
        ) from exc

    fake_backend = load_fake_backend(device_id)
    aer_backend = AerSimulator.from_backend(fake_backend)

    metadata = {
        "requested_device": device_id,
        "resolved_fake_backend": _backend_name(fake_backend),
        "num_qubits": int(getattr(fake_backend, "num_qubits", 0)),
        "backend_version": str(getattr(fake_backend, "backend_version", "unknown")),
        "simulation_method": "AerSimulator.from_backend",
        "source": "qiskit_ibm_runtime.fake_provider",
    }
    return aer_backend, metadata


def transpiled_resource_metrics(
    circuit,
    backend,
    seed: int = 12345,
    optimization_level: int = 1,
) -> dict[str, Any]:
    """Return post-transpilation circuit metrics for a target backend."""
    try:
        from qiskit import transpile
    except ImportError as exc:
        raise ImportError(
            "Transpilation requires Qiskit. Install with: pip install -e \".[quantum]\""
        ) from exc

    compiled = transpile(
        circuit,
        backend,
        seed_transpiler=seed,
        optimization_level=optimization_level,
    )
    metrics = circuit_resource_metrics(compiled)
    metrics["optimization_level"] = int(optimization_level)
    metrics["seed_transpiler"] = int(seed)
    return metrics


def estimate_tfim_energy_device_derived_aer(
    circuit,
    n_qubits: int,
    J: float = 1.0,
    h: float = 1.0,
    periodic: bool = False,
    shots: int = 20_000,
    seed: int = 12345,
    device_id: str = "fake_manila",
    optimization_level: int = 1,
) -> dict[str, Any]:
    """Estimate TFIM energy using a cached device-derived Aer noise model."""
    backend, metadata = make_device_derived_aer_backend(device_id)

    result = estimate_tfim_energy_backend(
        circuit=circuit,
        backend=backend,
        n_qubits=n_qubits,
        J=J,
        h=h,
        periodic=periodic,
        shots=shots,
        seed=seed,
        optimization_level=optimization_level,
    )
    result["backend"] = "aer_simulator_from_fake_backend"
    result["device_metadata"] = metadata
    result["transpiled_resources"] = transpiled_resource_metrics(
        circuit,
        backend,
        seed=seed,
        optimization_level=optimization_level,
    )
    return result


def run_cross_backend_comparison(
    circuit,
    n_qubits: int,
    J: float = 1.0,
    h: float = 1.0,
    periodic: bool = False,
    shots: int = 20_000,
    seed: int = 12345,
    device_id: str = "fake_manila",
    controlled_single_qubit_error: float = 0.001,
    controlled_two_qubit_error: float = 0.01,
    controlled_readout_error: float = 0.01,
) -> dict[str, Any]:
    """Run the canonical local three-way AfriQBench comparison."""
    from afriqbench.quantum.noise import estimate_tfim_energy_noisy_aer

    ideal = estimate_tfim_energy_aer(
        circuit,
        n_qubits=n_qubits,
        J=J,
        h=h,
        periodic=periodic,
        shots=shots,
        seed=seed,
    )

    controlled = estimate_tfim_energy_noisy_aer(
        circuit,
        n_qubits=n_qubits,
        J=J,
        h=h,
        periodic=periodic,
        shots=shots,
        seed=seed,
        single_qubit_error=controlled_single_qubit_error,
        two_qubit_error=controlled_two_qubit_error,
        readout_error=controlled_readout_error,
    )

    device_derived = estimate_tfim_energy_device_derived_aer(
        circuit,
        n_qubits=n_qubits,
        J=J,
        h=h,
        periodic=periodic,
        shots=shots,
        seed=seed,
        device_id=device_id,
        optimization_level=1,
    )

    return {
        "ideal_aer": ideal,
        "controlled_noise_aer": controlled,
        "device_derived_aer": device_derived,
    }
