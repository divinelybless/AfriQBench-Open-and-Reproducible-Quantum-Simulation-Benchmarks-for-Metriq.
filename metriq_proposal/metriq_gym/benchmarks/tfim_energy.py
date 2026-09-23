"""Proposed TFIM Energy benchmark for upstream Metriq-Gym.

This file is intentionally written against the current Metriq-Gym Benchmark,
BenchmarkData, BenchmarkResult, JSON-schema, and CircuitBatch conventions.

Benchmark definition:
    - Four-qubit open transverse-field Ising model.
    - J = 1 and h = 1.
    - Fixed two-layer AfriQBench RY/CX variational ansatz.
    - Seven independently measured Hamiltonian terms:
        3 nearest-neighbour ZZ terms + 4 X terms.
    - Reports measured energy with propagated finite-shot uncertainty.
    - Separates execution error from end-to-end application error.

The raw benchmark is intentionally unmitigated. Mitiq error mitigation remains
a companion analysis rather than part of the canonical score.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import TYPE_CHECKING, Any

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp, Statevector

from metriq_gym.benchmarks.benchmark import (
    Benchmark,
    BenchmarkData,
    BenchmarkResult,
    BenchmarkScore,
)
from metriq_gym.helpers.task_helpers import flatten_counts
from metriq_gym.qplatform.device import validate_qubit_capacity
from metriq_gym.resource_estimation import CircuitBatch, count_two_qubit_gates

if TYPE_CHECKING:
    from qbraid import GateModelResultData, QuantumDevice, QuantumJob
    from qbraid.runtime.result_data import MeasCount


TFIM_NUM_QUBITS = 4
TFIM_J = 1.0
TFIM_H = 1.0
TFIM_REPS = 2

# Fixed reproducible development baseline from the AfriQBench two-layer ansatz.
TFIM_PARAMETERS = (
    0.292792927,
    -0.0000282104047,
    -0.100168525,
    -0.100168480,
    -0.292808429,
    -0.518628570,
    -0.562315096,
    -0.518620523,
)


def _pauli_label(n_qubits: int, operators: dict[int, str]) -> str:
    """Build a Qiskit Pauli label from qubit-indexed operators."""
    label = ["I"] * n_qubits
    for qubit, symbol in operators.items():
        label[n_qubits - 1 - qubit] = symbol
    return "".join(label)


def tfim_operator(
    n_qubits: int = TFIM_NUM_QUBITS,
    coupling_j: float = TFIM_J,
    field_h: float = TFIM_H,
) -> SparsePauliOp:
    """Return the open-chain TFIM Hamiltonian.

    H = -J sum_i Z_i Z_(i+1) - h sum_i X_i
    """
    terms: list[tuple[str, complex]] = []

    for qubit in range(n_qubits - 1):
        terms.append(
            (
                _pauli_label(
                    n_qubits,
                    {qubit: "Z", qubit + 1: "Z"},
                ),
                -float(coupling_j),
            )
        )

    for qubit in range(n_qubits):
        terms.append(
            (
                _pauli_label(n_qubits, {qubit: "X"}),
                -float(field_h),
            )
        )

    return SparsePauliOp.from_list(terms)


def tfim_ansatz() -> QuantumCircuit:
    """Return the fixed four-qubit AfriQBench state-preparation circuit."""
    circuit = QuantumCircuit(TFIM_NUM_QUBITS, name="tfim_energy_ansatz")
    circuit.h(range(TFIM_NUM_QUBITS))

    parameter_index = 0
    for _ in range(TFIM_REPS):
        for qubit in range(TFIM_NUM_QUBITS):
            circuit.ry(TFIM_PARAMETERS[parameter_index], qubit)
            parameter_index += 1

        for qubit in range(TFIM_NUM_QUBITS - 1):
            circuit.cx(qubit, qubit + 1)

    return circuit


def reference_energies() -> tuple[float, float]:
    """Return exact ground-state and ideal ansatz energies."""
    operator = tfim_operator()

    exact_ground_energy = float(
        np.min(np.linalg.eigvalsh(operator.to_matrix())).real
    )

    state = Statevector.from_instruction(tfim_ansatz())
    ideal_variational_energy = float(
        np.real(state.expectation_value(operator))
    )

    return exact_ground_energy, ideal_variational_energy


def build_measurement_circuits() -> tuple[
    list[QuantumCircuit],
    list[str],
    list[float],
    list[list[int]],
]:
    """Build one measurement circuit per Hamiltonian term.

    Ordering is fixed and stored in TFIMEnergyData so poll-time reconstruction
    is independent of provider batching behavior.
    """
    base = tfim_ansatz()

    circuits: list[QuantumCircuit] = []
    labels: list[str] = []
    coefficients: list[float] = []
    measured_qubits: list[list[int]] = []

    for qubit in range(TFIM_NUM_QUBITS - 1):
        circuit = base.copy()
        circuit.measure_all()

        circuits.append(circuit)
        labels.append(f"Z{qubit}Z{qubit + 1}")
        coefficients.append(-TFIM_J)
        measured_qubits.append([qubit, qubit + 1])

    for qubit in range(TFIM_NUM_QUBITS):
        circuit = base.copy()
        circuit.h(qubit)
        circuit.measure_all()

        circuits.append(circuit)
        labels.append(f"X{qubit}")
        coefficients.append(-TFIM_H)
        measured_qubits.append([qubit])

    return circuits, labels, coefficients, measured_qubits


def pauli_expectation_from_counts(
    counts: "MeasCount | dict[str, int]",
    measured_qubits: list[int],
) -> tuple[float, float]:
    """Estimate a Pauli-string expectation and its finite-shot standard error.

    Because each measured Pauli product has eigenvalues +/-1,

        Var(mean) = (1 - <P>^2) / N.

    Qiskit count strings are reversed so string index q matches qubit q.
    """
    total = int(sum(counts.values()))
    if total <= 0:
        raise ValueError("Measurement counts must contain at least one shot.")

    weighted_sum = 0.0

    for bitstring, count in counts.items():
        bits = str(bitstring).replace(" ", "")[::-1]

        if max(measured_qubits) >= len(bits):
            raise ValueError(
                f"Count bitstring '{bitstring}' is too short for "
                f"measured qubits {measured_qubits}."
            )

        parity = sum(int(bits[qubit]) for qubit in measured_qubits) % 2
        eigenvalue = -1.0 if parity else 1.0
        weighted_sum += eigenvalue * int(count)

    expectation = weighted_sum / total
    uncertainty = sqrt(max(0.0, 1.0 - expectation**2) / total)

    return float(expectation), float(uncertainty)


class TFIMEnergyResult(BenchmarkResult):
    """Metrics reported by the proposed TFIM application benchmark."""

    energy: BenchmarkScore
    execution_energy_error: float
    application_energy_error: float
    relative_application_energy_error: float
    normalized_energy_accuracy: BenchmarkScore

    def compute_score(self) -> BenchmarkScore:
        """Use normalized end-to-end energy accuracy as the scalar score."""
        return self.normalized_energy_accuracy


@dataclass
class TFIMEnergyData(BenchmarkData):
    """Dispatch-time metadata needed to reconstruct the Hamiltonian energy."""

    shots: int
    exact_ground_energy: float
    ideal_variational_energy: float
    term_labels: list[str]
    term_coefficients: list[float]
    measured_qubits: list[list[int]]


def analyze_tfim_counts(
    data: TFIMEnergyData,
    counts_list: list["MeasCount | dict[str, int]"],
) -> TFIMEnergyResult:
    """Reconstruct the TFIM energy and benchmark metrics from term counts."""
    expected_terms = len(data.term_labels)

    if len(counts_list) != expected_terms:
        raise ValueError(
            f"Expected {expected_terms} Hamiltonian-term count sets, "
            f"received {len(counts_list)}."
        )

    energy = 0.0
    energy_variance = 0.0

    for counts, coefficient, qubits in zip(
        counts_list,
        data.term_coefficients,
        data.measured_qubits,
        strict=True,
    ):
        expectation, uncertainty = pauli_expectation_from_counts(
            counts,
            qubits,
        )
        energy += coefficient * expectation
        energy_variance += (coefficient * uncertainty) ** 2

    energy_uncertainty = sqrt(energy_variance)

    execution_error = abs(energy - data.ideal_variational_energy)
    application_error = abs(energy - data.exact_ground_energy)
    energy_scale = abs(data.exact_ground_energy)

    relative_application_error = (
        application_error / energy_scale if energy_scale > 0.0 else 0.0
    )

    normalized_accuracy = max(
        0.0,
        min(1.0, 1.0 - relative_application_error),
    )
    normalized_uncertainty = (
        energy_uncertainty / energy_scale if energy_scale > 0.0 else 0.0
    )

    return TFIMEnergyResult(
        energy=BenchmarkScore(
            value=float(energy),
            uncertainty=float(energy_uncertainty),
        ),
        execution_energy_error=float(execution_error),
        application_energy_error=float(application_error),
        relative_application_energy_error=float(relative_application_error),
        normalized_energy_accuracy=BenchmarkScore(
            value=float(normalized_accuracy),
            uncertainty=float(normalized_uncertainty),
        ),
    )


class TFIMEnergy(Benchmark):
    """Four-qubit TFIM application-level energy benchmark."""

    def _build_circuits(
        self,
        device: "QuantumDevice",
    ) -> tuple[
        list[QuantumCircuit],
        list[str],
        list[float],
        list[list[int]],
    ]:
        validate_qubit_capacity(device, TFIM_NUM_QUBITS)
        return build_measurement_circuits()

    def dispatch_handler(self, device: "QuantumDevice") -> TFIMEnergyData:
        circuits, labels, coefficients, measured_qubits = self._build_circuits(
            device
        )
        exact_energy, ideal_energy = reference_energies()

        two_qubit_counts = [
            count_two_qubit_gates(circuit)
            for circuit in circuits
        ]

        return TFIMEnergyData.from_quantum_job(
            quantum_job=device.run(
                circuits,
                shots=self.params.shots,
            ),
            input_two_qubit_gate_counts=two_qubit_counts,
            transpiled_two_qubit_gate_counts=two_qubit_counts,
            shots=self.params.shots,
            exact_ground_energy=exact_energy,
            ideal_variational_energy=ideal_energy,
            term_labels=labels,
            term_coefficients=coefficients,
            measured_qubits=measured_qubits,
        )

    def poll_handler(
        self,
        job_data: TFIMEnergyData,
        result_data: list["GateModelResultData"],
        quantum_jobs: list["QuantumJob"],
    ) -> TFIMEnergyResult:
        del quantum_jobs  # Results are fully determined by measurement data.
        return analyze_tfim_counts(
            job_data,
            flatten_counts(result_data),
        )

    def estimate_resources_handler(
        self,
        device: "QuantumDevice",
    ) -> list[CircuitBatch]:
        circuits, _, _, _ = self._build_circuits(device)
        return [
            CircuitBatch(
                circuits=circuits,
                shots=self.params.shots,
            )
        ]
