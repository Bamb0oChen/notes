import hashlib
import importlib.util
import json
import os
import re
import subprocess
from datetime import datetime
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
    assert paths <= set((ROOT / 'docs/随想').glob('*.md'))
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
                           title='Title', url='随想/test/', file=SimpleNamespace(src_uri='test.md'))


def test_literal_excerpt_and_images():
    text = '原文' * 150
    card = hook.make_card(fake_page('<p>' + text + '</p><img src="../images/example.jpg" alt="配图">'))
    assert card['excerpt'] == text[:220] + '…'
    assert card['image']['src'] == '随想/images/example.jpg'
    assert card['image']['alt'] == '配图'
    assert hook.make_card(fake_page('<p>保留</p><!-- more --><p>不进摘录</p>'))['excerpt'] == '保留'
    assert hook.make_card(fake_page('<p>&lt;script&gt;不执行&lt;/script&gt;</p>'))['excerpt'] == '<script>不执行</script>'


def test_bad_metadata_fails_build():
    for values in ({'date': '昨天'}, {'tags': 'not-a-list'}, {'date': '2026-09-26T12:00+08:00'}):
        with pytest.raises(Exception):
            hook.make_card(fake_page('<p>正文</p>', **values))


def test_plain_post_needs_no_frontmatter(tmp_path):
    path = tmp_path / 'docs/随想/随手写.md'
    path.parent.mkdir(parents=True)
    body = '# 今天路上想到的事\n\n想到什么就直接写。\n\n第二段也照常保留。'
    path.write_text(body, encoding='utf-8')
    page = SimpleNamespace(meta={}, title='随手写',
                           file=SimpleNamespace(src_uri='随想/随手写.md'))
    rendered = hook.on_page_markdown(body, page=page,
                                     config=SimpleNamespace(docs_dir=path.parents[1]), files=None)
    assert '# 今天路上想到的事' not in rendered
    assert '想到什么就直接写。' in rendered
    assert page.meta['date'] == hook.post_date(page.file.src_uri, SimpleNamespace(docs_dir=path.parents[1]))
    assert page.meta['title'] == page.title == '今天路上想到的事'
    assert page.meta['thought'] is True
    assert page.meta['template'] == 'thought-post.html'
    assert page.meta['untitled'] is False


def test_explicit_date_is_preserved_without_source_file():
    page = SimpleNamespace(meta={'date': '2026-09-24 20:05:49'}, title='随手写',
                           file=SimpleNamespace(src_uri='随想/随手写.md'))
    hook.on_page_markdown('# 原题\n\n正文', page=page, config=None, files=None)
    assert page.meta['date'] == '2026-09-24 20:05:49'
    assert page.meta['title'] == '原题'
    page.meta = {}
    # Empty local drafts stay out of the card list.
    page.meta = {'date': '2026-09-24'}
    hook.on_page_markdown('', page=page, config=None, files=None)
    assert page.meta['thought'] is False


def test_committed_post_uses_first_addition_not_checkout_time(tmp_path):
    repo = tmp_path
    path = repo / 'docs/随想/任意名字.md'
    path.parent.mkdir(parents=True)
    path.write_text('# 标题\n正文', encoding='utf-8')
    for command in (['git', 'init'], ['git', 'config', 'user.email', 'test@example.test'],
                    ['git', 'config', 'user.name', 'Test'], ['git', 'add', '.']):
        subprocess.run(command, cwd=repo, check=True, capture_output=True)
    env = {**os.environ, 'GIT_AUTHOR_DATE': '2026-09-24T20:05:49+08:00',
           'GIT_COMMITTER_DATE': '2026-09-24T20:05:49+08:00'}
    subprocess.run(['git', 'commit', '-m', 'Add post'], cwd=repo, env=env,
                   check=True, capture_output=True)
    config = SimpleNamespace(docs_dir=repo / 'docs')
    assert hook.post_date('随想/任意名字.md', config) == '2026-09-24 20:05:49'


def test_old_article_routes_redirect_to_flat_paths(tmp_path):
    docs = tmp_path / 'docs/随想'
    docs.mkdir(parents=True)
    (docs / '归档.md').write_text('source_header: 原始记录', encoding='utf-8')
    (docs / '日常.md').write_text('# 日常', encoding='utf-8')
    config = SimpleNamespace(docs_dir=tmp_path / 'docs', site_dir=tmp_path / 'site')
    hook.on_post_build(config=config)
    assert '../../%E5%BD%92%E6%A1%A3/' in (tmp_path / 'site/随想/第一阶段/归档/index.html').read_text(encoding='utf-8')
    assert '../../%E6%97%A5%E5%B8%B8/' in (tmp_path / 'site/随想/posts/日常/index.html').read_text(encoding='utf-8')


def test_site_has_no_api_login():
    template = (ROOT / 'overrides/thoughts.html').read_text(encoding='utf-8')
    js = (ROOT / 'docs/assets/javascripts/thoughts.js').read_text(encoding='utf-8')
    assert 'data-api' not in template and 'password' not in template
    assert 'fetch(' not in js and 'localStorage' not in js and '/auth/' not in js
