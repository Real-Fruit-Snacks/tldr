<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/Real-Fruit-Snacks/tldr/main/docs/assets/cover-dark.svg" />
  <img alt="tl;dr — offline command examples" src="https://raw.githubusercontent.com/Real-Fruit-Snacks/tldr/main/docs/assets/cover-light.svg" width="820" />
</picture>

<br/>

Fast, offline [tldr-pages](https://github.com/tldr-pages/tldr) — a fully static command
reference with instant search. No CDNs, no build step, no tracking. Host it anywhere
or open it straight from disk.

<br/>

[![License: MIT](https://img.shields.io/badge/License-MIT-f0c674?style=flat-square)](LICENSE)
&nbsp;[![Release](https://img.shields.io/github/v/release/Real-Fruit-Snacks/tldr?style=flat-square&color=6bdcff)](https://github.com/Real-Fruit-Snacks/tldr/releases/latest)
&nbsp;![Corpus](https://img.shields.io/badge/tldr--pages-v2.3-63f2ab?style=flat-square)
&nbsp;![Pages](https://img.shields.io/badge/pages-6880-b78cff?style=flat-square)

[Website](https://real-fruit-snacks.github.io/tldr/) · [Latest release](https://github.com/Real-Fruit-Snacks/tldr/releases/latest) · [Report an issue](https://github.com/Real-Fruit-Snacks/tldr/issues)

</div>

---

## Overview

The entire site — pre-rendered pages for the `common`, `linux`, and `windows`
platforms (English), search index, fonts, styling — is static files committed to this
repo under `docs/`. It makes **zero network calls** at runtime: no CDNs, no external
fonts, no analytics. Sibling project to the `manpages` offline manual; same
[terminal-workbench-design-system](https://github.com/Real-Fruit-Snacks/terminal-workbench-design-system)
look, shared theme and pet preferences.

## Features

- **6,880 pages** rendered from the tldr-pages corpus — every example command with
  highlighted `placeholders`, cross-linked command mentions, and per-page example TOCs.
- **Instant search** with platform filtering: `tar linux` filters to linux, a bare
  `windows` lists that platform, prefixes work (`wsl win`).
- **Keyboard-first**: `/` focus search · `↑` `↓` navigate · `Enter` open · `Esc` clear.
- **Dark / light theme** — follows your OS preference, with a manual toggle that persists.
- **Works from anywhere**: GitHub Pages, GitLab Pages, any static file server, or
  opened directly from disk as files.
- **A ghost** 👻 — the same companion as the sibling manpages site (ported from
  [Real-Fruit-Snacks/obsidian-vault-publisher](https://github.com/Real-Fruit-Snacks/obsidian-vault-publisher)). Click the ghost
  button in the header for settings; pet it to recolor it.

## Hosting

**GitHub / GitHub Enterprise**

1. Push this repo (or unzip the [latest release](https://github.com/Real-Fruit-Snacks/tldr/releases/latest) and push that).
2. Settings → Pages → Source: **Deploy from a branch** → branch `main`, folder `/docs`.
3. Done. No Actions, no build step, no internet access required on the server.

**GitLab / self-managed GitLab**

Push the repo — the included [`.gitlab-ci.yml`](.gitlab-ci.yml) publishes `docs/` via
GitLab Pages automatically.

**Anywhere else**

Serve the `docs/` folder with any static file server
(`python3 -m http.server --directory docs`), or just open `docs/index.html` in a browser.

## Refreshing the corpus (internet-connected side only)

    python build/fetch.py
    python build/build_site.py --zip build/cache/tldr-pages.en-<tag>.zip --release <tag> --out docs
    python build/smoke_test.py docs
    git add docs && git commit -m "chore: refresh corpus"

## How it works

- `build/fetch.py` downloads the `tldr-pages.en.zip` release asset (cached, sha256 recorded).
- `build/build_site.py` parses each page against the strict tldr format (fail-closed),
  wraps it in the app shell, cross-links `command` mentions that exist in the corpus,
  turns alias-stub pages into direct links, and emits `docs/data/index.js` — a compact
  name+description index loaded as a script (works on `file://`).
- Search is dependency-free JS (`docs/assets/search-core.js`).

## Licenses

- Page content: [tldr-pages](https://github.com/tldr-pages/tldr), CC-BY-4.0.
- Site code: MIT. Styling: [terminal-workbench-design-system](https://github.com/Real-Fruit-Snacks/terminal-workbench-design-system) tokens (MIT), vendored in `docs/assets/tokens.css`.
- Font: JetBrains Mono (OFL 1.1), vendored in `docs/assets/fonts/`.
