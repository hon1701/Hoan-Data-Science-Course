"""Execute every notebook cell on temporary synthetic data.

Synthetic data are used only to test code paths.  They are written to a
temporary directory, deleted after the test and never used in the report.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def make_data(path: Path) -> None:
    rng = np.random.default_rng(42)
    rows = 2_000
    target = np.zeros(rows, dtype=int)
    target[rng.choice(rows, size=100, replace=False)] = 1
    data: dict[str, np.ndarray] = {"Time": np.linspace(0, 172_000, rows)}
    for index in range(1, 29):
        values = rng.normal(0, 1, rows)
        if index in {10, 12, 14, 17}:
            values = values - target * (0.3 + index / 30)
        data[f"V{index}"] = values
    data["Amount"] = rng.lognormal(mean=3.0, sigma=1.1, size=rows)
    data["Class"] = target
    frame = pd.DataFrame(data)
    frame = pd.concat([frame, frame.iloc[:12]], ignore_index=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="eccc_a1_smoke_") as temporary:
        temp = Path(temporary)
        raw_path = temp / "creditcard.csv"
        output_root = temp / "run"
        make_data(raw_path)

        smoke_env = {
            "A1_PROJECT_ROOT": str(ROOT),
            "A1_DATA_PATH": str(raw_path),
            "A1_OUTPUT_ROOT": str(output_root),
            "A1_STRICT_DATASET": "0",
            "MPLBACKEND": "Agg",
        }
        previous_env = {key: os.environ.get(key) for key in smoke_env}
        previous_cwd = Path.cwd()
        notebook = json.loads((ROOT / "notebooks" / "01_data_eda.ipynb").read_text(encoding="utf-8"))
        namespace: dict[str, object] = {"__name__": "__a1_smoke__"}
        try:
            os.environ.update(smoke_env)
            os.chdir(ROOT)
            for index, cell in enumerate(notebook["cells"], start=1):
                if cell["cell_type"] != "code":
                    continue
                print(f"[..] Chạy code cell {index}")
                exec(compile(cell["source"], f"01_data_eda.ipynb:cell-{index}", "exec"), namespace)
        finally:
            os.chdir(previous_cwd)
            for key, value in previous_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

        subprocess.run(
            [
                sys.executable,
                "scripts/verify_a1_outputs.py",
                "--root",
                str(output_root),
                "--relaxed",
            ],
            cwd=ROOT,
            check=True,
        )
    print("[OK] Smoke test: toàn bộ cell chạy xong trên dữ liệu kiểm thử tạm thời.")


if __name__ == "__main__":
    main()
