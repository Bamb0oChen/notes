"""MkDocs 迁移（最小可用）助手

目标：
- 只读源目录（默认 public/），把所有内容复制到目标目录（默认 docs/）
- 在每个包含 README.md 的目录生成 index.md（复制一份），以兼容原有的“目录链接”(xxx/)

保证：
- 绝不修改/删除任何源 .md 文件
- 支持 --dry-run 预览
- 支持 --backup：在覆盖目标文件前做备份（只备份目标侧被覆盖的文件）

用法示例：
  python scripts/mkdocs_migrate.py --dry-run
  python scripts/mkdocs_migrate.py
  python scripts/mkdocs_migrate.py --src public --dst docs --backup

注意：
- Windows 下中文/空格路径 OK，但建议使用 Python 3.10+
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CopyStats:
    copied: int = 0
    skipped: int = 0
    backed_up: int = 0
    generated_indexes: int = 0


def _abs(path: Path) -> Path:
    return path.expanduser().resolve()


def _is_subpath(child: Path, parent: Path) -> bool:
    child = _abs(child)
    parent = _abs(parent)
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def _sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def _same_file(src: Path, dst: Path) -> bool:
    """尽量快速判断是否需要覆盖。

    规则：
    - size 不同 => 不同
    - mtime 相同且 size 相同 => 认为相同（足够用于迁移场景）
    - 否则再用 sha256 精确比较
    """
    if not dst.exists() or not dst.is_file():
        return False

    src_stat = src.stat()
    dst_stat = dst.stat()
    if src_stat.st_size != dst_stat.st_size:
        return False

    if int(src_stat.st_mtime) == int(dst_stat.st_mtime):
        return True

    return _sha256(src) == _sha256(dst)


def _ensure_dir(path: Path, dry_run: bool) -> None:
    if dry_run:
        return
    path.mkdir(parents=True, exist_ok=True)


def _copy_file(src_file: Path, dst_file: Path, *, dry_run: bool, backup: bool, backup_dir: Path | None, dst_root: Path) -> tuple[bool, bool]:
    """复制单个文件。

    返回：(copied, backed_up)
    """
    if _same_file(src_file, dst_file):
        return (False, False)

    backed_up = False
    if backup and dst_file.exists() and dst_file.is_file():
        assert backup_dir is not None
        rel = dst_file.relative_to(dst_root)
        backup_path = backup_dir / rel
        _ensure_dir(backup_path.parent, dry_run)
        if dry_run:
            print(f"[backup] {dst_file} -> {backup_path}")
        else:
            shutil.copy2(dst_file, backup_path)
        backed_up = True

    _ensure_dir(dst_file.parent, dry_run)
    if dry_run:
        print(f"[copy]   {src_file} -> {dst_file}")
    else:
        shutil.copy2(src_file, dst_file)

    return (True, backed_up)


def copy_tree(src_root: Path, dst_root: Path, *, dry_run: bool, backup: bool) -> CopyStats:
    copied = skipped = backed_up = 0

    backup_dir: Path | None = None
    if backup:
        # 备份目录放在目标目录旁边，避免污染 docs/ 内容
        backup_dir = dst_root.parent / (dst_root.name + ".backup")
        if dry_run:
            print(f"[info] backup dir: {backup_dir}")
        else:
            backup_dir.mkdir(parents=True, exist_ok=True)

    for src_path in src_root.rglob("*"):
        if src_path.is_dir():
            continue

        rel = src_path.relative_to(src_root)
        dst_path = dst_root / rel

        did_copy, did_backup = _copy_file(
            src_path,
            dst_path,
            dry_run=dry_run,
            backup=backup,
            backup_dir=backup_dir,
            dst_root=dst_root,
        )
        if did_copy:
            copied += 1
        else:
            skipped += 1
        if did_backup:
            backed_up += 1

    return CopyStats(copied=copied, skipped=skipped, backed_up=backed_up, generated_indexes=0)


def generate_indexes(dst_root: Path, *, dry_run: bool) -> int:
    """为每个目录生成 index.md（从 README.md 复制）。"""
    generated = 0

    for readme in dst_root.rglob("README.md"):
        if not readme.is_file():
            continue

        index_md = readme.with_name("index.md")
        if index_md.exists():
            continue

        if dry_run:
            print(f"[index]  {readme} -> {index_md}")
        else:
            shutil.copy2(readme, index_md)
        generated += 1

    return generated


def validate_paths(src_root: Path, dst_root: Path) -> None:
    if not src_root.exists() or not src_root.is_dir():
        raise SystemExit(f"src not found or not a directory: {src_root}")

    src_root = _abs(src_root)
    dst_root = _abs(dst_root)

    if src_root == dst_root:
        raise SystemExit("refuse to run: --src and --dst are the same")

    if _is_subpath(dst_root, src_root):
        raise SystemExit("refuse to run: --dst is inside --src (would recurse)")

    if _is_subpath(src_root, dst_root):
        raise SystemExit("refuse to run: --src is inside --dst (ambiguous)")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Copy notes to MkDocs docs/ without touching originals")
    parser.add_argument("--src", default="public", help="source directory (read-only)")
    parser.add_argument("--dst", default="docs", help="destination directory (generated)")
    parser.add_argument("--dry-run", action="store_true", help="print actions without writing")
    parser.add_argument("--backup", action="store_true", help="backup overwritten destination files")

    args = parser.parse_args(argv)

    src_root = Path(args.src)
    dst_root = Path(args.dst)

    validate_paths(src_root, dst_root)

    src_root = _abs(src_root)
    dst_root = _abs(dst_root)

    print(f"[info] src: {src_root}")
    print(f"[info] dst: {dst_root}")
    print(f"[info] dry-run: {args.dry_run}")
    print(f"[info] backup: {args.backup}")

    stats = copy_tree(src_root, dst_root, dry_run=args.dry_run, backup=args.backup)
    generated = generate_indexes(dst_root, dry_run=args.dry_run)

    stats = CopyStats(
        copied=stats.copied,
        skipped=stats.skipped,
        backed_up=stats.backed_up,
        generated_indexes=generated,
    )

    print(
        "[done] "
        f"copied={stats.copied}, skipped={stats.skipped}, "
        f"backed_up={stats.backed_up}, index_generated={stats.generated_indexes}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
