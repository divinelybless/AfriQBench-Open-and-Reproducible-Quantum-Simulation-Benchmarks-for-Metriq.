import numpy as np
import pytest

qiskit = pytest.importorskip("qiskit")

from afriqbench.models.tfim import tfim_hamiltonian
from afriqbench.quantum.qiskit_tfim import (
    bind_ansatz,
    build_hardware_efficient_ansatz,
    circuit_resource_metrics,
    statevector_energy,
    statevector_fidelity,
)
from afriqbench.reference.exact import ground_state


BASELINE_PARAMETERS = np.array(
    [
        0.292792927,
        -0.0000282104047,
        -0.100168525,
        -0.100168480,
        -0.292808429,
        -0.518628570,
        -0.562315096,
        -0.518620523,
    ]
)


def test_ansatz_resource_counts():
    circuit, parameters = build_hardware_efficient_ansatz(4, reps=2)
    metrics = circuit_resource_metrics(circuit)

    assert len(parameters) == 8
    assert metrics["n_qubits"] == 4
    assert metrics["two_qubit_gate_count"] == 6


def test_n4_variational_baseline_matches_reference():
    circuit = bind_ansatz(4, BASELINE_PARAMETERS, reps=2)
    energy = statevector_energy(circuit, 4, J=1.0, h=1.0)

    H = tfim_hamiltonian(4, J=1.0, h=1.0, periodic=False)
    exact_energy, exact_state = ground_state(H)
    fidelity = statevector_fidelity(circuit, exact_state)

    assert energy == pytest.approx(-4.7575478600, abs=1e-8)
    assert abs(energy - exact_energy) < 0.002
    assert fidelity > 0.999
