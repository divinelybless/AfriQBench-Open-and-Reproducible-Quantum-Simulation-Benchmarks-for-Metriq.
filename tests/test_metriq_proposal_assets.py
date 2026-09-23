import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
PROPOSAL = ROOT / "metriq_proposal"


def test_metriq_schema_and_example_are_consistent():
    schema = json.loads(
        (
            PROPOSAL
            / "metriq_gym"
            / "schemas"
            / "tfim_energy.schema.json"
        ).read_text(encoding="utf-8")
    )
    example = json.loads(
        (
            PROPOSAL
            / "metriq_gym"
            / "schemas"
            / "examples"
            / "tfim_energy.example.json"
        ).read_text(encoding="utf-8")
    )

    assert schema["properties"]["benchmark_name"]["const"] == "TFIM Energy"
    assert example["benchmark_name"] == "TFIM Energy"
    assert example["num_qubits"] == 4
    assert example["coupling_j"] == 1.0
    assert example["field_h"] == 1.0
    assert example["shots"] >= 1


def test_upstream_bundle_contains_required_files():
    required = [
        "README.md",
        "INTEGRATION_PATCH.md",
        "UPSTREAM_PROPOSAL.md",
        "metriq_gym/benchmarks/tfim_energy.py",
        "metriq_gym/schemas/tfim_energy.schema.json",
        "metriq_gym/schemas/examples/tfim_energy.example.json",
        "tests/unit/benchmarks/test_tfim_energy.py",
        "docs/content/benchmarks/tfim-energy.md",
    ]

    missing = [
        relative
        for relative in required
        if not (PROPOSAL / relative).exists()
    ]

    assert not missing, f"Missing proposal files: {missing}"
