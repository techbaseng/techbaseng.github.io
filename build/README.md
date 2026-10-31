# build

`bundle.mjs` packs the Firebase sign-in code (`src/auth/`) into `.build/js/auth.js` using the settings in GitHub secrets. `build.py` turns `content/` and `templates/` into the finished site in `dist/`. `content.py` and `academy_parse.py` hold the content loaders. `check_site.py` verifies the result. `sw.template.js` becomes the offline service worker. GitHub Actions runs all of this automatically.
