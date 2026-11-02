#!/usr/bin/env python3
"""Builds the parent/school training proposal (PowerPoint + PDF) from the same data files the website uses, so every age,
price, count and contact detail matches the site.

    pip install python-pptx qrcode pillow
    python tools/make_proposal_deck.py          # needs LibreOffice (soffice) for the PDF

Writes assets/downloads/Techbase-Training-Proposal.pptx and .pdf. The website build warns when these files are older than the data
(build/check_site.py compares assets/downloads/proposal.stamp with facts_hash()).
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "downloads"
NAME = "Techbase-Training-Proposal"


def load():
    rj = lambda p: json.loads((ROOT / p).read_text(encoding="utf8"))
    site, ages, price = rj("content/site.json"), rj("content/ages.json"), rj("content/company/pricing.json")
    courses = {}
    for c in rj("content/courses.json"):
        raw = rj(f"content/{c['slug']}/course.json")
        courses[c["slug"]] = sum(len(p["lessons"]) for p in raw["phases"])
    partners = rj("content/company/partners.json")
    return site, ages, price, courses, sum(len(v) for v in partners.values())


def facts_hash() -> str:
    site, ages, price, courses, partners = load()
    blob = json.dumps([site["company"], site["links"], ages, price, courses, partners], sort_keys=True, ensure_ascii=False)
    return hashlib.sha1((blob + Path(__file__).read_text(encoding="utf8")).encode()).hexdigest()[:12]


def naira(n, cur="₦"):
    return f"{cur}{n:,.0f}"


def build(path: Path) -> None:
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
    from pptx.util import Inches, Pt
    import qrcode

    site, ages, price, courses, n_partners = load()
    co, links = site["company"], site["links"]
    total = sum(courses.values())
    A = ages["courses"]; CAT = ages["catalogue"]
    base, fam, grp, gmin = price["base_fee"], price["family_discount_pct"], price["group_discount_pct"], price["group_min_students"]
    cur = price["currency"]; hrs = price["block_hours"]
    web_total = courses["techbase-html"] + courses["techbase-css"] + courses["techbase-js"]

    C = lambda h: RGBColor.from_string(h)
    INK, MUTED, BLUE, BLUE_T, WHITE, TINT = "0F1B33", "475569", "2457E6", "E8EEFD", "FFFFFF", "F4F7FC"
    AMBER, AMBER_T, GREEN, GREEN_T, TEAL, TEAL_T, PURP, PURP_T = "B45309", "FEF1DC", "1F7A5C", "E1F3EA", "0F766E", "DDF3F1", "6D3FA8", "EEE6F8"
    LINE = "D7DEEA"
    FONT = "Calibri"

    prs = Presentation(); prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    blank = prs.slide_layouts[6]
    state = {"n": 0}
    TOTAL = 13

    def box(s, x, y, w, h, fill=WHITE, line=LINE, r=0.12, shadow=False):
        sh = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if r else MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
        if r: sh.adjustments[0] = min(0.5, r / min(w, h))
        if fill: sh.fill.solid(); sh.fill.fore_color.rgb = C(fill)
        else: sh.fill.background()
        if line: sh.line.color.rgb = C(line); sh.line.width = Pt(1)
        else: sh.line.fill.background()
        sh.shadow.inherit = False
        return sh

    def text(s, x, y, w, h, t, size=14, bold=False, color=INK, align="l", anchor="t", italic=False, spacing=None):
        tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf = tb.text_frame; tf.word_wrap = True
        tf.margin_left = tf.margin_right = Inches(0.04); tf.margin_top = tf.margin_bottom = Inches(0.02)
        tf.vertical_anchor = {"t": MSO_ANCHOR.TOP, "m": MSO_ANCHOR.MIDDLE, "b": MSO_ANCHOR.BOTTOM}[anchor]
        lines = t if isinstance(t, list) else [t]
        for i, ln in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}[align]
            if spacing: p.line_spacing = spacing
            if i and isinstance(t, list): p.space_before = Pt(5)
            r = p.add_run(); r.text = ln; f = r.font
            f.size = Pt(size); f.bold = bold; f.italic = italic; f.color.rgb = C(color); f.name = FONT
        return tb

    def circle(s, x, y, d, fill, label="", size=16, color=WHITE):
        sh = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(d), Inches(d)); sh.fill.solid(); sh.fill.fore_color.rgb = C(fill); sh.line.fill.background(); sh.shadow.inherit = False
        if label:
            tf = sh.text_frame; tf.margin_left = tf.margin_right = 0; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER; r = p.add_run(); r.text = label; r.font.size = Pt(size); r.font.bold = True; r.font.color.rgb = C(color); r.font.name = FONT
        return sh

    def slide(bg=WHITE, eyebrow=None, title=None, sub=None):
        s = prs.slides.add_slide(blank); state["n"] += 1
        s.background.fill.solid(); s.background.fill.fore_color.rgb = C(bg)
        if eyebrow:
            bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(0.52), Inches(0.28), Inches(0.1)); bar.fill.solid(); bar.fill.fore_color.rgb = C(BLUE); bar.line.fill.background()
            text(s, 0.95, 0.42, 6, 0.3, eyebrow.upper(), 11, True, BLUE)
        if title: text(s, 0.56, 0.78, 12.2, 0.7, title, 32, True, INK)
        if sub: text(s, 0.56, 1.5, 12, 0.4, sub, 15, False, MUTED)
        text(s, 0.6, 7.05, 8, 0.3, f"{co['name']}  ·  {co['email']}  ·  {co['phone']}", 10, False, MUTED)
        text(s, 11.6, 7.05, 1.2, 0.3, f"{state['n']:02d} / {TOTAL}", 10, False, MUTED, "r")
        return s

    def card(s, x, y, w, h, head, body, accent=BLUE, tint=BLUE_T, tag=None, num=None, hs=17, bs=15):
        box(s, x, y, w, h, WHITE, LINE)
        strip = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y + 0.15), Inches(0.08), Inches(h - 0.3)); strip.fill.solid(); strip.fill.fore_color.rgb = C(accent); strip.line.fill.background()
        ox = x + 0.3
        if num is not None:
            circle(s, ox, y + 0.25, 0.6, tint, num, 20, accent); ox += 0.8
        text(s, ox, y + 0.2, w - (ox - x) - 0.2, 0.45, head, hs, True, INK)
        yy = y + 0.68
        if tag:
            pill = box(s, ox, yy, 1.9 if len(tag) > 12 else 1.3, 0.3, tint, None, 0.15)
            text(s, ox, yy + 0.01, 1.9 if len(tag) > 12 else 1.3, 0.28, tag, 11, True, accent, "c", "m"); yy += 0.42
        text(s, ox, yy, w - (ox - x) - 0.2, h - (yy - y) - 0.1, body, bs, False, MUTED)

    # 1 ---- cover
    s = prs.slides.add_slide(blank); state["n"] += 1
    s.background.fill.solid(); s.background.fill.fore_color.rgb = C(WHITE)
    side = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(4.6), Inches(7.5)); side.fill.solid(); side.fill.fore_color.rgb = C(TINT); side.line.fill.background()
    s.shapes.add_picture(str(tmp / "logo.png"), Inches(0.8), Inches(1.4), Inches(3.0), Inches(3.0))
    text(s, 0.5, 4.7, 3.6, 0.4, "TECHBASE STEM ACADEMY", 14, True, BLUE, "c")
    text(s, 0.5, 5.1, 3.6, 0.6, ["Coding · Robotics · Digital Skills", "Online & onsite · Nationwide"], 12, False, MUTED, "c")
    text(s, 5.2, 1.3, 7.5, 0.4, "CODING  ·  ROBOTICS  ·  DIGITAL SKILLS", 13, True, AMBER)
    text(s, 5.2, 1.8, 7.8, 1.9, ["A Real Head-Start", "in Tech, for Every Age."], 46, True, INK, spacing=1.0)
    text(s, 5.2, 3.75, 7.4, 0.9, f"A hands-on training programme for children and teens (ages {ages['overall']}), delivered online or onsite, anywhere in Nigeria.", 18, False, MUTED)
    for i, (big, small) in enumerate([(str(len(courses) + 3), "Courses to choose from"), ("Online", "& onsite"), ("Anywhere", "in Nigeria"), (f"Ages {ages['youngest']}+", "to adult")]):
        x = 5.2 + i * 1.95
        box(s, x, 5.1, 1.8, 1.15, BLUE_T, None, 0.12)
        text(s, x, 5.25, 1.8, 0.45, big, 20, True, BLUE, "c"); text(s, x, 5.78, 1.8, 0.35, small, 11, False, MUTED, "c")
    text(s, 5.2, 6.9, 7, 0.3, co["name"], 11, False, MUTED)

    # 2 ---- about
    s = slide(TINT, "About us", "Real Instructors. Real Skills.")
    text(s, 0.6, 1.8, 6.3, 2.6, [f"{co['name']} runs a dedicated STEM Academy teaching coding, robotics and digital skills to children and teenagers: live, mentor-led and practical.",
         "We take learners from their very first line of code to real, working projects: a website, a game, or a robot that moves and responds."], 18, False, MUTED)
    box(s, 0.6, 4.6, 6.2, 1.5, BLUE_T, None); text(s, 0.9, 4.75, 5.7, 1.2, "“Small groups. Real mentors. Projects your child can actually show off.”", 18, True, BLUE, "l", "m", True)
    for i, (n, t) in enumerate([(f"{total}", f"Free practice lessons and projects online, across {len(courses)} Academy courses (techbaseng.github.io)"),
                                ("4", "Core live training tracks, with 11 courses in the full catalogue"),
                                (f"{n_partners}", "Partner schools and organisations we have worked with")]):
        y = 1.85 + i * 1.7
        box(s, 7.4, y, 5.3, 1.45, WHITE, LINE); text(s, 7.6, y + 0.2, 1.7, 1.0, n, 36, True, BLUE, "c", "m"); text(s, 9.3, y + 0.15, 3.3, 1.2, t, 13, False, MUTED, "l", "m")

    # 3 ---- why
    s = slide(WHITE, "Why Techbase", "Why Learners Choose Us")
    items = [("Mentor-Led Classes", "Small groups taught live by qualified instructors, never a pre-recorded video dump.", BLUE, BLUE_T),
             ("Real Progression", "A genuine curriculum from Scratch to Python to Robotics, not a one-off workshop.", GREEN, GREEN_T),
             ("Delivered Anywhere", "Learn online from anywhere, or onsite at a location of your choice, nationwide.", AMBER, AMBER_T),
             ("Proven Track Record", f"Trusted by {n_partners} schools and organisations and by families across Nigeria for hands-on STEM training.", PURP, PURP_T)]
    for i, (h_, b_, a_, t_) in enumerate(items):
        card(s, 0.6 + (i % 2) * 6.2, 1.8 + (i // 2) * 2.45, 5.95, 2.2, h_, b_, a_, t_, num=str(i + 1), hs=20, bs=15)

    # 4 ---- roadmap
    s = slide(TINT, "Age-based roadmap", "Your Child's Learning Journey", "Learners join the track that fits their age, then progress along the path. Ages follow the makers' own guidance where it exists.")
    steps = [(f"{ages['youngest']}+", "Scratch Programming", f"Ages {A['techbase-scratch']}", "Block-based coding basics", AMBER, AMBER_T),
             (f"{ages['youngest']}+", "Micro:bit Robotics", f"Ages {A['techbase-robotics']}", "Code that controls real hardware", TEAL, TEAL_T),
             ("10+", "Web Development", f"Ages {A['techbase-html']}", "HTML, CSS & JavaScript", BLUE, BLUE_T),
             ("10+", "Python Programming", f"Ages {A['techbase-python']}", "Real-world applications", GREEN, GREEN_T),
             ("10+", "Mobile Apps", f"Ages {CAT['app-inventor']} (App Inventor)", f"Android Studio from age {A['techbase-android'].rstrip('+')}", PURP, PURP_T),
             ("13+", "Advanced Track", f"Ages {CAT['java-c-cpp']}", "Java · C/C++ · Arduino · AI", INK, "E3E8F1")]
    ln = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(2.82), Inches(11.5), Inches(0.05)); ln.fill.solid(); ln.fill.fore_color.rgb = C(LINE); ln.line.fill.background()
    for i, (age, name, rng, desc, a_, t_) in enumerate(steps):
        x = 0.6 + i * 2.07
        circle(s, x + 0.55, 2.52, 0.65, a_, age, 17)
        box(s, x, 3.45, 1.93, 2.55, WHITE, LINE)
        st = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(3.45), Inches(1.93), Inches(0.08)); st.fill.solid(); st.fill.fore_color.rgb = C(a_); st.line.fill.background()
        text(s, x + 0.1, 3.7, 1.73, 0.7, name, 15, True, INK, "c"); text(s, x + 0.1, 4.45, 1.73, 0.5, rng, 12, True, a_, "c"); text(s, x + 0.1, 5.0, 1.73, 0.9, desc, 12, False, MUTED, "c")
    box(s, 0.6, 6.3, 12.1, 0.55, WHITE, LINE, 0.27); text(s, 0.8, 6.33, 11.7, 0.5, "Also available at any age: Digital & Productivity Skills (Microsoft Word, Excel & PowerPoint)", 13, True, INK, "c", "m")

    # 5 ---- core tracks
    s = slide(WHITE, "Core programme", "Our Learning Tracks")
    tr = [("Scratch Programming", f"Ages {A['techbase-scratch']}", f"Block-based coding fundamentals: logic, loops, events, games and animation. {courses['techbase-scratch']} free practice projects online.", AMBER, AMBER_T),
          ("Web Development", f"Ages {A['techbase-html']}", f"HTML, CSS & JavaScript: building and styling real, working websites. {web_total} free practice lessons online.", BLUE, BLUE_T),
          ("Python Programming", f"Ages {A['techbase-python']}", f"Core programming concepts and Python syntax for real applications. {courses['techbase-python']} free practice lessons online.", GREEN, GREEN_T),
          ("Robotics (Micro:bit)", f"Ages {A['techbase-robotics']}", f"Robotics fundamentals with MakeCode block programming and a Starter Kit. {courses['techbase-robotics']} free micro:bit projects online.", TEAL, TEAL_T)]
    for i, (h_, tag, b_, a_, t_) in enumerate(tr):
        card(s, 0.6 + (i % 2) * 6.2, 1.75 + (i // 2) * 2.6, 5.95, 2.4, h_, b_, a_, t_, tag=tag, hs=20, bs=16)

    # 6 ---- catalogue
    s = slide(TINT, "Full catalogue", "More Courses We Offer")
    cat = [("Mobile App Development", f"App Inventor (ages {CAT['app-inventor']}): build real Android apps. Android Studio with Kotlin (ages {A['techbase-android']}): {courses['techbase-android']} free lessons online.", PURP, PURP_T),
           ("Digital & Productivity Skills", "Microsoft Word, Excel, PowerPoint and Office essentials. Any age.", BLUE, BLUE_T),
           ("More Programming Languages", f"Java Programming and C / C++ Programming (ages {CAT['java-c-cpp']}).", GREEN, GREEN_T),
           ("More Robotics & Hardware", f"Arduino Robotics (ages {CAT['arduino']}) and Practical Robotics with the Freenove kit (ages {A['techbase-practical-robotics']}): {courses['techbase-practical-robotics']} free projects online.", TEAL, TEAL_T),
           ("Emerging Technology", f"AI & Machine Learning Foundations (ages {CAT['ai-ml']}).", AMBER, AMBER_T),
           ("Don't See Your Track?", "Ask us. We tailor custom courses for schools, organisations and individuals too.", INK, "E3E8F1")]
    for i, (h_, b_, a_, t_) in enumerate(cat):
        card(s, 0.6 + (i % 3) * 4.1, 1.75 + (i // 3) * 2.6, 3.95, 2.4, h_, b_, a_, t_, hs=18, bs=15)

    # 7 ---- delivery
    s = slide(WHITE, "Delivery", "Class Format & What's Needed")
    n_ = price["needs"]
    cols = [("ONLINE CLASSES", "Live, instructor-led virtual sessions, from anywhere with an internet connection.", [n_["laptop"].replace(" (per learner)", ""), n_["internet"].replace(" (online classes)", ""), n_["microbit"]], BLUE, BLUE_T),
            ("ONSITE CLASSES", "In-person, hands-on sessions at any location you choose, nationwide.", [n_["laptop"], "A micro:bit Starter Kit for the Robotics track, provided or sourced for you", "Pricing discussed individually, based on location and logistics"], GREEN, GREEN_T)]
    for i, (h_, d_, bl, a_, t_) in enumerate(cols):
        x = 0.6 + i * 6.2
        box(s, x, 1.75, 5.95, 4.2, WHITE, LINE); hd = box(s, x, 1.75, 5.95, 0.75, t_, None, 0.12); text(s, x + 0.3, 1.82, 5.4, 0.6, h_, 20, True, a_, "l", "m")
        text(s, x + 0.3, 2.65, 5.4, 0.8, d_, 15, False, INK)
        text(s, x + 0.3, 3.5, 5.4, 2.4, ["•  " + b for b in bl], 16, False, MUTED)
    box(s, 0.6, 6.15, 12.1, 0.7, BLUE_T, None); text(s, 0.85, 6.18, 11.6, 0.65, "Certificate of proficiency on completion. Schools that cannot supply enough laptops can ask us about laptop provision for the duration of the training.", 13, True, BLUE, "l", "m")

    # 8 ---- pricing
    s = slide(TINT, "Investment", "Simple, Transparent Pricing")
    box(s, 0.6, 1.8, 5.95, 3.1, WHITE, LINE); text(s, 0.95, 2.0, 5.3, 0.4, "ONLINE TRAINING", 13, True, BLUE)
    text(s, 0.95, 2.55, 5.3, 1.0, naira(base, cur), 54, True, INK); text(s, 0.95, 3.75, 5.3, 0.9, f"per learner, per {hrs}-hour session block", 16, False, MUTED)
    box(s, 6.75, 1.8, 5.95, 3.1, WHITE, LINE); text(s, 7.1, 2.0, 5.3, 0.4, "ONSITE TRAINING", 13, True, GREEN)
    text(s, 7.1, 2.55, 5.3, 1.0, "Custom quote", 40, True, INK); text(s, 7.1, 3.75, 5.3, 1.0, f"Base fee plus location and logistics costs, agreed with each client individually.", 16, False, MUTED)
    box(s, 0.6, 5.2, 12.1, 1.35, AMBER_T, None); text(s, 0.9, 5.3, 11.5, 0.4, "Onsite note", 14, True, AMBER)
    text(s, 0.9, 5.7, 11.5, 0.8, f"We deliver onsite training to any location, priced on the same {naira(base, cur)} / {hrs}-hour base, plus transportation, venue and equipment costs specific to your location, confirmed before class begins.", 14, False, INK)

    # 9 ---- discounts
    comb = fam + grp
    s = slide(WHITE, "Save more", "Family & Group Discounts", "We reward families and groups who learn together. The discounts stack.")
    box(s, 0.6, 2.1, 5.95, 3.3, GREEN, None); text(s, 0.9, 2.3, 5.4, 0.9, f"{fam}% OFF", 44, True, WHITE); text(s, 0.9, 3.2, 5.4, 0.4, "Joint / Family Class", 17, True, WHITE)
    text(s, 0.9, 3.7, 5.4, 1.6, f"Register 2 or more students on the same learning track through the same parent or guardian: {fam}% off every additional student. Applies to online and onsite classes.", 14, False, WHITE)
    box(s, 6.75, 2.1, 5.95, 3.3, AMBER, None); text(s, 7.05, 2.3, 5.4, 0.9, f"+{grp}% MORE", 44, True, WHITE); text(s, 7.05, 3.2, 5.4, 0.4, f"Group Bookings: {gmin}+ Students", 17, True, WHITE)
    text(s, 7.05, 3.7, 5.4, 1.6, f"When a parent, school or community gathers {gmin} or more students in one location for the same track, every student gets an extra {grp}% off, stacked on the {fam}% family discount for a combined {comb}% off.", 14, False, WHITE)
    box(s, 0.6, 5.65, 12.1, 0.6, INK, None, 0.3); text(s, 0.6, 5.68, 12.1, 0.55, f"UP TO {comb}% OFF PER STUDENT  ·  GROUPS OF {gmin}+", 15, True, WHITE, "c", "m")
    text(s, 0.6, 6.4, 12.1, 0.5, f"Refer a school, family or organisation: when a client you refer enrols, you receive {price['referral_pct']}% commission on the total cost of their training.", 13, False, MUTED, "c")

    # 10 ---- worked example
    fam2 = base + base * (100 - fam) / 100
    first_g = base * (100 - grp) / 100; rest_g = base * (100 - fam - grp) / 100; grp12 = first_g + 11 * rest_g
    s = slide(TINT, "See it in action", "Worked Pricing Example")
    ex = [("1 student", "online, Robotics track", naira(base, cur), f"{naira(base, cur)} for one {hrs}-hour block", BLUE, BLUE_T),
          ("2 siblings", "same track, same parent", naira(fam2, cur), f"{naira(base, cur)} + {naira(base - base * fam / 100, cur)}\n({fam}% off the 2nd child)", GREEN, GREEN_T),
          ("Group of 12", "one location, same track", naira(grp12, cur), f"{naira(first_g, cur)} + (11 × {naira(rest_g, cur)})\n({grp}% off the first, {fam + grp}% off the rest)", AMBER, AMBER_T)]
    for i, (h_, sub_, tot, calc, a_, t_) in enumerate(ex):
        x = 0.6 + i * 4.1
        box(s, x, 1.8, 3.95, 3.7, WHITE, LINE); box(s, x, 1.8, 3.95, 0.95, t_, None, 0.12)
        text(s, x + 0.25, 1.85, 3.5, 0.5, h_, 22, True, a_); text(s, x + 0.25, 2.32, 3.5, 0.4, sub_, 13, False, MUTED)
        text(s, x + 0.25, 3.0, 3.5, 0.9, tot, 36, True, INK); text(s, x + 0.25, 4.05, 3.5, 1.2, calc.split("\n"), 15, False, MUTED)
    text(s, 0.6, 5.85, 12.1, 0.5, "Figures above are illustrative; your final quote is confirmed at registration.", 13, False, MUTED, "c", italic=True)

    # 11 ---- enrol
    s = slide(WHITE, "Getting started", "How to Enrol", "There is no formal application, just a conversation.")
    st = [("Contact us", "WhatsApp, call, email or the form on our website."), ("Tell us your track", "Preferred course(s), online or onsite, learner age(s) and how many students together."),
          ("Get your quote", "Confirmed price with any discount, plus a suitable schedule."), ("Start training", "Get set up and begin, with a certificate of proficiency at the end.")]
    for i, (h_, b_) in enumerate(st):
        x = 0.6 + i * 3.05
        circle(s, x + 0.1, 2.3, 0.8, BLUE, str(i + 1), 24); text(s, x, 3.3, 2.85, 0.5, h_, 19, True, INK); text(s, x, 3.9, 2.8, 1.8, b_, 14, False, MUTED)
        if i < 3:
            ar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x + 1.05), Inches(2.67), Inches(1.9), Inches(0.05)); ar.fill.solid(); ar.fill.fore_color.rgb = C(LINE); ar.line.fill.background()
    box(s, 0.6, 5.9, 12.1, 0.8, TINT, None); text(s, 0.9, 5.93, 11.5, 0.75, f"Office hours: {co['hours']}  ·  {co['address']}", 14, True, INK, "c", "m")

    # 12 ---- contact
    s = slide(TINT, "Let's talk", "Connect With Us")
    rows = [("WhatsApp", co["whatsapp"]["chat"].replace("https://", "")), ("Call / SMS", co["phone"]), ("Email", co["email"]), ("Website", links["website"].replace("https://", "")),
            ("Free Academy", site["url"].replace("https://", "")), ("Address", co["address"]), ("Hours", co["hours"])]
    for i, (k, v) in enumerate(rows):
        y = 1.75 + i * 0.67
        box(s, 0.6, y, 7.4, 0.58, WHITE, LINE, 0.1); text(s, 0.85, y + 0.04, 1.9, 0.5, k, 13, True, BLUE, "l", "m"); text(s, 2.7, y + 0.04, 5.2, 0.5, v, 14, False, INK, "l", "m")
    box(s, 8.4, 1.75, 4.3, 4.6, WHITE, LINE); text(s, 8.6, 1.9, 3.9, 0.4, "FOLLOW US", 13, True, BLUE, "c")
    soc = co["social"]
    text(s, 8.6, 2.4, 3.9, 3.8, ["LinkedIn: Techbase Consultant Services", f"Facebook: @{soc['facebook'].rsplit('/', 1)[-1]}", f"Instagram: @{soc['instagram'].rsplit('/', 1)[-1]}", f"X (Twitter): @{soc['x'].rsplit('/', 1)[-1]}", f"YouTube: @{soc['youtube'].rsplit('@', 1)[-1]}", "", "Same handle on all platforms:", "@techbasengr"], 14, False, INK, "c")

    # 13 ---- CTA
    s = slide(WHITE)
    s.shapes.add_picture(str(tmp / "logo.png"), Inches(0.9), Inches(1.3), Inches(2.6), Inches(2.6))
    text(s, 4.2, 1.2, 8.4, 1.0, "Ready to Get Started?", 44, True, INK)
    text(s, 4.2, 2.3, 8.2, 1.0, f"Give your child a real head-start in coding, robotics and digital skills, wherever you are. Ages {ages['overall']}.", 18, False, MUTED)
    text(s, 4.2, 3.6, 8, 0.5, f"WhatsApp: {co['phone']}", 20, True, BLUE); text(s, 4.2, 4.2, 8, 0.5, links["website"].replace("https://", ""), 20, True, BLUE); text(s, 4.2, 4.8, 8, 0.5, co["email"], 20, True, BLUE)
    qr = qrcode.make(co["whatsapp"]["chat"]); qr.save(tmp / "qr.png")
    s.shapes.add_picture(str(tmp / "qr.png"), Inches(10.6), Inches(3.5), Inches(2.0), Inches(2.0)); text(s, 10.4, 5.55, 2.4, 0.4, "Scan to chat on WhatsApp", 11, False, MUTED, "c")
    for i, (big, small) in enumerate([(str(len(courses) + 3), "Courses"), (f"Ages {ages['youngest']}+", "To adult"), ("Online & onsite", "Nationwide")]):
        x = 0.9 + i * 3.1
        box(s, x, 5.9, 2.9, 0.9, BLUE_T, None); text(s, x, 5.93, 2.9, 0.5, big, 18, True, BLUE, "c"); text(s, x, 6.4, 2.9, 0.3, small, 11, False, MUTED, "c")

    prs.core_properties.title = "Techbase Training Proposal"; prs.core_properties.author = co["name"]
    prs.save(path)


def main() -> int:
    global tmp
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp())
    from PIL import Image
    Image.open(ROOT / "assets" / "img" / "logo-full.webp").convert("RGBA").save(tmp / "logo.png")
    pptx = OUT / f"{NAME}.pptx"
    build(pptx)
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        print("LibreOffice not found: wrote the PowerPoint file only.")
    else:
        subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(tmp), str(pptx)], check=True, capture_output=True)
        shutil.copy(tmp / f"{NAME}.pdf", OUT / f"{NAME}.pdf")
    (OUT / "proposal.stamp").write_text(facts_hash() + "\n")
    print("Wrote", pptx, "and PDF" if soffice else "")
    return 0


tmp: Path
if __name__ == "__main__":
    sys.exit(main())
