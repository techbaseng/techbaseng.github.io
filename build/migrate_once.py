"""One-off migration helper: turns the seven old course repos into content/<slug>/.
Kept in the repo for provenance; not part of the regular build."""
import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

SRC = Path(sys.argv[1]); OUT = Path(sys.argv[2])
SLUGS = ["techbase-html","techbase-css","techbase-js","techbase-python","techbase-scratch","techbase-robotics","techbase-practical-robotics"]
B64 = re.compile(r'<img[^>]*src="data:[^"]+"[^>]*>')

def inner(el):
    return "".join(str(c) for c in el.children).strip() if el else ""

def clean(s): return re.sub(r"\s+"," ",s).strip()

for slug in SLUGS:
    root = SRC/slug/slug
    dst = OUT/slug; (dst/"lessons").mkdir(parents=True, exist_ok=True)
    for f in sorted((root/"lessons").glob("*.html")):
        t = f.read_text(encoding="utf8")
        t = B64.sub("", t)
        t = re.sub(r'data:[a-z/+\-]+;base64,[A-Za-z0-9+/=]+', '', t)
        (dst/"lessons"/f.name).write_text(t, encoding="utf8")
    soup = BeautifulSoup((root/"index.html").read_text(encoding="utf8"), "lxml")
    c = {"slug": slug}
    c["page_title"] = soup.title.string
    md = soup.find("meta", attrs={"name":"description"})
    c["meta_description"] = md["content"] if md else ""
    hero = soup.select_one(".hero-inner")
    c["eyebrow"] = clean(hero.select_one(".eyebrow").get_text())
    c["h1_html"] = inner(hero.select_one("h1"))
    c["hero_sub_html"] = inner(hero.select_one(".hero-sub"))
    c["stats"] = [{"n": clean(d.select_one(".stat-n").get_text()), "l": clean(d.select_one(".stat-l").get_text())} for d in hero.select(".hero-stats > div")]
    a = soup.select_one("#about")
    c["about"] = {
        "label": clean(a.select_one(".slbl").get_text()),
        "h2_html": inner(a.select_one(".about-text h2")),
        "paras_html": [inner(p) for p in a.select(".about-text > p")],
        "bullets_html": [inner(li) for li in a.select(".learn-list li")],
        "kit": [{"name": clean(k.select_one(".kit-name").get_text()), "info": clean(k.select_one(".kit-info").get_text())} for k in a.select(".kit-item")],
        "kit_note": next((clean(p.get_text()) for p in a.select("p") if p.get("style") and "margin-top:.9rem" in p["style"]), ""),
    }
    sec = soup.select_one("#lessons") or soup.select_one("#projects")
    c["lessons_label"] = clean(sec.select_one(".slbl").get_text())
    c["lessons_heading"] = clean(sec.select_one(".sec-h2").get_text())
    phases = []; cur = None
    for el in sec.select(".phase-div, .lc"):
        if "phase-div" in el.get("class", []):
            cur = {"name": clean(el.get_text()), "lessons": []}; phases.append(cur)
        else:
            lt = el.select_one(".ltitle")
            pill = lt.select_one(".level-pill")
            level = ""
            if pill:
                level = next((k.replace("pill-","") for k in pill.get("class",[]) if k.startswith("pill-")), "")
                pill.extract()
            desc = ""
            sp = lt.find("span")
            if sp: desc = clean(sp.get_text()); sp.extract()
            title = clean(lt.get_text())
            cur["lessons"].append({"num": clean(el.select_one(".lnum").get_text()), "file": Path(el["href"]).name, "title": title, "desc": desc, "level": level})
    c["phases"] = phases
    c["steps"] = [{"n": clean(s.select_one(".step-n").get_text()), "h": clean(s.select_one("h3").get_text()), "p_html": inner(s.select_one("p"))} for s in soup.select(".steps-row .step")]
    (dst/"course.raw.json").write_text(json.dumps(c, indent=1, ensure_ascii=False), encoding="utf8")
    n = sum(len(p["lessons"]) for p in phases)
    print(slug, "lessons", n, "files", len(list((dst/'lessons').glob('*.html'))), "phases", len(phases))
