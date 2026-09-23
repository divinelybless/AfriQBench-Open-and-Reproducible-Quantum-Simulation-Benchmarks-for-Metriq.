"""Qiskit utilities for the TFIM quantum benchmark."""

from __future__ import annotations

from math import sqrt
from typing import Any

import numpy as np


def _require_qiskit():
    try:
        from qiskit import QuantumCircuit, transpile
        from qiskit.circuit import ParameterVector
        from qiskit.quantum_info import SparsePauliOp, Statevector
    except ImportError as exc:
        raise ImportError(
            "Quantum benchmark support requires the optional 'quantum' dependencies. "
            "Install with: pip install -e \".[quantum]\""
        ) from exc

    return QuantumCircuit, transpile, ParameterVector, SparsePauliOp, Statevector


def _pauli_label(n_qubits: int, operators: dict[int, str]) -> str:
    """Build a Qiskit Pauli label from qubit-indexed single-qubit operators.

    Qiskit Pauli strings are written with qubit 0 at the right-hand side.
    """
    label = ["I"] * n_qubits
    for qubit, symbol in operators.items():
        label[n_qubits - 1 - qubit] = symbol
    return "".join(label)


def tfim_pauli_operator(
    n_qubits: int,
    J: float = 1.0,
    h: float = 1.0,
    periodic: bool = False,
):
    """Return the TFIM Hamiltonian as a Qiskit SparsePauliOp."""
    _, _, _, SparsePauliOp, _ = _require_qiskit()

    terms: list[tuple[str, complex]] = []

    for i in range(n_qubits - 1):
        terms.append(
            (_pauli_label(n_qubits, {i: "Z", i + 1: "Z"}), -float(J))
        )

    if periodic and n_qubits > 2:
        terms.append(
            (
                _pauli_label(n_qubits, {n_qubits - 1: "Z", 0: "Z"}),
                -float(J),
            )
        )

    for i in range(n_qubits):
        terms.append((_pauli_label(n_qubits, {i: "X"}), -float(h)))

    return SparsePauliOp.from_list(terms)


def build_hardware_efficient_ansatz(
    n_qubits: int,
    reps: int = 2,
):
    """Build the reproducible AfriQBench TFIM ansatz.

    The circuit starts in |+>^n, then alternates parameterized RY layers
    with a nearest-neighbour CNOT chain.
    """
    QuantumCircuit, _, ParameterVector, _, _ = _require_qiskit()

    if n_qubits < 2:
        raise ValueError("n_qubits must be at least 2")
    if reps < 1:
        raise ValueError("reps must be at least 1")

    parameters = ParameterVector("theta", length=n_qubits * reps)
    circuit = QuantumCircuit(n_qubits, name="afriqbench_tfim_ansatz")

    circuit.h(range(n_qubits))

    for layer in range(reps):
        offset = layer * n_qubits

        for qubit in range(n_qubits):
            circuit.ry(parameters[offset + qubit], qubit)

        for qubit in range(n_qubits - 1):
            circuit.cx(qubit, qubit + 1)

    return circuit, parameters


def bind_ansatz(
    n_qubits: int,
    parameter_values: list[float] | np.ndarray,
    reps: int = 2,
):
    """Return a numerical AfriQBench ansatz circuit."""
    circuit, parameters = build_hardware_efficient_ansatz(n_qubits, reps)
    values = np.asarray(parameter_values, dtype=float)

    if values.size != len(parameters):
        raise ValueError(
            f"Expected {len(parameters)} parameters, received {values.size}"
        )

    mapping = {
        parameter: float(value)
        for parameter, value in zip(parameters, values, strict=True)
    }
    return circuit.assign_parameters(mapping, inplace=False)


def statevector_energy(
    circuit,
    n_qubits: int,
    J: float = 1.0,
    h: float = 1.0,
    periodic: bool = False,
) -> float:
    """Evaluate the TFIM energy exactly for a state-preparation circuit."""
    _, _, _, _, Statevector = _require_qiskit()
    operator = tfim_pauli_operator(n_qubits, J, h, periodic)
    state = Statevector.from_instruction(circuit)
    return float(np.real(state.expectation_value(operator)))


def statevector_fidelity(circuit, reference_state: np.ndarray) -> float:
    """Return fidelity between a circuit state and a reference statevector."""
    _, _, _, _, Statevector = _require_qiskit()
    state = np.asarray(Statevector.from_instruction(circuit).data)
    reference = np.asarray(reference_state, dtype=complex)

    if state.shape != reference.shape:
        raise ValueError("Circuit and reference statevectors have different dimensions")

    return float(abs(np.vdot(reference, state)) ** 2)


