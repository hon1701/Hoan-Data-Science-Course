"""Chạy notebook ôn tập trong kernel sạch và báo cell lỗi đầu tiên."""

from __future__ import annotations

import argparse
from pathlib import Path

import nbformat
from nbclient import NotebookClient


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "notebooks"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("patterns", nargs="*", default=["on_tap_*.ipynb"])
    args = parser.parse_args()

    paths: list[Path] = []
    for pattern in args.patterns:
        paths.extend(NOTEBOOK_DIR.glob(pattern))

    paths = sorted(set(paths))
    if not paths:
        raise SystemExit("Không tìm thấy notebook cần kiểm tra.")

    failures: list[str] = []
    for path in paths:
        try:
            with path.open("r", encoding="utf-8") as stream:
                nb = nbformat.read(stream, as_version=4)
            NotebookClient(
                nb,
                timeout=120,
                kernel_name="python3",
                resources={"metadata": {"path": str(ROOT)}},
            ).execute()
            print(f"PASS {path.name} ({len(nb.cells)} cells)")
        except Exception as exc:  # báo gọn, traceback đầy đủ vẫn có ở exception nếu cần
            failures.append(f"FAIL {path.name}: {type(exc).__name__}: {exc}")
            print(failures[-1])

    if failures:
        raise SystemExit("\n".join(failures))


if __name__ == "__main__":
    main()
