"""Build the compact recent-document list from Git, including deleted files."""

import json
import subprocess
from pathlib import Path, PurePosixPath


_pages = {}


def on_nav(nav, *, config, files):
    global _pages
    _pages = {page.file.src_uri: page for page in nav.pages}
    return nav


def on_page_context(context, *, page, config, nav):
    # Published pages outside navigation (such as thoughts) still belong here.
    _pages[page.file.src_uri] = page
    return context


def recent_changes(repo, docs_prefix):
    result = subprocess.run(
        ["git", "log", "-n", "200", "--format=%x1e%cI", "--name-status", "-z",
         "--no-renames", "--", docs_prefix],
        cwd=repo, check=True, capture_output=True, encoding="utf-8",
    )
    seen = set()
    changes = []
    for commit in result.stdout.split("\x1e")[1:]:
        fields = commit.split("\0")
        date = fields[0].strip()
        for index in range(1, len(fields) - 1, 2):
            status, path = fields[index].strip(), fields[index + 1]
            if path in seen or not path.endswith(".md"):
                continue
            seen.add(path)
            if status not in ("A", "M", "D") or not path.startswith(docs_prefix + "/"):
                continue
            changes.append({"path": path[len(docs_prefix) + 1:], "date": date,
                            "status": {"A": "add", "M": "modify", "D": "delete"}[status]})
    return changes


def on_post_build(config):
    repo = Path(config.config_file_path).parent
    docs_prefix = Path(config.docs_dir).relative_to(repo).as_posix()
    labels = config.extra.get("top_tab_labels", {})
    entries = []
    for change in recent_changes(repo, docs_prefix):
        path = PurePosixPath(change["path"])
        if path.as_posix() == "rss.md" or path.parts[0] == "assets":
            continue
        page = _pages.get(path.as_posix())
        if page is None and change["status"] != "delete":
            continue
        if page and (page.parent or len(path.parts) == 1):
            parents = []
            parent = page.parent
            while parent:
                parents.append(parent.title)
                parent = parent.parent
            breadcrumb = list(reversed(parents)) + [page.title if path.stem == "index" else path.stem]
            url = page.url
        else:
            breadcrumb = [labels.get(part, part) if index == 0 else part
                          for index, part in enumerate(path.parts[:-1])] + [path.stem]
            url = page.url if page else None
        entries.append({**change, "breadcrumb": breadcrumb, "url": url})
    output = Path(config.site_dir) / "rss" / "changes.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(entries, ensure_ascii=False), encoding="utf-8")
