"""Local check of the fixed circuit before any IBM job is submitted."""

from __future__ import annotations

from typing import Any

from afriqbench.quantum.hardware.scorecard import build_scorecard
from afriqbench.quantum.hardware.workload import (
    ANSATZ_ENERGY,
    BASELINE_PARAMETERS,
    EXACT_ENERGY,
    H_FIELD,
    J,
    N_QUBITS,
    PERIODIC,
    REPS,
    attach_measurement,
    measurement_specs,
)


def run_local_preflight() -> dict[str, Any]:
    """Check the fixed circuit against the stored answer keys, with no IBM call."""
    from afriqbench.models.tfim import tfim_hamiltonian
    from afriqbench.quantum.qiskit_tfim import (
        bind_ansatz,
        circuit_resource_metrics,
        statevector_energy,
        statevector_fidelity,
    )
    from afriqbench.reference.exact import ground_state

    circuit = bind_ansatz(N_QUBITS, BASELINE_PARAMETERS, reps=REPS)
    measured = statevector_energy(
        circuit,
        N_QUBITS,
        J=J,
        h=H_FIELD,
        periodic=PERIODIC,
    )
    hamiltonian = tfim_hamiltonian(N_QUBITS, J=J, h=H_FIELD, periodic=PERIODIC)
    exact_energy, exact_state = ground_state(hamiltonian)
    if abs(exact_energy - EXACT_ENERGY) > 1e-9:
        raise RuntimeError(
            "The exact solver no longer matches the stored reference "
            f"{EXACT_ENERGY}."
        )
    if abs(measured - ANSATZ_ENERGY) > 1e-8:
        raise RuntimeError(
            "The fixed circuit energy no longer matches the stored ideal "
            f"circuit value {ANSATZ_ENERGY}."
        )

    fidelity = statevector_fidelity(circuit, exact_state)
    raw_resources = circuit_resource_metrics(circuit)
    terms = []
    for spec in measurement_specs():
        resources = circuit_resource_metrics(attach_measurement(circuit, spec))
        terms.append(
            {
                "term": spec["term"],
                "basis": spec["basis"],
                "coefficient": spec["coefficient"],
                "qubits": spec["qubits"],
                "depth": resources["depth"],
                "two_qubit_gate_count": resources["two_qubit_gate_count"],
                "size": resources["size"],
                "operation_counts": resources["operation_counts"],
            }
        )

    return build_scorecard(
        energy=measured,
        uncertainty=None,
        shots_per_term=None,
        terms=terms,
        mode="local_preflight",
        backend="statevector",
        fidelity=fidelity,
        raw_resources=raw_resources,
    )
