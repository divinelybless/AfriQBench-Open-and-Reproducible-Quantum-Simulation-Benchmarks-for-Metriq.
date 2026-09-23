import numpy as np
import pytest

pytest.importorskip("qiskit")
pytest.importorskip("mitiq")

from afriqbench.quantum.mitigation import (
    construct_global_zne_circuits,
    mitigation_quality,
    zne_cost_summary,
)
from afriqbench.quantum.qiskit_tfim import bind_ansatz


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


def test_global_zne_circuit_construction():
    circuit = bind_ansatz(4, BASELINE_PARAMETERS, reps=2)
    scaled = construct_global_zne_circuits(
        circuit,
        scale_factors=(1.0, 2.0, 3.0),
    )

    assert len(scaled) == 3
    assert scaled[0].num_qubits == 4
    assert scaled[0].size() <= scaled[1].size() <= scaled[2].size()


def test_zne_cost_summary_for_open_n4_tfim():
    circuit = bind_ansatz(4, BASELINE_PARAMETERS, reps=2)
    scaled = construct_global_zne_circuits(circuit, (1.0, 2.0, 3.0))
    cost = zne_cost_summary(
        scaled,
        n_qubits=4,
        shots_per_term=1_000,
        periodic=False,
    )

    assert cost["hamiltonian_term_count"] == 7
    assert cost["baseline_total_shots"] == 7_000
    assert cost["zne_total_shots"] == 21_000
    assert cost["shot_overhead_factor"] == pytest.approx(3.0)
    assert cost["logical_operation_overhead_factor"] > 3.0


def test_mitigation_quality_does_not_assume_success():
    improved = mitigation_quality(
        unmitigated_energy=-4.4,
        mitigated_energy=-4.7,
        exact_energy=-4.75,
    )
    worsened = mitigation_quality(
        unmitigated_energy=-4.7,
        mitigated_energy=-4.4,
        exact_energy=-4.75,
    )

    assert improved["mitigation_success"] is True
    assert improved["improvement_factor"] > 1.0
    assert worsened["mitigation_success"] is False
    assert worsened["improvement_factor"] < 1.0
