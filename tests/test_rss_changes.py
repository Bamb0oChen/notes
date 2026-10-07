"""Verify the list preserves real Git deletions and latest status per document."""

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path


spec = importlib.util.spec_from_file_location("rss_changes", Path(__file__).parents[1] / "hooks/rss_changes.py")
rss_changes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rss_changes)


class RecentChangesTests(unittest.TestCase):
    def test_latest_change_and_deleted_unicode_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)

            def git(*args):
                return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)

            git("init")
            git("config", "user.name", "Test")
            git("config", "user.email", "test@example.invalid")
            folder = repo / "docs/计算机科学/带 空格的目录"
            folder.mkdir(parents=True)
            modified = folder / "笔记.md"
            deleted = folder / "删掉的笔记.md"
            modified.write_text("first", encoding="utf-8")
            deleted.write_text("first", encoding="utf-8")
            git("add", ".")
            git("commit", "-m", "Add notes")
            modified.write_text("second", encoding="utf-8")
            deleted.unlink()
            added = folder / "新增.md"
            added.write_text("new", encoding="utf-8")
            git("add", "-A")
            git("commit", "-m", "Modify, delete, and add")
            changes = rss_changes.recent_changes(repo, "docs")
            self.assertEqual({item["path"]: item["status"] for item in changes}, {
                "计算机科学/带 空格的目录/笔记.md": "modify",
                "计算机科学/带 空格的目录/删掉的笔记.md": "delete",
                "计算机科学/带 空格的目录/新增.md": "add",
            })
            self.assertEqual(len(changes), 3)


if __name__ == "__main__":
    unittest.main()
