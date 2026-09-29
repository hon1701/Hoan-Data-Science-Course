"""Execute all notebooks in order and verify the complete project."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
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
    parser.add_argument("--skip-report", action="store_true", help="Chỉ chạy và kiểm tra code/notebook.")
    parser.add_argument("--rebuild-notebooks", action="store_true", help="Tạo lại 02/03/Final từ script mẫu.")
    args = parser.parse_args()

    manifest_path = ROOT / "outputs" / "run_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()
    manifest_path.write_text(json.dumps({"status": "running", "started_utc": started}), encoding="utf-8")
    if args.rebuild_notebooks:
        run([sys.executable, "scripts/build_notebooks.py"])
    run([sys.executable, "-m", "pytest", "-q", "--junitxml=outputs/tests.xml"])
    if not args.skip_data_check:
        run([sys.executable, "scripts/get_data.py"])
    execute_notebook("01_data_eda.ipynb", "01_data_eda.executed.ipynb")
    execute_notebook("02_modeling.ipynb", "02_modeling.executed.ipynb")
    execute_notebook("03_evaluation.ipynb", "03_evaluation.executed.ipynb")
    execute_notebook("Fraud_Project_Final.ipynb", "Fraud_Project_Final.executed.ipynb")
    run([sys.executable, "scripts/verify_project.py"])
    if not args.skip_report:
        run([sys.executable, "scripts/build_report.py"])
    files = {}
    for pattern in ("src/*.py", "scripts/*.py", "config/*.json", "notebooks/*.ipynb",
                    "outputs/tables/*", "outputs/figures/*.png", "outputs/notebooks/*.ipynb"):
        for path in sorted(ROOT.glob(pattern)):
            if path.is_file() and path.name != ".gitkeep":
                files[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    frozen = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True)
    (ROOT / "outputs" / "requirements-lock.txt").write_text(frozen, encoding="utf-8")
    payload = {"status": "complete", "started_utc": started,
               "completed_utc": datetime.now(timezone.utc).isoformat(),
               "source_commit": os.environ.get("GITHUB_SHA"),
               "workflow_run_id": os.environ.get("GITHUB_RUN_ID"),
               "report_built": not args.skip_report, "sha256": files}
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n[HOÀN TẤT] Xem outputs/notebooks, outputs/tables, outputs/figures và reports/.")


if __name__ == "__main__":
    main()
