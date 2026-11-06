"""Turns posts written in the admin area (stored in Firestore) into the same shape as the Markdown posts in content/blog,
so the site build can give each one a permanent, search-engine-friendly page.

Published posts are public by design (see firebase/firestore.rules), so this reads them over plain HTTPS with no password.
If Firebase cannot be reached the build carries on without them; visitors still see them through the live blog page.
"""
from __future__ import annotations

import base64
import io
import json
import math
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image

import content as cm

SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DATA_URL = re.compile(r"^data:image/(?:jpeg|png|webp);base64,([A-Za-z0-9+/=]+)$")


def _val(f: dict):
    for k in ("stringValue", "booleanValue", "integerValue", "timestampValue"):
        if k in f:
            return f[k]
    return ""


def _decode(doc: dict) -> dict:
    out = {k: _val(v) for k, v in (doc.get("fields") or {}).items()}
    out["slug"] = doc.get("name", "").rsplit("/", 1)[-1]
    return out


class Source:
    """Where posts come from: Firestore over HTTPS, or a JSON file (used by the automated tests)."""

    def __init__(self, fb: dict | None):
        self.fb = fb
        self.file = os.environ.get("TB_CLOUD_POSTS_FILE")
        self.skip = os.environ.get("TB_SKIP_CLOUD_POSTS") == "1"
        self.fixture = json.loads(Path(self.file).read_text(encoding="utf8")) if self.file else None
        self.base = f"https://firestore.googleapis.com/v1/projects/{fb['projectId']}/databases/(default)/documents" if fb else ""

    def _call(self, url: str, body: dict | None = None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"} if data else {})
        with urllib.request.urlopen(req, timeout=12) as r:
            return json.load(r)

    def posts(self) -> list[dict] | None:
        if self.fixture is not None:
            return [p for p in self.fixture["posts"] if p.get("published") is True]
        if self.skip or not self.fb:
            return []
        q = {"structuredQuery": {"from": [{"collectionId": "posts"}], "where": {"fieldFilter": {
            "field": {"fieldPath": "published"}, "op": "EQUAL", "value": {"booleanValue": True}}}}}
        try:
            rows = self._call(f"{self.base}:runQuery?key={self.fb['apiKey']}", q)
        except (urllib.error.URLError, OSError, ValueError):
            return None
        return [_decode(r["document"]) for r in rows if "document" in r]

    def image(self, image_id: str) -> dict | None:
        if not SLUG.match(image_id):
            return None
        if self.fixture is not None:
            return self.fixture.get("images", {}).get(image_id)
        try:
            return _decode(self._call(f"{self.base}/postImages/{image_id}?key={self.fb['apiKey']}"))
        except (urllib.error.URLError, OSError, ValueError):
            return None


def _save_image(src: Source, image_id: str, dist: Path, cache: dict) -> dict | None:
    if image_id in cache:
        return cache[image_id]
    cache[image_id] = None
    doc = src.image(image_id)
    m = DATA_URL.match((doc or {}).get("data", ""))
    if not m:
        return None
    try:
        with Image.open(io.BytesIO(base64.b64decode(m.group(1)))) as im:
            im = im.convert("RGB")
            w, h = im.size
            rel = f"assets/img/posts/{image_id}.webp"
            out = dist / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            im.save(out, "WEBP", quality=80, method=4)
            r, g, b = im.resize((1, 1), Image.BOX).getpixel((0, 0))
    except Exception:
        return None
    cache[image_id] = {"file": rel, "w": w, "h": h, "ph": f"#{r:02x}{g:02x}{b:02x}", "alt": doc.get("alt", "")}
    return cache[image_id]


def load(fb: dict | None, photos: dict, dist: Path, taken: set[str], note) -> list[dict]:
    """Returns the published admin-area posts, ready for the templates. `note` reports problems that should not fail the build."""
    src = Source(fb)
    rows = src.posts()
    if rows is None:
        note("could not reach Firebase to fetch posts written in the admin area; they stay visible through the live blog page")
        return []
    images: dict = {}
    out = []
    for r in rows:
        slug = r.get("slug", "")
        if not SLUG.match(slug) or not r.get("title") or not r.get("body") or not re.match(r"^\d{4}-\d{2}-\d{2}$", r.get("date", "")):
            note(f"skipped admin post '{slug}': it is missing a title, text or date")
            continue
        if slug in taken:
            note(f"skipped admin post '{slug}': a post with that address already exists in the website files")
            continue
        for iid in set(re.findall(r"\(img:([a-z0-9-]+)\)", r["body"])):
            _save_image(src, iid, dist, images)
        body = r["body"].strip()
        item = {
            "slug": slug, "title": r["title"], "date": r["date"], "date_label": cm.date_label(r["date"]), "year": r["date"][:4],
            "summary": r.get("summary", ""), "summary_short": cm.shorten(r.get("summary", ""), 150), "image": None, "location": "",
            "body": body, "reading": max(1, math.ceil(len(re.findall(r"\w+", body)) / 200)), "cloud": True,
            "images": images, "cover_alt": r.get("coverAlt", ""),
        }
        cp = r.get("coverPhoto", "")
        if cp and cp in photos:
            item["image"] = cp
        elif r.get("coverImage"):
            img = _save_image(src, r["coverImage"], dist, images)
            if img:
                item.update(cover_file=img["file"], cover_w=img["w"], cover_h=img["h"], cover_ph=img["ph"], cover_alt=item["cover_alt"] or img["alt"])
        out.append(item)
    return out
