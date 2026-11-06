# Security policy

The Techbase website is a static site hosted on GitHub Pages. Accounts, saved progress and the contact and careers forms use Google Firebase (Authentication and Firestore). Firebase settings are injected from GitHub Actions secrets during the build; no keys or passwords are stored in this repository. Database access is deny-by-default (see `firebase/firestore.rules`): learners can only read and change their own data, and form submissions can be created but not read from the website.

## Reporting a vulnerability

Please do not open a public issue. Use GitHub's private reporting instead: open the **Security** tab of this repository and click **Report a vulnerability**. We will reply as soon as we can.

## Blog administration

Blog posts written at `/admin/` are stored in Firestore. Only accounts listed in the `admins` collection (which only the project owner can edit, in the Firebase console) can create, change or delete posts or their pictures; everyone else can read published posts only. Posts are shown as plain text through a small Markdown reader that never inserts HTML, and are cleaned again at build time. Report problems as described above.
