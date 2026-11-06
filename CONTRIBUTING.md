# Contributing

Thank you for helping improve Techbase Academy. You can contribute from the GitHub website alone.

## Report a problem or suggest an idea

[Open an issue](../../issues/new/choose) and choose the matching form. Include the page address for lesson problems.

## Fix a lesson yourself

1. Open the lesson file under `content/<course>/lessons/` on GitHub.
2. Click the pencil icon, make your change, and choose **Create a new branch for this commit and start a pull request**.
3. Open the pull request. A check called **Build and deploy** runs automatically. A green tick means the site still builds.

## Developers: building locally

This is optional. All real builds run on GitHub.

```
pip install -r requirements.txt
npm ci
python build/build.py        # accounts are off unless FIREBASE_* settings are exported
python build/check_site.py
npm test                     # unit tests for the progress-sync code
```

The finished site is written to `dist/`. See [docs/CUSTOMIZING.md](docs/CUSTOMIZING.md) for where things live.
