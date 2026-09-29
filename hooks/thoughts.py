"""Build static thought cards from Markdown. No API, passwords or runtime fetches."""
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from html import escape
from pathlib import Path, PurePosixPath
import os
import re
import subprocess
from urllib.parse import quote, urljoin, urlsplit
from mkdocs.exceptions import PluginError


THOUGHTS_DIR = '随想/'
SITE_TIMEZONE = timezone(timedelta(hours=8))
TITLE = re.compile(r'^#\s+(.+?)\s*#*\s*$')


def first_title(markdown):
    """Find a top-level heading outside fenced code blocks."""
    offset = 0
    fence = None
    for line in markdown.splitlines(keepends=True):
        stripped = line.lstrip()
        marker = re.match(r'^(`{3,}|~{3,})', stripped)
        if marker:
            chars = marker.group(1)
            if fence is None:
                fence = (chars[0], len(chars))
            elif chars[0] == fence[0] and len(chars) >= fence[1]:
                fence = None
        elif fence is None:
            match = TITLE.match(line.rstrip('\r\n'))
            if match:
                return match.group(1).strip(), offset, offset + len(line)
        offset += len(line)
    return None


def post_date(source, config):
    """Use the first Git addition for a stable published date; local drafts use birth time."""
    docs = Path(config.docs_dir).resolve()
    path = docs.joinpath(*PurePosixPath(source).parts)
    repo = docs.parent
    relative = path.relative_to(repo).as_posix()
    tracked = subprocess.run(['git', 'ls-files', '--error-unmatch', '--', relative],
                             cwd=repo, capture_output=True, text=True, encoding='utf-8',
                             errors='replace', check=False)
    stamp = None
    if tracked.returncode == 0:
        history = subprocess.run(['git', 'log', '--follow', '--diff-filter=A',
                                  '--format=%cI', '--', relative], cwd=repo,
                                 capture_output=True, text=True, encoding='utf-8',
                                 errors='replace', check=False)
        dates = history.stdout.splitlines()
        if dates:
            stamp = datetime.fromisoformat(dates[-1]).astimezone(SITE_TIMEZONE)
        elif history.returncode:
            raise PluginError(f'{source}: 无法读取 Git 历史')
    if stamp is None:
        if not path.is_file():
            raise PluginError(f'{source}: 找不到 Markdown 源文件')
        stat = path.stat()
        birth = getattr(stat, 'st_birthtime', None)
        if birth is None:
            birth = stat.st_ctime if os.name == 'nt' else stat.st_mtime
        stamp = datetime.fromtimestamp(birth, SITE_TIMEZONE)
    return stamp.strftime('%Y-%m-%d %H:%M:%S')


def on_page_markdown(markdown, *, page, config, files):
    """Turn a plain Markdown file into a post without requiring front matter."""
    source = page.file.src_uri.replace('\\', '/')
    if (not source.startswith(THOUGHTS_DIR) or not source.endswith('.md')
            or '/' in source[len(THOUGHTS_DIR):] or source == '随想/index.md'):
        return markdown

    meta = page.meta
    if 'date' not in meta:
        meta['date'] = post_date(source, config)
        meta['date_label'] = meta['date']

    if not meta.get('title'):
        heading = first_title(markdown)
        if heading:
            meta['title'], start, end = heading
            markdown = markdown[:start] + markdown[end:]

    # A newly created but still empty file should not appear as a blank card.
    meta.setdefault('thought', bool(markdown.strip()))
    meta.setdefault('template', 'thought-post.html')
    meta.setdefault('comments', False)
    meta.setdefault('hide', ['navigation', 'toc'])
    meta['untitled'] = not bool(meta.get('title'))
    page.title = str(meta.get('title') or meta.get('date_label') or meta['date'])
    return markdown


class ContentInfo(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.image = None

    def handle_starttag(self, tag, attrs):
        if tag in ('p', 'li', 'h1', 'h2', 'h3', 'h4', 'br', 'pre', 'blockquote'):
            self.parts.append('\n')
        attrs = dict(attrs)
        if tag == 'img' and not self.image:
            self.image = (attrs.get('src', ''), attrs.get('alt', ''))

    def handle_endtag(self, tag):
        if tag in ('p', 'li', 'h1', 'h2', 'h3', 'h4', 'pre', 'blockquote'):
            self.parts.append('\n')

    def handle_data(self, data):
        self.parts.append(data)

    def text(self):
        return '\n'.join(line.strip() for line in ''.join(self.parts).splitlines() if line.strip())


def make_card(page):
    meta = page.meta
    try:
        value = meta['date']
        stamp = datetime.fromisoformat(str(value))
    except (KeyError, ValueError, TypeError):
        raise PluginError(f'{page.file.src_uri}: 随想需要有效的 date，如 "2026-09-26"')
    if stamp.tzinfo is not None:
        raise PluginError(f'{page.file.src_uri}: date 请使用本地日期时间，不带时区')
    tags = meta.get('tags', [])
    if not isinstance(tags, list) or any(not isinstance(tag, str) for tag in tags):
        raise PluginError(f'{page.file.src_uri}: tags 必须是字符串列表')
    content = page.content or ''
    info = ContentInfo()
    info.feed(content.split('<!-- more -->', 1)[0])
    text = info.text()
    # An excerpt is a literal slice, never an AI-written summary.
    long = len(text) > 220
    excerpt = text[:220].rstrip() + ('…' if long else '')
    image = None
    if info.image:
        src, alt = info.image
        if urlsplit(src).scheme in ('', 'http', 'https'):
            image = {'src': urljoin(page.url, src), 'alt': alt}
    return {
        'title': str(meta.get('title', page.title)),
        'untitled': bool(meta.get('untitled', False)),
        'date': stamp.date().isoformat(),
        'label': str(meta.get('date_label', stamp.date().isoformat())),
        'stamp': stamp.isoformat(), 'month': stamp.strftime('%Y-%m'),
        'stage': str(meta.get('stage', '随想')), 'tags': tags,
        'url': page.url, 'excerpt': excerpt, 'image': image,
        'note': str(meta.get('editor_note', '')),
        'long': long or '<!-- more -->' in content,
    }


def on_env(env, *, config, files):
    cards = [make_card(file.page) for file in files.documentation_pages()
             if file.page is not None and file.page.meta.get('thought') is True]
    cards.sort(key=lambda card: (card['stamp'], card['url']), reverse=True)
    env.globals['thought_cards'] = cards
    env.globals['thought_months'] = sorted({card['month'] for card in cards}, reverse=True)
    return env


def on_post_build(*, config):
    """Keep old article links working after flattening the source directory."""
    docs = Path(config.docs_dir) / '随想'
    site = Path(config.site_dir) / '随想'
    for source in docs.glob('*.md'):
        if source.name == 'index.md':
            continue
        body = source.read_text(encoding='utf-8-sig')
        old_dir = '第一阶段' if re.search(r'^source_header:', body, re.M) else 'posts'
        destination = site / old_dir / source.stem / 'index.html'
        destination.parent.mkdir(parents=True, exist_ok=True)
        target = f'../../{quote(source.stem)}/'
        safe = escape(target, quote=True)
        destination.write_text(
            '<!doctype html><html lang="zh"><meta charset="utf-8">'
            f'<meta http-equiv="refresh" content="0; url={safe}">'
            f'<link rel="canonical" href="{safe}">'
            f'<a href="{safe}">文章已移动，点击继续阅读</a></html>', encoding='utf-8')
