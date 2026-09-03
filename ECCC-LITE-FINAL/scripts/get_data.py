"""Download and verify the ULB credit-card fraud dataset.

The raw CSV is intentionally not committed because it is about 151 MB.  This
script downloads the byte-identical public copy used by TensorFlow's official
imbalanced-data tutorial, verifies SHA-256, size, schema and fraud count, then
atomically places it at data/raw/creditcard.csv.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.a1_utils import (  # noqa: E402
    EXPECTED_FILE_SIZE,
    EXPECTED_SHA256,
    sha256_file,
    validate_raw_dataframe,
    verify_raw_file,
)

DATA_URL = "https://storage.googleapis.com/download.tensorflow.org/data/creditcard.csv"
DESTINATION = ROOT / "data" / "raw" / "creditcard.csv"


def download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    if partial.exists():
        partial.unlink()

    request = urllib.request.Request(url, headers={"User-Agent": "ECCC-LITE-A1/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response, partial.open("wb") as output:
        shutil.copyfileobj(response, output, length=1 << 20)

    size = partial.stat().st_size
    digest = sha256_file(partial)
    if size != EXPECTED_FILE_SIZE or digest != EXPECTED_SHA256:
        partial.unlink(missing_ok=True)
        raise RuntimeError(
            "Tệp tải về không khớp manifest chuẩn: "
            f"size={size}, sha256={digest}. Không thay thế dữ liệu hiện có."
        )

    frame = pd.read_csv(partial)
    validate_raw_dataframe(frame, strict=True)
    partial.replace(destination)


def main() -> None:
    parser = argparse.ArgumentParser(description="Tải và kiểm chứng creditcard.csv")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Tải lại ngay cả khi data/raw/creditcard.csv đã tồn tại.",
    )
    args = parser.parse_args()

    if DESTINATION.exists() and not args.force:
        info = verify_raw_file(DESTINATION, strict=True)
        print(f"[OK] Dữ liệu đã có và đúng SHA-256: {info['sha256']}")
        return

    print(f"[..] Đang tải khoảng 151 MB từ {DATA_URL}")
    download(DATA_URL, DESTINATION)
    info = verify_raw_file(DESTINATION, strict=True)
    print(f"[OK] Đã lưu: {DESTINATION}")
    print(f"[OK] SHA-256: {info['sha256']}")


if __name__ == "__main__":
    main()

