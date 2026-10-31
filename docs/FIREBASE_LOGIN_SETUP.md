# Switching on accounts and login (Firebase)

This guide is for the site owner and assumes you have never used Firebase before. It takes about 30 minutes, you do it once, and everything is done in your web browser. You need a Google account and your GitHub login. The Firebase **Spark (free)** plan is enough. You will not be asked for a card.

**What you will have at the end:** visitors can create a free account (email and password, or Google), log in on any device, and have their lesson progress saved to their account. The first lesson of every course stays open to everyone. The contact and careers forms deliver messages to a private list you can read.

**Until you finish this guide the website still works.** Accounts, the sign-in buttons and the contact forms simply stay switched off, and every course stays open to read.

## Words you will see

| Word | Meaning |
|---|---|
| **Firebase** | A free service from Google that handles sign-in and stores small amounts of data. |
| **Authentication** | The Firebase part that creates accounts and checks passwords. You never see anyone's password. |
| **Firestore** | The Firebase database. It holds each learner's progress, and the messages sent through your forms. |
| **Secret (GitHub)** | A private setting stored in GitHub. The website build reads it, but nobody can look at it afterwards. |
| **Web app config** | Four short settings that tell the website which Firebase project to talk to. They are an address, not a password. |
| **Rules** | A list, kept in Firebase, of who may read or write what. Ours say "people can only see their own data". |

## Step 1. Create the Firebase project

1. Go to <https://console.firebase.google.com> and sign in with your Google account.
2. Click **Create a project** (or **Add project**).
3. Name it `techbase-academy` and click **Continue**.
4. Switch **off** "Enable Google Analytics" (the site does not use analytics) and click **Create project**.
5. Wait for "Your new project is ready" and click **Continue**.

**You should now see** the project's home screen with the project name at the top left.

## Step 2. Register the website

1. On the project home screen click the web icon, which looks like `</>` (under "Get started by adding Firebase to your app").
2. App nickname: type `Techbase website`. Leave "Firebase Hosting" **unticked**. Click **Register app**.
3. You will see a box of code that contains `const firebaseConfig = { ... }`. Keep this page open, or copy the four values listed here into a private note for Step 6:
   - `apiKey`
   - `authDomain` (looks like `techbase-academy.firebaseapp.com`)
   - `projectId`
   - `appId`
4. Click **Continue to console**.

**You should now see** the project home screen again, with "Techbase website" listed under your apps.

## Step 3. Switch on sign-in

1. In the left menu click **Build**, then **Authentication**, then **Get started**.
2. Under **Sign-in method** click **Email/Password**. Switch **Enable** on. Leave "Email link (passwordless sign-in)" off. Click **Save**.
3. Click **Add new provider**, then **Google**. Switch **Enable** on. For **Project public-facing name** type `Techbase Academy`. For **Project support email** choose your email address. Click **Save**.
4. Click the **Settings** tab (still inside Authentication), then **Authorized domains**.
5. You should already see `localhost` and `techbase-academy.firebaseapp.com`. Click **Add domain**, type `techbaseng.github.io` and click **Add**. If you later connect your own domain, add it here too.

**You should now see** `techbaseng.github.io` in the list of authorized domains, and two providers (Email/Password, Google) marked "Enabled".

**Optional, recommended:** on the **Templates** tab click the pencil beside **Email address verification**, change the **Sender name** to `Techbase Academy`, and click **Save**. Do the same for **Password reset**.

## Step 4. Create the database

1. In the left menu click **Build**, then **Firestore Database**, then **Create database**.
2. Choose the location closest to your learners, for example `eur3 (europe-west)`. You cannot change this later. Click **Next**.
3. Choose **Start in production mode** (this blocks everyone until we add the rules in the next step). Click **Create**.

**You should now see** an empty database with tabs named Data, Rules, Indexes and Usage.

## Step 5. Publish the security rules

1. Click the **Rules** tab.
2. On GitHub open the file `firebase/firestore.rules` in this repository and click the **Copy raw file** button (two squares icon, top right of the file).
3. Back in Firebase, click inside the rules editor, press **Ctrl + A** (Mac: Cmd + A) to select everything, and paste.
4. Click **Publish**.

**You should now see** "Rules published" with today's date. These rules refuse everything except: learners reading and changing only their own profile and progress, and anyone sending (but never reading) an enquiry or application.

## Step 6. Give the settings to GitHub

1. On GitHub open the repository **techbaseng/techbaseng.github.io**.
2. Click **Settings**, then in the left menu **Secrets and variables**, then **Actions**.
3. Click **New repository secret**. Create these four secrets, one at a time. The **Name** must be typed exactly as shown; the **Secret** is the matching value from Step 2.

| Name | Value |
|---|---|
| `FIREBASE_API_KEY` | the `apiKey` value |
| `FIREBASE_AUTH_DOMAIN` | the `authDomain` value |
| `FIREBASE_PROJECT_ID` | the `projectId` value |
| `FIREBASE_APP_ID` | the `appId` value |

