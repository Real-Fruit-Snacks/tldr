#!/usr/bin/env python3
"""Build the static tldr site from a cached tldr-pages release zip.

Usage:  python build/build_site.py --zip build/cache/tldr-pages.en-vX.Y.zip \
            --release vX.Y --out docs
Writes  <out>/pages/<platform>/<slug>.html and <out>/data/index.js.
Exits non-zero if validation fails (parse errors, slug collisions,
dangling internal links, index/file mismatch, suspiciously small corpus).
"""
import argparse
import datetime
import html
import json
import os
import re
import sys
import zipfile

PLATFORMS = ('common', 'linux', 'windows')
BAD_CHARS = re.compile(r'[:<>"\\|?*\s]')
RESERVED = ({'con', 'prn', 'aux', 'nul'}
            | set('com%d' % i for i in range(1, 10))
            | set('lpt%d' % i for i in range(1, 10)))
PLACEHOLDER_RE = re.compile(r'\{\{(.*?)\}\}')
CODESPAN_RE = re.compile(r'`([^`]+)`')
MOREINFO_RE = re.compile(r'^More information:\s*<?(https?://[^\s<>]+?)>?\.?\s*$', re.I)
SEEALSO_RE = re.compile(r'^See also:\s*(.+?)\.?\s*$', re.I)
INTERNAL_HREF_RE = re.compile(r'href="\.\./([^"#]+)"')


class ParseError(Exception):
    pass


def parse_page(text, src):
    """Parse one tldr markdown page (strict upstream format, fail-closed)."""
    name = None
    desc_lines = []
    more_url = None
    see_also = []
    examples = []
    pending_desc = None
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip()
        if not line.strip():
            continue
        if name is None:
            if not line.startswith('# '):
                raise ParseError('%s:%d: expected "# name" first' % (src, n))
            name = line[2:].strip()
        elif line.startswith('> '):
            if examples or pending_desc is not None:
                raise ParseError('%s:%d: description after examples' % (src, n))
            body = line[2:].strip()
            m = MOREINFO_RE.match(body)
            if m:
                more_url = m.group(1)
                continue
            m = SEEALSO_RE.match(body)
            if m:
                see_also = (CODESPAN_RE.findall(m.group(1))
                            or [s.strip() for s in m.group(1).split(',') if s.strip()])
                continue
            desc_lines.append(body)
        elif line.startswith('- '):
            if pending_desc is not None:
                raise ParseError('%s:%d: example missing command' % (src, n))
            pending_desc = line[2:].strip().rstrip(':')
        elif line.startswith('`') and line.endswith('`') and len(line) > 1:
            if pending_desc is None:
                raise ParseError('%s:%d: command without description' % (src, n))
            examples.append((pending_desc, line[1:-1]))
            pending_desc = None
        else:
            raise ParseError('%s:%d: unrecognized line %r' % (src, n, line[:60]))
    if name is None or pending_desc is not None or not examples:
        raise ParseError('%s: incomplete page' % src)
    return {'name': name, 'desc_lines': desc_lines, 'more_url': more_url,
            'see_also': see_also, 'examples': examples}


def esc(s):
    return html.escape(s, quote=False)


def render_command(cmd):
    """Escape a command line; {{placeholders}} become <var>."""
    out, pos = [], 0
    for m in PLACEHOLDER_RE.finditer(cmd):
        out.append(esc(cmd[pos:m.start()]))
        out.append('<var>%s</var>' % esc(m.group(1)))
        pos = m.end()
    out.append(esc(cmd[pos:]))
    return ''.join(out)


def render_inline(s, link_target):
    """Escape a description line; `spans` become <code>, linked when
    link_target(name) returns a relative href."""
    out, pos = [], 0
    for m in CODESPAN_RE.finditer(s):
        out.append(esc(s[pos:m.start()]))
        href = link_target(m.group(1))
        code = '<code>%s</code>' % esc(m.group(1))
        out.append('<a href="%s">%s</a>' % (esc(href), code) if href else code)
        pos = m.end()
    out.append(esc(s[pos:]))
    return ''.join(out)


def plain_text(s):
    """Markdown line -> plain text (index descriptions, TOC labels)."""
    return CODESPAN_RE.sub(r'\1', s)


def index_desc(desc_lines):
    d = plain_text(desc_lines[0]) if desc_lines else ''
    if len(d) > 120:
        d = d[:120].rsplit(' ', 1)[0].rstrip(',;:') + '…'
    return d


def slugify(stem):
    """tldr stems are already lowercase-safe; guard NTFS anyway."""
    slug = BAD_CHARS.sub('_', stem)
    if slug.lower().split('.')[0] in RESERVED:
        slug += '_'
    return slug


