"""Execute all notebooks in order and verify the complete project."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> None:
    environment = os.environ.copy()
    environment["PYTHONUTF8"] = "1"
    environment["MPLBACKEND"] = "Agg"
    print("\n$", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True, env=environment)


def execute_notebook(source_name: str, output_name: str) -> None:
    run(
        [
            sys.executable,
            "-m",
            "nbconvert",
            "--to",
            "notebook",
            "--execute",
            f"notebooks/{source_name}",
            "--output",
            output_name,
            "--output-dir",
            "outputs/notebooks",
            "--ExecutePreprocessor.timeout=3600",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-data-check", action="store_true")
    args = parser.parse_args()

    run([sys.executable, "scripts/build_notebooks.py"])
    if not args.skip_data_check:
        run([sys.executable, "scripts/get_data.py"])
    execute_notebook("01_data_eda.ipynb", "01_data_eda.executed.ipynb")
    execute_notebook("02_modeling.ipynb", "02_modeling.executed.ipynb")
    execute_notebook("03_evaluation.ipynb", "03_evaluation.executed.ipynb")
    execute_notebook("Fraud_Project_Final.ipynb", "Fraud_Project_Final.executed.ipynb")
    run([sys.executable, "scripts/verify_project.py"])
    print("\n[HOÀN TẤT] Xem outputs/notebooks, outputs/tables, outputs/figures và reports/.")


if __name__ == "__main__":
    main()
