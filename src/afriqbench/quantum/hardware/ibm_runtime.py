"""Submit the fixed TFIM exam to IBM Quantum and score the returned counts."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from afriqbench.quantum.hardware.env import ENV_NAMES, load_project_env
from afriqbench.quantum.hardware.preflight import run_local_preflight
from afriqbench.quantum.hardware.scorecard import (
    build_scorecard,
    combine_expectations,
    output_directory,
    write_json,
)
from afriqbench.quantum.hardware.workload import (
    BASELINE_PARAMETERS,
    N_QUBITS,
    OPTIMIZATION_LEVEL,
    REPS,
    attach_measurement,
    measurement_specs,
)


def run_ibm_hardware(
    *,
    shots: int = 1024,
    backend_name: str | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Submit the seven measurement circuits to IBM and score the result."""
    if shots < 1:
        raise ValueError("shots must be positive")

    preflight = run_local_preflight()
    destination = output_directory(output_dir)
    service = ibm_service()
    backend = select_backend(service, backend_name)
    prepared = prepare_hardware_circuits(backend)
    job = submit_sampler(backend, prepared["compiled"], shots)
    pending = {
        "job_id": job.job_id(),
        "backend": backend_name_of(backend),
        "shots_per_term": int(shots),
        "specs": prepared["specs"],
        "resources": prepared["resources"],
        "raw_resources": prepared["raw_resources"],
        "preflight_energy": preflight["result"]["energy"],
    }
    pending_path = destination / f"pending_{job.job_id()}.json"
    write_json(pending_path, pending)
    print(f"Submitted job {job.job_id()} on {pending['backend']}.")
    print(f"Pending record: {pending_path}")

    try:
        primitive_result = job.result()
    except Exception:
        print(
            "The job was submitted. Resume it with "
            f"--fetch {job.job_id()} once IBM finishes it."
        )
        raise

    return scorecard_from_runtime_result(
        primitive_result,
        pending,
        sampler_job_id=job.job_id(),
    )


def fetch_ibm_job(job_id: str, output_dir: Path | None = None) -> dict[str, Any]:
    """Rebuild a scorecard from a previously submitted IBM job."""
    destination = output_directory(output_dir)
    pending_path = destination / f"pending_{job_id}.json"
    if not pending_path.is_file():
        raise FileNotFoundError(
            f"No pending record at {pending_path}. Submit the job from this folder first."
        )
    pending = json.loads(pending_path.read_text())
    if pending.get("job_id") != job_id:
        raise RuntimeError(
            f"Pending record {pending_path} belongs to job {pending.get('job_id')}."
        )
    service = ibm_service()
    job = service.job(job_id)
    return scorecard_from_runtime_result(
        job.result(),
        pending,
        sampler_job_id=job_id,
    )


def prepare_hardware_circuits(backend) -> dict[str, Any]:
    """Compile the seven measurement circuits for one IBM backend."""
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

    from afriqbench.quantum.qiskit_tfim import bind_ansatz, circuit_resource_metrics

    circuit = bind_ansatz(N_QUBITS, BASELINE_PARAMETERS, reps=REPS)
    raw_resources = circuit_resource_metrics(circuit)
    specs = measurement_specs()
    logical = [attach_measurement(circuit, spec) for spec in specs]
    pass_manager = generate_preset_pass_manager(
        backend=backend,
        optimization_level=OPTIMIZATION_LEVEL,
    )
    compiled = [pass_manager.run(item) for item in logical]
    resources = [circuit_resource_metrics(item) for item in compiled]
    return {
        "compiled": compiled,
        "specs": specs,
        "resources": resources,
        "raw_resources": raw_resources,
    }


def submit_sampler(backend, compiled: list[Any], shots: int):
    """Send compiled circuits to the IBM Sampler."""
    from qiskit_ibm_runtime import SamplerV2 as Sampler

    sampler = Sampler(mode=backend)
    sampler.options.default_shots = int(shots)
    return sampler.run(compiled)


def scorecard_from_runtime_result(
    primitive_result,
    pending: dict[str, Any],
    sampler_job_id: str,
) -> dict[str, Any]:
    """Turn Sampler counts into the benchmark energy scorecard."""
    from afriqbench.quantum.qiskit_tfim import _expectation_from_counts

    specs = pending["specs"]
    resources = pending["resources"]
    if len(primitive_result) != len(specs):
        raise RuntimeError(
            f"IBM returned {len(primitive_result)} results for {len(specs)} terms."
        )

    terms: list[dict[str, Any]] = []
    for spec, resource, pub in zip(specs, resources, primitive_result, strict=True):
        counts = counts_from_pub(pub)
        expectation, uncertainty = _expectation_from_counts(counts, tuple(spec["qubits"]))
        terms.append(
            {
                "term": spec["term"],
                "basis": spec["basis"],
                "coefficient": spec["coefficient"],
                "qubits": spec["qubits"],
                "expectation": expectation,
                "uncertainty": uncertainty,
                "counts": {str(key): int(value) for key, value in counts.items()},
                "depth": resource["depth"],
                "two_qubit_gate_count": resource["two_qubit_gate_count"],
                "size": resource["size"],
                "operation_counts": resource["operation_counts"],
            }
        )

    energy, uncertainty = combine_expectations(terms)
    return build_scorecard(
        energy=energy,
        uncertainty=uncertainty,
        shots_per_term=int(pending["shots_per_term"]),
        terms=terms,
        mode="ibm_hardware",
        backend=str(pending["backend"]),
        job_id=sampler_job_id,
        raw_resources=pending["raw_resources"],
    )


def ibm_service():
    """Open an IBM Runtime session from the environment, without printing secrets."""
    load_project_env()
    missing = [name for name in ENV_NAMES if not os.environ.get(name)]
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(
            f"Missing IBM settings: {joined}. Put them in .env in the project folder."
        )

    from qiskit_ibm_runtime import QiskitRuntimeService

    return QiskitRuntimeService(
        channel=os.environ["QISKIT_IBM_CHANNEL"],
        token=os.environ["QISKIT_IBM_TOKEN"],
        instance=os.environ["QISKIT_IBM_INSTANCE"],
    )


def select_backend(service, backend_name: str | None):
    """Choose a named chip, or the least busy chip with at least four qubits."""
    if backend_name:
        return service.backend(backend_name)
    return service.least_busy(
        operational=True,
        simulator=False,
        min_num_qubits=N_QUBITS,
    )


def backend_name_of(backend) -> str:
    """Read a backend name whether Qiskit exposes it as a string or a method."""
    name = getattr(backend, "name", None)
    if callable(name):
        name = name()
    return str(name)


def counts_from_pub(pub) -> dict[str, int]:
    """Read measurement counts from a Sampler pub result."""
    data = pub.data
    if hasattr(data, "meas"):
        return dict(data.meas.get_counts())
    names = list(getattr(data, "keys", lambda: [])())
    if len(names) == 1:
        return dict(data[names[0]].get_counts())
    raise RuntimeError(
        "The Sampler result has no 'meas' register. "
        f"Available fields: {names}"
    )