def _expectation_from_counts(
    counts: dict[str, int],
    qubits: tuple[int, ...],
) -> tuple[float, float]:
    """Return a Pauli expectation estimate and standard error from counts."""
    total = int(sum(counts.values()))
    if total <= 0:
        raise ValueError("Counts are empty")

    weighted = 0.0

    for bitstring, count in counts.items():
        bits = bitstring.replace(" ", "")[::-1]
        parity = sum(int(bits[q]) for q in qubits) % 2
        eigenvalue = -1.0 if parity else 1.0
        weighted += eigenvalue * count

    expectation = weighted / total
    variance_of_mean = max(0.0, 1.0 - expectation**2) / total
    return expectation, sqrt(variance_of_mean)


def estimate_tfim_energy_backend(
    circuit,
    backend,
    n_qubits: int,
    J: float = 1.0,
    h: float = 1.0,
    periodic: bool = False,
    shots: int = 20_000,
    seed: int = 12345,
    optimization_level: int = 0,
) -> dict[str, Any]:
    """Estimate TFIM energy from finite-shot measurements on a Qiskit backend.

    Each Hamiltonian term is measured independently. A deterministic but
    distinct simulator seed is used for each term to avoid reusing the same
    pseudo-random stream across all observables.
    """
    _, transpile, _, _, _ = _require_qiskit()

    if shots < 1:
        raise ValueError("shots must be positive")

    term_results: list[dict[str, Any]] = []
    energy = 0.0
    energy_variance = 0.0
    term_index = 0

    zz_pairs = [(i, i + 1) for i in range(n_qubits - 1)]
    if periodic and n_qubits > 2:
        zz_pairs.append((n_qubits - 1, 0))

    for i, j in zz_pairs:
        measurement = circuit.copy()
        measurement.measure_all()
        compiled = transpile(
            measurement,
            backend,
            optimization_level=optimization_level,
            seed_transpiler=seed,
        )
        run_seed = seed + term_index
        counts = backend.run(
            compiled,
            shots=shots,
            seed_simulator=run_seed,
        ).result().get_counts()

        value, uncertainty = _expectation_from_counts(counts, (i, j))
        coefficient = -float(J)
        energy += coefficient * value
        energy_variance += (coefficient * uncertainty) ** 2

        term_results.append(
            {
                "term": f"Z{i}Z{j}",
                "coefficient": coefficient,
                "expectation": value,
                "uncertainty": uncertainty,
                "seed": run_seed,
            }
        )
        term_index += 1

    for i in range(n_qubits):
        measurement = circuit.copy()
        measurement.h(i)
        measurement.measure_all()
        compiled = transpile(
            measurement,
            backend,
            optimization_level=optimization_level,
            seed_transpiler=seed,
        )
        run_seed = seed + term_index
        counts = backend.run(
            compiled,
            shots=shots,
            seed_simulator=run_seed,
        ).result().get_counts()

        value, uncertainty = _expectation_from_counts(counts, (i,))
        coefficient = -float(h)
        energy += coefficient * value
        energy_variance += (coefficient * uncertainty) ** 2

        term_results.append(
            {
                "term": f"X{i}",
                "coefficient": coefficient,
                "expectation": value,
                "uncertainty": uncertainty,
                "seed": run_seed,
            }
        )
        term_index += 1

    return {
        "energy": float(energy),
        "uncertainty": float(sqrt(energy_variance)),
        "shots_per_term": int(shots),
        "seed": int(seed),
        "optimization_level": int(optimization_level),
        "terms": term_results,
    }


def estimate_tfim_energy_aer(
    circuit,
    n_qubits: int,
    J: float = 1.0,
    h: float = 1.0,
    periodic: bool = False,
    shots: int = 20_000,
    seed: int = 12345,
) -> dict[str, Any]:
    """Estimate TFIM energy with finite-shot measurements on ideal Qiskit Aer."""
    try:
        from qiskit_aer import AerSimulator
    except ImportError as exc:
        raise ImportError(
            "Finite-shot ideal simulation requires qiskit-aer. "
            "Install with: pip install -e \".[quantum]\""
        ) from exc

    backend = AerSimulator()
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
    result["backend"] = "aer_simulator"
    result["noise_model"] = None
    return result


def circuit_resource_metrics(circuit) -> dict[str, Any]:
    """Return provider-independent resource metrics for a circuit."""
    operations = dict(circuit.count_ops())

    return {
        "n_qubits": int(circuit.num_qubits),
        "depth": int(circuit.depth()),
        "size": int(circuit.size()),
        "two_qubit_gate_count": int(
            sum(
                count
                for gate, count in operations.items()
                if gate in {"cx", "cz", "ecr", "rzz", "swap"}
            )
        ),
        "operation_counts": {
            str(gate): int(count)
            for gate, count in operations.items()
        },
    }
