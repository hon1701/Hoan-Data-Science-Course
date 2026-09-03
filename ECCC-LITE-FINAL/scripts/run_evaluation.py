"""Run locked validation/test evaluation for the full project."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evaluation import evaluate_project  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bootstrap-iterations", type=int, default=1_000)
    args = parser.parse_args()
    summary = evaluate_project(ROOT, bootstrap_iterations=args.bootstrap_iterations)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("[OK] Evaluation và test cuối đã hoàn tất.")


if __name__ == "__main__":
    main()

