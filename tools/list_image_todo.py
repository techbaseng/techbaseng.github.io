#!/usr/bin/env python3
"""Writes docs/IMAGE_TODO.md: every blog post that is still waiting for a picture, with a suggestion for what to add."""
import re
from pathlib import Path

root = Path(__file__).resolve().parent.parent
rows = []
for f in sorted((root / "content" / "blog").glob("*.md")):
    head = f.read_text(encoding="utf8").split("---")[1]
    meta = dict(l.split(":", 1) for l in head.strip().splitlines() if ":" in l)
    meta = {k.strip(): v.strip().strip('"') for k, v in meta.items()}
    if meta.get("image_todo") and not meta.get("image"):
        rows.append((meta["date"], meta["title"], f.stem, meta["image_todo"]))
rows.sort()
out = ["# Pictures still needed for blog posts\n",
       "Each post below shows a plain placeholder until you add a picture. To add one:\n",
       "1. Save the picture in `content/photos/` (a `.jpg`, for example `my-picture.jpg`).",
       "2. Add one line for it in `content/photos/photos.json` with a short description of what the picture shows (`\"my-picture\": {\"alt\": \"...\"}`).",
       "3. In the post file in `content/blog/`, delete the `image_todo:` line and add `image: my-picture` under the date.\n",
       "Company posts need your own photos. For the technology posts, use a picture you are allowed to use (for example from Wikimedia Commons, with the credit it asks for, or one you took yourself). Please avoid computer-generated pictures.\n",
       "| Date | Post | File | What to add |", "|---|---|---|---|"]
for d, t, s, n in rows:
    out.append(f"| {d} | {t} | `content/blog/{s}.md` | {n} |")
(root / "docs" / "IMAGE_TODO.md").write_text("\n".join(out) + "\n", encoding="utf8")
print(len(rows), "posts waiting for a picture")