4. Click **Add secret** after each one.
5. Click the **Actions** tab, choose **Build and deploy** in the left list, click **Run workflow**, then the green **Run workflow** button. (A merge to `main` also does this.)
6. Wait for the green tick (about three minutes).

**You should now see** at `https://techbaseng.github.io` a **Log in** and **Create account** button at the top right.

## Step 7. Test it (about 10 minutes)

Work through each line. Use a private (incognito) window so nothing is already remembered.

1. Open `https://techbaseng.github.io/learn/`. Open the **CSS Styling** course. You should see a small lock on every lesson except the first.
2. Open lesson 2. You should see the "Create a free account to keep going" box and a faded lesson behind it.
3. Click **Create free account**, fill in your name, an email you can open, a password of at least 8 characters, tick the privacy box and click **Create my free account**. You should see "Check your email". Open the email, click the link, and return to the website.
4. Open lesson 2 again. The lesson should now be fully open and your first name should show at the top right.
5. Open the first lesson of the Scratch course, click **Mark as done**, wait 5 seconds, then open `https://techbaseng.github.io/account/`. Your progress list should show 1 of 35 done for Scratch.
6. Click your name at the top right, then **Sign out**. Click **Log in**, sign in again, and check that your progress is still there. Try the same in a different browser or on your phone.
7. Try **Continue with Google**.
8. Open the **Contact** page, send yourself a test enquiry, then in Firebase open **Firestore Database > Data**. You should see an `enquiries` collection with your message.
9. On the **Account** page click **Send password reset email** and check the email arrives.

To remove test accounts: Firebase console > **Authentication > Users** > the three dots beside a user > **Delete account**, or use **Delete my account** on the Account page.

## Reading messages sent through your forms

Firebase console > **Firestore Database > Data**. The collections `enquiries` and `applications` hold what people sent. Click one to read it. Nobody except you (signed in to Firebase) can read them. Firebase does not send you an email when one arrives, so check this page,.

## Strongly recommended: App Check (stops bots)

App Check lets Firebase refuse requests that do not come from your real website. It is free.

1. Go to <https://www.google.com/recaptcha/admin/create>. Label: `Techbase`. Choose **reCAPTCHA v3**. Under **Domains** add `techbaseng.github.io`. Submit.
2. Copy the **Site key** (the public one) and the **Secret key** (private, never paste it anywhere on GitHub).
3. In Firebase console > **Build > App Check > Apps**, click your web app, choose **reCAPTCHA**, paste the **Secret key**, and click **Save**.
4. Create one more GitHub secret (as in Step 6): `FIREBASE_APPCHECK_SITE_KEY` with the **Site key**. Run **Build and deploy** again.
5. Test the website as in Step 7. If sign-in still works, go to Firebase **App Check > APIs**, click **Authentication** and **Cloud Firestore**, and click **Enforce** for both.

If anything stops working after enforcing, click **Unenforce** and the site works again.

## Common errors

| What you see | What it means and what to do |
|---|---|
| No Log in button on the website | The four secrets are missing or misspelled, or **Build and deploy** has not run since. Re-check Step 6, then run the workflow again. |
| "This website address is not approved for sign-in yet" | Step 3 item 5: add `techbaseng.github.io` to **Authorized domains**. |
| "This sign-in method is not switched on yet" | Step 3: enable Email/Password and Google. |
| Sign-up works but progress does not follow you to a second device | The rules were not published (Step 5) or were published without the **progress** section. Paste the rules again and click **Publish**. |
| Contact form says "That did not send" | Same cause: rules not published, or **App Check** is enforced but its site key secret is missing. |
| The Google pop-up is blocked | The visitor's browser blocked pop-ups. They should allow pop-ups for the site and try again. |
| "Too many attempts" | Firebase slows repeated wrong passwords. Wait a few minutes. |
| Build shows a red cross after adding secrets | Open the failed run and read the line starting `ERROR`. A secret with a stray space or quote around it is the usual cause: delete it and add it again. |

## What NOT to share or commit

- Never paste your **reCAPTCHA secret key**, a Firebase **service account** file (a `.json` file with `private_key` inside), or any password into GitHub, an issue, a pull request or a chat.
- The four web app config values are not secret in the way a password is (they are visible to anyone who opens the website), but keep them in GitHub secrets as set up above rather than writing them into files.
- If you ever commit a private key by mistake: do not just delete it. In Google Cloud console > **IAM & Admin > Service accounts**, delete that key (or reset the credential), and tell whoever maintains the site.
- Anything you type in the Firebase console stays private to you. Anyone you add under **Project settings > Users and permissions** can see learners' emails, so add only people you trust.

## Costs

The free Spark plan allows about 50,000 reads and 20,000 writes per day, and plenty of sign-ins. For a training academy this is ample. If you ever approach the limit Firebase emails you, and nothing is charged unless you move to the paid plan yourself.
