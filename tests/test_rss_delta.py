import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

import markdown
from bs4 import BeautifulSoup


spec = importlib.util.spec_from_file_location("rss_delta", Path(__file__).parents[1] / "hooks/rss_delta.py")
rss_delta = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rss_delta)


class DeltaTests(unittest.TestCase):
    def test_paragraph_context_additions_and_omitted_deletions(self):
        old = "<p>远处上下文</p><p>前文</p><p>旧段落</p><p>后文</p><p>远处尾部</p>"
        new = "<p>远处上下文</p><p>前文</p><p>新增段落</p><p>后文</p><p>远处尾部</p>"
        soup = BeautifulSoup(rss_delta.paragraph_delta(old, new), "html.parser")
        self.assertNotIn("旧段落", soup.get_text())
        self.assertEqual([p.get_text() for p in soup.find_all("p")],
                         ["远处上下文", "前文", "新增段落", "后文", "远处尾部"])
        for text in ("远处上下文", "前文", "后文", "远处尾部"):
            self.assertIn("color:#808080", soup.find("p", string=text)["style"])
        self.assertIn("color:#808080", soup.find("p", string="前文")["style"])
        added_style = soup.find("p", string="新增段落")["style"]
        self.assertIn("color:#000000", added_style)
        self.assertIn("font-weight:700", added_style)
        self.assertIn("Microsoft YaHei", added_style)

    def test_code_and_delete_only_change(self):
        old = "<p>前文</p><p>被删除的内容</p><p>后文</p>"
        new = "<p>前文</p><p>后文</p>"
        delta = rss_delta.paragraph_delta(old, new)
        self.assertNotIn("被删除的内容", delta)
        self.assertNotIn("font-weight:700", delta)
        code = "<pre><code>if ready:\n    run()\n</code></pre>"
        soup = BeautifulSoup(rss_delta.paragraph_delta("", code), "html.parser")
        self.assertEqual(soup.pre.get_text(), "if ready:\n    run()\n")

    def test_git_metadata_only_update_and_rename_keep_original_revision(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)

            def git(*args):
                return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True).stdout

            def commit(message):
                git("add", "-A")
                git("commit", "-m", message)

            git("init")
            git("config", "user.name", "Test")
            git("config", "user.email", "test@example.invalid")
            docs = repo / "docs"
            docs.mkdir()
            note = docs / "旧文件名.md"
            note.write_text("前文\n\n旧段落\n\n后文", encoding="utf-8")
            commit("Create")
            note.write_text("前文\n\n新段落\n\n后文", encoding="utf-8")
            commit("Change paragraph")
            revision = git("rev-parse", "HEAD").decode().strip()
            note.write_text("---\ntitle: 新标题\n---\n\n前文\n\n新段落\n\n后文\n", encoding="utf-8")
            commit("Change metadata")
            note.rename(docs / "新文件名.md")
            commit("Rename")
            current, delta = rss_delta.latest_delta(repo, "docs/新文件名.md", lambda text, _: markdown.markdown(text))
            self.assertEqual(current["revision"], revision)
            self.assertIn("新段落", delta)
            self.assertNotIn("旧段落", delta)
            self.assertNotIn("新标题", delta)
            self.assertEqual((current, delta), rss_delta.latest_delta(
                repo, "docs/新文件名.md", lambda text, _: markdown.markdown(text)))


if __name__ == "__main__":
    unittest.main()
