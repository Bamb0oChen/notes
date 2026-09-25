"""Build static thought cards from Markdown. No API, passwords or runtime fetches."""
from datetime import date, datetime
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
from mkdocs.exceptions import PluginError


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
