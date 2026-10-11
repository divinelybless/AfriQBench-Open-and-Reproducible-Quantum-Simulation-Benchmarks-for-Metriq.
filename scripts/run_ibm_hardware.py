#!/usr/bin/env python3
"""Run the AfriQBench four-qubit TFIM exam on IBM hardware.

Examples:
    python scripts/run_ibm_hardware.py
    python scripts/run_ibm_hardware.py --run --shots 1024
    python scripts/run_ibm_hardware.py --run --shots 20000 --backend ibm_fez
    python scripts/run_ibm_hardware.py --fetch JOB_ID
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _prepare_import() -> None:
    root = Path(__file__).resolve().parents[1]
    src = root / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


def main(argv: list[str] | None = None) -> int:
    _prepare_import()

    from afriqbench.quantum.hardware import (
        CANONICAL_SHOTS,
        fetch_ibm_job,
        format_report,
        load_project_env,
        run_ibm_hardware,
        run_local_preflight,
        save_scorecard,
    )

    parser = argparse.ArgumentParser(
        description=(
            "Check and run the fixed AfriQBench TFIM benchmark: "
            "N=4, J=1, h=1, open chain."
        )
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Submit the seven measurement circuits to IBM after the local check passes.",
    )
    parser.add_argument(
        "--fetch",
        metavar="JOB_ID",
        help="Score a job that was already submitted.",
    )
    parser.add_argument(
        "--shots",
        type=int,
        default=1024,
        help=(
            "Shots for each of the seven Hamiltonian terms. "
            f"The stored simulator scorecards use {CANONICAL_SHOTS}."
        ),
    )
    parser.add_argument(
        "--backend",
        help="IBM backend name. Omit this to use the least busy chip with at least 4 qubits.",
    )
    args = parser.parse_args(argv)

    load_project_env()
    preflight = run_local_preflight()
    print(format_report(preflight))
    print()
    json_path, figure_path = save_scorecard(preflight)
    print(f"Preflight scorecard: {json_path}")
    print(f"Preflight figure:    {figure_path}")

    if args.fetch:
        print()
        hardware = fetch_ibm_job(args.fetch)
        print(format_report(hardware))
        print()
        hardware_json, hardware_figure = save_scorecard(hardware)
        print(f"Hardware scorecard: {hardware_json}")
        print(f"Hardware figure:    {hardware_figure}")
        return 0

    if not args.run:
        print()
        print(
            "Local check passed. No IBM job was submitted. "
            "Start the hardware run with:"
        )
        print("  python scripts/run_ibm_hardware.py --run --shots 1024")
        return 0

    print()
    hardware = run_ibm_hardware(shots=args.shots, backend_name=args.backend)
    print()
    print(format_report(hardware))
    print()
    hardware_json, hardware_figure = save_scorecard(hardware)
    print(f"Hardware scorecard: {hardware_json}")
    print(f"Hardware figure:    {hardware_figure}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nStopped.", file=sys.stderr)
        raise SystemExit(130) from None
