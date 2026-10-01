"""One-command runner: verify/download data, execute notebook, verify outputs."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> None:
    print("\n$", " ".join(command))
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Chạy toàn bộ Phụ lục A.1")
    parser.add_argument("--skip-download", action="store_true")
    args = parser.parse_args()

    if not args.skip_download:
        run([sys.executable, "scripts/get_data.py"])

    (ROOT / "outputs" / "notebooks").mkdir(parents=True, exist_ok=True)
    run(
        [
            sys.executable,
            "-m",
            "nbconvert",
            "--to",
            "notebook",
            "--execute",
            "notebooks/01_data_eda.ipynb",
            "--output",
            "01_data_eda.executed.ipynb",
            "--output-dir",
            "outputs/notebooks",
            "--ExecutePreprocessor.timeout=1200",
        ]
    )
    run([sys.executable, "scripts/verify_a1_outputs.py"])
    print("\n[HOÀN TẤT] Xem notebook đã chạy tại outputs/notebooks/.")


if __name__ == "__main__":
    main()
