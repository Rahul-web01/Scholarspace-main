#!/usr/bin/env python3
"""Step 1 of the Ask AI index: extract text, page by page, from every file published on the site.

    python3 tools/rag/extract_text.py            # uses the default local folders below
    SS_DATA_ROOT=... SS_BBA_ROOT=... python3 tools/rag/extract_text.py

Reads assets/js/catalog.js (which files are on the site), the approved student uploads (from the uploads web app
in assets/js/config.js, saved to tools/rag/community.json) and the Drive trees (where each file lives). Each file is
taken from the local copy of the Drive folder, or downloaded from its public Drive link if there is no local copy,
and written to tools/rag/.cache/<drive id>.json = {"pages": ["text of page 1", ...]}.
Files already in the cache are skipped, so re-runs only process new uploads.
Scanned or handwritten PDFs have no text layer and come out empty; they are simply not searchable.
"""
import concurrent.futures as cf
import html
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(os.path.dirname(HERE))
CACHE = os.path.join(HERE, ".cache")
ROOTS = [
    ("drive-tree.tsv", os.environ.get("SS_DATA_ROOT", "/run/media/rahul-singh/New Volume/ScholarSpace Data")),
    ("bba-drive-tree.tsv", os.environ.get("SS_BBA_ROOT", "/run/media/rahul-singh/New Volume/BBA")),
]


def catalog():
    src = open(os.path.join(SITE, "assets", "js", "catalog.js"), encoding="utf8").read()
    return json.loads(re.search(r"window\.CATALOG = (.*);\s*$", src, re.S).group(1))


COMMUNITY = os.path.join(HERE, "community.json")


def uploads_url():
    src = open(os.path.join(SITE, "assets", "js", "config.js"), encoding="utf8").read()
    m = re.search(r'uploadsUrl:\s*"([^"]*)"', src)
    return m.group(1) if m else ""


def refresh_community():
    """Save the list of approved student uploads (if the uploads web app is set up)."""
    url = uploads_url()
    if not url:
        return
    try:
        req = urllib.request.Request(url + "?action=list", headers={"User-Agent": "Mozilla/5.0"})
        items = json.load(urllib.request.urlopen(req, timeout=60)).get("items", [])
    except Exception as e:  # keep the last saved list if the web app can't be reached
        print("could not fetch approved uploads:", e, file=sys.stderr)
        return
    with open(COMMUNITY, "w", encoding="utf8") as f:
        json.dump(sorted(items, key=lambda it: it.get("id", "")), f, ensure_ascii=False, indent=1)


def published_files():
    """Every file the site shows: [{"id", "x" (extension), "k" (type), "t" (title), "subject" (id)}]."""
    files, seen = [], set()
    for s in catalog()["subjects"]:
        for f in s.get("files", []):
            files.append({"id": f["id"], "x": f["x"], "k": f["k"], "t": f["t"], "subject": s["id"]})
            seen.add(f["id"])
    if os.path.exists(COMMUNITY):  # approved student uploads
        for it in json.load(open(COMMUNITY, encoding="utf8")):
            if it.get("f") and it["f"] not in seen:
                files.append({"id": it["f"], "x": it.get("x") or "pdf", "k": it.get("k") or "notes",
                              "t": it.get("t") or "Student upload", "subject": it.get("s", ""), "community": True})
                seen.add(it["f"])
    return files


def local_paths():
    paths = {}
    for tree, root in ROOTS:
        for line in open(os.path.join(SITE, "tools", tree), encoding="utf8"):
            p, kind, fid = line.rstrip("\n").split("\t")
            if kind == "file":
                paths[fid] = os.path.join(root, p)
    return paths


def xml_text(raw):
    raw = re.sub(r"</w:p>|</a:p>|<w:br/>|<w:tab/>", "\n", raw)
    return html.unescape(re.sub(r"<[^>]+>", "", raw))


def pages_of(path, ext):
    if ext == "pdf":
        out = subprocess.run(["pdftotext", "-q", "-enc", "UTF-8", path, "-"], capture_output=True, timeout=300).stdout
        return out.decode("utf8", "replace").split("\f")
    if ext == "docx":
        z = zipfile.ZipFile(path)
        text = xml_text(z.read("word/document.xml").decode("utf8", "replace"))
        # Word files have no fixed pages: cut them into ~3000-character "pages" at paragraph breaks.
        out, cur = [], ""
        for para in text.split("\n"):
            if len(cur) > 3000:
                out.append(cur); cur = ""
            cur += para + "\n"
        return out + [cur]
    if ext == "pptx":
        z = zipfile.ZipFile(path)
        slides = sorted((n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)),
                        key=lambda n: int(re.search(r"(\d+)", n.rsplit("/", 1)[1]).group(1)))
        return [xml_text(z.read(n).decode("utf8", "replace")) for n in slides]
    return []  # images and old .ppt files have no extractable text


def download(fid, ext):
    # drive.usercontent with confirm=t also works for big files that show a "can't scan for viruses" page
    url = "https://drive.usercontent.google.com/download?export=download&confirm=t&id=" + fid
    data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=120).read()
    if data[:200].lstrip().lower().startswith((b"<!doctype html", b"<html")):
        raise RuntimeError("Drive returned a web page instead of the file (is it shared publicly?)")
    tmp = tempfile.NamedTemporaryFile(suffix="." + ext, delete=False)
    tmp.write(data); tmp.close()
    return tmp.name


def work(item):
    fid, ext, path = item
    out = os.path.join(CACHE, fid + ".json")
    if os.path.exists(out):
        return fid, "cached"
    tmp = None
    try:
        if not path or not os.path.exists(path):
            if ext not in ("pdf", "docx", "pptx"):
                pages = []
            else:
                tmp = path = download(fid, ext)
        pages = pages_of(path, ext) if path else []
        status = "ok"
    except Exception as e:  # a broken file should not stop the whole build
        pages, status = [], "error: " + str(e)[:80]
    finally:
        if tmp:
            os.unlink(tmp)
    with open(out, "w", encoding="utf8") as f:
        json.dump({"pages": [re.sub(r"[ \t\r\x00-\x08\x0b-\x1f]+", " ", p).strip() for p in pages]}, f, ensure_ascii=False)
    return fid, status


def main():
    os.makedirs(CACHE, exist_ok=True)
    refresh_community()
    paths = local_paths()
    items = [(f["id"], f["x"], paths.get(f["id"])) for f in published_files()]
    done = errors = 0
    with cf.ThreadPoolExecutor(max(2, (os.cpu_count() or 4))) as ex:
        for fid, status in ex.map(work, items):
            done += 1
            if status.startswith("error"):
                errors += 1
                print("PROBLEM", fid, status, file=sys.stderr)
    print(f"files {done}, errors {errors}, cache {CACHE}")


if __name__ == "__main__":
    main()
