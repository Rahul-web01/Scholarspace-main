#!/usr/bin/env python3
"""Step 1b of the Ask Notes index: read scanned and handwritten pages with OCR, so they become searchable too.

    pip install rapidocr onnxruntime          # CPU (slow: ~3 s per page)
    pip install rapidocr "onnxruntime-gpu[cuda,cudnn]"   # NVIDIA GPU (much faster)
    python3 tools/rag/extract_text.py         # first: normal text extraction
    python3 tools/rag/ocr_pages.py [--gpu]    # then: OCR the pages that had no text

Uses RapidOCR (PaddleOCR models, free and offline). For every published PDF page that has no text layer, and every
published image, it renders the page, reads it, and stores the result in tools/rag/.cache/<drive id>.json:
  "pages":    page texts (OCR text is written into the empty pages)
  "ocr":      page numbers (1-based) whose text came from OCR
  "ocr_done": page numbers already tried (so the script can be stopped and resumed at any time)
"""
import argparse
import collections
import concurrent.futures as cf
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from rag.extract_text import CACHE, download, local_paths, published_files  # noqa: E402

DPI = 150
MIN_TEXT = 120  # a page with less text than this is treated as scanned
AHEAD = 4       # pages rendered in advance on spare CPU cores while the OCR engine reads the current page
WORK = os.path.join(CACHE, ".work")


def make_engine(gpu):
    import logging
    from rapidocr import RapidOCR
    logging.getLogger("RapidOCR").setLevel(logging.WARNING)
    params = {}
    if gpu:
        import onnxruntime
        if hasattr(onnxruntime, "preload_dlls"):
            onnxruntime.preload_dlls()  # load the CUDA/cuDNN libraries installed by pip
        params = {"EngineConfig.onnxruntime.use_cuda": True}
    return RapidOCR(params=params)


def page_count(path):
    out = subprocess.run(["pdfinfo", path], capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("Pages:"):
            return int(line.split()[1])
    return 0


def render(path, page, out_dir):
    base = os.path.join(out_dir, "p")
    subprocess.run(["pdftoppm", "-f", str(page), "-l", str(page), "-r", str(DPI), "-gray", "-png", path, base],
                   check=True, capture_output=True, timeout=120)
    files = [f for f in os.listdir(out_dir) if f.startswith("p") and f.endswith(".png")]
    return os.path.join(out_dir, files[0]) if files else None


def render_job(path, page):
    """Render one page to a PNG in its own folder; returns (folder, png path, blank?)."""
    tmp = tempfile.mkdtemp(prefix="ocr-", dir=WORK)
    png = render(path, page, tmp)
    return tmp, png, (png is None or mostly_blank(png))


def mostly_blank(png):
    import cv2
    img = cv2.imread(png, cv2.IMREAD_GRAYSCALE)
    return img is None or (img < 128).mean() < 0.004  # under 0.4% dark pixels: an empty page


def read_image(engine, png):
    result = engine(png)
    return "\n".join(t for t in (result.txts or []) if t.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gpu", action="store_true", help="use an NVIDIA GPU (needs onnxruntime-gpu)")
    ap.add_argument("--limit", type=int, default=0, help="stop after this many pages (for testing)")
    ap.add_argument("--only", default="", help="read just this Drive file id")
    ap.add_argument("--max-minutes", type=float, default=0, help="stop (progress saved) after this many minutes")
    args = ap.parse_args()

    paths = local_paths()
    todo = []
    for f in published_files():
        if args.only and f["id"] != args.only:
            continue
        cache = os.path.join(CACHE, f["id"] + ".json")
        if f["x"] not in ("pdf", "jpg", "jpeg", "png") or not os.path.exists(cache):
            continue
        data = json.load(open(cache, encoding="utf8"))
        done = set(data.get("ocr_done", []))
        if f["x"] == "pdf":
            pages = [i + 1 for i, t in enumerate(data["pages"]) if len(t) < MIN_TEXT and i + 1 not in done]
        else:
            pages = [] if 1 in done else [1]
        if pages:
            todo.append((f["id"], f["x"], paths.get(f["id"]), pages))
    total = sum(len(p) for *_, p in todo)
    print(f"{len(todo)} files, {total} pages to read", flush=True)
    if not total:
        return

    engine = make_engine(args.gpu)
    shutil.rmtree(WORK, ignore_errors=True)  # leftovers from a run that was stopped
    os.makedirs(WORK, exist_ok=True)
    pool = cf.ThreadPoolExecutor(3)
    started, n = time.time(), 0
    for fid, ext, path, pages in todo:
        tmp_file = None
        try:
            if not path or not os.path.exists(path):
                tmp_file = path = download(fid, ext)
            cache = os.path.join(CACHE, fid + ".json")
            data = json.load(open(cache, encoding="utf8"))
            if ext != "pdf":
                data["pages"] = data.get("pages") or [""]
            ocr, done = set(data.get("ocr", [])), set(data.get("ocr_done", []))
            if ext == "pdf":  # pdftotext adds an empty "page" after the last form feed; skip pages past the end
                count = page_count(path)
                done |= {p for p in pages if p > count}
                pages = [p for p in pages if p <= count]
                n += len([p for p in done if p > count])
                if not pages:
                    data["ocr_done"] = sorted(done)
                    json.dump(data, open(cache, "w", encoding="utf8"), ensure_ascii=False)
                    continue
            queue, upcoming = collections.deque(), iter(pages)
            for page in pages[:AHEAD]:
                queue.append(pool.submit(render_job, path, page) if ext == "pdf" else None)
                next(upcoming)
            for k, page in enumerate(pages):
                job = queue.popleft()
                nxt = next(upcoming, None)
                if nxt is not None:
                    queue.append(pool.submit(render_job, path, nxt))
                if ext == "pdf":
                    tmp, png, blank = job.result()
                    try:
                        text = "" if blank else read_image(engine, png)
                    finally:
                        shutil.rmtree(tmp, ignore_errors=True)
                else:
                    text = read_image(engine, path)
                if len(text) >= 40:
                    data["pages"][page - 1] = text
                    ocr.add(page)
                done.add(page)
                n += 1
                if k % 10 == 9 or k == len(pages) - 1:  # save progress regularly so a stop loses little work
                    data["ocr"], data["ocr_done"] = sorted(ocr), sorted(done)
                    json.dump(data, open(cache + ".tmp", "w", encoding="utf8"), ensure_ascii=False)
                    os.replace(cache + ".tmp", cache)
                    rate = n / (time.time() - started)
                    print(f"{n}/{total} pages  {rate:.2f} pages/s  about {(total - n) / rate / 60:.0f} min left", flush=True)
                out_of_time = args.max_minutes and time.time() - started > args.max_minutes * 60
                if (args.limit and n >= args.limit) or out_of_time:
                    data["ocr"], data["ocr_done"] = sorted(ocr), sorted(done)
                    json.dump(data, open(cache + ".tmp", "w", encoding="utf8"), ensure_ascii=False)
                    os.replace(cache + ".tmp", cache)
                    print("stopping: time or page limit reached; the next run continues from here", flush=True)
                    return
        except Exception as e:  # one broken file must not stop the run
            print("PROBLEM", fid, repr(e)[:120], flush=True)
        finally:
            if tmp_file:
                os.unlink(tmp_file)


if __name__ == "__main__":
    main()
