"""Exact reference solvers for small benchmark instances."""

from __future__ import annotations

import numpy as np


def ground_state(
    hamiltonian: np.ndarray,
) -> tuple[float, np.ndarray]:
    """Return the ground-state energy and normalized eigenvector."""
    evals, evecs = np.linalg.eigh(hamiltonian)
    idx = int(np.argmin(evals))
    return float(np.real(evals[idx])), evecs[:, idx]


def expectation(
    state: np.ndarray,
    operator: np.ndarray,
) -> float:
    """Return the real expectation value <psi|O|psi>."""
    value = np.vdot(state, operator @ state)
    return float(np.real_if_close(value))
