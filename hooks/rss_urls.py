"""Resolve links inside RSS item HTML against the article URL."""

import re
from html import unescape
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from xml.etree import ElementTree as ET

from mkdocs.plugins import event_priority


TAG = re.compile(r"<(?:a|img|source)\b[^>]*>", re.IGNORECASE)
ATTRIBUTE = re.compile(r'''\b(href|src|srcset)\s*=\s*(["'])(.*?)\2''', re.IGNORECASE | re.DOTALL)


def absolute_urls(html: str, article_url: str) -> str:
    def replace_tag(match: re.Match) -> str:
        def replace_attribute(attribute: re.Match) -> str:
            name, quote, raw = attribute.groups()
            if name.lower() == "srcset":
                parts = []
                for candidate in raw.split(","):
                    url, separator, descriptor = candidate.strip().partition(" ")
                    parts.append(f"{urljoin(article_url, unescape(url))}{separator}{descriptor}" if url else candidate)
                value = ", ".join(parts)
            else:
                url = unescape(raw)
                value = url if urlsplit(url).scheme or url.startswith(("#", "data:")) else urljoin(article_url, url)
            return f"{name}={quote}{value}{quote}"

        return ATTRIBUTE.sub(replace_attribute, match.group())

    return TAG.sub(replace_tag, html)


@event_priority(-100)
def on_post_build(config):
    ET.register_namespace("atom", "http://www.w3.org/2005/Atom")
    ET.register_namespace("dc", "http://purl.org/dc/elements/1.1/")
    site_dir = Path(config.site_dir)
    for filename in ("feed_rss_created.xml", "feed_rss_updated.xml", "feed_rss_essays.xml"):
        feed_path = site_dir / filename
        if not feed_path.exists():
            continue
        stylesheet = re.search(rb"<\?xml-stylesheet\b[^?]*\?>", feed_path.read_bytes())
        parser = ET.XMLParser(target=ET.TreeBuilder(insert_pis=True))
        tree = ET.parse(feed_path, parser=parser)
        for item in tree.findall("./channel/item"):
            article_url = item.findtext("link")
            description = item.find("description")
            if article_url and description is not None and description.text:
                description.text = absolute_urls(description.text, article_url)
        tree.write(feed_path, encoding="utf-8", xml_declaration=True)
        if stylesheet:
            content = feed_path.read_bytes()
            feed_path.write_bytes(content.replace(b"?>", b"?> " + stylesheet.group(), 1))
