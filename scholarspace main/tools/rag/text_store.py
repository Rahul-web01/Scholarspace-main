#!/usr/bin/env python3
"""Keep the extracted and OCR text in the repository, compressed, so nothing is ever read twice.

    python3 tools/rag/text_store.py pack     # tools/rag/.cache/*.json  -> tools/rag/text/*.json.gz (committed)
    python3 tools/rag/text_store.py unpack   # tools/rag/text/*.json.gz -> tools/rag/.cache/*.json

The nightly GitHub Action unpacks the store, reads only new files and pages, then packs it again. Packing is
deterministic (sorted keys, no timestamps), so unchanged files produce identical bytes and Git stores nothing new.
"""
import glob
import gzip
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, ".cache")
STORE = os.path.join(HERE, "text")


def pack():
    os.makedirs(STORE, exist_ok=True)
    changed = 0
    for path in glob.glob(os.path.join(CACHE, "*.json")):
        data = json.load(open(path, encoding="utf8"))
        raw = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf8")
        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode="wb", compresslevel=9, mtime=0) as gz:
            gz.write(raw)
        out = os.path.join(STORE, os.path.basename(path) + ".gz")
        if not os.path.exists(out) or open(out, "rb").read() != buf.getvalue():
            with open(out, "wb") as f:
                f.write(buf.getvalue())
            changed += 1
    print(f"packed {changed} changed file(s) into {os.path.relpath(STORE)}")


def unpack():
    os.makedirs(CACHE, exist_ok=True)
    n = 0
    for path in glob.glob(os.path.join(STORE, "*.json.gz")):
        out = os.path.join(CACHE, os.path.basename(path)[:-3])
        if os.path.exists(out) and os.path.getmtime(out) >= os.path.getmtime(path):
            continue  # the working copy is newer (e.g. a local run in progress)
        with gzip.open(path, "rb") as f, open(out, "wb") as g:
            g.write(f.read())
        n += 1
    print(f"unpacked {n} file(s) into {os.path.relpath(CACHE)}")


if __name__ == "__main__":
    {"pack": pack, "unpack": unpack}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: sys.exit(__doc__))()
