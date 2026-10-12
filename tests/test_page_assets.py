"""Page-specific resources must not become global dependencies again."""

from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_page_assets_are_not_global():
    config = yaml.safe_load((ROOT / 'mkdocs.yml').read_text(encoding='utf-8'))
    assert 'assets/stylesheets/intro.css' not in config['extra_css']
    assert 'assets/stylesheets/local-ebooks.css' not in config['extra_css']
    assert 'assets/javascripts/local-ebooks.js' not in config['extra_javascript']
    template = (ROOT / 'overrides/main.html').read_text(encoding='utf-8')
    assert "page.file.src_uri == 'index.md'" in template
    assert "page.file.src_uri == '杂项课程资料/电子书.md'" in template


def test_removed_local_picker_has_no_styles():
    css = (ROOT / 'docs/assets/stylesheets/local-ebooks.css').read_text(encoding='utf-8')
    assert 'local-ebook-picker' not in css
    assert 'local-ebook-toolbar' not in css
    assert 'is-available' not in css
