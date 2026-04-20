"""Fix common MathJax delimiter issues in Markdown files.

This script is intentionally conservative and only changes whitespace/newlines.
It aims to prevent '$' delimiters from "sticking" together or spanning lines
in a way that breaks MathJax parsing.

Edits performed (outside fenced code blocks and inline code spans):
1) Insert a single space between adjacent inline math: `$a$$b$` -> `$a$ $b$`
2) Replace newlines inside inline math: `$a\n+b$` -> `$a +b$` (newlines -> spaces)
   (skips if the inline span contains a blank line)
3) Rewrite inline `$$...$$` that appears on a line with other text into a
   block form with `$$` on their own lines.

Non-goals:
- Does not change any non-whitespace characters.
- Does not reflow paragraphs, headings, lists, or tables.
- Does not touch fenced code blocks (``` / ~~~) or inline code (`...`, ``...``).

Usage:
  python scripts/fix_math_dollars.py --check
  python scripts/fix_math_dollars.py

By default, processes docs/**/*.md (excluding docs/assets/**).
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import os
from pathlib import Path
import re
import sys
from typing import Iterable


INLINE_CODE_RE = re.compile(r"(`+)([^`]*?)\1", re.DOTALL)
FENCE_START_RE = re.compile(r"^(?P<indent>[ \t]*)(?P<fence>`{3,}|~{3,})")


@dataclasses.dataclass
class ChangeStats:
    files_scanned: int = 0
    files_changed: int = 0
    inline_adjacent_fixes: int = 0
    inline_newline_fixes: int = 0
    inline_doubledollar_to_block: int = 0
    display_singleline_to_multiline: int = 0
    display_blankline_fixes: int = 0


def _norm_include_prefix(prefix: str) -> str:
    prefix = prefix.replace("\\", "/")
    prefix = prefix.lstrip("./")
    prefix = prefix.strip("/")
    return prefix


def _is_included(rel_posix: str, include_prefixes: list[str]) -> bool:
    if not include_prefixes:
        return True
    for prefix in include_prefixes:
        if rel_posix == prefix or rel_posix.startswith(prefix + "/"):
            return True
    return False


def iter_markdown_files(root: Path, include_prefixes: list[str] | None = None) -> Iterable[Path]:
    docs_dir = root / "docs"
    if not docs_dir.is_dir():
        return []

    include_prefixes = include_prefixes or []
    include_prefixes = [_norm_include_prefix(p) for p in include_prefixes if p.strip()]

    for path in docs_dir.rglob("*.md"):
        # Skip built assets folders if any
        if "assets" in path.parts and path.parts[path.parts.index("assets") - 1] == "docs":
            # docs/assets/**
            continue

        rel_posix = path.relative_to(docs_dir).as_posix()
        if not _is_included(rel_posix, include_prefixes):
            continue
        yield path


def protect_inline_code(text: str) -> tuple[str, list[str]]:
    """Replace inline code spans with placeholders and return mapping."""
    code_spans: list[str] = []

    def repl(m: re.Match[str]) -> str:
        code_spans.append(m.group(0))
        return f"\u0000CODE{len(code_spans)-1}\u0000"

    return INLINE_CODE_RE.sub(repl, text), code_spans


def restore_inline_code(text: str, code_spans: list[str]) -> str:
    for i, span in enumerate(code_spans):
        text = text.replace(f"\u0000CODE{i}\u0000", span)
    return text


def fix_adjacent_inline_math(text: str) -> tuple[str, int]:
    """Insert a space between `$...$` `$...$` when written as `$...$$...$`.

    Only matches within a single line (no newlines inside either span).
    """
    count = 0
    pattern = re.compile(r"(\$[^\n\$]+\$)(\$[^\n\$]+\$)")
    while True:
        new_text, n = pattern.subn(r"\1 \2", text)
        if n == 0:
            break
        count += n
        text = new_text
    return text, count


def fix_newlines_inside_inline_math(text: str) -> tuple[str, int]:
    """Replace newlines inside single-$ inline math with spaces.

    This is done with a small scanner to avoid matching across blank lines.
    """
    out: list[str] = []
    i = 0
    fixes = 0
    n = len(text)

    while i < n:
        ch = text[i]

        # Keep escaped dollars as-is.
        if ch == "\\" and i + 1 < n and text[i + 1] == "$":
            out.append("\\$")
            i += 2
            continue

        if ch != "$":
            out.append(ch)
            i += 1
            continue

        # If this is $$, treat as display delimiter and leave unchanged.
        if i + 1 < n and text[i + 1] == "$":
            out.append("$$")
            i += 2
            continue

        # Potential inline math: find closing unescaped single '$'.
        j = i + 1
        while True:
            j = text.find("$", j)
            if j == -1:
                # No closing found; leave '$' as-is.
                out.append("$")
                i += 1
                break
            if text[j - 1] == "\\":
                j += 1
                continue
            # If the content contains a blank line, likely not intended inline math.
            content = text[i + 1 : j]
            if "\n\n" in content or "\r\n\r\n" in content:
                out.append("$")
                i += 1
                break

            if "\n" in content or "\r" in content:
                # Normalize to \n for replacement, keep other whitespace.
                content_fixed = content.replace("\r\n", "\n").replace("\r", "\n")
                content_fixed = content_fixed.replace("\n", " ")
                out.append("$" + content_fixed + "$")
                fixes += 1
            else:
                out.append("$" + content + "$")

            i = j + 1
            break

    return "".join(out), fixes


INLINE_DOUBLEDOLLAR_RE = re.compile(r"^(?P<prefix>.*?)(?P<open>\$\$)(?P<content>.+?)(?P<close>\$\$)(?P<suffix>.*)$")


def rewrite_inline_doubledollar_to_block(text: str) -> tuple[str, int]:
    """Rewrite `$$...$$` that shares a line with other text into block form."""
    lines = text.splitlines(keepends=True)
    out_lines: list[str] = []
    fixes = 0

    for line in lines:
        # Fast path
        if "$$" not in line:
            out_lines.append(line)
            continue

        stripped = line.strip("\r\n")
        m = INLINE_DOUBLEDOLLAR_RE.match(stripped)
        if not m:
            out_lines.append(line)
            continue

        prefix = m.group("prefix")
        content = m.group("content")
        suffix = m.group("suffix")

        # If there are additional $$ in content/suffix/prefix, skip to avoid surprises.
        if "$$" in prefix or "$$" in suffix or "$$" in content:
            out_lines.append(line)
            continue

        # Only rewrite when the line contains non-whitespace outside $$...$$
        if prefix.strip() == "" and suffix.strip() == "":
            out_lines.append(line)
            continue

        # Preserve original line ending
        line_ending = "\n"
        if line.endswith("\r\n"):
            line_ending = "\r\n"
        elif line.endswith("\n"):
            line_ending = "\n"
        else:
            line_ending = ""

        # Emit: prefix (trim right) + newline + $$ + newline + content(trim) + newline + $$ + newline + suffix(trim left)
        prefix_out = prefix.rstrip()
        suffix_out = suffix.lstrip()
        content_out = content.strip()

        if prefix_out:
            out_lines.append(prefix_out + line_ending)
        out_lines.append("$$" + line_ending)
        out_lines.append(content_out + line_ending)
        out_lines.append("$$" + line_ending)
        if suffix_out:
            out_lines.append(suffix_out + line_ending)

        fixes += 1

    return "".join(out_lines), fixes


DISPLAY_SINGLELINE_RE = re.compile(r"^(?P<indent>[ \t]*)\$\$(?P<content>.+?)\$\$(?P<trailing>[ \t]*)$")
DISPLAY_DELIM_LINE_RE = re.compile(r"^(?P<indent>[ \t]*)\$\$[ \t]*$")


def _line_ending(line: str) -> str:
    if line.endswith("\r\n"):
        return "\r\n"
    if line.endswith("\n"):
        return "\n"
    return ""


def normalize_display_doubledollar_blocks(text: str) -> tuple[str, ChangeStats]:
    """Normalize display-math `$$` blocks.

    Goals (whitespace/newlines only):
    - Convert single-line `$$...$$` (even when the line is otherwise empty) into
      a 3-line block with `$$` delimiters on their own lines.
    - Ensure a blank line before an opening `$$` and after a closing `$$` so the
      Markdown parser doesn't keep it inside a paragraph.
    """

    stats = ChangeStats()
    lines = text.splitlines(keepends=True)

    # First pass: single-line $$...$$ -> multi-line
    expanded: list[str] = []
    for line in lines:
        stripped = line.strip("\r\n")
        m = DISPLAY_SINGLELINE_RE.match(stripped)
        if not m:
            expanded.append(line)
            continue

        indent = m.group("indent")
        content = m.group("content")
        # Skip if content itself contains $$ to avoid surprises
        if "$$" in content:
            expanded.append(line)
            continue

        le = _line_ending(line)
        expanded.append(f"{indent}$$" + le)
        expanded.append(f"{indent}{content}" + le)
        expanded.append(f"{indent}$$" + le)
        stats.display_singleline_to_multiline += 1

    # Second pass: ensure blank lines around $$ blocks
    out: list[str] = []
    in_block = False
    need_blank_before_next = False

    for line in expanded:
        le = _line_ending(line)
        core = line.strip("\r\n")

        if need_blank_before_next:
            if core.strip() != "":
                out.append(le)  # blank line
                stats.display_blankline_fixes += 1
            need_blank_before_next = False

        m_delim = DISPLAY_DELIM_LINE_RE.match(core)
        if m_delim:
            indent = m_delim.group("indent")

            # Opening delimiter: ensure a blank line before it
            if not in_block:
                if out:
                    prev_core = out[-1].strip("\r\n")
                    if prev_core.strip() != "":
                        out.append(le)
                        stats.display_blankline_fixes += 1
                in_block = True
            else:
                # Closing delimiter: ensure a blank line after it (unless already present)
                in_block = False
                need_blank_before_next = True

            out.append(f"{indent}$$" + le)
            continue

        out.append(line)

    return "".join(out), stats


def process_non_fenced_segment(segment: str) -> tuple[str, ChangeStats]:
    stats = ChangeStats()

    protected, code_spans = protect_inline_code(segment)

    protected, n_block = rewrite_inline_doubledollar_to_block(protected)
    stats.inline_doubledollar_to_block += n_block

    protected, n_adj = fix_adjacent_inline_math(protected)
    stats.inline_adjacent_fixes += n_adj

    protected, n_nl = fix_newlines_inside_inline_math(protected)
    stats.inline_newline_fixes += n_nl

    # Display-math blocks: normalize $$ blocks to be recognized as blocks.
    protected, disp_stats = normalize_display_doubledollar_blocks(protected)
    stats.display_singleline_to_multiline += disp_stats.display_singleline_to_multiline
    stats.display_blankline_fixes += disp_stats.display_blankline_fixes

    restored = restore_inline_code(protected, code_spans)
    return restored, stats


def process_markdown(text: str) -> tuple[str, ChangeStats]:
    """Process a Markdown file while preserving fenced code blocks."""
    stats_total = ChangeStats()

    lines = text.splitlines(keepends=True)
    out: list[str] = []

    in_fence = False
    fence_marker = ""
    buffer: list[str] = []

    def flush_buffer() -> None:
        nonlocal buffer, stats_total
        if not buffer:
            return
        segment = "".join(buffer)
        fixed, seg_stats = process_non_fenced_segment(segment)
        stats_total.inline_adjacent_fixes += seg_stats.inline_adjacent_fixes
        stats_total.inline_newline_fixes += seg_stats.inline_newline_fixes
        stats_total.inline_doubledollar_to_block += seg_stats.inline_doubledollar_to_block
        stats_total.display_singleline_to_multiline += seg_stats.display_singleline_to_multiline
        stats_total.display_blankline_fixes += seg_stats.display_blankline_fixes
        out.append(fixed)
        buffer = []

    for line in lines:
        m = FENCE_START_RE.match(line)
        if m:
            fence = m.group("fence")
            # Starting fence
            if not in_fence:
                flush_buffer()
                in_fence = True
                fence_marker = fence[0]  # ` or ~
                out.append(line)
                continue
            # Ending fence: must match same fence char
            if in_fence and fence and fence[0] == fence_marker:
                in_fence = False
                fence_marker = ""
                out.append(line)
                continue

        if in_fence:
            out.append(line)
        else:
            buffer.append(line)

    flush_buffer()
    return "".join(out), stats_total


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root (default: script's parent)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Do not write files; exit 1 if changes would be made.",
    )
    parser.add_argument(
        "--include",
        action="append",
        default=[],
        help=(
            "Only process Markdown files under docs/ that match these path prefixes "
            "(repeatable). Example: --include '数学基础/常微分方程'"
        ),
    )
    args = parser.parse_args(argv)

    root: Path = args.root

    stats = ChangeStats()
    changed_paths: list[Path] = []

    for md_path in iter_markdown_files(root, include_prefixes=args.include):
        stats.files_scanned += 1
        original = md_path.read_text(encoding="utf-8")
        fixed, file_stats = process_markdown(original)

        # Aggregate stats
        stats.inline_adjacent_fixes += file_stats.inline_adjacent_fixes
        stats.inline_newline_fixes += file_stats.inline_newline_fixes
        stats.inline_doubledollar_to_block += file_stats.inline_doubledollar_to_block
        stats.display_singleline_to_multiline += file_stats.display_singleline_to_multiline
        stats.display_blankline_fixes += file_stats.display_blankline_fixes

        if sha256_text(original) != sha256_text(fixed):
            stats.files_changed += 1
            changed_paths.append(md_path)
            if not args.check:
                md_path.write_text(fixed, encoding="utf-8")

    # Report
    print(f"Scanned: {stats.files_scanned} markdown files")
    print(f"Changed: {stats.files_changed} files")
    print(f"Fixes: adjacent inline math: {stats.inline_adjacent_fixes}")
    print(f"Fixes: newlines inside $...$: {stats.inline_newline_fixes}")
    print(f"Fixes: inline $$...$$ -> block: {stats.inline_doubledollar_to_block}")
    print(f"Fixes: display $$...$$ single-line -> multi-line: {stats.display_singleline_to_multiline}")
    print(f"Fixes: blank lines around $$ blocks: {stats.display_blankline_fixes}")

    if args.check and stats.files_changed > 0:
        print("\nFiles that would change (first 30):")
        for p in changed_paths[:30]:
            rel = p.relative_to(root)
            print(f"- {rel.as_posix()}")
        if len(changed_paths) > 30:
            print(f"... and {len(changed_paths) - 30} more")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
