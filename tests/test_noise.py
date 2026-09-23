import numpy as np
import pytest

pytest.importorskip("qiskit")
pytest.importorskip("qiskit_aer")

from afriqbench.quantum.noise import (
    build_controlled_noise_model,
    estimate_tfim_energy_noisy_aer,
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


def test_controlled_noise_model_can_be_built():
    model = build_controlled_noise_model(
        single_qubit_error=0.001,
        two_qubit_error=0.01,
        readout_error=0.02,
    )
    assert model is not None


def test_invalid_noise_rate_rejected():
    with pytest.raises(ValueError):
        build_controlled_noise_model(single_qubit_error=-0.1)

    with pytest.raises(ValueError):
        build_controlled_noise_model(two_qubit_error=1.0)


def test_zero_noise_path_returns_finite_energy():
    circuit = bind_ansatz(4, BASELINE_PARAMETERS, reps=2)
    result = estimate_tfim_energy_noisy_aer(
        circuit,
        n_qubits=4,
        J=1.0,
        h=1.0,
        shots=2_000,
        seed=12345,
        single_qubit_error=0.0,
        two_qubit_error=0.0,
        readout_error=0.0,
    )

    assert np.isfinite(result["energy"])
    assert result["uncertainty"] > 0.0
    assert result["noise_model"]["type"] == "synthetic_controlled"
