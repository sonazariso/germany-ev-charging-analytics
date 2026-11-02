#!/usr/bin/env python3
"""Report measured free disk and current project folder usage on macOS."""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
GB = 1024 ** 3


def size(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def main():
    usage = shutil.disk_usage(ROOT)
    print(f"Disk free on volume: {usage.free / GB:.2f} GiB")
    print(f"Disk total: {usage.total / GB:.2f} GiB")
    print(f"Current project size: {size(ROOT) / GB:.3f} GiB")
    for rel in ("data/raw", "data/staging", "data/analytics", "data/tmp", "data/profiles", "tableau"):
        print(f"  {rel:<16}: {size(ROOT / rel) / GB:.4f} GiB")
    if usage.free < 5 * GB:
        print("WARNING: Less than 5 GiB free. Remove old temp files / free space before large ETL.")
    elif usage.free < 10 * GB:
        print("NOTICE: 5–10 GiB free; use a smaller temporary data budget.")
    else:
        print("OK: >10 GiB free; sufficient initial headroom for Phase 01.")


if __name__ == "__main__":
    main()
