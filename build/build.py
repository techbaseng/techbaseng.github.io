#!/usr/bin/env python3
"""Techbase Academy site builder.

Reads /content (course metadata + lesson sources) and /templates, and writes the
finished static site to /dist. Runs in GitHub Actions; nothing here has to be run
by hand. See docs/CUSTOMIZING.md for what to edit where.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound

ROOT = Path(__file__).resolve().parent.parent
CONTENT, TEMPLATES, ASSETS, DIST = ROOT / "content", ROOT / "templates", ROOT / "assets", ROOT / "dist"

EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿⭐️‍]+")
LEVELS = {"beg": "Beginner", "int": "Intermediate", "adv": "Advanced"}
LEXERS = {
    "html": "html", "starter.html": "html", "xml": "xml", "css": "css", "scss": "scss",
    "javascript": "javascript", "js": "javascript", "python": "python", "starter.py": "python",
    "json": "json", "bash": "bash", "php": "php", "sql": "sql", "java": "java",
    "csharp": "csharp", "apache": "apache", "nginx": "nginx",
}
warnings: list[str] = []


def warn(msg: str) -> None:
    warnings.append(msg)


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def strip_emoji(text: str) -> str:
    return clean(EMOJI.sub("", text))


def frag(html: str):
    return BeautifulSoup(html, "html.parser")


# --------------------------------------------------------------------------- #
# Lesson body cleanup (shared by both lesson layouts)
# --------------------------------------------------------------------------- #
def eval_template_literal(raw: str) -> str:
    """The old pages passed starter code to JS as a `template literal`; undo that."""
    out = re.sub(r"\\(.)", lambda m: {"n": "\n", "t": "\t"}.get(m.group(1), m.group(1)), raw)
    return out


def convert_handlers(scope) -> None:
    """Replace inline onclick handlers with data-action attributes (CSP-safe)."""
    for el in scope.select("[onclick]"):
        oc = el["onclick"]
        del el["onclick"]
        label = clean(EMOJI.sub("", el.get_text()))
        if oc.startswith("unlockNext("):
            el["data-action"] = "unlock"
            el["data-n"] = re.search(r"\((\d+)\)", oc).group(1)
            el.string = re.sub(r"\s*[✓✅]\s*$", "", label)
        elif oc.startswith("copyCode"):
            el["data-action"] = "copy"
            el["aria-label"] = "Copy code"
            el.clear()
            el.extend(list(frag('<svg class="icon" aria-hidden="true"><use href="#i-copy"></use></svg><span data-label>Copy</span>').contents))
        elif oc.startswith(("toggleReveal", "toggleCode")):
            el["data-action"] = "reveal"
            el["aria-expanded"] = "false"
            el["data-show"] = label
            el["data-hide"] = re.sub(r"^Reveal", "Hide", label)
            el.string = label
        elif oc.startswith("showGithub"):
            el["data-action"] = "github"
            el.string = label
        elif oc.startswith("toggleGh"):
            el["data-action"] = "toggle-gh"
        elif oc.startswith("showEnd"):
            el["data-action"] = "finish"
            el.string = label
        elif oc.startswith("downloadStarter("):
            body = oc[oc.index("`") + 1: oc.rindex("`")]
            el["data-action"] = "download"
            el["data-starter"] = eval_template_literal(body)
            el["data-filename"] = "starter.html"
            el.string = label
        elif oc.startswith("alert("):
            el["data-action"] = "alert"
            el["data-msg"] = re.search(r"alert\(['\"](.*)['\"]\)", oc).group(1)
        else:
            warn(f"unhandled onclick: {oc[:60]!r}")


REPAIRED: list[str] = []


def repair_stray_markup(scope, name: str) -> None:
    """A few sources contain sample code that was never escaped, so it became real page
    elements (extra <h1>, <link>, <img>). Show it as the code it was meant to be."""
    for el in scope.select("link, meta, base, img[src]"):
        src = el.get("src", "")
        if el.name == "img" and (src.startswith(("http", "data:")) or el.find_parent(class_="pb2") is None and el.find_parent(class_="build-req") is None):
            continue
        code = scope.new_tag("code")
        code.string = str(el)
        el.replace_with(code)
        REPAIRED.append(name)
    for el in scope.select("h1"):
        el.name = "h2"
        REPAIRED.append(name)


def normalise_body(scope, name: str = "") -> None:
    repair_stray_markup(scope, name)
    convert_handlers(scope)
    # tidy inline styles that existed only to colour buttons / lay out button rows
    for el in scope.select("[style]"):
        style = el["style"].replace(" ", "")
        if el.name == "img":
            continue
        if el.name == "button" and "#10b981" in style:
            el["class"] = el.get("class", []) + ["is-green"]
        elif el.name == "button" and "#059669" in style:
            el["class"] = el.get("class", []) + ["is-green"]
        elif el.name == "button" and "#0f172a" in style:
            el["class"] = el.get("class", []) + ["is-secondary"]
        elif el.name == "div" and "display:flex" in style:
            el["class"] = el.get("class", []) + ["btn-row"]
        del el["style"]
    for el in scope.select("a[href^='http']"):
        el["rel"] = "noopener noreferrer"
    for el in scope.select(".v2-dot"):
        el["aria-hidden"] = "true"
    for el in scope.select(".v2-code-body"):
        el["tabindex"] = "0"
        el["role"] = "region"
        lang = el.parent.select_one(".v2-code-lang")
        el["aria-label"] = f"{clean(lang.get_text()) if lang else 'Code'} example"
    for el in scope.select("img:not([alt])"):
        el["alt"] = ""
    # syntax highlighting at build time
    for wrap in scope.select(".v2-code-wrap"):
        lang_el = wrap.select_one(".v2-code-lang")
        code = wrap.select_one("code")
        if not (lang_el and code):
            continue
        name = LEXERS.get(clean(lang_el.get_text()).lower())
        if not name:
            continue
        try:
            lexer = get_lexer_by_name(name, startinline=True) if name == "php" else get_lexer_by_name(name)
        except ClassNotFound:
            continue
        html = highlight(code.get_text(), lexer, HtmlFormatter(nowrap=True, classprefix="tk-"))
        code.clear()
        code.append(frag(html))


# --------------------------------------------------------------------------- #
# Parsers
# --------------------------------------------------------------------------- #
def parse_interactive(path: Path) -> dict:
    soup = BeautifulSoup(path.read_text(encoding="utf8"), "lxml")
    body = soup.body
    main = soup.select_one("main")
    # some sources have unbalanced <div>s, so the parser keeps the old page chrome inside <main>
    for junk in main.select("footer, #toast, #go-top, #cc, script"):
        junk.decompose()
    phases = [clean(p.get_text()) for p in main.select(".phase .pt")]
    for p in main.select(".phase"):
        p["class"] = [c for c in p.get("class", []) if c != "locked"]
    for se in main.select(".se"):
        for ln in se.select(".ln"):
            ln.decompose()
        for li in se.select("li"):
            li.string = strip_emoji(li.get_text())
    for gh in main.select(".gh-acc"):
        if gh.has_attr("style"):
            del gh["style"]
        hd = gh.select_one(".gh-hd")
        if hd:
            hd.name = "button"
            hd["type"] = "button"
            hd["aria-label"] = "Show or hide the GitHub Pages steps"
            hd.clear()
            hd.extend(list(frag('<span style="transform:none">Push to GitHub Pages</span><span aria-hidden="true">▾</span>').contents))
            hd.select("span")[0]["style"] = "transform:none"
    # un-hide the structure the old script toggled with inline styles
    normalise_body(main, path.parent.parent.name + "/" + path.name)
    for hd in main.select(".gh-hd span:first-child"):
        del hd["style"]
    for ph in main.select(".phase .ph"):
        ph["id"] = None
        del ph["id"]
    chips = [strip_emoji(s.get_text()) for s in soup.select(".wm span")]
    return {
        "title_tag": clean(soup.title.get_text()),
        "h1": clean(soup.select_one(".l-hero h1").get_text()),
        "kicker": clean(soup.select_one(".badge").get_text()),
        "chips": [c for c in chips if c],
        "phases": phases,
        "key": body.get("data-key", ""),
        "total": int(body.get("data-total", len(phases))),
        "body": main.decode_contents(),
    }


def card_html(head: str, body_el, course_label: str) -> str:
    for el in body_el.select("[style]"):
        del el["style"]
    for a in body_el.select("a[href^='http']"):
        a["rel"] = "noopener noreferrer"
    if head == "Official Project":
        a = body_el.select_one("a")
        note = body_el.select_one("p")
        label = strip_emoji(a.get_text()).replace("↗", "").strip()
        return (
            f'<div class="side-card"><div class="side-head">{head}</div><div class="side-official">'
            f'<a class="btn btn--course" href="{a["href"]}" target="_blank" rel="noopener noreferrer">{label} '
            '<svg class="icon" aria-hidden="true"><use href="#i-external"></use></svg></a>'
            f'<p>{clean(note.get_text()) if note else ""}</p></div></div>'
        )
    cls = "side-card side-card--list" if body_el.select(".side-row") else "side-card"
    return f'<div class="{cls}"><div class="side-head">{head}</div><div class="side-body">{body_el.decode_contents()}</div></div>'


def parse_project(path: Path, course_label: str) -> dict:
    soup = BeautifulSoup(path.read_text(encoding="utf8"), "lxml")
    hero = soup.select_one(".lesson-hero-inner")
    badge = hero.select_one(".level-badge")
    btn = hero.select_one(".rpi-btn")
    note = hero.select_one(".rpi-note")
    body = soup.select_one(".lesson-body")
    for nav in body.select(".lesson-nav"):
        nav.decompose()
    for el in body.select("[style]"):
        del el["style"]
    for a in body.select("a[href^='http']"):
        a["rel"] = "noopener noreferrer"
    sidebar = "".join(
        card_html(clean(c.select_one(".side-head").get_text()), c.select_one(".side-body"), course_label)
        for c in soup.select(".side-card")
    )
    meta = soup.find("meta", attrs={"name": "description"})
    badge_classes = [c for c in (badge.get("class", []) if badge else []) if c.startswith("badge-")]
    return {
        "title_tag": clean(soup.title.get_text()),
        "h1": clean(hero.select_one("h1").get_text()),
        "kicker": clean(hero.select_one(".lesson-n").get_text()),
        "tagline": clean(hero.select_one(".lesson-tagline").get_text()) if hero.select_one(".lesson-tagline") else "",
        "level_label": clean(badge.get_text()) if badge else "",
        "level_class": badge_classes[0] if badge_classes else "",
        "ext": {
            "href": btn["href"],
            "label": strip_emoji(btn.get_text()).replace("↗", "").strip(),
            "note": clean(note.get_text()) if note else "",
        } if btn else None,
        "meta_description": meta["content"] if meta else "",
        "body": body.decode_contents(),
        "sidebar": sidebar,
    }


# --------------------------------------------------------------------------- #
# Site assembly
# --------------------------------------------------------------------------- #
def load_courses() -> list[dict]:
    meta = json.loads((CONTENT / "courses.json").read_text(encoding="utf8"))
    by_slug = {c["slug"]: c for c in meta}
    out = []
    for m in meta:
        raw = json.loads((CONTENT / m["slug"] / "course.json").read_text(encoding="utf8"))
        c = {**raw, **m}
        files = sorted(p.name for p in (CONTENT / m["slug"] / "lessons").glob("lesson_*.html"))
        flat = [l for ph in c["phases"] for l in ph["lessons"]]
        listed = [l["file"] for l in flat]
        if sorted(listed) != files:
            warn(f"{m['slug']}: index lists {len(listed)} lessons but folder has {len(files)}")
        c["flat"] = flat
        c["total"] = len(flat)
        c["count"] = f"{len(flat)} {m['noun']}s"
        c["first"] = flat[0]
        for ph in c["phases"]:
            mt = re.match(r"^(.*?)\s*\(([^)]*)\)\s*(?:·\s*(.*))?$", ph["name"])
            ph["name_main"] = mt.group(1) if mt else ph["name"]
            ph["range"] = (mt.group(2) + (" · " + mt.group(3).lower() if mt.group(3) else "")) if mt else ""
            for l in ph["lessons"]:
                l["level_label"] = LEVELS.get(l["level"], "")
        used = {l["level"] for l in flat if l["level"]}
        c["levels"] = [{"id": k, "label": v} for k, v in LEVELS.items() if k in used]
        out.append(c)
    for c in out:
        c["prev_course"] = next((x for x in out if x["slug"] == c.get("prev")), None)
        c["next_course"] = next((x for x in out if x["slug"] == c.get("next")), None)
    return out


def pager_html(course: dict, idx: int) -> str:
    flat = course["flat"]
    parts = []
    if idx > 0:
        p = flat[idx - 1]
        parts.append(f'<a class="prev" href="{p["file"]}"><small>Previous {course["noun"]}</small><b>{p["num"]} · {esc(p["title"])}</b></a>')
    if idx < len(flat) - 1:
        n = flat[idx + 1]
        parts.append(f'<a class="next" href="{n["file"]}"><small>Next {course["noun"]}</small><b>{n["num"]} · {esc(n["title"])}</b></a>')
    else:
        nc = course["next_course"]
        href, small, big = ("../../" + nc["slug"] + "/index.html", "Course complete. Up next", nc["title"]) if nc else ("../index.html", "Course complete", "Back to all " + course["noun"] + "s")
        parts.append(f'<a class="next" href="{href}"><small>{small}</small><b>{esc(big)}</b></a>')
    return '<nav class="lesson-pager" aria-label="Lesson navigation">' + "".join(parts) + "</nav>"


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main() -> int:
    site = json.loads((CONTENT / "site.json").read_text(encoding="utf8"))
    paths = json.loads((CONTENT / "paths.json").read_text(encoding="utf8"))
    courses = load_courses()
    course_by_slug = {c["slug"]: c for c in courses}
    for p in paths:
        p["key"] = course_by_slug[p["start"]]["key"]
    total_lessons = sum(c["total"] for c in courses)
    base_url = site["url"].rstrip("/")

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    # old files from the previous hub site are ignored if they are still in the repository
    shutil.copytree(ASSETS, DIST / "assets", ignore=shutil.ignore_patterns("site.css", "site.js"))
    for name in ("favicon.ico",):
        if (ASSETS / "img" / name).exists():
            shutil.move(str(DIST / "assets" / "img" / name), DIST / name)
    for static in (ROOT / "static").glob("*") if (ROOT / "static").exists() else []:
        shutil.copy(static, DIST / static.name)

    theme_script = (TEMPLATES / "theme_inline.js").read_text(encoding="utf8").strip()
    theme_hash = "sha256-" + __import__("base64").b64encode(hashlib.sha256(theme_script.encode()).digest()).decode()
    csp = ("default-src 'self'; script-src 'self' '" + theme_hash + "'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
           "font-src https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'none'")
    asset_v = hashlib.md5(b"".join(p.read_bytes() for p in sorted(ASSETS.glob("*/*.*")) if p.suffix in (".css", ".js"))).hexdigest()[:8]

    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape(["html"]), trim_blocks=False)

    def render(tpl: str, out: Path, *, root: str, path: str, title: str, description: str, og: str, og_alt: str, jsonld=None, **ctx):
        html = env.get_template(tpl).render(
            site=site, courses=courses, paths=paths, total_lessons=total_lessons, root=root, abs_root=root,
            csp=csp, theme_script=theme_script, asset_v=asset_v, title=title, description=description,
            canonical=f"{base_url}/{path}", og_image=f"{base_url}/assets/img/og/{og}.png", og_alt=og_alt,
            jsonld=json.dumps(jsonld, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") if jsonld else None, **ctx,
        )
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf8")

    org = {"@type": "EducationalOrganization", "name": site["org"], "url": site["links"]["website"], "address": {"@type": "PostalAddress", "addressLocality": "Ibadan", "addressCountry": "NG"}}
    sitemap = [f"{base_url}/"]
    search = []

    # ---- hub
    render("hub.html", DIST / "index.html", root="", path="", title="Techbase STEM Academy — Free Coding Courses",
           description=site["description"], og="default", og_alt="Techbase Academy: free coding and robotics courses from Ibadan, Nigeria", nav_active="courses",
           jsonld={"@context": "https://schema.org", "@graph": [
               {"@type": "WebSite", "name": site["full_name"], "url": base_url + "/", "inLanguage": "en", "publisher": org},
               org]})

    # ---- 404 (root-absolute so it works at any depth)
    render("404.html", DIST / "404.html", root="/", path="404.html", title="Page not found — Techbase Academy",
           description="This page could not be found.", og="default", og_alt="Techbase Academy", robots="noindex")

    # ---- courses + lessons
    n_pages = 2
    for c in courses:
        slug = c["slug"]
        sitemap.append(f"{base_url}/{slug}/")
        desc = c["meta_description"] or f"Free {c['title']} course: {c['total']} {c['noun']}s from Techbase Consultant Services, Ibadan, Nigeria."
        n_pages += 1
        for idx, l in enumerate(c["flat"]):
            src = CONTENT / slug / "lessons" / l["file"]
            if not src.exists():
                warn(f"missing lesson file {src}")
                continue
            interactive = c["kind"] == "interactive"
            data = parse_interactive(src) if interactive else parse_project(src, c["title"])
            if data["h1"].lower().strip(" .") != l["title"].lower().strip(" ."):
                pass  # titles differ slightly between index and page in some lessons; the page heading wins
            if interactive:
                l["key"], l["phases"] = data["key"], data["total"]
                description = (f"Lesson {l['num']} of {c['total']} in Techbase's free {c['short']} course: {l['title']}. "
                               f"{len(data['phases'])} guided phases with practice tasks and a mini project.")
            else:
                description = f"{data['meta_description'] or data['tagline']} Free {c['short']} project {l['num']} of {c['total']} from Techbase Academy."
            if len(data["title_tag"]) > 75:
                short = re.split(r" · | — |: ", data["h1"])[0]
                label = "Lesson" if interactive else "Project"
                data["title_tag"] = f"{label} {l['num']}: {short} — Techbase {c['short']}"
            lesson = {**data, "file": l["file"], "num": l["num"], "interactive": interactive, "pager": pager_html(c, idx)}
            lesson["tagline"] = data.get("tagline", "")
            url = f"{base_url}/{slug}/lessons/{l['file']}"
            ld = {"@context": "https://schema.org", "@graph": [
                {"@type": "LearningResource", "name": data["h1"], "description": description, "url": url, "inLanguage": "en", "isAccessibleForFree": True,
                 "learningResourceType": "lesson" if interactive else "project guide", "isPartOf": {"@type": "Course", "name": c["title"], "url": f"{base_url}/{slug}/"}, "provider": org},
                {"@type": "BreadcrumbList", "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Techbase Academy", "item": base_url + "/"},
                    {"@type": "ListItem", "position": 2, "name": c["title"], "item": f"{base_url}/{slug}/"},
                    {"@type": "ListItem", "position": 3, "name": data["h1"], "item": url}]}]}
            render("lesson.html", DIST / slug / "lessons" / l["file"], root="../../", path=f"{slug}/lessons/{l['file']}", title=data["title_tag"],
                   description=description[:300], og=slug, og_alt=f"{c['title']}: {data['h1']}", course=c, lesson=lesson, nav_active="course",
                   body_class=f"c-{c['key']}", og_type="article", jsonld=ld)
            sitemap.append(url)
            search.append({"c": c["key"], "cs": c["short"], "n": l["num"], "t": data["h1"], "d": l.get("desc", ""), "u": f"{slug}/lessons/{l['file']}"})
            n_pages += 1

    # ---- course pages need per-lesson keys (known only after lessons are parsed): re-render course pages
    for c in courses:
        render("course.html", DIST / c["slug"] / "index.html", root="../", path=f"{c['slug']}/", title=c["page_title"],
               description=c["meta_description"] or f"Free {c['title']} course: {c['total']} {c['noun']}s from Techbase Consultant Services, Ibadan, Nigeria.",
               og=c["slug"], og_alt=f"{c['title']}: a free Techbase Academy course", course=c, nav_active="course", body_class=f"c-{c['key']}",
               jsonld={"@context": "https://schema.org", "@type": "Course", "name": c["title"], "provider": org, "inLanguage": "en", "isAccessibleForFree": True,
                       "url": f"{base_url}/{c['slug']}/", "description": c["meta_description"] or c["title"]})

    # ---- data + SEO files
    (DIST / "assets" / "data").mkdir(parents=True, exist_ok=True)
    (DIST / "assets" / "data" / "search.json").write_text(json.dumps(search, ensure_ascii=False, separators=(",", ":")), encoding="utf8")
    urls = "".join(f"  <url><loc>{u}</loc></url>\n" for u in sitemap)
    (DIST / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n', encoding="utf8")
    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {base_url}/sitemap.xml\n", encoding="utf8")
    (DIST / "manifest.webmanifest").write_text(json.dumps({
        "name": site["full_name"], "short_name": site["name"], "description": site["tagline"], "start_url": "/", "scope": "/", "display": "standalone",
        "background_color": "#fafaf8", "theme_color": site["theme_color"], "lang": "en",
        "icons": [
            {"src": "/assets/img/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/assets/img/icon-512.png", "sizes": "512x512", "type": "image/png"},
            {"src": "/assets/img/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}]}, indent=2), encoding="utf8")
    (DIST / ".nojekyll").write_text("", encoding="utf8")
    (DIST / "_headers").write_text(
        "/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n  X-Frame-Options: SAMEORIGIN\n"
        "  Permissions-Policy: camera=(), microphone=(), geolocation=()\n", encoding="utf8")

    if REPAIRED:
        print("Repaired unescaped sample markup in:", ", ".join(sorted(set(REPAIRED))))
    print(f"Built {n_pages} pages ({total_lessons} lessons) into {DIST}")
    for w in warnings:
        print("ERROR:", w)
    return 1 if warnings else 0


if __name__ == "__main__":
    sys.exit(main())
