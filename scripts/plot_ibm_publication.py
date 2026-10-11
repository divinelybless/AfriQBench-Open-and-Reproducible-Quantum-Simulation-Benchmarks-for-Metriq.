#!/usr/bin/env python3
"""Publication figures for the ibm_fez TFIM hardware scorecard.

Reads the saved hardware JSON and compares it with the exact ground state
and the ideal fixed circuit. Writes one PDF and one PNG per figure.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from afriqbench.models.tfim import X, Z, _single_site_operator, _two_site_operator, tfim_hamiltonian
from afriqbench.quantum.hardware.workload import BASELINE_PARAMETERS, H_FIELD, J, N_QUBITS, REPS
from afriqbench.quantum.qiskit_tfim import bind_ansatz
from afriqbench.reference.exact import expectation, ground_state

SCORECARD = ROOT / "results/hardware/tfim_n4_h1_ibm_fez_db5ghn84qg6s73c3emu0.json"
OUT = ROOT / "results/publication"

EXACT_COLOR = "#0072B2"
CIRCUIT_COLOR = "#009E73"
HARDWARE_COLOR = "#D55E00"
NEUTRAL = "#333333"


def main() -> None:
    scorecard = json.loads(SCORECARD.read_text())
    terms = scorecard["terms"]
    names = [term["term"] for term in terms]
    exact_values = exact_expectations()
    circuit_values = circuit_expectations()
    hardware = np.array([term["expectation"] for term in terms])
    hardware_sigma = np.array([term["uncertainty"] for term in terms])
    coefficients = np.array([term["coefficient"] for term in terms])

    OUT.mkdir(parents=True, exist_ok=True)
    apply_style()

    energy_comparison(scorecard)
    error_sources(scorecard)
    pauli_expectations(names, exact_values, circuit_values, hardware, hardware_sigma)
    energy_contributions(names, coefficients, exact_values, circuit_values, hardware, hardware_sigma)
    compilation_cost(scorecard, terms)
    depth_curve(scorecard, terms)
    expectation_curve(names, exact_values, circuit_values, hardware, hardware_sigma)
    cumulative_energy_curve(names, coefficients, exact_values, circuit_values, hardware, hardware_sigma)
    running_error_curve(names, coefficients, exact_values, hardware, hardware_sigma)
    print(f"Wrote publication figures to {OUT}")


def exact_expectations() -> np.ndarray:
    hamiltonian = tfim_hamiltonian(N_QUBITS, J=J, h=H_FIELD, periodic=False)
    _, state = ground_state(hamiltonian)
    return np.array([expectation(state, operator(spec)) for spec in measurement_order()])


def circuit_expectations() -> np.ndarray:
    from qiskit.quantum_info import Statevector

    circuit = bind_ansatz(N_QUBITS, BASELINE_PARAMETERS, reps=REPS)
    state = np.asarray(Statevector.from_instruction(circuit).data)
    return np.array([expectation(state, operator(spec)) for spec in measurement_order()])


def measurement_order() -> list[tuple[str, tuple[int, ...]]]:
    return [
        ("ZZ", (0, 1)),
        ("ZZ", (1, 2)),
        ("ZZ", (2, 3)),
        ("X", (0,)),
        ("X", (1,)),
        ("X", (2,)),
        ("X", (3,)),
    ]


def operator(spec: tuple[str, tuple[int, ...]]):
    kind, qubits = spec
    if kind == "ZZ":
        return _two_site_operator(N_QUBITS, qubits[0], qubits[1], Z, Z)
    return _single_site_operator(N_QUBITS, qubits[0], X)


def energy_comparison(scorecard: dict) -> None:
    references = scorecard["references"]
    result = scorecard["result"]
    labels = ["Exact\nground state", "Ideal\ncircuit", "ibm_fez\n1024 shots"]
    values = [
        references["exact_ground_state_energy"],
        references["ideal_circuit_energy"],
        result["energy"],
    ]
    figure, axis = plt.subplots(figsize=(6.2, 4.2))
    bars = axis.bar(labels, values, color=[EXACT_COLOR, CIRCUIT_COLOR, HARDWARE_COLOR], width=0.72)
    axis.errorbar(
        2,
        result["energy"],
        yerr=result["uncertainty"],
        fmt="none",
        ecolor=NEUTRAL,
        elinewidth=1.2,
        capsize=4,
    )
    uncertainty = result["uncertainty"]
    axis.bar_label(
        bars,
        labels=[
            f"{values[0]:.3f}",
            f"{values[1]:.3f}",
            f"{values[2]:.3f}\n± {uncertainty:.3f}",
        ],
        label_type="center",
        color="white",
        fontsize=10,
    )
    axis.axhline(0.0, color="#888888", linewidth=0.6)
    axis.set_ylabel("Energy (units of J)")
    axis.set_title("Four-site TFIM energy: exact, ideal circuit, and ibm_fez")
    _pad_negative(axis, values, result["uncertainty"])
    save(figure, "fig1_energy_comparison")


def error_sources(scorecard: dict) -> None:
    references = scorecard["references"]
    result = scorecard["result"]
    ansatz_gap = abs(references["ideal_circuit_energy"] - references["exact_ground_state_energy"])
    labels = [
        "Ideal circuit\nvs exact",
        "ibm_fez\nvs ideal circuit",
        "ibm_fez\nvs exact",
    ]
    values = [ansatz_gap, result["execution_error"], result["absolute_energy_error"]]
    figure, axis = plt.subplots(figsize=(6.2, 4.2))
    bars = axis.bar(labels, values, color=[CIRCUIT_COLOR, HARDWARE_COLOR, "#882255"], width=0.72)
    axis.bar_label(bars, fmt="%.3f", padding=3, fontsize=9)
    axis.set_ylabel("Absolute energy gap (units of J)")
    axis.set_title("Source of the energy miss on ibm_fez")
    axis.set_ylim(0, max(values) * 1.25)
    save(figure, "fig2_error_sources")


def pauli_expectations(names, exact, circuit, hardware, sigma) -> None:
    figure, axis = plt.subplots(figsize=(7.4, 4.4))
    positions = np.arange(len(names))
    width = 0.26
    axis.bar(positions - width, exact, width, label="Exact ground state", color=EXACT_COLOR)
    axis.bar(positions, circuit, width, label="Ideal circuit", color=CIRCUIT_COLOR)
    axis.bar(
        positions + width,
        hardware,
        width,
        yerr=sigma,
        capsize=2,
        label="ibm_fez",
        color=HARDWARE_COLOR,
        error_kw={"elinewidth": 0.9, "ecolor": NEUTRAL},
    )
    axis.set_xticks(positions, names)
    axis.set_ylabel("Expectation value")
    axis.set_xlabel("Hamiltonian term")
    axis.set_title("Pauli expectations for the N=4, J=1, h=1 open chain")
    axis.legend(frameon=False, ncol=3, loc="upper left")
    axis.set_ylim(0, 1.15)
    save(figure, "fig3_pauli_expectations")


def energy_contributions(names, coefficients, exact, circuit, hardware, sigma) -> None:
    figure, axis = plt.subplots(figsize=(7.4, 4.4))
    positions = np.arange(len(names))
    width = 0.26
    exact_energy = coefficients * exact
    circuit_energy = coefficients * circuit
    hardware_energy = coefficients * hardware
    axis.bar(positions - width, exact_energy, width, label="Exact ground state", color=EXACT_COLOR)
    axis.bar(positions, circuit_energy, width, label="Ideal circuit", color=CIRCUIT_COLOR)
    axis.bar(
        positions + width,
        hardware_energy,
        width,
        yerr=np.abs(coefficients) * sigma,
        capsize=2,
        label="ibm_fez",
        color=HARDWARE_COLOR,
        error_kw={"elinewidth": 0.9, "ecolor": NEUTRAL},
    )
    axis.set_xticks(positions, names)
    axis.set_ylabel("Contribution to energy, c⟨P⟩ (units of J)")
    axis.set_xlabel("Hamiltonian term")
    axis.set_title("How each term adds up to the total energy")
    axis.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.18))
    save(figure, "fig4_energy_contributions")


def compilation_cost(scorecard: dict, terms: list[dict]) -> None:
    raw = scorecard["resources"]["raw"]
    names = [term["term"] for term in terms]
    figure, axes = plt.subplots(1, 2, figsize=(8.4, 4.2))

    depth_axis = axes[0]
    positions = np.arange(len(names))
    depth_axis.bar(positions, [term["depth"] for term in terms], color=HARDWARE_COLOR, label="Compiled for ibm_fez")
    depth_axis.axhline(raw["depth"], color=EXACT_COLOR, linestyle="--", linewidth=1.3, label=f"Raw circuit depth ({raw['depth']})")
    depth_axis.set_xticks(positions, names, rotation=40, ha="right")
    depth_axis.set_ylabel("Circuit depth")
    depth_axis.set_title("Depth after compilation")
    depth_axis.legend(frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.28))
    depth_axis.set_ylim(0, 32)

    gate_axis = axes[1]
    raw_counts = raw["operation_counts"]
    compiled = terms[0]["operation_counts"]
    raw_labels = ["h", "ry", "cx"]
    compiled_labels = ["sx", "rz", "cz"]
    gate_positions = np.arange(3)
    gate_axis.bar(gate_positions - 0.18, [raw_counts[name] for name in raw_labels], 0.36, label="Raw circuit", color=EXACT_COLOR)
    gate_axis.bar(
        gate_positions + 0.18,
        [compiled[name] for name in compiled_labels],
        0.36,
        label="Compiled Z0Z1",
        color=HARDWARE_COLOR,
    )
    gate_axis.set_xticks(gate_positions, ["h  →  sx", "ry  →  rz", "cx  →  cz"])
    gate_axis.set_ylabel("Gate count")
    gate_axis.set_title("Gate mix: raw circuit vs compiled Z0Z1")
    gate_axis.legend(frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.18))
    figure.suptitle("Compilation cost of the same four-qubit circuit on ibm_fez", fontsize=12)
    save(figure, "fig5_compilation_cost")


def depth_curve(scorecard: dict, terms: list[dict]) -> None:
    names = [term["term"] for term in terms]
    steps = np.arange(1, len(names) + 1)
    depths = [term["depth"] for term in terms]
    gates = [term["two_qubit_gate_count"] for term in terms]
    raw_depth = scorecard["resources"]["raw"]["depth"]

    figure, axis = plt.subplots(figsize=(7.2, 4.4))
    axis.plot(steps, depths, marker="o", color=HARDWARE_COLOR, linewidth=2, label="Compiled depth on ibm_fez")
    axis.plot(steps, gates, marker="s", color=EXACT_COLOR, linewidth=2, label="Compiled two-qubit gates")
    axis.axhline(raw_depth, color=CIRCUIT_COLOR, linestyle="--", linewidth=1.3, label=f"Raw circuit depth ({raw_depth})")
    axis.set_xticks(steps, names)
    axis.set_xlabel("Measurement step")
    axis.set_ylabel("Count")
    axis.set_title("Circuit depth and two-qubit gates across the seven terms")
    axis.legend(frameon=False)
    axis.set_ylim(0, 34)
    save(figure, "fig6_depth_curve")


def expectation_curve(names, exact, circuit, hardware, sigma) -> None:
    steps = np.arange(1, len(names) + 1)
    figure, axis = plt.subplots(figsize=(7.2, 4.4))
    axis.plot(steps, exact, marker="o", color=EXACT_COLOR, linewidth=2, label="Exact ground state")
    axis.plot(steps, circuit, marker="o", color=CIRCUIT_COLOR, linewidth=2, label="Ideal circuit")
    axis.plot(steps, hardware, marker="o", color=HARDWARE_COLOR, linewidth=2, label="ibm_fez")
    axis.fill_between(
        steps,
        hardware - sigma,
        hardware + sigma,
        color=HARDWARE_COLOR,
        alpha=0.18,
        linewidth=0,
        label="ibm_fez shot uncertainty",
    )
    axis.set_xticks(steps, names)
    axis.set_xlabel("Measurement step")
    axis.set_ylabel("Expectation value")
    axis.set_title("Pauli expectations across the seven measurement steps")
    axis.legend(frameon=False, ncol=2)
    axis.set_ylim(0.3, 1.05)
    save(figure, "fig7_expectation_curve")


def cumulative_energy_curve(names, coefficients, exact, circuit, hardware, sigma) -> None:
    steps = np.arange(1, len(names) + 1)
    exact_running = np.cumsum(coefficients * exact)
    circuit_running = np.cumsum(coefficients * circuit)
    hardware_running = np.cumsum(coefficients * hardware)
    hardware_band = np.sqrt(np.cumsum((np.abs(coefficients) * sigma) ** 2))

    figure, axis = plt.subplots(figsize=(7.2, 4.4))
    axis.plot(steps, exact_running, marker="o", color=EXACT_COLOR, linewidth=2, label="Exact ground state")
    axis.plot(steps, circuit_running, marker="o", color=CIRCUIT_COLOR, linewidth=2, label="Ideal circuit")
    axis.plot(steps, hardware_running, marker="o", color=HARDWARE_COLOR, linewidth=2, label="ibm_fez")
    axis.fill_between(
        steps,
        hardware_running - hardware_band,
        hardware_running + hardware_band,
        color=HARDWARE_COLOR,
        alpha=0.18,
        linewidth=0,
        label="ibm_fez shot uncertainty",
    )
    axis.set_xticks(steps, names)
    axis.set_xlabel("Terms included, in measurement order")
    axis.set_ylabel("Running energy (units of J)")
    axis.set_title("Running energy as each Hamiltonian term is added")
    axis.legend(frameon=False)
    save(figure, "fig8_energy_learning_curve")


def running_error_curve(names, coefficients, exact, hardware, sigma) -> None:
    steps = np.arange(1, len(names) + 1)
    exact_running = np.cumsum(coefficients * exact)
    hardware_running = np.cumsum(coefficients * hardware)
    running_error = np.abs(hardware_running - exact_running)
    running_sigma = np.sqrt(np.cumsum((np.abs(coefficients) * sigma) ** 2))

    figure, axis = plt.subplots(figsize=(7.2, 4.4))
    axis.plot(steps, running_error, marker="o", color="#882255", linewidth=2, label="Absolute energy error")
    axis.fill_between(
        steps,
        np.maximum(running_error - running_sigma, 0),
        running_error + running_sigma,
        color="#882255",
        alpha=0.15,
        linewidth=0,
        label="Shot uncertainty of the running sum",
    )
    axis.axhline(running_error[-1], color=HARDWARE_COLOR, linestyle="--", linewidth=1.2, label=f"Final error {running_error[-1]:.3f}")
    axis.set_xticks(steps, names)
    axis.set_xlabel("Terms included, in measurement order")
    axis.set_ylabel("Absolute energy gap (units of J)")
    axis.set_title("How the 0.397 hardware miss builds up term by term")
    axis.legend(frameon=False)
    axis.set_ylim(0, max(running_error) * 1.25)
    save(figure, "fig9_error_learning_curve")


def apply_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.size": 11,
            "axes.labelsize": 12,
            "axes.titlesize": 12,
            "figure.dpi": 150,
            "savefig.dpi": 300,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def _pad_negative(axis, values, uncertainty: float) -> None:
    low = min(values) - uncertainty
    high = max(max(values), 0.0)
    span = high - low
    axis.set_ylim(low - 0.18 * span, high + 0.22 * span)


def save(figure, stem: str) -> None:
    figure.tight_layout()
    figure.savefig(OUT / f"{stem}.png", bbox_inches="tight")
    figure.savefig(OUT / f"{stem}.pdf", bbox_inches="tight")
    plt.close(figure)


if __name__ == "__main__":
    main()
