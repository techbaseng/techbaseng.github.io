# Techbase STEM Academy — Free Coding Courses

**Live:** https://techbaseng.github.io/

The course hub for **Techbase Consultant Services** — a free, self-serve STEM
curriculum for learners in Nigeria and beyond. This repo is the org's special
`<org>.github.io` GitHub Pages site: pushing to `main` publishes automatically,
with no Settings → Pages configuration needed.

**356 total lessons and projects across 6 free courses**, with video walkthroughs
on the [YouTube channel](https://www.youtube.com/@techbasengr).

## Tech stack

Single-file static HTML page — no build step, no framework, no dependencies
beyond Google Fonts (Plus Jakarta Sans, Space Grotesk, JetBrains Mono, loaded
via CDN `<link>` tags). All styling is inline `<style>` in `index.html`.

## Courses

| Course | Lessons | Level | Repo |
|--------|---------|-------|------|
| 🌐 HTML Fundamentals | 34 | Beginner | [techbase-html →](https://github.com/techbaseng/techbase-html) |
| 🎨 CSS Styling | 73 | Beginner → Advanced | [techbase-css →](https://github.com/techbaseng/techbase-css) |
| ⚡ JavaScript | 46 | Intermediate | [techbase-js →](https://github.com/techbaseng/techbase-js) |
| 🐍 Python Programming | 45 | Beginner → Advanced | [techbase-python →](https://github.com/techbaseng/techbase-python) |
| 🟠 Scratch Programming | 35 | Beginner · Ages 8–16 | [techbase-scratch →](https://github.com/techbaseng/techbase-scratch) |
| 🤖 Robotics & micro:bit | 123 | Beginner → Advanced | [techbase-robotics →](https://github.com/techbaseng/techbase-robotics) |

## Recommended learning paths

| Goal | Path |
|------|------|
| Young learners (8–12) | Scratch → micro:bit Robotics |
| Web development | HTML → CSS → JavaScript |
| Data science | Python (all phases) |
| Physical computing | Scratch → micro:bit Robotics |

## Structure

```
index.html    The entire live site — hero, stats ticker, course grid, about
              section, learning paths, footer. Single file, self-contained.
README.md     This file.
```

## Editing content

There's no templating system or CMS — `index.html` is one static file. Course
counts, descriptions, and card links are hand-written directly in the markup
(search for the course name or a lesson-count string to find the right
section). Design tokens (colors, spacing, fonts) live in the `:root { ... }`
CSS custom-property block near the top of the `<style>` tag.

If a course's lesson count changes (a repo gains or loses lessons), update it
in three places: this README's table above, the meta description tag, and the
matching card in `index.html`.

## Related

- Org profile: [github.com/techbaseng](https://github.com/techbaseng) — see
  [`techbaseng/.github`](https://github.com/techbaseng/.github) for the org
  README linking every Techbase repo, plus related projects on
  [github.com/babatundeawo](https://github.com/babatundeawo)
- Website: [techbasengr.com.ng](https://techbasengr.com.ng)
- YouTube: [@techbasengr](https://www.youtube.com/@techbasengr)

---
MIT Licence · © 2025–2026 Techbase Consultant Services · Built by [Babatunde Awoyemi](https://github.com/babatundeawo) · Made with ❤️ in Ibadan, Nigeria
