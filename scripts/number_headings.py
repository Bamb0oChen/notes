"""Number Markdown headings based on numeric file prefix.

Rules (per user spec):
- For a file named like "1.xxxxx.md", headings are numbered:
  ##     -> 1.1, 1.2, ...
  ###    -> 1.1.1, 1.1.2, ...
  ####   -> 1.1.1.1, ...
  #####  -> 1.1.1.1.1, ...

Only files whose *basename* starts with "<int>." are processed.
Only ATX headings from level 2 to level 5 are numbered.
Headings inside fenced code blocks are ignored.

Usage:
  python scripts/number_headings.py --root docs --dry-run
  python scripts/number_headings.py --root docs --write
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


FILE_PREFIX_RE = re.compile(r"^(?P<major>\d+)\..+\.md$", re.IGNORECASE)
FENCE_RE = re.compile(r"^\s*(```|~~~)")
HEADING_RE = re.compile(r"^(?P<hashes>#{2,5})\s+(?P<title>.*?)(?P<trailing>\s+#+\s*)?$\s*$")
EXISTING_NUMBER_RE = re.compile(r"^(?P<num>\d+(?:\.\d+){1,5})\s+")


@dataclass
class FileResult:
    path: Path
    changed: bool
    headings_numbered: int


def _numbered_title(original_title: str) -> str:
    # Remove an existing section-like prefix (e.g. "2.1.3 ") to avoid double numbering.
    # Require at least one dot to reduce false positives like "2025 ...".
    return EXISTING_NUMBER_RE.sub("", original_title.strip())


def process_markdown(text: str, major: int) -> tuple[str, int]:
    counters = {2: 0, 3: 0, 4: 0, 5: 0}
    in_fence = False
    out_lines: list[str] = []
    numbered = 0

    for line in text.splitlines(keepends=True):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            out_lines.append(line)
            continue

        if in_fence:
            out_lines.append(line)
            continue

        m = HEADING_RE.match(line)
        if not m:
            out_lines.append(line)
            continue

        level = len(m.group("hashes"))
        title = m.group("title")
        trailing = m.group("trailing") or ""

        if level == 2:
            counters[2] += 1
            counters[3] = counters[4] = counters[5] = 0
        elif level == 3:
            if counters[2] == 0:
                counters[2] = 1
            counters[3] += 1
            counters[4] = counters[5] = 0
        elif level == 4:
            if counters[2] == 0:
                counters[2] = 1
            if counters[3] == 0:
                counters[3] = 1
            counters[4] += 1
            counters[5] = 0
        elif level == 5:
            if counters[2] == 0:
                counters[2] = 1
            if counters[3] == 0:
                counters[3] = 1
            if counters[4] == 0:
                counters[4] = 1
            counters[5] += 1
        else:
            out_lines.append(line)
            continue

        parts = [major] + [counters[i] for i in range(2, level + 1)]
        section = ".".join(str(p) for p in parts)
        cleaned = _numbered_title(title)
        new_line = f"{m.group('hashes')} {section} {cleaned}{trailing}\n"
        out_lines.append(new_line)
        numbered += 1

    return "".join(out_lines), numbered


def process_file(path: Path, *, dry_run: bool) -> FileResult:
    m = FILE_PREFIX_RE.match(path.name)
    if not m:
        return FileResult(path=path, changed=False, headings_numbered=0)

    major = int(m.group("major"))
    original = path.read_text(encoding="utf-8")
    updated, numbered = process_markdown(original, major)
    changed = updated != original

    if changed and not dry_run:
        path.write_text(updated, encoding="utf-8")

    return FileResult(path=path, changed=changed, headings_numbered=numbered)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="docs", help="Root folder to scan (default: docs)")
    parser.add_argument("--write", action="store_true", help="Write changes back to files")
    parser.add_argument("--dry-run", action="store_true", help="Do not write changes (default)")
    args = parser.parse_args()

    dry_run = True
    if args.write:
        dry_run = False
    if args.dry_run:
        dry_run = True

    root = Path(args.root)
    if not root.exists():
        raise SystemExit(f"Root not found: {root}")

    md_files = sorted(p for p in root.rglob("*.md") if p.is_file())
    results: list[FileResult] = []

    for path in md_files:
        res = process_file(path, dry_run=dry_run)
        if res.headings_numbered:
            results.append(res)

    changed_files = [r for r in results if r.changed]
    total_numbered = sum(r.headings_numbered for r in results)

    mode = "DRY-RUN" if dry_run else "WRITE"
    print(f"[{mode}] processed={len(results)} changed={len(changed_files)} headings_numbered={total_numbered}")
    for r in changed_files:
        print(f"- {r.path.as_posix()} (headings={r.headings_numbered})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
