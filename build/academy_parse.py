"""Lesson parsers for the Academy: turn each source lesson file into clean page data.
Moved unchanged from the original build script so the 472 lessons render exactly as before."""
from __future__ import annotations

import re
from pathlib import Path

from bs4 import BeautifulSoup
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound

EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿⭐️‍]+")
LEVELS = {"beg": "Beginner", "int": "Intermediate", "adv": "Advanced"}
LEXERS = {
    "html": "html", "starter.html": "html", "xml": "xml", "css": "css", "scss": "scss",
    "javascript": "javascript", "js": "javascript", "python": "python", "starter.py": "python",
    "json": "json", "bash": "bash", "php": "php", "sql": "sql", "java": "java",
    "csharp": "csharp", "apache": "apache", "nginx": "nginx",
    "kotlin": "kotlin", "kts": "kotlin", "gradle": "groovy", "toml": "toml", "swift": "swift", "yaml": "yaml",
    "properties": "properties", "text": "text",
}
# code labels that are file names (MainActivity.kt, build.gradle.kts) pick a lexer by extension
EXT_LEXERS = {
    ".kt": "kotlin", ".kts": "kotlin", ".gradle": "groovy", ".xml": "xml", ".toml": "toml", ".swift": "swift",
    ".json": "json", ".py": "python", ".sql": "sql", ".java": "java", ".properties": "properties",
    ".yml": "yaml", ".yaml": "yaml", ".sh": "bash", ".html": "html", ".css": "css", ".js": "javascript",
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
        if el.name == "button" and "#10b981" in style or el.name == "button" and "#059669" in style:
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
        label = clean(lang_el.get_text()).lower()
        name = LEXERS.get(label) or EXT_LEXERS.get(Path(label).suffix)
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


