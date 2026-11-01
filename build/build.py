#!/usr/bin/env python3
"""Techbase site builder.

Reads /content (company pages, Academy courses and lesson sources) and /templates, and writes the
finished static site to /dist. Runs in GitHub Actions; nothing here has to be run by hand.
See docs/CUSTOMIZING.md for what to edit where.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, pass_context, select_autoescape

sys.path.insert(0, str(Path(__file__).resolve().parent))
import academy_parse as ap

import cloudposts
import content as cm

ROOT = cm.ROOT
CONTENT, TEMPLATES, ASSETS, DIST = ROOT / "content", ROOT / "templates", ROOT / "assets", ROOT / "dist"
JS_BUILD = ROOT / ".build" / "js"  # written by build/bundle.mjs (Firebase code), before this script runs
CACHE = ROOT / ".cache" / "lessons"

NAV = [
    {"label": "Services", "href": "services/", "key": "services"},
    {"label": "Learn", "href": "learn/", "key": "learn"},
    {"label": "Portfolio", "href": "portfolio/", "key": "portfolio"},
    {"label": "About", "href": "about/", "key": "about"},
    {"label": "Blog", "href": "blog/", "key": "blog"},
    {"label": "Contact", "href": "contact/", "key": "contact"},
]
warnings: list[str] = []
notes: list[str] = []   # things worth knowing that must not fail a build


def warn(msg: str) -> None:
    warnings.append(msg)


# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
def firebase_config() -> dict | None:
    """Firebase web settings come from GitHub Actions secrets. They identify the project; they are not passwords."""
    cfg = {
        "apiKey": os.environ.get("FIREBASE_API_KEY", "").strip(),
        "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN", "").strip(),
        "projectId": os.environ.get("FIREBASE_PROJECT_ID", "").strip(),
        "appId": os.environ.get("FIREBASE_APP_ID", "").strip(),
    }
    if not all(cfg.values()):
        return None
    cfg["appCheckSiteKey"] = os.environ.get("FIREBASE_APPCHECK_SITE_KEY", "").strip()
    return cfg


def build_csp(theme_hash: str, fb: dict | None) -> str:
    scripts = ["'self'", f"'{theme_hash}'"]
    connect = ["'self'"]
    frames: list[str] = []
    if fb:
        scripts.append("https://apis.google.com")
        connect += ["https://*.googleapis.com", "https://*.firebaseio.com"]
        frames += [f"https://{fb['authDomain']}", "https://accounts.google.com"]
        if fb["appCheckSiteKey"]:
            scripts += ["https://www.google.com/recaptcha/", "https://www.gstatic.com/recaptcha/"]
            frames += ["https://www.google.com", "https://recaptcha.google.com"]
    parts = [
        "default-src 'self'",
        "script-src " + " ".join(scripts),
        "style-src 'self' 'unsafe-inline'",
        "font-src 'self'",
        "img-src 'self' data:",
        "connect-src " + " ".join(connect),
        "worker-src 'self'",
        "manifest-src 'self'",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'none'",
    ]
    if frames:
        parts.append("frame-src " + " ".join(frames))
    return "; ".join(parts)


# --------------------------------------------------------------------------- #
# Academy data
# --------------------------------------------------------------------------- #
def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def load_courses() -> list[dict]:
    meta = cm.read_json(CONTENT / "courses.json")
    out = []
    for m in meta:
        raw = cm.read_json(CONTENT / m["slug"] / "course.json")
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
                l["level_label"] = ap.LEVELS.get(l["level"], "")
        used = {l["level"] for l in flat if l["level"]}
        c["levels"] = [{"id": k, "label": v} for k, v in ap.LEVELS.items() if k in used]
        out.append(c)
    for c in out:
        c["prev_course"] = next((x for x in out if x["slug"] == c.get("prev")), None)
        c["next_course"] = next((x for x in out if x["slug"] == c.get("next")), None)
    return out


def pager_html(course: dict, idx: int, u) -> str:
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
        href, small, big = ("../../" + nc["slug"] + "/index.html", "Course complete. Up next", nc["title"]) if nc else ("../../learn/index.html", "Course complete", "Back to all courses")
        parts.append(f'<a class="next" href="{href}"><small>{small}</small><b>{esc(big)}</b></a>')
    return '<nav class="lesson-pager" aria-label="Lesson navigation">' + "".join(parts) + "</nav>"


def parse_lesson_cached(src: Path, interactive: bool, course_title: str) -> dict:
    """Parsing 472 lessons takes about a minute, so results are cached by file content (cache is not committed)."""
    key = hashlib.sha1(src.read_bytes() + Path(ap.__file__).read_bytes() + (b"i" if interactive else b"p")).hexdigest()
    f = CACHE / f"{key}.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf8"))
    data = ap.parse_interactive(src) if interactive else ap.parse_project(src, course_title)
    CACHE.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(data, ensure_ascii=False), encoding="utf8")
    return data


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> int:
    site = cm.read_json(CONTENT / "site.json")
    paths = cm.read_json(CONTENT / "paths.json")
    fb = firebase_config()
    site["accounts"] = bool(fb)
    courses = load_courses()
    course_by_slug = {c["slug"]: c for c in courses}
    for p in paths:
        p["key"] = course_by_slug[p["start"]]["key"]
    total_lessons = sum(c["total"] for c in courses)
    base_url = site["url"].rstrip("/")
    free_n = int(site.get("free_preview_lessons", 1))

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    shutil.copytree(ASSETS, DIST / "assets", ignore=shutil.ignore_patterns("site.css.old", "README.md"))
    shutil.move(str(DIST / "assets" / "img" / "favicon.ico"), DIST / "favicon.ico")
    if JS_BUILD.exists():
        for f in JS_BUILD.iterdir():
            shutil.copy(f, DIST / "assets" / "js" / f.name)
    elif fb:
        warn("accounts are on but .build/js is missing: run `node build/bundle.mjs` first (the deploy workflow does)")

    photos = cm.build_photos(DIST, warn)
    company = cm.load_company(photos, total_lessons, len(courses))
    portfolio = cm.load_articles("portfolio", photos, "portfolio")
    posts = cm.load_articles("blog", photos, "blog")
    static_slugs = [p["slug"] for p in posts]
    cloud_posts = cloudposts.load(fb, photos, DIST, set(static_slugs), notes.append)
    todo = [p["slug"] for p in posts if p.get("image_todo") and not p["image"]]
    if todo:
        notes.append(f"{len(todo)} blog posts are waiting for a picture (see docs/IMAGE_TODO.md)")
    posts = sorted(posts + cloud_posts, key=lambda p: p["date"], reverse=True)
    years = sorted({e["year"] for e in portfolio}, reverse=True)

    theme_script = (TEMPLATES / "theme_inline.js").read_text(encoding="utf8").strip()
    theme_hash = "sha256-" + base64.b64encode(hashlib.sha256(theme_script.encode()).digest()).decode()
    csp = build_csp(theme_hash, fb)
    sources = sorted(p for d in (DIST / "assets" / "css", DIST / "assets" / "js") for p in d.glob("*") if p.suffix in (".css", ".js"))
    asset_v = hashlib.md5(b"".join(p.read_bytes() for p in sources)).hexdigest()[:8]

    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape(["html"]), trim_blocks=False)

    @pass_context
    def u(ctx, path: str) -> str:
        """Relative link to a page: 'about/' -> '../about/index.html' (works on the live site and from a downloaded preview)."""
        if path.startswith(("http", "mailto:", "tel:", "#")):
            return path
        frag = ""
        if "#" in path:
            path, frag = path.split("#", 1)
            frag = "#" + frag
        if path == "" or path.endswith("/"):
            path += "index.html"
        return ctx.get("root", "") + path + frag

    env.filters["u"] = u

    org = {"@type": "EducationalOrganization", "name": site["company"]["name"], "url": base_url + "/", "logo": base_url + "/assets/img/icon-512.png",
           "telephone": site["company"]["phone"], "email": site["company"]["email"],
           "address": {"@type": "PostalAddress", "streetAddress": "Moniya", "addressLocality": "Ibadan", "addressRegion": "Oyo State", "addressCountry": "NG"},
           "sameAs": list(site["company"]["social"].values())}
    sitemap: list[str] = []
    search: list[dict] = []
    written: set[str] = set()

    def render(tpl: str, out: str, *, title: str, description: str, og: str = "company", og_alt: str = "Techbase Consultant Services, Ibadan, Nigeria",
               og_path: str | None = None, jsonld=None, index: bool = True, absolute: bool = False, **ctx) -> None:
        depth = out.count("/")
        root = "/" if absolute else "../" * depth
        canon_path = out.removesuffix("index.html")
        og_rel = og_path or f"assets/img/og/{og}.png"
        html = env.get_template(tpl).render(
            site=site, courses=courses, paths=paths, total_lessons=total_lessons, root=root, nav=NAV, photos=photos,
            csp=csp, theme_script=theme_script, asset_v=asset_v, title=title, description=description[:300],
            fb_public=({"project": fb["projectId"], "key": fb["apiKey"]} if fb else None),
            canonical=f"{base_url}/{canon_path}", og_image=f"{base_url}/{og_rel}", og_alt=og_alt,
            robots=None if index else "noindex, follow",
            jsonld=json.dumps(jsonld, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") if jsonld else None, **ctx,
        )
        html = html.replace("{{ROOT}}", root)
        target = DIST / out
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf8")
        written.add(out)
        if index:
            sitemap.append(f"{base_url}/{canon_path}")

    def add_search(kind, label, t, d, url, c="site", n=""):
        search.append({"k": kind, "c": c, "cs": label, "n": n, "t": t, "d": d, "u": url})

    company_ctx = dict(services=company["services"], why=company["why"], process=company["process"], team=company["team"],
                       testimonials=company["testimonials"], partners=company["partners"], partners_flat=company["partners_flat"],
                       tools=company["tools"], faq=company["faq"], faq_by=company["faq_by"], careers=company["careers"],
                       portfolio=portfolio, posts=posts, years=years,
                       post_years=[{"year": y, "posts": [p for p in posts[1:] if p["year"] == y]} for y in sorted({p["year"] for p in posts[1:]}, reverse=True)])

    crumb = lambda *items: {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": f"{base_url}/{p}"} for i, (n, p) in enumerate(items)]}

    # ---- company pages ------------------------------------------------------
    render("home.html", "index.html", title="Techbase Consultant Services: STEM, coding and robotics training in Nigeria",
           description="Techbase empowers youth for the digital future through STEM excellence: coding and robotics training, curriculum design, web and app development and AI tools, from Ibadan, Nigeria.",
           og="company", nav_active="home", section="site", jsonld={"@context": "https://schema.org", "@graph": [org, {"@type": "WebSite", "name": site["company"]["name"], "url": base_url + "/", "inLanguage": "en", "publisher": {"@type": "EducationalOrganization", "name": site["company"]["name"]}}]},
           **company_ctx)
    add_search("page", "Home", "Techbase Consultant Services", "STEM education, coding and robotics training, web and app development, AI tools", "index.html")

    simple_pages = [
        ("about.html", "about/", "About Techbase Consultant Services", "Techbase is a STEM education and technology consultancy in Ibadan, Nigeria, making technology education accessible, structured and practical.", "about", "About", "Who we are, our process and our partners"),
        ("services.html", "services/", "Services: STEM training, web and app development, curriculum and AI", "STEM coding and robotics training, web and app development, curriculum and teaching aids, and AI and tech solutions for schools, businesses and individuals.", "services", "Services", "STEM training, web and app development, curriculum, AI solutions"),
        ("team.html", "team/", "Our team: educators, developers and STEM practitioners", "Meet the Techbase team: experienced STEM educators and developers making technology accessible to every learner.", "about", "Team", "Meet the Techbase instructors and consultants"),
        ("testimonials.html", "testimonials/", "Testimonials: what schools, parents and professionals say", "Read what schools, parents and professionals say about working with Techbase Consultant Services.", "about", "Testimonials", "What clients say about Techbase"),
        ("tools.html", "tools/", "Tools and resources built by Techbase", "Free tools and guides built by Techbase: the STEM Academy, an AI prompt library, career and Android guides and climate resources.", None, "Tools", "Free tools, guides and resources built by Techbase"),
        ("contact.html", "contact/", "Contact Techbase: start a conversation", "Contact Techbase Consultant Services in Moniya, Ibadan by WhatsApp, phone, email or the enquiry form.", "contact", "Contact", "Send an enquiry, call, email or WhatsApp"),
        ("careers.html", "careers/", "Careers: join the Techbase team", "Join Techbase as a STEM instructor, developer or curriculum designer and help Nigerian learners build digital skills.", "about", "Careers", "Apply to teach or build with Techbase"),
        ("privacy.html", "privacy/", "Privacy: how this website handles your data", "A plain-language description of what the Techbase website stores, where, and the choices you have.", None, "Privacy", "How this website handles your data"),
    ]
    for tpl, path, title, desc, nav, label, sdesc in simple_pages:
        extra = {}
        if tpl == "privacy.html":
            extra["updated"] = "October 2026"
        render(tpl, path + "index.html", title=title, description=desc, nav_active=nav, section="site",
               jsonld={"@context": "https://schema.org", **crumb(("Home", ""), (label, path))} if False else {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Home", "item": base_url + "/"}, {"@type": "ListItem", "position": 2, "name": label, "item": f"{base_url}/{path}"}]},
               **company_ctx, **extra)
        add_search("page", label, label, sdesc, path + "index.html")

    faq_ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in company["faq"]]}
    render("faq.html", "faq/index.html", title="FAQ: your questions about Techbase programmes", description="Answers to common questions about Techbase training: ages, virtual and in-school delivery, certificates, laptops, AI training for teachers and how to enrol.",
           nav_active=None, section="site", jsonld=faq_ld, **company_ctx)
    add_search("page", "FAQ", "Frequently asked questions", "Ages, delivery, certificates, laptops, enrolling", "faq/index.html")
    for f in company["faq"]:
        add_search("faq", "FAQ", f["q"], cm.shorten(f["a"], 110), f"faq/index.html#{f['slug']}")

    # portfolio
    render("portfolio.html", "portfolio/index.html", title="Portfolio: programmes and events by Techbase", description="Photos and stories from Techbase programmes: school coding and robotics, community STEM sessions, girls in tech days and conferences.",
           nav_active="portfolio", section="site", **company_ctx)
    add_search("page", "Portfolio", "Portfolio", "Programmes and events we have run", "portfolio/index.html")
    for i, e in enumerate(portfolio):
        og_rel = f"assets/img/og/p-{e['slug']}.jpg"
        cm.make_og_from_photo(e["image"], DIST / og_rel)
        prev = portfolio[i + 1] if i + 1 < len(portfolio) else None
        nxt = portfolio[i - 1] if i > 0 else None
        html = cm.render_markdown(e["body"], photos)
        render("portfolio_item.html", f"portfolio/{e['slug']}/index.html", title=f"{e['title']}: Techbase programme", description=e["summary"], og_path=og_rel, og_alt=e["title"],
               nav_active="portfolio", section="site", item={**e, "html": html}, prev=prev, next=nxt, og_type="article",
               jsonld={"@context": "https://schema.org", "@graph": [
                   {"@type": "Article", "headline": e["title"], "datePublished": e["date"], "description": e["summary"], "image": f"{base_url}/{og_rel}", "author": {"@type": "Organization", "name": site["company"]["name"]}, "publisher": org},
                   {"@type": "BreadcrumbList", "itemListElement": [
                       {"@type": "ListItem", "position": 1, "name": "Home", "item": base_url + "/"},
                       {"@type": "ListItem", "position": 2, "name": "Portfolio", "item": base_url + "/portfolio/"},
                       {"@type": "ListItem", "position": 3, "name": e["title"], "item": f"{base_url}/portfolio/{e['slug']}/"}]}]},
               **company_ctx)
        add_search("event", "Portfolio", e["title"], e["location"], f"portfolio/{e['slug']}/index.html")

    # blog
    render("blog.html", "blog/index.html", title="Blog: coding, robotics and AI guides for Nigerian parents and teachers", description="Practical guides on why children should learn to code, robotics for schools, AI for teachers and the STEM skills Nigerian children need for 2030.",
           nav_active="blog", section="site", **company_ctx)
    add_search("page", "Blog", "Blog", "Guides for parents, teachers and schools", "blog/index.html")
    for i, p in enumerate(posts):
        og_rel = f"assets/img/og/b-{p['slug']}.jpg"
        if p["image"]:
            cm.make_og_from_photo(p["image"], DIST / og_rel)
        elif p.get("cover_file"):
            cm.make_og_from_file(DIST / p["cover_file"], DIST / og_rel)
        else:
            og_rel = "assets/img/og/company.png"
        lo = max(0, min(i - 1, len(posts) - 4))   # posts published around the same time
        related = [x for x in posts[lo:lo + 4] if x["slug"] != p["slug"]][:3]
        render("post.html", f"blog/{p['slug']}/index.html", title=p["title"] if len(p["title"]) < 65 else cm.shorten(p["title"], 62), description=p["summary"], og_path=og_rel, og_alt=p["title"],
               nav_active="blog", section="site", post={**p, "html": cm.render_markdown(p["body"], photos, images=p.get("images"), untrusted=bool(p.get("cloud")))}, related=related, og_type="article",
               jsonld={"@context": "https://schema.org", "@graph": [
                   {"@type": "Article", "headline": p["title"], "datePublished": p["date"], "description": p["summary"], "image": f"{base_url}/{og_rel}", "author": {"@type": "Organization", "name": site["company"]["name"]}, "publisher": org, "mainEntityOfPage": f"{base_url}/blog/{p['slug']}/"},
                   {"@type": "BreadcrumbList", "itemListElement": [
                       {"@type": "ListItem", "position": 1, "name": "Home", "item": base_url + "/"},
                       {"@type": "ListItem", "position": 2, "name": "Blog", "item": base_url + "/blog/"},
                       {"@type": "ListItem", "position": 3, "name": p["title"], "item": f"{base_url}/blog/{p['slug']}/"}]}]},
               **company_ctx)
        add_search("post", "Blog", p["title"], cm.shorten(p["summary"], 110), f"blog/{p['slug']}/index.html")

    # accounts
    render("login.html", "login/index.html", title="Log in or create a free account | Techbase Academy", description="Sign in or create a free Techbase account to save your progress across devices.",
           index=False, section="learn", nav_active="learn", **company_ctx)
    render("account.html", "account/index.html", title="Your account | Techbase Academy", description="Manage your Techbase account and see your learning progress.",
           index=False, section="learn", nav_active="learn", **company_ctx)
    if site["accounts"]:
        add_search("page", "Account", "Log in or create an account", "Save your progress across devices", "login/index.html")
    # blog admin + the live page for posts published since the last build (neither is listed in search engines)
    render("admin.html", "admin/index.html", title="Admin | Techbase", description="Write and publish blog posts.", index=False, section="site", nav_active="blog", **company_ctx)
    render("post_live.html", "blog/post/index.html", title="Article | Techbase blog", description="A Techbase blog article.", index=False, section="site", nav_active="blog", **company_ctx)
    render("offline.html", "offline.html", title="Offline | Techbase", description="You are offline.", index=False, section="site", **company_ctx)

    # ---- Academy ------------------------------------------------------------
    render("learn.html", "learn/index.html", title="Techbase STEM Academy: free coding courses", description=site["description"],
           og="learn", og_alt="Techbase Academy: free coding and robotics courses from Ibadan, Nigeria", nav_active="learn", section="learn", **company_ctx,
           jsonld={"@context": "https://schema.org", "@graph": [{"@type": "WebSite", "name": site["full_name"], "url": base_url + "/learn/", "inLanguage": "en", "publisher": org}, org]})
    add_search("page", "Academy", "Techbase Academy", f"{total_lessons} free lessons across {len(courses)} courses", "learn/index.html")

    render("404.html", "404.html", title="Page not found | Techbase", description="This page could not be found.", index=False, section="site", absolute=True, **company_ctx)  # served at any depth, so links are root-absolute
    sitemap[:] = [s for s in sitemap if not s.endswith("/404.html")]

    n_pages = len(written)
    for c in courses:
        slug = c["slug"]
        sitemap.append(f"{base_url}/{slug}/")
        add_search("course", "Course", c["title"], c["blurb"], f"{slug}/index.html", c=c["key"])
        for idx, l in enumerate(c["flat"]):
            src = CONTENT / slug / "lessons" / l["file"]
            if not src.exists():
                warn(f"missing lesson file {src}")
                continue
            interactive = c["kind"] == "interactive"
            data = parse_lesson_cached(src, interactive, c["title"])
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
            lesson = {**data, "file": l["file"], "num": l["num"], "interactive": interactive, "pager": pager_html(c, idx, u)}
            lesson["tagline"] = data.get("tagline", "")
            url = f"{base_url}/{slug}/lessons/{l['file']}"
            ld = {"@context": "https://schema.org", "@graph": [
                {"@type": "LearningResource", "name": data["h1"], "description": description, "url": url, "inLanguage": "en", "isAccessibleForFree": True,
                 "learningResourceType": "lesson" if interactive else "project guide", "isPartOf": {"@type": "Course", "name": c["title"], "url": f"{base_url}/{slug}/"}, "provider": org},
                {"@type": "BreadcrumbList", "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Techbase Academy", "item": base_url + "/learn/"},
                    {"@type": "ListItem", "position": 2, "name": c["title"], "item": f"{base_url}/{slug}/"},
                    {"@type": "ListItem", "position": 3, "name": data["h1"], "item": url}]}]}
            gate = "free" if idx < free_n else "locked"
            render("lesson.html", f"{slug}/lessons/{l['file']}", title=data["title_tag"], description=description, og=slug,
                   og_alt=f"{c['title']}: {data['h1']}", course=c, lesson=lesson, nav_active="learn", section="learn",
                   body_class=f"c-{c['key']}", og_type="article", jsonld=ld, gate=gate, **company_ctx)
            sitemap[-1] = url  # lessons keep their own file URL (not a folder)
            add_search("lesson", c["short"], data["h1"], l.get("desc", ""), f"{slug}/lessons/{l['file']}", c=c["key"], n=l["num"])
            n_pages += 1

    for c in courses:
        render("course.html", f"{c['slug']}/index.html", title=c["page_title"],
               description=c["meta_description"] or f"Free {c['title']} course: {c['total']} {c['noun']}s from Techbase Consultant Services, Ibadan, Nigeria.",
               og=c["slug"], og_alt=f"{c['title']}: a free Techbase Academy course", course=c, nav_active="learn", section="learn", body_class=f"c-{c['key']}", **company_ctx,
               jsonld={"@context": "https://schema.org", "@type": "Course", "name": c["title"], "provider": org, "inLanguage": "en", "isAccessibleForFree": True,
                       "url": f"{base_url}/{c['slug']}/", "description": c["meta_description"] or c["title"]})
        sitemap.pop()  # the first render call above already counted this page; dedupe below
        sitemap.append(f"{base_url}/{c['slug']}/")
    n_pages = len(written) + 0

    # ---- redirects from the old WordPress addresses -------------------------
    redirects = {f"testimonials/{t['slug']}": f"testimonials/#{t['slug']}" for t in company["testimonials"]}
    redirects["testimonials/joshua-mgbakogu"] = "testimonials/"
    redirects.update({f"faq-item/{f['slug']}": f"faq/#{f['slug']}" for f in company["faq"]})
    redirects.update({f"team-member/{m['slug']}": f"team/#{m['slug']}" for m in company["team"]})
    redirects["team-member/sanni-mayowa"] = "team/"
    wordpress_posts = {"5-stem-skills-every-nigerian-child-needs-for-jobs-in-2030", "from-scratch-to-python-a-parents-guide-to-the-techbase-learning-journey",
                       "how-ai-prompts-are-changing-the-way-teachers-work-in-nigeria", "how-to-use-ai-to-create-better-lesson-plans-a-practical-guide-for-nigerian-teachers",
                       "what-is-robotics-a-simple-guide-for-parents-and-schools-in-nigeria", "why-every-nigerian-child-should-learn-to-code"}
    redirects.update({p["slug"]: f"blog/{p['slug']}/" for p in posts if p["slug"] in wordpress_posts})   # old WordPress addresses only
    for old, new in redirects.items():
        dest = f"{base_url}/{new}"
        stub = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Redirecting…</title><meta name="robots" content="noindex">'
                f'<link rel="canonical" href="{dest}"><meta http-equiv="refresh" content="0; url={dest}"></head>'
                f'<body><p>This page has moved to <a href="{dest}">{dest}</a>.</p></body></html>')
        target = DIST / old / "index.html"
        if target.exists():
            warn(f"redirect {old} would overwrite a real page")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(stub, encoding="utf8")
    (DIST / "redirects.json").write_text(json.dumps(redirects, indent=1), encoding="utf8")

    # ---- data + SEO files ----------------------------------------------------
    (DIST / "assets" / "data").mkdir(parents=True, exist_ok=True)
    (DIST / "assets" / "data" / "search.json").write_text(json.dumps(search, ensure_ascii=False, separators=(",", ":")), encoding="utf8")
    (DIST / "assets" / "data" / "blog.json").write_text(json.dumps({
        "static": [p["slug"] for p in posts],
        "photos": {k: {"widths": v["widths"], "default": v["default"], "w": v["w"], "h": v["h"], "alt": v["alt"]} for k, v in photos.items()}},
        ensure_ascii=False, separators=(",", ":")), encoding="utf8")
    uniq = list(dict.fromkeys(sitemap))
    urls = "".join(f"  <url><loc>{x}</loc></url>\n" for x in uniq)
    (DIST / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n', encoding="utf8")
    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\nDisallow: /login/\nDisallow: /account/\nDisallow: /admin/\nDisallow: /blog/post/\n\nSitemap: {base_url}/sitemap.xml\n", encoding="utf8")
    (DIST / "manifest.webmanifest").write_text(json.dumps({
        "name": site["company"]["name"], "short_name": site["company"]["short"], "description": site["company"]["tagline"], "start_url": "/", "scope": "/", "display": "standalone",
        "background_color": "#fafaf8", "theme_color": site["theme_color"], "lang": "en",
        "icons": [
            {"src": "/assets/img/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/assets/img/icon-512.png", "sizes": "512x512", "type": "image/png"},
            {"src": "/assets/img/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}],
        "shortcuts": [{"name": "Techbase Academy", "url": "/learn/"}, {"name": "Contact", "url": "/contact/"}]}, indent=2), encoding="utf8")
    sw = (ROOT / "build" / "sw.template.js").read_text(encoding="utf8").replace("__VERSION__", asset_v)
    (DIST / "sw.js").write_text(sw, encoding="utf8")
    (DIST / ".nojekyll").write_text("", encoding="utf8")
    cname = site.get("custom_domain")
    if cname:
        (DIST / "CNAME").write_text(cname + "\n", encoding="utf8")
    (DIST / "_headers").write_text(
        "/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n  X-Frame-Options: SAMEORIGIN\n"
        "  Permissions-Policy: camera=(), microphone=(), geolocation=()\n", encoding="utf8")

    for n in notes:
        print("NOTE:", n)
    if ap.REPAIRED:
        print("Repaired unescaped sample markup in:", ", ".join(sorted(set(ap.REPAIRED))))
    print(f"Built {len(written)} pages ({total_lessons} lessons, {len(photos)} photos) into {DIST}; accounts {'ON' if fb else 'off'}")
    for w in warnings + ap.warnings:
        print("ERROR:", w)
    return 1 if (warnings or ap.warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
