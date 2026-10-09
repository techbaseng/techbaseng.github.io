# Customizing the site

Everything below can be done on the GitHub website. Click a file, click the pencil icon, edit, then commit. The site rebuilds and deploys by itself (see [DEPLOYMENT.md](DEPLOYMENT.md)).

## Change text

| What | File |
|---|---|
| Site name, address, links (website, YouTube, GitHub), copyright years | `content/site.json` |
| Course names, short descriptions, difficulty text, order | `content/courses.json` |
| The "Not sure where to begin?" list on the home page | `content/paths.json` |
| Home page wording (headline, about text) | `templates/hub.html` |
| A course page: headline, about text, "what you need", steps, lesson list | `content/<course>/course.json` |
| A lesson | `content/<course>/lessons/lesson_NN.html` |
| Footer and menu | `templates/base.html` |

## Change colours

Open `assets/css/app.css`. The first block, `:root`, holds the brand colours.

- `--brand` is the Techbase blue used for buttons and links.
- `--accent` is the amber highlight.
- The block below it, `:root[data-theme="dark"]`, holds the dark theme.
- Each course colour is a line starting `.c-html`, `.c-css` and so on. Change `--c` (graphics) and `--c-ink` (text). Keep `--c-ink` dark enough to read on white.

## Change fonts

Fonts load from Google Fonts in one line near the top of `templates/base.html` (look for `fonts.googleapis.com`). Replace the family names there, then update `--font-display`, `--font-body` and `--font-mono` at the top of `assets/css/app.css`.

## Change images and the logo

Files live in `assets/img/`: `logo-mark.svg` (logo), `favicon.svg`, `favicon.ico`, the app icons and the social preview images in `assets/img/og/`. To replace one, open the folder on GitHub, choose **Add file > Upload files**, and upload a file with the same name. Social preview images are 1200 x 630 pixels.

## Add a lesson

1. Copy the last lesson file in the course folder, rename it with the next number (for example `lesson_74.html`) and edit its content. Keep the same structure as the other files.
2. Add the lesson to the list in `content/<course>/course.json`, under the right phase, with `num`, `file`, `title` and `desc`.
3. Commit. The build fails with a clear message if a lesson file is not listed or a listed file is missing.

## How a lesson file is read

Step-by-step courses (HTML, CSS, JavaScript, Python) are read for their title (`<h1>` inside `.l-hero`), their `.phase` blocks, and the build-it, GitHub steps and session-end blocks. Project courses (Scratch, Micro:bit, Practical Robotics) are read for the hero details, the `.lesson-body` and the sidebar cards. The old page header and footer in each file are ignored because the site rebuilds them.
