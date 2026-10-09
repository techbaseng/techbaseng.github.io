# build

`build.py` turns `content/` and `templates/` into the finished site in `dist/`. `check_site.py` verifies the result (links, anchors, headings, duplicate ids). `migrate_once.py` is the one-time script that imported the seven original course repositories. GitHub Actions runs all of this automatically.
