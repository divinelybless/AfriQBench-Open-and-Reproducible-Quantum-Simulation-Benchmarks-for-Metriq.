"""Benchmark metrics."""


def absolute_error(
    estimate: float,
    reference: float,
) -> float:
    """Return absolute error between estimate and reference."""
    return abs(float(estimate) - float(reference))


def relative_error(
    estimate: float,
    reference: float,
    eps: float = 1e-12,
) -> float:
    """Return relative error with protection near zero."""
    scale = max(abs(float(reference)), eps)
    return abs(float(estimate) - float(reference)) / scale
