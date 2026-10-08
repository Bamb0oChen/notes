"""Publish paragraph deltas in the update feed with stable content-version IDs."""

import hashlib
import copy
import json
import posixpath
import re
import subprocess
from datetime import datetime
from difflib import SequenceMatcher
from email.utils import format_datetime, parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote, unquote, urljoin, urlsplit
from xml.etree import ElementTree as ET

import markdown
from bs4 import BeautifulSoup, Comment, NavigableString, Tag
from mkdocs.plugins import event_priority
from mkdocs.utils.meta import get_data


_pages = {}
_file_urls = {}
FONT = "font-family:'Microsoft YaHei','微软雅黑',sans-serif;"


def is_essay(path):
    return path.split("/", 1)[0] in ("杂谈文章", "随想")


def on_pre_build(config):
    _pages.clear()
    _file_urls.clear()


def on_files(files, *, config):
    _file_urls.update({file.src_uri: urljoin(config.site_url, quote(file.url, safe="/%")) for file in files})
    return files


def on_page_context(context, *, page, config, nav):
    _pages[urljoin(config.site_url, page.url)] = page
    return context


def blocks(html):
    """Paragraphs and headings are units; keep code, lists and tables intact."""
    result = []

    def visit(node):
        if isinstance(node, Comment):
            return
        if isinstance(node, NavigableString):
            if str(node).strip():
                paragraph = BeautifulSoup("<p></p>", "html.parser").p
                paragraph.string = str(node)
                result.append(str(paragraph))
            return
        if not isinstance(node, Tag) or node.name in ("script", "style"):
            return
        if node.name in ("div", "section", "article") and not set(node.get("class", [])) & {
            "admonition", "highlight", "arithmatex", "mermaid",
        }:
            for child in node.children:
                visit(child)
        else:
            result.append(str(node))

    for node in BeautifulSoup(html, "html.parser").contents:
        visit(node)
    return result


def fingerprint(block):
    soup = BeautifulSoup(block, "html.parser")
    for node in soup.find_all(True):
        for attribute in ("id", "class", "style"):
            node.attrs.pop(attribute, None)
    # Whitespace in code remains meaningful; ordinary prose wrapping does not.
    return str(soup) if soup.find("pre") else re.sub(r"\s+", " ", str(soup)).strip()


def styled(block, added):
    soup = BeautifulSoup(block, "html.parser")
    for node in soup.find_all(True):
        style = FONT + f"color:{'#000000' if added else '#808080'};font-weight:{700 if added else 400};"
        if node.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            style += "font-size:1em;"
        if node.name == "pre":
            style += "white-space:pre-wrap;overflow-wrap:anywhere;"
        node["style"] = style
    return str(soup)


def paragraph_delta(old, new):
    old_blocks, new_blocks = blocks(old), blocks(new)
    matcher = SequenceMatcher(None, list(map(fingerprint, old_blocks)),
                              list(map(fingerprint, new_blocks)), autojunk=False)
    output = []
    for operation, _, _, start, end in matcher.get_opcodes():
        if operation != "delete":
            output.extend(styled(block, operation != "equal") for block in new_blocks[start:end])
    if not output and old_blocks != new_blocks:
        output.append('<p style="color:#808080;font-weight:400;">本次更新删去了正文内容。</p>')
    return (f'<div style="{FONT}font-size:16px;line-height:1.8;background-color:#ffffff;'
            'color:#000000;padding:16px;">' + "\n".join(output) + "</div>")


def revisions(repo, path):
    history = subprocess.run(
        ["git", "log", "-n", "50", "--follow", "--find-renames", "--format=%x1e%H%x09%cI",
         "--name-status", "-z", "--", path],
        cwd=repo, check=True, capture_output=True, encoding="utf-8",
    ).stdout
    for commit in history.split("\x1e")[1:]:
        fields = commit.split("\0")
        sha, date = fields[0].strip().split("\t", 1)
        status = fields[1].strip()
        if status == "D":
            continue
        version_path = fields[3] if status.startswith("R") else fields[2]
        content = subprocess.run(["git", "show", f"{sha}:{version_path}"], cwd=repo,
                                 check=True, capture_output=True, encoding="utf-8").stdout
        yield content, date, sha, version_path


def latest_delta(repo, path, render):
    current = None
    for source, date, sha, version_path in revisions(repo, path):
        body = render(get_data(source)[0], version_path)
        keys = list(map(fingerprint, blocks(body)))
        if current is None:
            current = {"html": body, "keys": keys, "date": date, "revision": sha}
        elif keys == current["keys"]:
            current["date"] = date
            current["revision"] = sha
        else:
            return current, paragraph_delta(body, current["html"])
    return (current, paragraph_delta("", current["html"])) if current else (None, None)


