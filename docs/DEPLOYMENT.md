# Publishing and maintaining the site

This guide is for the site owner. You never need a terminal or to install anything. Everything happens on github.com, in your web browser.

## How publishing works

- All changes are made on a **branch** (a safe copy) and sent as a **pull request**: a page where GitHub shows what changed and builds a preview. **The live website does not change until you press "Merge".**
- When you merge into `main`, GitHub rebuilds the whole site (all 472 lessons and every page) and publishes it on GitHub Pages. This takes about three minutes. You do nothing else.

## One-time setup

1. Open the repository **techbaseng/techbaseng.github.io** on GitHub.
2. Click **Settings > Pages**. Under **Build and deployment**, set **Source** to **GitHub Actions**.
3. Click **Settings > Advanced Security** (it may say **Code security**) and switch on **Dependabot alerts**, **Dependabot security updates** and **Secret scanning** (with **Push protection**). These are free and warn you if a password or key is ever pasted into the repository by mistake, or if a tool the site uses has a known weakness.
4. Turn on accounts and login by following [FIREBASE_LOGIN_SETUP.md](FIREBASE_LOGIN_SETUP.md). The site works without this; accounts and forms just stay off.

## Reviewing and publishing the new website (pull request)

The new website arrives as a pull request named **Premium redesign: company site with accounts, and the Academy under /learn/**.

1. Click the **Pull requests** tab and open it.
2. Scroll to the checks list near the bottom. Wait until **Build and deploy** shows a green tick (about three minutes). A red cross means the build found a problem; the message in **Details** says which file to fix.
3. Click **Details** next to **Build and deploy**. At the bottom of the run page, under **Artifacts**, download **site-preview**. Unzip it and double-click `index.html` to browse the new site on your computer. (Search with Ctrl + K, login, forms and offline mode work only on the live site.)
4. Happy? Go back to the pull request and click **Merge pull request**, then **Confirm merge**.
5. Click the **Actions** tab. The newest **Build and deploy** run turns green after about three minutes. Open `https://techbaseng.github.io` and refresh.
6. Not happy? Click **Close pull request** instead. Nothing changes on the live site. Tell your developer or Claude what to adjust.

### After merging: switch off the seven old course sites

The seven courses used to be separate repositories. They now live inside this one at the **same web addresses**, so no link breaks. GitHub keeps showing an old course website at its address until that repository's own site is switched off. For each of `techbase-html`, `techbase-css`, `techbase-js`, `techbase-python`, `techbase-scratch`, `techbase-robotics` and `techbase-practical-robotics`:

1. Open the repository, then **Settings > Pages**.
2. Click **Unpublish site** (or set **Source** to **None**).
3. Optional: **Settings > Danger Zone > Archive this repository** keeps it, read-only.

New pages appear at that address within about a minute. Learners keep their saved progress because the addresses and saved-progress names are unchanged.

## Checking that a deployment worked

Open the **Actions** tab. Yellow dot: still working. Green tick: published, refresh the site. Red cross: something failed, and the site stays on the last good version.

### Reading an error

Click the failed run, then the red **build** job, then the step with a red cross. Lines starting with `ERROR:` name the file and the problem, for example `techbase-css/lessons/lesson_07.html: broken link ...`. Fix that file and commit again. The Lighthouse and lint steps only report; they never block publishing.

## Rolling back

- **Undo a change:** open the pull request that made it, click **Revert** at the bottom, and merge the new pull request GitHub creates.
- **Redeploy an older version:** in **Actions** open an older green run and click **Re-run all jobs**.

## Updating content later

1. Open the file on GitHub (see [CUSTOMIZING.md](CUSTOMIZING.md) for which file).
2. Click the pencil icon and edit.
3. At the bottom choose **Create a new branch for this commit and start a pull request**, then **Propose changes**, then **Create pull request**. Check the green tick, then **Merge pull request**.
   (You may instead commit straight to `main` for small fixes; it publishes at once.)

## The old WordPress site

The WordPress website is separate and keeps working until you change where your domain (for example `techbasengr.com.ng`) points. This GitHub site does not touch it. Old WordPress addresses (for example `/faq-item/...` and `/testimonials/...`) are covered by redirect pages here; the full list is in the pull request description and in `redirects.json` in the published site.

## Connecting your own domain (optional)

1. **Settings > Pages > Custom domain**: type the domain and click **Save**.
2. At your domain provider add the records GitHub shows you (an `A` record set for the main domain, or a `CNAME` pointing to `techbaseng.github.io` for a subdomain such as `www`).
3. When GitHub shows a green check, tick **Enforce HTTPS**.
4. Change `url` in `content/site.json` (and add `"custom_domain": "yourdomain.com"` next to it) and commit.
5. In Firebase **Authentication > Settings > Authorized domains**, add the domain, and in the reCAPTCHA admin add it too if you use App Check.
