<div align="center">

<img src="assets/img/logo-mark.svg" width="72" height="72" alt="Techbase Academy logo">

# Techbase Academy

**Free coding and robotics courses from Ibadan, Nigeria.**

[![Build and deploy](https://github.com/techbaseng/techbaseng.github.io/actions/workflows/deploy.yml/badge.svg)](https://github.com/techbaseng/techbaseng.github.io/actions/workflows/deploy.yml)
[![Live site](https://img.shields.io/website?url=https%3A%2F%2Ftechbaseng.github.io&label=live%20site)](https://techbaseng.github.io)
[![License: MIT](https://img.shields.io/badge/license-MIT-2457e6.svg)](LICENSE)

[Live site](https://techbaseng.github.io) · [Documentation](docs/) · [Report an issue](../../issues/new/choose)

</div>

![Techbase Academy home page showing the eight courses](docs/assets/preview.png)

## About

Techbase Academy is a free learning platform built by Techbase Consultant Services in Ibadan, Nigeria. It gives students of any background a complete, self-paced path from first lesson to advanced topics, with no sign-up. The curriculum runs from Scratch and HTML to data science, algorithms, AI and hands-on micro:bit robotics, for ages 8 through adult.

## Courses

| Course | Lessons | Level |
|---|---|---|
| [HTML Fundamentals](https://techbaseng.github.io/techbase-html/) | 34 | Beginner |
| [CSS Styling](https://techbaseng.github.io/techbase-css/) | 73 | Beginner to Advanced |
| [JavaScript](https://techbaseng.github.io/techbase-js/) | 46 | Intermediate |
| [Python Programming](https://techbaseng.github.io/techbase-python/) | 45 | Beginner to Advanced |
| [Scratch Programming](https://techbaseng.github.io/techbase-scratch/) | 35 | Beginner, ages 8 to 16 |
| [Micro:bit Fundamentals (Stage 1)](https://techbaseng.github.io/techbase-robotics/) | 123 | Beginner to Advanced |
| [Practical Robotics (Stage 2)](https://techbaseng.github.io/techbase-practical-robotics/) | 44 | Beginner to Advanced |
| [Google Android Studio](https://techbaseng.github.io/techbase-android/) | 72 | Beginner to Advanced |

Video walkthroughs are on the [Techbase YouTube channel](https://www.youtube.com/@techbasengr).

## Features

- 472 lessons and projects across eight courses
- Step-by-step lessons that unlock phase by phase, with practice tasks and a mini project
- Search every lesson with Ctrl + K (or `/`)
- Progress saved on your own device, with a "Continue" shortcut
- Copy buttons and syntax-highlighted code in every lesson
- Light and dark themes that follow your device setting
- Works on phones, tablets and desktops, and stays readable with JavaScript off

## How to use it

1. Open the [live site](https://techbaseng.github.io) and pick a course. The home page lists suggested learning paths.
2. Start at lesson 1, or search for a topic with Ctrl + K.
3. In step-by-step lessons, finish each phase to unlock the next. Project lessons link to the official micro:bit, Raspberry Pi or Freenove guide.
4. Come back any time. Your progress is stored in your browser on that device.

## Tech stack

- Static site generated with Python (Jinja2, Beautiful Soup, Pygments)
- Plain HTML, CSS and JavaScript in the browser, with no framework
- Inter, Bricolage Grotesque and JetBrains Mono via Google Fonts
- GitHub Actions and GitHub Pages for building and hosting

## Project structure

```
content/      Course details and every lesson source file, one folder per course
templates/    Page layouts (home, course, lesson, 404)
assets/       Stylesheets, scripts, logo, favicons and social images
build/        The site generator and the quality checks
tools/        Maintainer script that regenerates icons and social images
docs/         Guides for maintaining and deploying the site
.github/      Automated build, deploy and security workflows
```

## Contributing

Spotted a typo or a broken lesson? [Open an issue](../../issues/new/choose) or edit the file on GitHub and open a pull request. See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## Security

Please report vulnerabilities privately, as described in [SECURITY.md](SECURITY.md).

## License and credits

Released under the [MIT License](LICENSE). Scratch projects follow the Raspberry Pi Foundation curriculum, micro:bit projects come from [microbit.org](https://microbit.org), and Practical Robotics follows the Freenove Ultimate Starter Kit for micro:bit (FNK0045). Each lesson links to the official source. Fonts: Inter, Bricolage Grotesque and JetBrains Mono, all under the SIL Open Font License.

## Contact

[techbasengr.com.ng](https://techbasengr.com.ng)
