"""Figures for an AfriQBench hardware scorecard."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from afriqbench.quantum.hardware.scorecard import display, format_optional


def plot_scorecard(scorecard: dict[str, Any], path: Path) -> Path:
    """Save a four-panel figure of energy, error, depth, and gate count."""
    plt = _pyplot()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    references = scorecard["references"]
    result = scorecard["result"]
    terms = scorecard["terms"]
    execution = scorecard["execution"]
    names = [term["term"] for term in terms]

    figure, axes = plt.subplots(2, 2, figsize=(11.5, 8.0))
    figure.suptitle(
        (
            f"AfriQBench TFIM  N=4  J=1  h=1    "
            f"{scorecard['mode']}    {execution['backend']}"
        ),
        fontsize=13,
    )

    energy_labels = ["Exact reference", "Ideal circuit", "This run"]
    energy_values = [
        references["exact_ground_state_energy"],
        references["ideal_circuit_energy"],
        result["energy"],
    ]
    energy_axis = axes[0, 0]
    energy_bars = energy_axis.bar(
        energy_labels,
        energy_values,
        color=["#1b4f72", "#148f77", "#b9770e"],
    )
    energy_axis.bar_label(
        energy_bars,
        fmt="%.4f",
        label_type="center",
        color="white",
        fontsize=9,
    )
    energy_axis.set_ylabel("Energy, in units of J")
    energy_axis.set_title("Energy")
    energy_axis.axhline(0.0, color="#666666", linewidth=0.6)
    _pad_ylim(energy_axis, energy_values)

    error_values = [
        result["absolute_energy_error"],
        result["execution_error"],
    ]
    error_axis = axes[0, 1]
    error_bars = error_axis.bar(
        ["Energy error", "Execution error"],
        error_values,
        color=["#6c3483", "#1a5276"],
    )
    error_axis.bar_label(error_bars, fmt="%.5f", padding=3)
    error_axis.set_ylabel("Absolute gap")
    error_axis.set_title("Error against the two answer keys")
    error_high = max(error_values)
    error_axis.set_ylim(0.0, max(error_high * 1.45, 0.001))

    depths = [int(term.get("depth", 0)) for term in terms]
    depth_axis = axes[1, 0]
    depth_bars = depth_axis.bar(names, depths, color="#1a5276")
    depth_axis.bar_label(depth_bars, padding=3)
    depth_axis.set_ylabel("Circuit depth")
    depth_axis.set_title("Circuit depth of each measured term")
    depth_axis.tick_params(axis="x", rotation=45)
    depth_axis.set_ylim(0, max(depths, default=1) * 1.25)

    gates = [int(term.get("two_qubit_gate_count", 0)) for term in terms]
    gate_axis = axes[1, 1]
    gate_bars = gate_axis.bar(names, gates, color="#922b21")
    gate_axis.bar_label(gate_bars, padding=3)
    gate_axis.set_ylabel("Two-qubit gates")
    gate_axis.set_title("Two-qubit gates of each measured term")
    gate_axis.tick_params(axis="x", rotation=45)
    gate_axis.set_ylim(0, max(gates, default=1) * 1.25)

    figure.text(
        0.01,
        0.01,
        (
            f"Shots per term: {display(execution['shots_per_term'])}    "
            f"Total shots: {display(execution['shots_total'])}    "
            f"Uncertainty: {format_optional(result['uncertainty'])}    "
            f"Relative energy error: {result['relative_energy_error']:.6f}    "
            f"Max depth: {scorecard['resources']['max_depth']}    "
            f"Max two-qubit gates: {scorecard['resources']['max_two_qubit_gate_count']}"
        ),
        fontsize=8,
    )
    figure.tight_layout(rect=(0, 0.04, 1, 0.95))
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return path


def _pad_ylim(axis, values: list[float]) -> None:
    low = min(min(values), 0.0)
    high = max(max(values), 0.0)
    span = max(high - low, 0.05)
    axis.set_ylim(low - 0.2 * span, high + 0.28 * span)


def _pyplot():
    try:
        import matplotlib
    except ImportError as exc:
        raise ImportError(
            "Plots require matplotlib. Install with: "
            'python -m pip install -e ".[quantum,notebook]"'
        ) from exc

    if matplotlib.get_backend().lower() != "agg":
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt
