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

## Write blog posts without touching GitHub (the admin area)

Once you have done Step 8 in `FIREBASE_LOGIN_SETUP.md`, sign in and open `/admin/` on your website.

- **New post:** click **New post**, fill in the title, summary and date, choose a cover photo, write the article and tick **Published** when it is ready. Leave it unticked to keep a private draft.
- **Photos:** choose one of the Techbase photos already on the site, or upload your own. Uploaded photos are shrunk automatically and need a short description for screen readers. Please use real photos from your own classes and events, not computer-generated pictures.
- **Formatting:** use the buttons above the text box. A post is live on the blog the moment you save it as published. About every six hours the site rebuilds itself and gives the post a permanent page that Google can find. To make that happen sooner, open the **Actions** tab on GitHub, click **Build and deploy**, then **Run workflow**.
- **Edit or delete:** open `/admin/`, click **Edit** on a post. Deleting a post also removes its uploaded pictures.
- **Not in the admin area:** the original posts and the monthly archive are files in `content/blog/`. Edit those on GitHub as described below.

## The monthly blog archive and its pictures

`content/blog/` holds one post for each month from January 2022. Company milestones (KBI Schools, community holiday classes, Baptist Model High Schools, Rise Conference, the Akinyele Spelling Challenge, International Day of the Girl) come from your Portfolio. Posts about technology news and events are general write-ups; please read them once and change anything you disagree with.

Posts that still need a picture show a plain book icon. The list is in `docs/IMAGE_TODO.md` (run `python tools/list_image_todo.py` to refresh it). To add a picture, follow the three steps at the top of that file.

## Add a blog post (as a file) or a programme

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
