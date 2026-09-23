import numpy as np
import pytest

pytest.importorskip("qiskit")
pytest.importorskip("qiskit_aer")
pytest.importorskip("qiskit_ibm_runtime")

from afriqbench.quantum.cross_backend import (
    load_fake_backend,
    make_device_derived_aer_backend,
    normalize_fake_device_id,
    transpiled_resource_metrics,
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


@pytest.mark.parametrize(
    ("alias", "expected"),
    [
        ("fake_manila", "fake_manila"),
        ("ibm_manila", "fake_manila"),
        ("ibm-manila", "fake_manila"),
        ("manila", "fake_manila"),
    ],
)
def test_fake_backend_alias_normalization(alias, expected):
    assert normalize_fake_device_id(alias) == expected


def test_fake_manila_can_be_loaded():
    backend = load_fake_backend("manila")
    name = backend.name() if callable(backend.name) else backend.name
    assert str(name).lower().replace("-", "_") == "fake_manila"


def test_device_derived_backend_transpiles_benchmark_circuit():
    circuit = bind_ansatz(4, BASELINE_PARAMETERS, reps=2)
    backend, metadata = make_device_derived_aer_backend("fake_manila")
    metrics = transpiled_resource_metrics(
        circuit,
        backend,
        seed=12345,
        optimization_level=1,
    )

    assert metadata["resolved_fake_backend"].lower().replace("-", "_") == "fake_manila"
    assert metadata["num_qubits"] >= 4
    assert metrics["depth"] > 0
    assert metrics["two_qubit_gate_count"] > 0
