"""Energy scorecard shared by the local check and the IBM run."""

from __future__ import annotations

import json
from math import sqrt
from pathlib import Path
from typing import Any

from afriqbench.metrics import absolute_error, relative_error
from afriqbench.quantum.hardware.env import repo_root
from afriqbench.quantum.hardware.workload import (
    CANONICAL_SHOTS,
    EXACT_ENERGY,
    ANSATZ_ENERGY,
    H_FIELD,
    J,
    N_QUBITS,
    OPTIMIZATION_LEVEL,
)


def combine_expectations(terms: list[dict[str, Any]]) -> tuple[float, float]:
    """Combine Pauli expectations into an energy and its shot uncertainty."""
    energy = 0.0
    variance = 0.0
    for term in terms:
        coefficient = float(term["coefficient"])
        expectation = float(term["expectation"])
        uncertainty = float(term["uncertainty"])
        energy += coefficient * expectation
        variance += (coefficient * uncertainty) ** 2
    return float(energy), float(sqrt(variance))


def build_scorecard(
    *,
    energy: float,
    uncertainty: float | None,
    shots_per_term: int | None,
    terms: list[dict[str, Any]],
    mode: str,
    backend: str,
    job_id: str | None = None,
    fidelity: float | None = None,
    raw_resources: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble the benchmark record for one run of the fixed molecule."""
    energy = float(energy)
    n_terms = len(terms)
    shots_total = None
    if shots_per_term is not None:
        shots_total = int(shots_per_term) * n_terms

    depths = [int(term["depth"]) for term in terms if "depth" in term]
    gate_counts = [
        int(term["two_qubit_gate_count"])
        for term in terms
        if "two_qubit_gate_count" in term
    ]

    return {
        "benchmark_id": "tfim-ibm-hardware-n4-h1-v0",
        "mode": mode,
        "model": {
            "name": "transverse_field_ising",
            "n_qubits": N_QUBITS,
            "J": J,
            "h": H_FIELD,
            "boundary": "open",
        },
        "references": {
            "exact_ground_state_energy": EXACT_ENERGY,
            "ideal_circuit_energy": ANSATZ_ENERGY,
        },
        "execution": {
            "backend": backend,
            "job_id": job_id,
            "shots_per_term": shots_per_term,
            "shots_total": shots_total,
            "term_count": n_terms,
            "optimization_level": OPTIMIZATION_LEVEL,
            "canonical_shots_per_term": CANONICAL_SHOTS,
        },
        "result": {
            "energy": energy,
            "uncertainty": None if uncertainty is None else float(uncertainty),
            "absolute_energy_error": absolute_error(energy, EXACT_ENERGY),
            "relative_energy_error": relative_error(energy, EXACT_ENERGY),
            "execution_error": absolute_error(energy, ANSATZ_ENERGY),
            "fidelity_to_exact_ground_state": fidelity,
        },
        "resources": {
            "raw": raw_resources,
            "max_depth": max(depths) if depths else None,
            "max_two_qubit_gate_count": max(gate_counts) if gate_counts else None,
        },
        "terms": terms,
    }


def format_report(scorecard: dict[str, Any]) -> str:
    """Return a plain-text scorecard for the terminal."""
    model = scorecard["model"]
    execution = scorecard["execution"]
    result = scorecard["result"]
    resources = scorecard["resources"]
    references = scorecard["references"]
    lines = [
        "AfriQBench TFIM scorecard",
        (
            f"Problem: N={model['n_qubits']}, J={model['J']}, "
            f"h={model['h']}, boundary={model['boundary']}"
        ),
        f"Mode: {scorecard['mode']}",
        f"Backend: {execution['backend']}",
        f"Job: {execution['job_id'] or 'none'}",
        f"Shots per term: {display(execution['shots_per_term'])}",
        f"Total shots: {display(execution['shots_total'])}",
        "",
        "Energy, in units of J",
        f"  Exact reference:     {references['exact_ground_state_energy']:.10f}",
        f"  Ideal circuit:       {references['ideal_circuit_energy']:.10f}",
        f"  This run:            {result['energy']:.10f}",
        f"  Uncertainty:         {format_optional(result['uncertainty'])}",
        f"  Energy error:        {result['absolute_energy_error']:.10f}",
        f"  Relative error:      {result['relative_energy_error']:.10f}",
        f"  Execution error:     {result['execution_error']:.10f}",
        f"  Fidelity:            {format_optional(result['fidelity_to_exact_ground_state'])}",
        "",
        "Circuit cost",
        f"  Compiled max depth:           {resources['max_depth']}",
        f"  Compiled max two-qubit gates: {resources['max_two_qubit_gate_count']}",
    ]

    raw = resources.get("raw") or {}
    if raw:
        lines.append(f"  Raw depth:                    {raw.get('depth')}")
        lines.append(f"  Raw two-qubit gates:          {raw.get('two_qubit_gate_count')}")
        lines.append(f"  Qubits:                       {raw.get('n_qubits')}")

    lines.extend(["", "Terms"])
    lines.append(
        f"  {'term':<8} {'expect':>12} {'uncertainty':>12} {'depth':>8} {'2q gates':>10}"
    )
    for term in scorecard["terms"]:
        lines.append(
            "  "
            f"{term['term']:<8} "
            f"{format_optional(term.get('expectation'), 12)} "
            f"{format_optional(term.get('uncertainty'), 12)} "
            f"{term.get('depth', ''):>8} "
            f"{term.get('two_qubit_gate_count', ''):>10}"
        )

    shots = execution["shots_per_term"]
    if shots is not None and int(shots) != CANONICAL_SHOTS:
        lines.extend(
            [
                "",
                (
                    "This is a pilot shot budget. The stored simulator "
                    f"scorecards use {CANONICAL_SHOTS} shots per term."
                ),
            ]
        )
    return "\n".join(lines)


def save_scorecard(
    scorecard: dict[str, Any],
    output_dir: Path | None = None,
) -> tuple[Path, Path]:
    """Write the JSON scorecard and its figure. Return both paths."""
    from afriqbench.quantum.hardware.plotting import plot_scorecard

    destination = output_directory(output_dir)
    execution = scorecard["execution"]
    backend = str(execution["backend"]).replace("/", "_")
    job_id = execution["job_id"] or scorecard["mode"]
    stem = f"tfim_n4_h1_{backend}_{job_id}"
    json_path = destination / f"{stem}.json"
    figure_path = destination / f"{stem}.png"
    write_json(json_path, scorecard)
    plot_scorecard(scorecard, figure_path)
    return json_path, figure_path


def output_directory(output_dir: Path | None) -> Path:
    """Return the folder that holds hardware scorecards."""
    destination = repo_root() / "results" / "hardware" if output_dir is None else Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    return destination


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write a scorecard record without changing key order surprises."""
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def display(value: Any) -> str:
    """Render a missing value as n/a."""
    if value is None:
        return "n/a"
    return str(value)


def format_optional(value: Any, width: int | None = None) -> str:
    """Render a float to ten places, or n/a when the value was not measured."""
    if value is None:
        text = "n/a"
    else:
        text = f"{float(value):.10f}"
    if width is None:
        return text
    return f"{text:>{width}}"
