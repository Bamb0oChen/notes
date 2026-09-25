import hashlib
import importlib.util
import json
import os
import re
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('thoughts_hook', ROOT / 'hooks/thoughts.py')
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)


def frontmatter(path):
    _, header, body = path.read_text(encoding='utf-8').split('---', 2)
    return yaml.safe_load(header), body.strip()


def test_archive_manifest():
    manifest = json.loads((ROOT / 'content-audits/thoughts-phase-1.json').read_text(encoding='utf-8'))
    paths = {ROOT / e['path'] for e in manifest['entries']}
    assert len(paths) == manifest['count'] == 138
    assert paths == set((ROOT / 'docs/随想/第一阶段').glob('*.md'))
    used_lines = set()
    for entry in manifest['entries']:
        meta, body = frontmatter(ROOT / entry['path'])
        assert meta['source_header'] == entry['header']
        assert meta['source_lines'] == f"{entry['start']}-{entry['end']}"
        assert meta['date'] == entry['date']
        assert meta['thought'] is True and body
        span = set(range(entry['start'], entry['end'] + 1))
        assert not used_lines & span
        used_lines.update(span)
    assert not used_lines & set(range(1989, 2001))
    assert 1699 not in used_lines and 4385 not in used_lines


def test_source_fidelity():
    source = os.environ.get('THOUGHTS_SOURCE')
    if not source:
        pytest.skip('Set THOUGHTS_SOURCE to verify the original private attachment')
    source = Path(source)
    manifest = json.loads((ROOT / 'content-audits/thoughts-phase-1.json').read_text(encoding='utf-8'))
    assert hashlib.sha256(source.read_bytes()).hexdigest() == manifest['sha256']
    lines = source.read_text(encoding='utf-8-sig').splitlines()
    for entry in manifest['entries']:
        original = '\n'.join(lines[entry['start']:entry['end']]).strip()
        _, body = frontmatter(ROOT / entry['path'])
        body = re.sub(r'^## 原文后续条目：', '', body, flags=re.M)
        body = re.sub(r'^## ', '', body, flags=re.M)
        assert re.sub(r'\s', '', body) == re.sub(r'\s', '', original), entry['path']


def fake_page(content, **meta):
    return SimpleNamespace(content=content, meta={'date': '2026-09-26', 'thought': True, **meta},
                           title='Title', url='随想/第一阶段/test/', file=SimpleNamespace(src_uri='test.md'))


def test_literal_excerpt_and_images():
    text = '原文' * 150
    card = hook.make_card(fake_page('<p>' + text + '</p><img src="../images/example.jpg" alt="配图">'))
    assert card['excerpt'] == text[:220] + '…'
    assert card['image']['src'] == '随想/第一阶段/images/example.jpg'
    assert card['image']['alt'] == '配图'
    assert hook.make_card(fake_page('<p>保留</p><!-- more --><p>不进摘录</p>'))['excerpt'] == '保留'
    assert hook.make_card(fake_page('<p>&lt;script&gt;不执行&lt;/script&gt;</p>'))['excerpt'] == '<script>不执行</script>'


def test_bad_metadata_fails_build():
    for values in ({'date': '昨天'}, {'tags': 'not-a-list'}, {'date': '2026-09-26T12:00+08:00'}):
        with pytest.raises(Exception):
            hook.make_card(fake_page('<p>正文</p>', **values))


def test_site_has_no_api_login():
    template = (ROOT / 'overrides/thoughts.html').read_text(encoding='utf-8')
    js = (ROOT / 'docs/assets/javascripts/thoughts.js').read_text(encoding='utf-8')
    assert 'data-api' not in template and 'password' not in template
    assert 'fetch(' not in js and 'localStorage' not in js and '/auth/' not in js
