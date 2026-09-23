"""Transverse-field Ising model reference utilities."""

from __future__ import annotations

import numpy as np

I2 = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Z = np.array([[1, 0], [0, -1]], dtype=complex)


def _kron_all(ops: list[np.ndarray]) -> np.ndarray:
    out = ops[0]
    for op in ops[1:]:
        out = np.kron(out, op)
    return out


def _single_site_operator(
    n_qubits: int,
    site: int,
    op: np.ndarray,
) -> np.ndarray:
    ops = [I2 for _ in range(n_qubits)]
    ops[site] = op
    return _kron_all(ops)


def _two_site_operator(
    n_qubits: int,
    site_a: int,
    site_b: int,
    op_a: np.ndarray,
    op_b: np.ndarray,
) -> np.ndarray:
    ops = [I2 for _ in range(n_qubits)]
    ops[site_a] = op_a
    ops[site_b] = op_b
    return _kron_all(ops)


def tfim_hamiltonian(
    n_qubits: int,
    J: float = 1.0,
    h: float = 1.0,
    periodic: bool = False,
) -> np.ndarray:
    """Return the dense TFIM Hamiltonian for small reference instances.

    Convention:
        H = -J sum_i Z_i Z_(i+1) - h sum_i X_i

    The dense implementation is intentionally limited to small benchmark
    instances used for exact classical validation.
    """
    if n_qubits < 2:
        raise ValueError("n_qubits must be at least 2")

    dim = 2**n_qubits
    H = np.zeros((dim, dim), dtype=complex)

    for i in range(n_qubits - 1):
        H -= J * _two_site_operator(n_qubits, i, i + 1, Z, Z)

    if periodic and n_qubits > 2:
        H -= J * _two_site_operator(
            n_qubits,
            n_qubits - 1,
            0,
            Z,
            Z,
        )

    for i in range(n_qubits):
        H -= h * _single_site_operator(n_qubits, i, X)

    return H
