"""Loads the company-site content (JSON, Markdown, photos) and prepares it for templates.

Everything here is plain data work: no HTML pages are written in this file.
"""
from __future__ import annotations

import json
import math
import re
from datetime import date
from pathlib import Path

import markdown
from bs4 import BeautifulSoup
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
PHOTO_WIDTHS = (480, 960, 1600)
PHOTO_EXT = {".jpg", ".jpeg", ".png"}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf8"))


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def date_label(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%B %Y')}"


def shorten(text: str, limit: int = 150) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(",;: ")
    return cut + "…"


# --------------------------------------------------------------------------- #
# Photos: content/photos/* -> dist/assets/img/photos/<name>-<width>.webp
# --------------------------------------------------------------------------- #
def build_photos(dist: Path, warn) -> dict:
    """Creates responsive WebP copies of every photo and returns the manifest used by templates."""
    src_dir = CONTENT / "photos"
    out_dir = dist / "assets" / "img" / "photos"
    out_dir.mkdir(parents=True, exist_ok=True)
    meta_path = src_dir / "photos.json"
    alts = read_json(meta_path) if meta_path.exists() else {}
    manifest = {}
    for src in sorted(src_dir.iterdir()):
        if src.suffix.lower() not in PHOTO_EXT:
            continue
        name = src.stem
        with Image.open(src) as im:
            im = ImageOps.exif_transpose(im).convert("RGB")
            full_w, full_h = im.size
            widths = [w for w in PHOTO_WIDTHS if w < full_w] + [min(full_w, PHOTO_WIDTHS[-1])]
            widths = sorted(set(widths))
            for w in widths:
                target = out_dir / f"{name}-{w}.webp"
                if target.exists() and target.stat().st_mtime >= src.stat().st_mtime:
                    continue
                h = round(full_h * w / full_w)
                im.resize((w, h), Image.LANCZOS).save(target, "WEBP", quality=78, method=4)
            top = widths[-1]
            avg = im.resize((1, 1), Image.BOX).getpixel((0, 0))
            alt = alts.get(name, {}).get("alt")
            if not alt:
                warn(f"photo {name}: no alt text in content/photos/photos.json")
            manifest[name] = {
                "widths": widths,
                "default": 960 if 960 in widths else widths[-1],
                "w": top,
                "h": round(full_h * top / full_w),
                "ph": "#%02x%02x%02x" % avg,
                "alt": alt or name.replace("-", " "),
            }
    return manifest


def make_og_from_photo(photo_name: str, out: Path) -> None:
    """1200x630 social preview cropped from a photo."""
    src = next((p for p in (CONTENT / "photos").iterdir() if p.stem == photo_name), None)
    if not src:
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        im = ImageOps.fit(ImageOps.exif_transpose(im).convert("RGB"), (1200, 630), Image.LANCZOS, centering=(0.5, 0.4))
        im.save(out, "JPEG", quality=82, optimize=True)


def logo_sizes() -> dict:
    sizes = {}
    for f in (ROOT / "assets" / "img" / "partners").glob("*.webp"):
        with Image.open(f) as im:
            sizes[f.stem] = im.size
    return sizes


# --------------------------------------------------------------------------- #
# Markdown articles (blog + portfolio)
# --------------------------------------------------------------------------- #
def parse_front_matter(text: str) -> tuple[dict, str]:
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not m:
        raise ValueError("missing front matter")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, m.group(2).strip()


def render_markdown(body: str, photos: dict, root_hint: str = "{{ROOT}}") -> str:
    """Markdown -> HTML. ![alt](photo:name) becomes a responsive, click-to-enlarge figure.
    {{ROOT}} is replaced per page by the caller."""
    html = markdown.markdown(body, extensions=["sane_lists"])
    soup = BeautifulSoup(html, "html.parser")
    for h in soup.find_all("h1"):
        h.name = "h2"
    for a in soup.find_all("a", href=True):
        if a["href"].startswith("http"):
            a["rel"] = "noopener noreferrer"
            a["target"] = "_blank"
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if not src.startswith("photo:"):
            continue
        name = src[6:]
        p = photos[name]
        alt = img.get("alt") or p["alt"]
        srcset = ", ".join(f"{root_hint}assets/img/photos/{name}-{w}.webp {w}w" for w in p["widths"])
        fig = BeautifulSoup(
            f'<figure class="body-fig"><a href="{root_hint}assets/img/photos/{name}-{p["widths"][-1]}.webp" data-lightbox data-caption="{alt}">'
            f'<img src="{root_hint}assets/img/photos/{name}-{p["default"]}.webp" srcset="{srcset}" sizes="(min-width: 900px) 760px, 94vw" '
            f'width="{p["w"]}" height="{p["h"]}" alt="{alt}" loading="lazy" decoding="async" style="--ph:{p["ph"]}"></a></figure>',
            "html.parser",
        )
        target = img.parent if img.parent.name == "p" and len(img.parent.contents) == 1 else img
        target.replace_with(fig)
    return str(soup)


def load_articles(folder: str, photos: dict, kind: str) -> list[dict]:
    items = []
    for path in sorted((CONTENT / folder).glob("*.md")):
        meta, body = parse_front_matter(path.read_text(encoding="utf8"))
        words = len(re.findall(r"\w+", body))
        item = {
            "slug": path.stem,
            "title": meta["title"],
            "date": meta["date"],
            "date_label": date_label(meta["date"]),
            "year": meta["date"][:4],
            "summary": meta.get("summary", ""),
            "summary_short": shorten(meta.get("summary", ""), 150),
            "image": meta.get("image") or None,
            "location": meta.get("location", ""),
            "body": body,
            "reading": max(1, math.ceil(words / 200)),
        }
        if item["image"] and item["image"] not in photos:
            raise ValueError(f"{path.name}: unknown photo '{item['image']}' (add it to content/photos)")
        items.append(item)
    items.sort(key=lambda i: i["date"], reverse=True)
    return items


# --------------------------------------------------------------------------- #
# Company JSON data
# --------------------------------------------------------------------------- #
def load_company(photos: dict, total_lessons: int, course_count: int) -> dict:
    d = {p.stem: read_json(p) for p in (CONTENT / "company").glob("*.json")}
    for m in d["team"]:
        if m["photo"] not in photos:
            raise ValueError(f"team photo '{m['photo']}' missing")
    for f in d["faq"]:
        f.setdefault("slug", slugify(f["q"]))
    for t in d["testimonials"]:
        t.setdefault("slug", slugify(t["name"]))
    for t in d["tools"]:
        t["desc"] = t["desc"].replace("{lessons}", str(total_lessons)).replace("{courses}", str(course_count))
    sizes = logo_sizes()
    flat = []
    for group in ("schools", "orgs"):
        for p in d["partners"][group]:
            p["w"], p["h"] = sizes[p["logo"]]
            flat.append(p)
    d["partners_flat"] = flat
    d["faq_by"] = {f["slug"]: f for f in d["faq"]}
    return d
