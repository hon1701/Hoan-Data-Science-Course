"""Train validation-selected models for the full ECCC-LITE project."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.modeling import train_models  # noqa: E402


def main() -> None:
    summary = train_models(ROOT)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("[OK] Modeling hoàn tất; test chưa được truy cập.")


if __name__ == "__main__":
    main()

