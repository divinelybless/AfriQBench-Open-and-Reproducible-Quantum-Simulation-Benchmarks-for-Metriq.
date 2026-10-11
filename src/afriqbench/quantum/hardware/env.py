"""Project environment loading for an IBM hardware run."""

from __future__ import annotations

import os
from pathlib import Path

ENV_NAMES = (
    "QISKIT_IBM_TOKEN",
    "QISKIT_IBM_INSTANCE",
    "QISKIT_IBM_CHANNEL",
)


def repo_root() -> Path:
    """Return the repository root from this package's location."""
    return Path(__file__).resolve().parents[4]


def load_env_file(path: Path) -> None:
    """Load ``KEY=value`` or ``export KEY=value`` lines into the environment.

    Existing variables win, so a shell export is kept. Values are never logged.
    """
    if not path.is_file():
        return

    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


def load_project_env(root: Path | None = None) -> None:
    """Load the project ``.env`` file, then a ``.env`` in the working directory."""
    search_root = repo_root() if root is None else root
    load_env_file(search_root / ".env")
    cwd_env = Path.cwd() / ".env"
    if cwd_env.resolve() != (search_root / ".env").resolve():
        load_env_file(cwd_env)
