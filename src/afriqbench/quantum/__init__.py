"""Quantum execution layers, in benchmark order.

1. ``qiskit_tfim`` builds the fixed circuit and measures its energy.
2. ``noise`` adds a controlled noise model.
3. ``cross_backend`` compares ideal, controlled, and device-derived runs.
4. ``mitigation`` studies error mitigation beside the raw score.
5. ``hardware`` checks the same exam locally, then can submit it to IBM.
"""
