"""Regenerates PNG/ICO brand assets from the SVG mark (needs Playwright + Pillow).
Run by the maintainer only when the logo changes; outputs are committed."""
import json
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "assets" / "img"
mark = (IMG / "logo-mark.svg").read_text()
courses = json.loads((ROOT / "content" / "courses.json").read_text())
COLORS = {"html": "#e34f26", "css": "#0284c7", "js": "#d97706", "python": "#059669", "scratch": "#ea580c", "microbit": "#7c3aed", "practical": "#e11d48", "android": "#3ddc84"}

def tile(size, pad=0, bg=None):
    inner = mark.replace('width="64" height="64"', f'width="{size-2*pad}" height="{size-2*pad}"')
    bgd = f"background:{bg};" if bg else ""
    return f'<html><body style="margin:0;{bgd}width:{size}px;height:{size}px;display:grid;place-items:center">{inner}</body></html>'

def og(title, sub, accent, stats, label="ACADEMY"):
    return f'''<html><body style="margin:0;width:1200px;height:630px;font-family:Inter,'Inter Display',sans-serif;color:#eef1f6;
background:radial-gradient(60% 80% at 10% 0%,{accent}55,transparent 70%),radial-gradient(40% 60% at 100% 100%,#f5a52430,transparent 70%),#0a0e17;position:relative;overflow:hidden">
<div style="position:absolute;inset:0;background-image:linear-gradient(#ffffff0d 1px,transparent 1px),linear-gradient(90deg,#ffffff0d 1px,transparent 1px);background-size:56px 56px;-webkit-mask-image:radial-gradient(80% 80% at 50% 0%,#000,transparent 80%)"></div>
<div style="position:absolute;left:72px;top:64px;display:flex;align-items:center;gap:18px"><div style="width:56px;height:56px">{mark.replace('width="64" height="64"','width="56" height="56"')}</div>
<div style="font:700 34px/1 'Inter Display',Inter;letter-spacing:-.03em">Tech<span style="color:#7f9fff">base</span> <span style="font:500 15px Inter;letter-spacing:.14em;color:#97a3b8;margin-left:6px">{label}</span></div></div>
<div style="position:absolute;left:72px;top:210px;right:72px"><div style="font:700 92px/1 'Inter Display',Inter;letter-spacing:-.045em">{title}</div>
<div style="font:400 30px/1.4 Inter;color:#c5cddb;margin-top:28px;max-width:1000px">{sub}</div></div>
<div style="position:absolute;left:72px;bottom:56px;display:flex;gap:14px">{''.join(f'<div style="padding:12px 22px;border:1px solid #2c384d;border-radius:99px;font:600 22px Inter;color:#eef1f6;background:#ffffff0a">{s}</div>' for s in stats)}</div>
<div style="position:absolute;right:72px;bottom:60px;font:500 22px 'JetBrains Mono',monospace;color:#97a3b8">techbaseng.github.io</div></body></html>'''

with sync_playwright() as p:
    b = p.chromium.launch()
    def shot(html, out, w, h, transparent=False):
        pg = b.new_page(viewport={"width": w, "height": h}); pg.set_content(html); pg.wait_for_timeout(200)
        pg.screenshot(path=str(out), omit_background=transparent); pg.close()
    shot(tile(180), IMG / "apple-touch-icon.png", 180, 180)
    shot(tile(192), IMG / "icon-192.png", 192, 192, True)
    shot(tile(512), IMG / "icon-512.png", 512, 512, True)
    shot(tile(512, pad=64, bg="#2457e6"), IMG / "icon-maskable-512.png", 512, 512)
    shot(tile(64), IMG / "favicon-64.png", 64, 64, True)
    (IMG / "og").mkdir(exist_ok=True)
    total = sum(1 for _ in range(0))
    shot(og("Learn to code.<br>Build the future.", "Free coding and robotics courses from Ibadan, Nigeria.", "#2457e6", ["8 courses", "472 lessons", "100% free"]), IMG / "og" / "learn.png", 1200, 630)
    shot(og("Empowering youth for the digital future.", "STEM, coding and robotics training, web and app development, and AI tools. Ibadan, Nigeria.", "#2457e6", ["Ages 5 to adult", "In schools or virtual", "Free Academy"], "CONSULTANT SERVICES"), IMG / "og" / "company.png", 1200, 630)
    for c in courses:
        n = len(list((ROOT / "content" / c["slug"] / "lessons").glob("*.html")))
        shot(og(c["title"], c["blurb"], COLORS[c["key"]], [f"{n} {c['noun']}s", c["level"], "Free"]), IMG / "og" / f"{c['slug']}.png", 1200, 630)
    b.close()
Image.open(IMG / "favicon-64.png").save(ROOT / "assets" / "img" / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
(IMG / "favicon-64.png").unlink()
print("brand assets written")