def load_corpus(zip_path):
    """Read pages/<platform>/*.md from the release zip -> (pages, errors)."""
    entry_re = re.compile(r'^(?:[^/]+/)?pages/(%s)/([^/]+)\.md$' % '|'.join(PLATFORMS))
    pages, errors, seen_paths = [], [], set()
    with zipfile.ZipFile(zip_path) as zf:
        for info in sorted(zf.infolist(), key=lambda i: i.filename):
            m = entry_re.match(info.filename)
            if not m:
                continue
            platform, stem = m.group(1), m.group(2)
            text = zf.read(info).decode('utf-8', errors='replace')
            try:
                p = parse_page(text, info.filename)
            except ParseError as e:
                errors.append(str(e))
                continue
            slug = slugify(stem)
            path = 'pages/%s/%s.html' % (platform, slug)
            if path.lower() in seen_paths:
                errors.append('slug collision: %s' % path)
                continue
            seen_paths.add(path.lower())
            p.update(platform=platform, stem=stem, slug=slug, path=path)
            pages.append(p)
    return pages, errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--zip', required=True)
    ap.add_argument('--release', required=True)
    ap.add_argument('--out', default='docs')
    ap.add_argument('--templates',
                    default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'))
    args = ap.parse_args()

    pages, errors = load_corpus(args.zip)
    by_key = dict(((p['stem'], p['platform']), p) for p in pages)
    by_name = {}
    for p in pages:
        by_name.setdefault(p['name'], []).append(p)

    def resolve(name, platform):
        """Command name -> page: same platform, then common, then a lone other."""
        stem = name.replace(' ', '-').lower()
        for plat in (platform, 'common'):
            t = by_key.get((stem, plat))
            if t:
                return t
        others = [t for t in by_name.get(name, []) if t['platform'] != platform]
        return others[0] if len(others) == 1 else None

    with open(os.path.join(args.templates, 'page.html'), encoding='utf-8') as f:
        tpl = f.read()
    gen_date = datetime.date.today().isoformat()

    written = set()
    internal_hrefs = []
    for p in pages:
        def target(nm, _p=p):
            t = resolve(nm, _p['platform'])
            if t is None or t is _p:
                return None
            return '../%s/%s.html' % (t['platform'], t['slug'])

        desc_html = [render_inline(l, target) for l in p['desc_lines']]
        if p['see_also']:
            links = []
            for nm in p['see_also']:
                href = target(nm)
                code = '<code>%s</code>' % esc(nm)
                links.append('<a href="%s">%s</a>' % (esc(href), code) if href else code)
            desc_html.append('See also: %s.' % ', '.join(links))
        if p['more_url']:
            desc_html.append('More information: <a class="ext" href="%s" rel="noopener">%s</a>'
                             % (esc(p['more_url']), esc(p['more_url'])))
        content = ['<p class="cmd-desc">%s</p>' % '<br>\n'.join(desc_html)]
        toc = []
        for i, (d, c) in enumerate(p['examples'], 1):
            content.append(
                '<section class="example" id="ex-%d">\n'
                '<h2 class="ex-desc">%s</h2>\n'
                '<pre class="ex-cmd"><code>%s</code></pre>\n</section>'
                % (i, render_inline(d, target), render_command(c)))
            label = plain_text(d)
            if len(label) > 48:
                label = label[:48].rsplit(' ', 1)[0] + '…'
            toc.append('<li><a href="#ex-%d">%s</a></li>' % (i, esc(label)))

        siblings = sorted((s for s in by_name.get(p['name'], []) if s is not p),
                          key=lambda s: s['platform'])
        also = ''
        if siblings:
            also = '<span class="also">also for: %s</span>' % ', '.join(
                '<a href="../%s/%s.html">%s</a>' % (s['platform'], s['slug'], s['platform'])
                for s in siblings)

        body = '\n'.join(content)
        internal_hrefs.extend(INTERNAL_HREF_RE.findall(body + also))
        page_html = (tpl.replace('{root}', '../../')
                     .replace('{title}', esc(p['name']))
                     .replace('{desc}', html.escape(index_desc(p['desc_lines']), quote=True))
                     .replace('{platform}', p['platform'])
                     .replace('{also}', also)
                     .replace('{generated}', gen_date)
                     .replace('{release}', esc(args.release))
                     .replace('{toc}', ''.join(toc))
                     .replace('{content}', body))
        dest = os.path.join(args.out, p['path'])
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, 'w', encoding='utf-8', newline='\n') as f:
            f.write(page_html)
        written.add('%s/%s.html' % (p['platform'], p['slug']))

    db = {'v': 1, 'generated': gen_date, 'release': args.release,
          'pages': [[p['name'], p['platform'], index_desc(p['desc_lines']), p['path']]
                    for p in pages]}
    os.makedirs(os.path.join(args.out, 'data'), exist_ok=True)
    with open(os.path.join(args.out, 'data', 'index.js'), 'w',
              encoding='utf-8', newline='\n') as f:
        f.write('window.TLDRDB=')
        f.write(json.dumps(db, ensure_ascii=False, separators=(',', ':')))
        f.write(';\n')

    # ---- validation (fail-closed) ----
    for p in pages:
        if not os.path.exists(os.path.join(args.out, p['path'])):
            errors.append('index path missing: %s' % p['path'])
    for h in set(internal_hrefs):
        if h not in written:
            errors.append('dangling internal link: ../%s' % h)
    if len(pages) < 2000:
        errors.append('suspiciously small corpus: %d pages' % len(pages))

    print('pages=%d errors=%d' % (len(pages), len(errors)))
    if errors:
        for e in errors[:20]:
            print('ERROR', e, file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