@event_priority(-90)
def on_post_build(config):
    path = Path(config.site_dir) / "feed_rss_updated.xml"
    if not path.exists():
        return
    repo = Path(config.config_file_path).parent
    source_prefix = Path(config.docs_dir).relative_to(repo).as_posix()
    file_urls = {**_file_urls, **{page.file.src_uri: urljoin(config.site_url, page.url) for page in _pages.values()}}
    stylesheet = re.search(rb"<\?xml-stylesheet\b[^?]*\?>", path.read_bytes())
    parser = ET.XMLParser(target=ET.TreeBuilder(insert_pis=True))
    tree = ET.parse(path, parser=parser)
    channel = tree.find("channel")
    original_links = {item.findtext("link") for item in channel.findall("item")}
    # Collect the whole essay scope, even when it falls outside the global latest 30.
    for article_url, page in _pages.items():
        if is_essay(page.file.src_uri) and article_url not in original_links:
            item = ET.SubElement(channel, "item")
            for name, value in (("title", page.title), ("link", article_url),
                                ("description", ""), ("pubDate", "")):
                ET.SubElement(item, name).text = value

    for item in list(channel.findall("item")):
        article_url = item.findtext("link")
        page = _pages.get(article_url)
        if not page or page.file.src_uri == "rss.md":
            channel.remove(item)
            continue

        def render(source, version_path):
            html = markdown.Markdown(extensions=config.markdown_extensions,
                                     extension_configs=config.mdx_configs).convert(source)
            soup = BeautifulSoup(html, "html.parser")
            source_path = version_path[len(source_prefix) + 1:]
            for node in soup.find_all(True):
                for attribute in ("href", "src"):
                    if not node.get(attribute):
                        continue
                    link = urlsplit(node[attribute])
                    if not link.scheme and not link.netloc and link.path and not link.path.startswith("/"):
                        target = posixpath.normpath(posixpath.join(posixpath.dirname(source_path), unquote(link.path)))
                        if target in file_urls:
                            node[attribute] = file_urls[target] + ("#" + link.fragment if link.fragment else "")
            return str(soup)

        current, delta = latest_delta(repo, f"{source_prefix}/{page.file.src_uri}", render)
        if current is None or not current["keys"]:
            channel.remove(item)
            continue
        item.find("description").text = delta
        identity = [current["revision"], current["keys"]]
        digest = hashlib.sha256(json.dumps(identity, ensure_ascii=False).encode()).hexdigest()[:20]
        guid = item.find("guid")
        if guid is None:
            guid = ET.SubElement(item, "guid")
        guid.set("isPermaLink", "false")
        guid.text = f"{article_url}#update-{digest}"
        item.find("pubDate").text = format_datetime(datetime.fromisoformat(current["date"]))
    items = channel.findall("item")
    for item in items:
        channel.remove(item)
    for item in sorted(items, key=lambda entry: parsedate_to_datetime(entry.findtext("pubDate")), reverse=True):
        channel.append(item)
    if items:
        channel.find("pubDate").text = max(items, key=lambda entry: parsedate_to_datetime(entry.findtext("pubDate"))).findtext("pubDate")
    essay_tree = copy.deepcopy(tree)
    essay_channel = essay_tree.find("channel")
    essay_channel.find("title").text = "杂谈文章与随想"
    essay_channel.find("description").text = "杂谈文章和随想的全文更新，按更新时间排列。"
    for item in list(essay_channel.findall("item")):
        if not is_essay(_pages[item.findtext("link")].file.src_uri):
            essay_channel.remove(item)
    essay_items = essay_channel.findall("item")
    if essay_items:
        essay_channel.find("pubDate").text = essay_items[0].findtext("pubDate")
    for node in essay_channel:
        if node.tag == "{http://www.w3.org/2005/Atom}link" and node.get("rel") == "self":
            node.set("href", urljoin(config.site_url, "feed_rss_essays.xml"))
    essay_path = Path(config.site_dir) / "feed_rss_essays.xml"
    essay_tree.write(essay_path, encoding="utf-8", xml_declaration=True)
    if stylesheet:
        essay_path.write_bytes(essay_path.read_bytes().replace(b"?>", b"?> " + stylesheet.group(), 1))
    for item in list(channel.findall("item")):
        if item.findtext("link") not in original_links:
            channel.remove(item)
    tree.write(path, encoding="utf-8", xml_declaration=True)
    if stylesheet:
        path.write_bytes(path.read_bytes().replace(b"?>", b"?> " + stylesheet.group(), 1))
