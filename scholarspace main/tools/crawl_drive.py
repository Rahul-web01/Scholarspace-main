#!/usr/bin/env python3
"""Crawl a public Drive folder via embeddedfolderview. Usage: crawl_drive.py <root_id> <out.tsv>"""
import html, re, sys, urllib.request, concurrent.futures as cf
root, out = sys.argv[1], sys.argv[2]
ENTRY = re.compile(r'<a href="(https://drive\.google\.com/(?:drive/folders/|file/d/)([\w-]+)[^"]*)".*?flip-entry-title">([^<]*)<', re.S)
def fetch(fid):
    for _ in range(4):
        try:
            req = urllib.request.Request(f"https://drive.google.com/embeddedfolderview?id={fid}", headers={"User-Agent": "Mozilla/5.0"})
            return urllib.request.urlopen(req, timeout=60).read().decode("utf8", "replace")
        except Exception as e:
            err = e
    print("FAILED", fid, err, file=sys.stderr); return ""
rows, todo = [("", "folder", root)], [("", root)]
with cf.ThreadPoolExecutor(8) as ex:
    while todo:
        pages = list(ex.map(lambda t: (t[0], fetch(t[1])), todo)); todo = []
        for path, page in pages:
            for url, fid, name in ENTRY.findall(page):
                name = html.unescape(name); p = f"{path}/{name}" if path else name
                kind = "folder" if "/folders/" in url else "file"
                rows.append((p, kind, fid))
                if kind == "folder": todo.append((p, fid))
with open(out, "w") as f:
    for r in rows: f.write("\t".join(r) + "\n")
print("folders", sum(r[1]=="folder" for r in rows), "files", sum(r[1]=="file" for r in rows))
