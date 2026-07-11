#!/usr/bin/env python3
"""Unit tests for build_site parsing/rendering. Run from build/: python test_build_site.py"""
import build_site as bs

SAMPLE = """# tar

> Archiving utility.
> Often combined with a compression method, such as `gzip`.
> See also: `star`, `zip`.
> More information: <https://www.gnu.org/software/tar>.

- [c]reate an archive and write it to a [f]ile:

`tar cf {{path/to/target.tar}} {{path/to/file1 path/to/file2}}`

- E[x]tract a (compressed) archive [f]ile into the current directory [v]erbosely:

`tar xvf {{path/to/source.tar[.gz|.bz2|.xz]}}`
"""


def test_parse_page():
    p = bs.parse_page(SAMPLE, 'pages/common/tar.md')
    assert p['name'] == 'tar'
    assert p['desc_lines'] == ['Archiving utility.',
                               'Often combined with a compression method, such as `gzip`.']
    assert p['more_url'] == 'https://www.gnu.org/software/tar'
    assert p['see_also'] == ['star', 'zip']
    assert len(p['examples']) == 2
    assert p['examples'][0][0] == '[c]reate an archive and write it to a [f]ile'
    assert p['examples'][0][1].startswith('tar cf {{')


def test_parse_more_info_without_brackets():
    p = bs.parse_page('# x\n\n> Desc.\n> More information: https://x.dev.\n\n- a:\n\n`x`\n', 'x.md')
    assert p['more_url'] == 'https://x.dev'


def test_parse_rejects_garbage():
    for bad in ('not a page', '# x\n\nstray prose\n', '# x\n\n- desc without command:\n'):
        try:
            bs.parse_page(bad, 'bad.md')
            assert False, 'should have raised: %r' % bad
        except bs.ParseError:
            pass


def test_render_command_placeholders():
    h = bs.render_command('tar cf {{target.tar}} -C {{dir}}')
    assert h == 'tar cf <var>target.tar</var> -C <var>dir</var>'


def test_render_command_escapes_html():
    h = bs.render_command('echo "<b>" > {{a & b}}')
    assert '<b>' not in h and '&lt;b&gt;' in h and '<var>a &amp; b</var>' in h


def test_render_inline_links_known_commands():
    h = bs.render_inline('Such as `gzip` or `-v`.',
                         lambda t: '../common/gzip.html' if t == 'gzip' else None)
    assert '<a href="../common/gzip.html"><code>gzip</code></a>' in h
    assert '<code>-v</code>' in h and '<a' not in h.split('gzip.html')[1]


def test_render_inline_escapes_outside_spans():
    assert bs.render_inline('a < b', lambda t: None) == 'a &lt; b'


def test_plain_text():
    assert bs.plain_text('Use `tar` well.') == 'Use tar well.'


def test_index_desc_first_line_truncated():
    d = bs.index_desc(['w' * 60 + ' ' + 'x' * 80, 'second line ignored'])
    assert d.endswith('…') and len(d) <= 121
    assert bs.index_desc(['Short.']) == 'Short.'
    assert bs.index_desc([]) == ''


def test_slugify():
    assert bs.slugify('git-checkout') == 'git-checkout'
    assert bs.slugify('nul') == 'nul_'
    assert bs.slugify('a b:c') == 'a_b_c'


if __name__ == '__main__':
    fails = 0
    for n in sorted(list(globals())):
        if n.startswith('test_'):
            try:
                globals()[n]()
                print('ok', n)
            except AssertionError as e:
                fails += 1
                print('FAIL', n, e)
    raise SystemExit(1 if fails else 0)
