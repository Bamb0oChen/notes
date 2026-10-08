"""Publish stable static feeds for the RSS page's folder/status selections."""

import copy
import hashlib
import html
import json
import importlib.util
from datetime import datetime
from email.utils import format_datetime
from pathlib import Path
from urllib.parse import urljoin
from xml.etree import ElementTree as ET

from mkdocs.plugins import event_priority
def _load_sibling(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


recent_changes = _load_sibling("rss_changes").recent_changes
absolute_urls = _load_sibling("rss_urls").absolute_urls

_pages = {}
STATUSES = ("", "add", "modify")
LABELS = {"": "全部", "add": "新增", "modify": "修改"}


def on_nav(nav, *, config, files):
    global _pages
    _pages = {page.file.src_uri: page for page in nav.pages}
    return nav


def on_page_context(context, *, page, config, nav):
    _pages[page.file.src_uri] = page
    return context


def preset_name(folder, status):
    identity = json.dumps([folder, status], ensure_ascii=False)
    return hashlib.sha256(identity.encode()).hexdigest()[:24] + ".xml"


@event_priority(-110)
def on_post_build(config):
    site = Path(config.site_dir)
    base_path = site / "feed_rss_updated.xml"
    if not base_path.exists():
        return
    repo = Path(config.config_file_path).parent
    prefix = Path(config.docs_dir).relative_to(repo).as_posix()
    changes = recent_changes(repo, prefix)
    base = ET.parse(base_path)
    existing = {item.findtext("link"): item for item in base.findall("./channel/item")}
    # Essay feed contains rendered deltas beyond the global feed's latest 30.
    essay_path = site / "feed_rss_essays.xml"
    if essay_path.exists():
        existing.update({item.findtext("link"): item for item in ET.parse(essay_path).findall("./channel/item")})
    folders = ("", "essays")

    entries = []
    for change in changes:
        source = change["path"]
        if source == "rss.md" or source.startswith("assets/") or change["status"] == "delete":
            continue
        page = _pages.get(source)
        if not page and change["status"] != "delete":
            continue
        link = urljoin(config.site_url, page.url if page else "rss/")
        item = copy.deepcopy(existing.get(link)) if page and link in existing else ET.Element("item")
        def put(name, value):
            node = item.find(name)
            if node is None:
                node = ET.SubElement(item, name)
            node.text = value
            return node
        put("title", page.title if page else f"已删除：{Path(source).stem}")
        put("link", link)
        if not item.findtext("description"):
            content = page.content if page else f"<p>文章已删除：{html.escape(source)}</p>"
            put("description", absolute_urls(content or "", link))
        put("pubDate", format_datetime(datetime.fromisoformat(change["date"])))
        if item.find("guid") is None or change["status"] == "delete":
            put("guid", f"{config.site_url}#change-{hashlib.sha256(json.dumps(change, sort_keys=True).encode()).hexdigest()}").set("isPermaLink", "false")
        put("category", change["status"])
        entries.append((change, item))

    output = site / "rss" / "feeds"
    output.mkdir(parents=True, exist_ok=True)
    catalog = []
    for folder in folders:
        label = "杂谈随想" if folder == "essays" else "全部文件夹"
        for status in STATUSES:
            name = preset_name(folder, status)
            href = urljoin(config.site_url, f"rss/feeds/{name}")
            tree = copy.deepcopy(base)
            channel = tree.find("channel")
            for item in list(channel.findall("item")):
                channel.remove(item)
            selected = [(change, item) for change, item in entries if
                        (not folder or change["path"].split("/", 1)[0] in ("杂谈文章", "随想")) and
                        (not status or change["status"] == status)][:30]
            for _, item in selected:
                channel.append(copy.deepcopy(item))
            channel.find("title").text = f"移动的大图书馆 · {label} · {LABELS[status]}"
            channel.find("description").text = f"{label}的{LABELS[status]}，最近 30 条变更。"
            date_node = channel.find("pubDate")
            if date_node is not None:
                if selected:
                    date_node.text = selected[0][1].findtext("pubDate")
                else:
                    channel.remove(date_node)
            for node in channel:
                if node.tag == "{http://www.w3.org/2005/Atom}link" and node.get("rel") == "self":
                    node.set("href", href)
            tree.write(output / name, encoding="utf-8", xml_declaration=True)
            catalog.append({"folder": folder, "status": status, "label": label, "url": href})
    (site / "rss" / "presets.json").write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")
