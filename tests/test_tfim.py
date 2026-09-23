import numpy as np
import pytest

from afriqbench.metrics import absolute_error
from afriqbench.models.tfim import tfim_hamiltonian
from afriqbench.reference.exact import ground_state


def test_tfim_is_hermitian():
    H = tfim_hamiltonian(n_qubits=3, J=1.0, h=0.8)
    assert np.allclose(H, H.conj().T)


def test_ground_state_energy_is_finite():
    H = tfim_hamiltonian(n_qubits=2, J=1.0, h=1.0)
    energy, state = ground_state(H)

    assert np.isfinite(energy)
    assert np.isclose(np.linalg.norm(state), 1.0)


def test_absolute_error():
    assert absolute_error(0.9, 1.0) == pytest.approx(0.1)
