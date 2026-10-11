"""Fixed four-qubit TFIM exam used by every hardware scorecard."""

from __future__ import annotations

from typing import Any

N_QUBITS = 4
J = 1.0
H_FIELD = 1.0
REPS = 2
PERIODIC = False
CANONICAL_SHOTS = 20_000
OPTIMIZATION_LEVEL = 1

EXACT_ENERGY = -4.758770483143628
ANSATZ_ENERGY = -4.757547860047003
BASELINE_PARAMETERS = (
    0.292792927,
    -0.0000282104047,
    -0.100168525,
    -0.100168480,
    -0.292808429,
    -0.518628570,
    -0.562315096,
    -0.518620523,
)


def measurement_specs(
    n_qubits: int = N_QUBITS,
    coupling: float = J,
    field: float = H_FIELD,
    periodic: bool = PERIODIC,
) -> list[dict[str, Any]]:
    """Return the ZZ and X measurement terms used by the energy estimator."""
    specs: list[dict[str, Any]] = []
    pairs = [(i, i + 1) for i in range(n_qubits - 1)]
    if periodic and n_qubits > 2:
        pairs.append((n_qubits - 1, 0))

    for left, right in pairs:
        specs.append(
            {
                "term": f"Z{left}Z{right}",
                "qubits": [left, right],
                "basis": "Z",
                "coefficient": -float(coupling),
            }
        )

    for qubit in range(n_qubits):
        specs.append(
            {
                "term": f"X{qubit}",
                "qubits": [qubit],
                "basis": "X",
                "coefficient": -float(field),
            }
        )
    return specs


def attach_measurement(circuit, spec: dict[str, Any]):
    """Copy a state-preparation circuit and measure one Hamiltonian term."""
    measurement = circuit.copy()
    if spec["basis"] == "X":
        measurement.h(int(spec["qubits"][0]))
    elif spec["basis"] != "Z":
        raise ValueError(f"Unsupported measurement basis {spec['basis']}")
    measurement.measure_all()
    return measurement
