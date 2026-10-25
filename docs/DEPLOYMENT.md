# Deploying and maintaining the site

This guide is for the site owner. You never need a terminal. Everything happens on github.com.

## How deployment works

Every time a change lands on the `main` branch, GitHub builds the whole site (all 472 lessons) and publishes it on GitHub Pages. That takes about two minutes. You do nothing except make the change.

## One-time setup

1. Open the repository **techbaseng/techbaseng.github.io** on GitHub.
2. Click **Settings > Pages**.
3. Under **Build and deployment**, set **Source** to **GitHub Actions**.
4. Click **Settings > Code security** (or **Advanced Security**) and switch on **Secret scanning** and **Dependabot alerts**.

You should now see "Your site is live" on the Pages screen after the first deployment.

## First launch: moving all seven courses into this one repository

The seven course websites used to live in seven repositories. They now live inside this one, at the **same web addresses** (for example `techbaseng.github.io/techbase-css/`), so no link breaks and no redirects are needed. The live site does not change until you merge.

### A. Upload the new project to a separate branch

1. In the **techbaseng/techbaseng.github.io** repository, click the branch button (it says `main`), type `rebrand/single-build`, and click **Create branch**.
2. The `upload-batches` folder you received holds six small zip files (`batch-00-hidden-files`, then `batch-01` to `batch-05`). Unzip each one into its own folder on your computer. GitHub accepts at most 100 files per upload, so you upload one batch at a time. `batch-00-hidden-files` contains the automation (`.github` folder) and `.gitignore`; if you cannot see them after unzipping, turn on hidden files (Windows: View > Show > Hidden items; Mac: press Cmd + Shift + period).
3. With the new branch selected, click **Add file > Upload files**. Drag in the contents of `batch-00-hidden-files` (the files and folders inside it, not a zip). Wait until every file shows, then under **Commit changes** choose **Commit directly to the rebrand/single-build branch** and click **Commit changes**.
4. Repeat step 3 for `batch-01`, `batch-02` and so on up to `batch-05`, so all six batches are in.
5. Delete the two old hub files that are no longer used: open `assets/css/site.css`, click the three dots, then **Delete file**, and commit to the same branch. Do the same for `assets/js/site.js`. (The site ignores them either way.)

If you use GitHub Desktop, you can instead copy the project folder into your local copy of the repository, commit to a new branch and push it. The result is identical.

### B. Open a pull request and review the preview

1. GitHub shows a banner **rebrand/single-build had recent pushes**. Click **Compare & pull request**, then **Create pull request**.
2. The **Build and deploy** check starts. Wait for a green tick (about three minutes). A red cross means something needs fixing, see "Reading an error" below.
3. Click **Details** next to the check, then at the bottom of the run page open **Artifacts** and download **site-preview**. Unzip it and double-click `index.html`. You can browse the whole new site on your computer. Search (Ctrl + K) works only on the live site.
4. Not happy? Click **Close pull request**. Nothing changes on the live site.

### C. Go live

1. On the pull request, click **Merge pull request**, then **Confirm merge**.
2. Click the **Actions** tab. The newest run, **Build and deploy**, shows a yellow dot, then a green tick. Open `https://techbaseng.github.io` and refresh.
3. Now switch off the seven old course websites. Do this for each of the seven repositories (`techbase-html`, `techbase-css`, `techbase-js`, `techbase-python`, `techbase-scratch`, `techbase-robotics`, `techbase-practical-robotics`):
   - Open the repository, then **Settings > Pages**.
   - Click **Unpublish site** (or set Source to **None**).
   - Optional: scroll to **Danger Zone** and click **Archive this repository**, so it is kept but read-only.

Until you unpublish a course repository, GitHub keeps showing that course's old pages at its address. After you unpublish it, the new pages appear within a minute. Do this right after merging, one repository at a time.

Learners keep their saved progress, because the addresses and the saved-progress keys are unchanged.

## Updating content later

1. Open the file on GitHub (see [CUSTOMIZING.md](CUSTOMIZING.md) for which file).
2. Click the pencil icon, edit, and click **Commit changes**.
3. For a change you want to review first, choose **Create a new branch** instead and open a pull request, as above.

## Checking that a deployment worked

Open the **Actions** tab. Each run has an icon:

- Yellow dot: still working.
- Green tick: published. Refresh the live site.
- Red cross: something failed. The site stays on the last good version.

## Reading an error

Click the failed run, then the red **build** job, then the step marked with a red cross. Lines that start with `ERROR:` name the file and the problem, for example `techbase-css/lessons/lesson_07.html: broken link ...` or `index lists 73 lessons but folder has 72`. Fix that file and commit again. Lighthouse and lint steps only report; they never block a deployment.

## Rolling back

- **Undo the last change:** open the pull request that made it and click **Revert** at the bottom. Merge the new pull request it creates.
- **Redeploy an older version:** in the **Actions** tab open an older green run and click **Re-run all jobs**.

## Connecting a custom domain (optional)

1. **Settings > Pages > Custom domain**, type your domain and click **Save**.
2. At your domain provider, add the records GitHub shows you (an `A` record set for the main domain, or a `CNAME` pointing to `techbaseng.github.io` for a subdomain such as `learn`).
3. When GitHub shows a green check, tick **Enforce HTTPS**.
4. Change `url` in `content/site.json` to your new address and commit, so search engines and social previews use it.
