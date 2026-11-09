#!/usr/bin/env python3
"""Step 2 of the Ask AI index: turn the extracted text into a small SQLite search index for api/ask.py.

    python3 tools/rag/extract_text.py && python3 tools/rag/build_index.py

Output: api/_rag/index.db with
  files(id, subject_id, subject, course, title, kind)  one row per published file that has usable text
  chunks(id, file_id, page, text, ocr)           ~1,000-character passages; text is zlib-compressed;
                                                 ocr = 1 when the text was read from a scanned page by OCR
  chunks_fts                                     SQLite FTS5 full-text index over chunk text + file/subject names
Pages whose "text" is mostly OCR noise (common in scanned handwriting) are dropped.
"""
import collections
import json
import os
import re
import sqlite3
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(os.path.dirname(HERE))
CACHE = os.path.join(HERE, ".cache")
OUT = os.path.join(SITE, "api", "_rag", "index.db")
CHUNK = 1000      # target characters per passage
MIN_PAGE = 120    # characters; shorter pages are cover pages or blanks
WORD = re.compile(r"[a-z]{3,}")

sys.path.insert(0, os.path.dirname(HERE))
from rag.extract_text import catalog, published_files  # noqa: E402


def vocabulary(texts):
    words = set()
    for path in ("/usr/share/dict/words", "/usr/share/dict/american-english"):
        if os.path.exists(path):
            words |= {w.strip().lower() for w in open(path, encoding="utf8", errors="ignore")}
    seen_in = collections.Counter()
    for pages in texts.values():  # technical words used in several files count as real words too
        seen_in.update({w for p in pages for w in WORD.findall(p.lower())})  # (OCR typos rarely repeat across 4 files)
    return words | {w for w, n in seen_in.items() if n >= 4}


def readable(page, vocab, ocr=False):
    toks = WORD.findall(page.lower())
    if ocr:  # handwriting OCR is noisy; keep the page if enough real words came through for search
        return len(toks) >= 8 and sum(t in vocab for t in toks) / len(toks) >= 0.45
    return len(toks) >= 15 and sum(t in vocab for t in toks) / len(toks) >= 0.6


def chunks_of(page):
    """Split a page into ~CHUNK-character passages at sentence or line boundaries."""
    parts = re.split(r"(?<=[.!?:;])\s+|\n+", page)
    out, cur = [], ""
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if len(cur) + len(part) > CHUNK and len(cur) > CHUNK * 0.4:
            out.append(cur.strip()); cur = ""
        cur += part + " "
    if cur.strip():
        if out and len(cur) < CHUNK * 0.3:
            out[-1] += " " + cur.strip()
        else:
            out.append(cur.strip())
    return out


def main():
    cat = catalog()
    programs = {p["id"]: p for p in cat["programs"]}
    years = {1: "1st Year", 2: "2nd Year", 3: "3rd Year", 4: "4th Year"}
    files, subjects = {}, {}
    for s in cat["subjects"]:
        p = programs.get(s["program"], {})
        course = p.get("name", "") + (" · " + years[s["year"]] if s.get("year") else "")
        subjects[s["id"]] = (s["name"], course)
    for f in published_files():  # site files plus approved student uploads
        if f["subject"] in subjects:
            name, course = subjects[f["subject"]]
            files[f["id"]] = (f["subject"], name, course, f["t"], f["k"])
    texts, ocr_pages = {}, {}
    for fid in files:
        path = os.path.join(CACHE, fid + ".json")
        if os.path.exists(path):
            data = json.load(open(path, encoding="utf8"))
            texts[fid], ocr_pages[fid] = data["pages"], set(data.get("ocr", []))
    vocab = vocabulary(texts)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    if os.path.exists(OUT):
        os.remove(OUT)
    db = sqlite3.connect(OUT)
    db.executescript("""
        CREATE TABLE files(id TEXT PRIMARY KEY, subject_id TEXT, subject TEXT, course TEXT, title TEXT, kind TEXT);
        CREATE TABLE chunks(id INTEGER PRIMARY KEY, file_id TEXT, page INTEGER, text BLOB, ocr INTEGER);
        CREATE INDEX chunks_file ON chunks(file_id);
        CREATE VIRTUAL TABLE chunks_fts USING fts5(body, label, content='', tokenize='porter unicode61 remove_diacritics 2');
    """)
    n_files = n_chunks = dropped = n_ocr = 0
    for fid, pages in texts.items():
        sid, subject, course, title, kind = files[fid]
        rows = []
        for i, page in enumerate(pages, 1):
            page = re.sub(r"lOMoARcPSD\|\d+", " ", page)  # Studocu download watermark
            if len(page) < MIN_PAGE:
                continue
            is_ocr = i in ocr_pages.get(fid, ())
            if not readable(page, vocab, is_ocr):
                dropped += 1
                continue
            rows += [(i, c, int(is_ocr)) for c in chunks_of(page)]
        if not rows:
            continue
        db.execute("INSERT INTO files VALUES (?,?,?,?,?,?)", (fid, sid, subject, course, title, kind))
        label = f"{title} {subject}"
        for page, text, is_ocr in rows:
            cur = db.execute("INSERT INTO chunks(file_id, page, text, ocr) VALUES (?,?,?,?)",
                             (fid, page, zlib.compress(text.encode("utf8"), 9), is_ocr))
            db.execute("INSERT INTO chunks_fts(rowid, body, label) VALUES (?,?,?)", (cur.lastrowid, text, label))
            n_chunks += 1
            n_ocr += is_ocr
        n_files += 1
    db.execute("INSERT INTO chunks_fts(chunks_fts) VALUES ('optimize')")
    db.commit()
    db.execute("VACUUM")
    db.close()
    print(f"indexed files {n_files} of {len(files)}, passages {n_chunks} ({n_ocr} from scanned pages), noisy pages dropped {dropped}, "
          f"index {os.path.getsize(OUT) / 1e6:.1f} MB -> {os.path.relpath(OUT, SITE)}")


if __name__ == "__main__":
    main()
