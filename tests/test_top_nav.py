import importlib.util
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('top_nav_hook', ROOT / 'hooks/top_nav.py')
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)


def page(source, title):
    return SimpleNamespace(is_page=True, file=SimpleNamespace(src_uri=source),
                           title=title, children=[], previous_page=None, next_page=None)


def section(title, children):
    return SimpleNamespace(is_page=False, title=title, children=children)


def test_only_headbar_is_curated():
    home = page('index.md', '前言')
    article = page('数学基础/一元微积分/1.md', '第一节')
    math = section('自然科学基础', [section('数学基础', [article])])
    hidden = section('未列入顶部', [page('other/index.md', '其他')])
    nav = SimpleNamespace(items=[math, hidden, home], pages=[])
    config = SimpleNamespace(extra={'top_tabs': ['index.md', '自然科学基础'],
                                    'top_tab_labels': {}})

    hook.on_nav(nav, config=config, files=None)

    assert nav.items == [home, math]
    assert math.children[0].children == [article]
    assert nav.pages == [home, article]
    assert home.next_page is article and article.previous_page is home
