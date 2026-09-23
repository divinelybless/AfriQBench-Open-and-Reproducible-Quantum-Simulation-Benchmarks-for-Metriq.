"""Reference observables for small TFIM benchmark instances."""

from __future__ import annotations

import numpy as np

from afriqbench.models.tfim import X, Z, _single_site_operator, _two_site_operator
from afriqbench.reference.exact import expectation


def transverse_magnetization(state: np.ndarray, n_qubits: int) -> float:
    """Return the site-averaged transverse magnetization <X>."""
    values = [
        expectation(state, _single_site_operator(n_qubits, site, X))
        for site in range(n_qubits)
    ]
    return float(np.mean(values))


def nearest_neighbor_zz(
    state: np.ndarray,
    n_qubits: int,
    periodic: bool = False,
) -> float:
    """Return the mean nearest-neighbour ZZ correlation."""
    pairs = [(i, i + 1) for i in range(n_qubits - 1)]

    if periodic and n_qubits > 2:
        pairs.append((n_qubits - 1, 0))

    values = [
        expectation(
            state,
            _two_site_operator(n_qubits, i, j, Z, Z),
        )
        for i, j in pairs
    ]
    return float(np.mean(values))
