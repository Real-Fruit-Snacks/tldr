# tldr — offline command examples

A lightning-fast [tldr-pages](https://github.com/tldr-pages/tldr) lookup site. The
entire site — pre-rendered pages for the `common`, `linux`, and `windows` platforms
(English), search index, fonts, styling — is static files committed to this repo under
`docs/`. It makes **zero network calls**: no CDNs, no external fonts, no analytics. It
works on an air-gapped GitHub Enterprise instance and even opened straight from disk.

Sibling project to the `manpages` offline manual; same
[terminal-workbench-design-system](https://github.com/Real-Fruit-Snacks/terminal-workbench-design-system)
look, shared theme/pet preferences.

## Deploy (any GitHub / GitHub Enterprise)

1. Push this repo.
2. Settings → Pages → Source: **Deploy from a branch** → branch `main`, folder `/docs`.
3. Done. No Actions, no build step, no internet access required on the server.

## Local / offline use

Open `docs/index.html` directly in a browser, or serve it:
`python3 -m http.server --directory docs`.

## Keyboard shortcuts

`/` focus search · `↑` `↓` navigate results · `Enter` open · `Esc` clear.
Search accepts a platform filter: `tar linux` filters to linux; a bare `windows`
lists that platform. Prefixes work too (`wsl win`).
Theme toggle (dark/light) is in the header; it follows your OS preference by default.

## The ghost

The same ghost companion as the sibling manpages site (ported from
[Real-Fruit-Snacks/vault](https://github.com/Real-Fruit-Snacks/vault)). Click the ghost
button in the header for settings; preferences are shared with the manpages site.

## Refreshing the corpus (internet-connected side only)

    python build/fetch.py
    python build/build_site.py --zip build/cache/tldr-pages.en-<tag>.zip --release <tag> --out docs
    python build/smoke_test.py docs
    git add docs && git commit -m "chore: refresh corpus"

## How it works

- `build/fetch.py` downloads the `tldr-pages.en.zip` release asset (cached, sha256 recorded).
- `build/build_site.py` parses each page against the strict tldr format (fail-closed),
  wraps it in the app shell, cross-links `command` mentions that exist in the corpus,
  and emits `docs/data/index.js` — a compact name+description index loaded as a script
  (works on `file://`).
- Search is dependency-free JS (`docs/assets/search-core.js`).

## Licenses

- Page content: [tldr-pages](https://github.com/tldr-pages/tldr), CC-BY-4.0.
- Site code: MIT. Styling: [terminal-workbench-design-system](https://github.com/Real-Fruit-Snacks/terminal-workbench-design-system) tokens (MIT), vendored in `docs/assets/tokens.css`.
- Font: JetBrains Mono (OFL 1.1), vendored in `docs/assets/fonts/`.
