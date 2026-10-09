#!/usr/bin/env python3
"""Quality gate: checks the built site in /dist.
Fails (exit 1) on broken internal links, missing assets, duplicate ids or leftover
inline handlers. Prints warnings (exit 0) for softer problems such as long titles."""
import re, sys
from pathlib import Path
from urllib.parse import urldefrag, urlparse, unquote
from bs4 import BeautifulSoup

DIST = Path(__file__).resolve().parent.parent / "dist"
errors, warns = [], []
pages = sorted(DIST.rglob("*.html"))
ids_cache = {}

def page_ids(p):
    if p not in ids_cache:
        ids_cache[p] = {el["id"] for el in BeautifulSoup(p.read_text(encoding="utf8"), "lxml").select("[id]")}
    return ids_cache[p]

for page in pages:
    html = page.read_text(encoding="utf8")
    soup = BeautifulSoup(html, "lxml")
    rel = page.relative_to(DIST)
    if page.name == "404.html":
        base_is_root = True
    t = soup.title.get_text().strip() if soup.title else ""
    if not t: errors.append(f"{rel}: missing <title>")
    if len(t) > 110: warns.append(f"{rel}: long title ({len(t)} chars)")
    if not soup.find("meta", attrs={"name": "description"}): errors.append(f"{rel}: missing meta description")
    if len(soup.find_all("h1")) != 1: errors.append(f"{rel}: expected exactly one <h1>")
    if soup.select("[onclick],[onload],[onerror]"): errors.append(f"{rel}: inline event handler left in markup")
    seen = set()
    for el in soup.select("[id]"):
        if el["id"] in seen: errors.append(f"{rel}: duplicate id {el['id']!r}")
        seen.add(el["id"])
    for el in soup.select("a[href], link[href], script[src], img[src], source[src]"):
        ref = el.get("href") or el.get("src")
        if not ref or ref.startswith(("mailto:", "tel:", "data:", "javascript:")): continue
        u = urlparse(ref)
        if u.scheme in ("http", "https"):
            if el.name == "a" and el.get("target") == "_blank" and "noopener" not in (el.get("rel") or []): errors.append(f"{rel}: external link without rel=noopener: {ref}")
            continue
        path, frag = urldefrag(ref); path = path.split("?")[0]
        if not path: target = page
        else:
            target = (DIST / unquote(path.lstrip("/"))) if path.startswith("/") else (page.parent / unquote(path)).resolve()
            if target.is_dir(): target = target / "index.html"
            if not target.exists(): errors.append(f"{rel}: broken link {ref}"); continue
        if frag and target.suffix == ".html" and frag not in page_ids(target): errors.append(f"{rel}: missing anchor {ref}")

for need in ("sitemap.xml", "robots.txt", "manifest.webmanifest", "404.html", "favicon.ico", "assets/data/search.json"):
    if not (DIST / need).exists(): errors.append(f"missing {need}")
for w in warns[:20]: print("WARNING:", w)
for e in errors[:60]: print("ERROR:", e)
print(f"Checked {len(pages)} pages: {len(errors)} error(s), {len(warns)} warning(s)")
sys.exit(1 if errors else 0)
