# Metriq-Gym Integration Patch

The proposed upstream files in this directory are designed to be copied to their corresponding paths in `unitaryfoundation/metriq-gym`.

## 1. Add the job type and schema mapping

In `metriq_gym/constants.py`:

```diff
 class JobType(StrEnum):
     ...
     QAT_OLE = "QAT OLE"
+    TFIM_ENERGY = "TFIM Energy"

 SCHEMA_MAPPING = {
     ...
     JobType.QAT_OLE: "qat_ole.schema.json",
+    JobType.TFIM_ENERGY: "tfim_energy.schema.json",
 }
```

## 2. Register the benchmark classes

In `metriq_gym/registry.py`:

```diff
+from metriq_gym.benchmarks.tfim_energy import (
+    TFIMEnergy,
+    TFIMEnergyData,
+    TFIMEnergyResult,
+)

 BENCHMARK_HANDLERS = {
     ...
+    JobType.TFIM_ENERGY: TFIMEnergy,
 }

 BENCHMARK_DATA_CLASSES = {
     ...
+    JobType.TFIM_ENERGY: TFIMEnergyData,
 }

 BENCHMARK_RESULT_CLASSES = {
     ...
+    JobType.TFIM_ENERGY: TFIMEnergyResult,
 }
```

## 3. Proposed file destinations

| AfriQBench proposal file | Metriq-Gym destination |
|---|---|
| `metriq_gym/benchmarks/tfim_energy.py` | `metriq_gym/benchmarks/tfim_energy.py` |
| `metriq_gym/schemas/tfim_energy.schema.json` | `metriq_gym/schemas/tfim_energy.schema.json` |
| `metriq_gym/schemas/examples/tfim_energy.example.json` | `metriq_gym/schemas/examples/tfim_energy.example.json` |
| `tests/unit/benchmarks/test_tfim_energy.py` | `tests/unit/benchmarks/test_tfim_energy.py` |
| `docs/content/benchmarks/tfim-energy.md` | `docs/content/benchmarks/tfim-energy.md` |

## 4. Documentation navigation

If maintainers want a dedicated benchmark page in the documentation navigation, add `benchmarks/tfim-energy.md` to the relevant section of `docs/mkdocs.yml`.

## 5. Validation checklist

After applying the files to a Metriq-Gym branch:

```bash
uv sync --all-extras

uv run pytest tests/unit/benchmarks/test_tfim_energy.py -q

uv run mgym job estimate \
  metriq_gym/schemas/examples/tfim_energy.example.json \
  --provider local --device aer_simulator

uv run mgym job dispatch \
  metriq_gym/schemas/examples/tfim_energy.example.json \
  --provider local --device aer_simulator

uv run mgym job poll latest
```

Then run the full test suite and formatting/lint checks required by Metriq-Gym before opening the upstream pull request.
