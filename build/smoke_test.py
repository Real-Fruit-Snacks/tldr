#!/usr/bin/env python3
"""Post-build integrity + zero-network audit. Usage: python build/smoke_test.py [docs]"""
import json
import pathlib
import random
import re
import sys

docs = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'docs')
pages = list(docs.glob('pages/*/*.html'))
fails = []

if len(pages) < 2000:
    fails.append('only %d generated pages' % len(pages))

idx = (docs / 'data' / 'index.js').read_text(encoding='utf-8')
db = json.loads(idx[idx.index('=') + 1:].rstrip().rstrip(';'))
if len(db['pages']) != len(pages):
    fails.append('index has %d entries but %d page files' % (len(db['pages']), len(pages)))
for e in db['pages']:
    if not (docs / e[3]).exists():
        fails.append('index path missing: %s' % e[3])
        break

sample = random.sample(pages, min(300, len(pages)))
for p in sample:
    t = p.read_text(encoding='utf-8', errors='replace')
    if '</html>' not in t or 'class="example"' not in t or 'class="cmd-desc"' not in t:
        fails.append('broken structure: %s' % p)

# zero-network audit: after removing opt-in content links (<a class="ext" ...>),
# no external URL may remain in any src/href across the whole site.
EXT_A = re.compile(r'<a class="ext" href="https?://[^"]*"[^>]*>')
NET = re.compile(r'(?:src|href)="(?:https?:)?//', re.I)
for p in pages + [docs / 'index.html', docs / '404.html']:
    t = p.read_text(encoding='utf-8', errors='replace')
    if NET.search(EXT_A.sub('', t)):
        fails.append('external reference: %s' % p)

print('pages=%d sampled=%d fails=%d' % (len(pages), len(sample), len(fails)))
for f in fails[:20]:
    print('FAIL', f)
sys.exit(1 if fails else 0)
