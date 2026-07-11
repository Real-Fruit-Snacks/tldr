#!/usr/bin/env python3
"""Download the tldr-pages English release bundle into build/cache/.

Usage: python build/fetch.py [--tag vX.Y]
Writes <cache>/tldr-pages.en-<tag>.zip and <cache>/RELEASE (tag, asset, sha256).
Reuses the cached zip when present. Prints the zip path and tag on stdout.
"""
import argparse
import hashlib
import json
import os
import urllib.request

API_LATEST = 'https://api.github.com/repos/tldr-pages/tldr/releases/latest'
ASSET = 'tldr-pages.en.zip'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tag')
    ap.add_argument('--cache', default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'cache'))
    args = ap.parse_args()
    os.makedirs(args.cache, exist_ok=True)

    if args.tag:
        tag = args.tag
        url = 'https://github.com/tldr-pages/tldr/releases/download/%s/%s' % (tag, ASSET)
    else:
        with urllib.request.urlopen(API_LATEST) as r:
            rel = json.load(r)
        tag = rel['tag_name']
        url = next(a['browser_download_url'] for a in rel['assets'] if a['name'] == ASSET)

    dest = os.path.join(args.cache, 'tldr-pages.en-%s.zip' % tag)
    if not os.path.exists(dest):
        print('downloading', url)
        with urllib.request.urlopen(url) as r, open(dest + '.part', 'wb') as f:
            while True:
                chunk = r.read(1 << 16)
                if not chunk:
                    break
                f.write(chunk)
        os.replace(dest + '.part', dest)
    with open(dest, 'rb') as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    with open(os.path.join(args.cache, 'RELEASE'), 'w', encoding='utf-8') as f:
        f.write('%s\n%s\n%s\n' % (tag, ASSET, sha))
    print('%s\n%s' % (dest, tag))


if __name__ == '__main__':
    main()
