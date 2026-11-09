"""ScholarSpace "Ask Notes": free full-text search inside the notes. No AI, no API keys, standard library only.

GET /api/search?q=<question>&subject=<optional subject id>
-> {"terms": [...], "keyPoints": [{"text", "n"}], "results": [{"n", "title", "subject", "subjectId", "course",
    "page", "url", "snippet"}]}

The index (api/_rag/index.db) is built by tools/rag/build_index.py: ~1,000-character passages from every
published PDF, Word and PowerPoint file, with an SQLite FTS5 full-text index.
1. Find the best passages with BM25 ranking (syllabus pages and papers weighted lower, max two per file).
2. In each passage, pick the sentences that match the question best ("key points" and a short snippet).
"""
import json
import math
import os
import re
import sqlite3
import threading
import zlib
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_rag", "index.db")
MAX_QUERY = 300
MAX_RESULTS = 6
SNIPPET = 480  # characters

STOP = set("""a an the is are was were be been being of in on at to for and or not no what which who whom how why
when where explain define definition describe discuss write short note notes about with by from as it its this that
these those give list difference differentiate between do does did can could should would will shall i me my we you
your please tell detail details brief briefly mean meaning example examples also more than then there their them
they he she his her us our any all some into over under using use used""".split())
SUFFIXES = ("ization", "ations", "ation", "ments", "ment", "ness", "ities", "ity", "ings", "ing", "ies", "ed", "es", "s")

_lock = threading.Lock()
_db = None
_fts = None
_memory = None  # fallback when the runtime's SQLite has no FTS5: [(id, file_id, page, lowercase text)]


def stem(word):
    for suf in SUFFIXES:
        if word.endswith(suf) and len(word) - len(suf) >= 3:
            return word[: -len(suf)]
    return word


def terms_of(text):
    return [t for t in dict.fromkeys(re.findall(r"[a-z0-9]+", text.lower())) if t not in STOP and len(t) > 1][:16]


def db():
    global _db, _fts
    with _lock:
        if _db is None:
            _db = sqlite3.connect(f"file:{DB_PATH}?mode=ro&immutable=1", uri=True, check_same_thread=False)
            try:
                _db.execute("SELECT rowid FROM chunks_fts WHERE chunks_fts MATCH 'test' LIMIT 1").fetchall()
                _fts = True
            except sqlite3.OperationalError:
                _fts = False
        return _db


def candidates(con, terms):
    """[(chunk id, score)] best first. FTS5 BM25 when available, else a simple in-memory TF-IDF scan."""
    global _memory
    if _fts:
        match = " OR ".join('"%s"' % t for t in terms)
        return con.execute("SELECT rowid, bm25(chunks_fts, 1.0, 0.75) FROM chunks_fts WHERE chunks_fts MATCH ? "
                           "ORDER BY bm25(chunks_fts, 1.0, 0.75) LIMIT 300", (match,)).fetchall()
    with _lock:
        if _memory is None:
            _memory = [(cid, zlib.decompress(t).decode("utf8").lower())
                       for cid, t in con.execute("SELECT id, text FROM chunks")]
    stems = [stem(t) for t in terms]
    df = [sum(1 for _, t in _memory if s in t) or 1 for s in stems]
    n = len(_memory)
    scored = []
    for cid, text in _memory:
        score = -sum(math.log(1 + text.count(s)) * math.log(n / d) for s, d in zip(stems, df))
        if score < 0:
            scored.append((cid, score))
    scored.sort(key=lambda r: r[1])
    return scored[:300]


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9•\-(])|\s*[•]\s*|\n+", text) if s.strip()]


def sentence_score(sent, stems):
    low = sent.lower()
    words = set(re.findall(r"[a-z0-9]+", low))
    hits = sum(1 for s in stems if any(w.startswith(s) for w in words))
    if hits and re.search(r"\b(is|are|refers to|means|defined as|known as)\b", low):
        hits += 0.5  # definitions make good answers
    if len(sent) < 30 or len(sent) > 400:
        hits *= 0.6
    return hits


def readable(sent):
    """A key point should be prose, not a table row, code or a list of numbers."""
    letters = sum(c.isalpha() for c in sent)
    return letters / len(sent) >= 0.7 and len(re.findall(r"[A-Za-z]{3,}", sent)) >= 6


