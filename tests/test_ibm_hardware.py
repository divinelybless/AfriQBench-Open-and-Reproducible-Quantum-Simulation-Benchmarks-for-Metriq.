import json
import os
from math import sqrt
from pathlib import Path

import pytest

from afriqbench.metrics import absolute_error, relative_error
from afriqbench.quantum.hardware import (
    ANSATZ_ENERGY,
    CANONICAL_SHOTS,
    EXACT_ENERGY,
    build_scorecard,
    combine_expectations,
    format_report,
    load_env_file,
    measurement_specs,
    plot_scorecard,
)


def test_measurement_plan_is_the_seven_term_hamiltonian():
    specs = measurement_specs()

    assert [spec["term"] for spec in specs] == [
        "Z0Z1",
        "Z1Z2",
        "Z2Z3",
        "X0",
        "X1",
        "X2",
        "X3",
    ]
    assert all(spec["coefficient"] == pytest.approx(-1.0) for spec in specs)


def test_energy_and_uncertainty_follow_the_simulator_rule():
    energy, uncertainty = combine_expectations(
        [
            {"coefficient": -1.0, "expectation": 0.5, "uncertainty": 0.1},
            {"coefficient": -1.0, "expectation": 0.25, "uncertainty": 0.2},
        ]
    )

    assert energy == pytest.approx(-0.75)
    assert uncertainty == pytest.approx(sqrt(0.1**2 + 0.2**2))


def test_scorecard_uses_both_answer_keys():
    scorecard = _sample_scorecard(energy=-4.70, shots=1024)
    result = scorecard["result"]

    assert result["absolute_energy_error"] == pytest.approx(
        absolute_error(-4.70, EXACT_ENERGY)
    )
    assert result["relative_energy_error"] == pytest.approx(
        relative_error(-4.70, EXACT_ENERGY)
    )
    assert result["execution_error"] == pytest.approx(
        absolute_error(-4.70, ANSATZ_ENERGY)
    )
    assert scorecard["execution"]["shots_total"] == 1024 * 7
    assert scorecard["resources"]["max_depth"] == 14
    assert scorecard["resources"]["max_two_qubit_gate_count"] == 9


def test_report_names_the_recorded_quantities():
    report = format_report(_sample_scorecard(energy=-4.70, shots=1024))

    assert "N=4, J=1.0, h=1.0" in report
    assert f"{EXACT_ENERGY:.10f}" in report
    assert "Energy error" in report
    assert "Compiled max depth" in report
    assert "Z0Z1" in report
    assert str(CANONICAL_SHOTS) in report


def test_env_file_does_not_override_or_echo_values(tmp_path: Path, monkeypatch, capsys):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                'export QISKIT_IBM_TOKEN="secret-token"',
                "QISKIT_IBM_INSTANCE='crn:example'",
                "QISKIT_IBM_CHANNEL=ibm_quantum_platform",
                "",
            ]
        )
    )

    monkeypatch.setenv("QISKIT_IBM_TOKEN", "already-set")
    monkeypatch.delenv("QISKIT_IBM_INSTANCE", raising=False)
    monkeypatch.delenv("QISKIT_IBM_CHANNEL", raising=False)
    load_env_file(env_path)
    captured = capsys.readouterr()

    assert os.environ["QISKIT_IBM_TOKEN"] == "already-set"
    assert os.environ["QISKIT_IBM_INSTANCE"] == "crn:example"
    assert os.environ["QISKIT_IBM_CHANNEL"] == "ibm_quantum_platform"
    assert "secret-token" not in captured.out
    assert "secret-token" not in captured.err


def test_plot_writes_the_scorecard_figure(tmp_path: Path):
    pytest.importorskip("matplotlib")
    figure_path = tmp_path / "scorecard.png"

    saved = plot_scorecard(_sample_scorecard(energy=-4.70, shots=1024), figure_path)

    assert saved == figure_path
    assert figure_path.is_file()
    assert figure_path.stat().st_size > 1000


def test_local_preflight_matches_the_stored_answer_keys(tmp_path: Path):
    pytest.importorskip("qiskit")
    from afriqbench.quantum.hardware import run_local_preflight, save_scorecard

    scorecard = run_local_preflight()

    assert scorecard["result"]["energy"] == pytest.approx(ANSATZ_ENERGY, abs=1e-8)
    assert scorecard["result"]["fidelity_to_exact_ground_state"] > 0.999
    assert scorecard["resources"]["raw"]["n_qubits"] == 4
    assert scorecard["resources"]["raw"]["two_qubit_gate_count"] == 6
    assert len(scorecard["terms"]) == 7

    json_path, figure_path = save_scorecard(scorecard, tmp_path)
    payload = json.loads(json_path.read_text())
    assert payload["references"]["exact_ground_state_energy"] == EXACT_ENERGY
    assert figure_path.is_file()


def _sample_scorecard(energy: float, shots: int) -> dict:
    terms = []
    for index, name in enumerate(["Z0Z1", "Z1Z2", "Z2Z3", "X0", "X1", "X2", "X3"]):
        terms.append(
            {
                "term": name,
                "expectation": -0.4,
                "uncertainty": 0.01,
                "depth": 8 + index,
                "two_qubit_gate_count": 6 + (index % 4),
            }
        )
    return build_scorecard(
        energy=energy,
        uncertainty=0.02,
        shots_per_term=shots,
        terms=terms,
        mode="ibm_hardware",
        backend="ibm_example",
        job_id="job-1",
        raw_resources={
            "n_qubits": 4,
            "depth": 7,
            "two_qubit_gate_count": 6,
        },
    )
