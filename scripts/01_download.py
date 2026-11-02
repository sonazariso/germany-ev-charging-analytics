#!/usr/bin/env python3
"""Download complete, original official XLSX files; never sample or rewrite sources.

Python standard library only. Usage: python3 scripts/01_download.py
To register files downloaded manually: python3 scripts/01_download.py --verify-only
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config/sources.json"


def sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def metadata(source: dict, path: Path) -> dict:
    if not zipfile.is_zipfile(path):
        raise ValueError(f"Not a valid XLSX/ZIP: {path}. Check for an HTML error page instead.")
    with zipfile.ZipFile(path) as zf:
        required = {"[Content_Types].xml", "xl/workbook.xml"}
        if not required.issubset(zf.namelist()):
            raise ValueError(f"ZIP exists but is not a valid Excel workbook: {path}")
    return {
        "id": source["id"], "reference_date": source["reference_date"],
        "relative_path": source["path"], "download_url": source["url"],
        "bytes": path.stat().st_size, "sha256": sha256(path), "format": "xlsx",
    }


def download(url: str, dest: Path, retries: int = 2) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")
    headers = {"User-Agent": "Mozilla/5.0 (compatible; EVAnalyticsPortfolio/1.0)",
               "Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/octet-stream,*/*"}
    for attempt in range(retries + 1):
        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=90) as response, part.open("wb") as out:
                while chunk := response.read(1024 * 1024):
                    out.write(chunk)
            if not zipfile.is_zipfile(part):
                raise ValueError("Downloaded response is not XLSX (possibly blocked by remote website)")
            with zipfile.ZipFile(part) as archive:
                if "xl/workbook.xml" not in archive.namelist():
                    raise ValueError("Downloaded ZIP does not contain xl/workbook.xml")
            os.replace(part, dest)
            return
        except (OSError, urllib.error.URLError, ValueError) as exc:
            part.unlink(missing_ok=True)
            if attempt >= retries:
                raise RuntimeError(f"Failed to fetch {url}: {exc}") from exc
            time.sleep(2 * (attempt + 1))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true", help="Only inspect files already downloaded manually")
    parser.add_argument("--source", action="append", help="Download only selected source IDs (repeatable)")
    args = parser.parse_args()
    sources = json.loads(MANIFEST.read_text(encoding="utf-8"))["sources"]
    if args.source:
        sources = [s for s in sources if s["id"] in args.source]
        if len(sources) != len(set(args.source)):
            parser.error("Unknown --source ID; check config/sources.json")
    inventory = []
    failed = []
    for source in sources:
        path = ROOT / source["path"]
        try:
            if not path.exists():
                if args.verify_only:
                    print(f"[MISSING] {source['id']} => {path}")
                    failed.append(source["id"])
                    continue
                print(f"[DOWNLOAD] {source['id']} => {path}", flush=True)
                download(source["url"], path)
            else:
                print(f"[EXISTING] {source['id']}")
            item = metadata(source, path)
            inventory.append(item)
            print(f"[OK] {item['bytes'] / 1024 / 1024:.2f} MiB | SHA256 {item['sha256'][:16]}…")
        except Exception as exc:
            print(f"[ERROR] {source['id']}: {exc}")
            failed.append(source["id"])
    output = ROOT / "data/profiles/download_inventory.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {output.relative_to(ROOT)} | verified: {len(inventory)} | missing/failed: {len(failed)}")
    if failed:
        print("If automatic downloads are blocked, use the official source_page in config/sources.json,")
        print("download the XLSX manually into the exact path specified, then rerun --verify-only.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
