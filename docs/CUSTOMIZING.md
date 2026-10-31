# Customizing the site

Everything below can be done on the GitHub website: click a file, click the pencil icon, edit, and commit (ideally into a new branch and pull request, see [DEPLOYMENT.md](DEPLOYMENT.md)). The site rebuilds by itself.

## Things only you can confirm

I wrote these from your WordPress site. Please read them once and correct anything that is out of date:

| What | Where |
|---|---|
| Privacy notice wording and its "last updated" date (a plain-language draft, **not legal advice**) | `templates/privacy.html` and `updated` in `build/build.py` |
| Stats such as "5+ age our youngest learners start", "9 partner schools" (the number is counted from your partner list) | `templates/home.html`, `content/company/partners.json` |
| Team bios, roles, LinkedIn links | `content/company/team.json` |
| Client testimonials (copied word for word from WordPress; add or remove freely) | `content/company/testimonials.json` |
| Opening hours, phone, email, address, WhatsApp and social links | `content/site.json`, under `company` |
| Which lessons are open without an account (`free_preview_lessons`: the first N lessons of each course) | `content/site.json` |

## Change text

| What | File |
|---|---|
| Site name, contact details, links, copyright years | `content/site.json` |
| Home page wording | `templates/home.html` |
| About, Services, Team, Contact, Careers, FAQ, Tools pages | `templates/<name>.html` |
| Services (four boxes and the Services page) | `content/company/services.json` |
| "Why Techbase" boxes, "How we work" steps | `content/company/why.json`, `process.json` |
| FAQ questions and answers | `content/company/faq.json` |
| Careers page benefits | `content/company/careers.json` |
| Tools page cards | `content/company/tools.json` |
| Academy course names and descriptions | `content/courses.json` |
| The "Which path fits you?" box | `content/paths.json` |
| A lesson | `content/<course>/lessons/lesson_NN.html` |

## Add a blog post or a programme

1. Copy an existing file in `content/blog/` (or `content/portfolio/`), give the copy a new name with dashes, for example `my-new-post.md`. The name becomes the web address.
2. Change the lines between the `---` markers at the top (`title`, `date` as `YYYY-MM-DD`, `summary`, and `image`, which must be the name of a photo in `content/photos/` without `.jpg`) and write the text below in plain Markdown: `## Heading`, `**bold**`, `- list`, `[link](https://...)`. To place a photo inside the text: `![describe the photo](photo:photo-name)`.
3. To add a photo, upload a `.jpg` (any size up to about 3000 pixels wide) to `content/photos/` and add a line with its description to `content/photos/photos.json` (this description is what screen readers read out; the build stops if it is missing).

## Change colours and fonts

Open `assets/css/app.css`. The `:root` block at the top holds the brand colours: `--brand` (Techbase blue) and `--accent` (amber). The `:root[data-theme="dark"]` block below holds the dark theme. Fonts are stored in `assets/fonts/` and declared at the top of the same file, so there is nothing to load from Google.

## Change the logo and images

Logo and icons are in `assets/img/`. To replace one, open the folder, click **Add file > Upload files** and upload a file with the same name. The social preview images are 1200 × 630 pixels (`assets/img/og/`).

## Add a lesson

1. Copy the last lesson file in the course folder, rename it with the next number, and edit it, keeping the same structure.
2. Add it to `content/<course>/course.json` under the right phase.
3. Commit. The build stops with a clear message if a lesson is missing from, or not listed in, the index.

## What "locked lessons" really means

Lessons after the first in each course show a "Create a free account" box to visitors who are not signed in. This is a **convenience gate, not a lock**: the lesson text is still in the page and a technical visitor can read it, because GitHub Pages is a static host with no server to hide anything. If you ever need real protection (paid content), the lessons would have to move to a server or to Firebase.

## Read the enquiries and applications

Firebase console > Firestore Database > Data > `enquiries` and `applications`. See [FIREBASE_LOGIN_SETUP.md](FIREBASE_LOGIN_SETUP.md).

## Credits

- Fonts: Inter, Bricolage Grotesque, JetBrains Mono (SIL Open Font License 1.1).
- Icons: Lucide (ISC licence) and Simple Icons (CC0).
- Photos and partner logos are Techbase's own, from the WordPress media library.
