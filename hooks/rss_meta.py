"""Supply an RSS description for existing empty placeholder pages."""
from pathlib import PurePosixPath


def on_page_markdown(markdown, *, page, config, files):
    if not markdown.strip() and not page.meta.get('description'):
        title = page.meta.get('title') or PurePosixPath(page.file.src_uri).stem
        page.meta['description'] = f'「{title}」暂无正文，内容待更新。'
    return markdown
