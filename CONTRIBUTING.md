# Contributing to AfriQBench

AfriQBench is intended to be community-developed.

During the MVP phase, contributions are especially welcome in:

- benchmark specification review;
- TFIM reference validation;
- provider-independent circuit definitions;
- Metriq integration;
- tests and reproducibility checks;
- quantum hardware execution;
- benchmark-data validation;
- documentation; and
- tutorial notebooks.

## Development principle

The canonical benchmark should remain reproducible and clearly separated from optional mitigation or provider-specific analysis.

Please open an issue before implementing a major benchmark-interface change so that design decisions remain aligned with upstream Metriq conventions.

## Local development

```bash
python -m pip install -e ".[dev]"
pytest
```

The quantum layers, including the hardware local check, need the quantum extra:

```bash
python -m pip install -e ".[dev,quantum,notebook]"
python scripts/run_ibm_hardware.py
```

That command checks the fixed four-qubit exam and does not submit an IBM job. Add `--run` only when a hardware scorecard is intended.

Contributors should add or update tests when changing scientific reference calculations, metrics, configuration parsing, or execution behavior.
