import pytest

from afriqbench.models.tfim import tfim_hamiltonian
from afriqbench.observables import nearest_neighbor_zz, transverse_magnetization
from afriqbench.reference.exact import ground_state


def test_known_n4_reference_at_h_equals_one():
    H = tfim_hamiltonian(n_qubits=4, J=1.0, h=1.0, periodic=False)
    energy, state = ground_state(H)

    assert energy == pytest.approx(-4.7587704831, abs=1e-9)
    assert transverse_magnetization(state, 4) == pytest.approx(
        0.8100954855, abs=1e-9
    )
    assert nearest_neighbor_zz(state, 4) == pytest.approx(
        0.5061295137, abs=1e-9
    )


def test_zero_field_has_perfect_nearest_neighbor_order():
    H = tfim_hamiltonian(n_qubits=4, J=1.0, h=0.0, periodic=False)
    _, state = ground_state(H)

    assert nearest_neighbor_zz(state, 4) == pytest.approx(1.0, abs=1e-12)
    assert transverse_magnetization(state, 4) == pytest.approx(0.0, abs=1e-12)
