"""Hardware exam for the fixed four-qubit TFIM benchmark.

Import order follows the run: the workload, the scorecard, the local check,
then the IBM submission. Importing this package does not contact IBM.
"""

from afriqbench.quantum.hardware.workload import (
    ANSATZ_ENERGY,
    CANONICAL_SHOTS,
    EXACT_ENERGY,
    measurement_specs,
)
from afriqbench.quantum.hardware.scorecard import (
    build_scorecard,
    combine_expectations,
    format_report,
    save_scorecard,
)
from afriqbench.quantum.hardware.plotting import plot_scorecard
from afriqbench.quantum.hardware.preflight import run_local_preflight
from afriqbench.quantum.hardware.env import load_env_file, load_project_env
from afriqbench.quantum.hardware.ibm_runtime import fetch_ibm_job, run_ibm_hardware

__all__ = [
    "ANSATZ_ENERGY",
    "CANONICAL_SHOTS",
    "EXACT_ENERGY",
    "build_scorecard",
    "combine_expectations",
    "fetch_ibm_job",
    "format_report",
    "load_env_file",
    "load_project_env",
    "measurement_specs",
    "plot_scorecard",
    "run_ibm_hardware",
    "run_local_preflight",
    "save_scorecard",
]