def search(query, subject=None):
    terms = terms_of(query)
    if not terms:
        return {"terms": [], "keyPoints": [], "results": []}
    con = db()
    rows = candidates(con, terms)
    if not rows:
        return {"terms": terms, "keyPoints": [], "results": []}
    ids = [r[0] for r in rows]
    meta = {}
    for i in range(0, len(ids), 500):
        part = ids[i:i + 500]
        for cid, fid, page, text, sid, subj, course, title, kind, ocr in con.execute(
                "SELECT c.id, c.file_id, c.page, c.text, f.subject_id, f.subject, f.course, f.title, f.kind, c.ocr FROM chunks c "
                "JOIN files f ON f.id = c.file_id WHERE c.id IN (%s)" % ",".join("?" * len(part)), part):
            meta[cid] = (fid, page, text, sid, subj, course, title, kind, ocr)
    wants_papers = bool(re.search(r"\b(question|paper|pyq|exam|important)\b", query.lower()))
    weight = {"syllabus": 0.45, "papers": 1.0 if wants_papers else 0.8}
    ranked = sorted(((score * weight.get(meta[cid][7], 1.0), cid) for cid, score in rows
                     if cid in meta and (not subject or meta[cid][3] == subject)), key=lambda r: r[0])

    stems = [stem(t) for t in terms]
    results, per_file, points = [], {}, []
    for _, cid in ranked:
        fid, page, blob, sid, subj, course, title, kind, ocr = meta[cid]
        if per_file.get(fid, 0) >= 2:
            continue
        per_file[fid] = per_file.get(fid, 0) + 1
        n = len(results) + 1
        sents = sentences(zlib.decompress(blob).decode("utf8"))
        scores = [sentence_score(s, stems) for s in sents]
        best = max(range(len(sents)), key=lambda i: scores[i]) if sents else 0
        # snippet: the best sentence plus its neighbours, up to SNIPPET characters
        lo = hi = best
        snippet = sents[best] if sents else ""
        while len(snippet) < SNIPPET:
            grew = False
            if hi < len(sents) - 1:
                hi += 1
                grew = True
            if lo > 0 and len(" ".join(sents[lo - 1:hi + 1])) <= SNIPPET:
                lo -= 1
                grew = True
            snippet = " ".join(sents[lo:hi + 1])
            if not grew:
                break
        if len(snippet) > SNIPPET + 120:
            snippet = snippet[: SNIPPET + 120].rsplit(" ", 1)[0] + " …"
        results.append({"n": n, "title": title, "subject": subj, "subjectId": sid, "course": course, "page": page,
                         "url": "https://drive.google.com/file/d/%s/view" % fid, "scanned": bool(ocr),
                         "snippet": ("… " if lo > 0 else "") + snippet + (" …" if hi < len(sents) - 1 else "")})
        need = max(1, math.ceil(len(stems) * 0.6))
        for s, sc in zip(sents, scores):
            if kind != "syllabus" and sc >= max(1, need - 0.5) and 30 <= len(s) <= 400 and readable(s):
                points.append((bool(ocr), -sc, n, s))  # typed text first: OCR sentences only fill the gaps
        if len(results) >= MAX_RESULTS:
            break

    # key points must contain the question's most specific word (the one found in the fewest passages)
    texts = [" ".join(sentences(r["snippet"])).lower() for r in results]
    found = {st: sum(1 for t in texts if st in t) for st in stems}
    specific = min((st for st in stems if found[st]), key=lambda st: found[st], default=None)
    key_points, seen = [], set()
    for _, _, n, s in sorted(points)[:30]:
        if specific and len(stems) > 1 and specific not in s.lower():
            continue
        sig = re.sub(r"[^a-z0-9]", "", s.lower())[:80]
        if sig in seen:
            continue
        seen.add(sig)
        key_points.append({"text": s, "n": n})
        if len(key_points) >= 4:
            break
    return {"terms": stems, "keyPoints": key_points, "results": results}


class handler(BaseHTTPRequestHandler):
    def _send(self, status, body, cache=False):
        data = json.dumps(body, ensure_ascii=False).encode("utf8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        # identical searches are served from Vercel's cache for a day
        self.send_header("Cache-Control", "public, s-maxage=86400, max-age=300" if cache else "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        try:
            qs = parse_qs(urlparse(self.path).query)
            query = re.sub(r"\s+", " ", (qs.get("q") or [""])[0]).strip()[:MAX_QUERY]
            subject = (qs.get("subject") or [""])[0]
            if not re.fullmatch(r"[a-z0-9-]{2,60}", subject or ""):
                subject = None
            if len(query) < 2:
                return self._send(400, {"error": "Please type a question or topic."})
            self._send(200, search(query, subject), cache=True)
        except Exception as e:  # never show internals to visitors
            print("search failed:", repr(e))
            self._send(500, {"error": "Search isn't working right now. Please try again."})
