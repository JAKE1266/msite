"""构建器与 CLI 端到端测试(临时目录真实构建)。"""

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from msite.cli import main
from msite.core.builder import build_site


class TempDocs(unittest.TestCase):
    """源目录:

    index.md  → # 首页
    guide.md  → # 指南,链接 [目录](index.md) 与 [下一页](sub/advance.md)
    sub/advance.md → # 进阶,链接 [指南](../guide.md)
    _draft.md / .hidden.md → 应被跳过
    """

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.src = Path(tmp.name) / "我的文档"
        (self.src / "sub").mkdir(parents=True)
        (self.src / "index.md").write_text("# 首页\n\n欢迎。", encoding="utf-8")
        (self.src / "guide.md").write_text(
            "# 指南\n\n回[首页](index.md),再看[进阶](sub/advance.md)。", encoding="utf-8")
        (self.src / "sub" / "advance.md").write_text(
            "# 进阶\n\n返回[指南](../guide.md)。", encoding="utf-8")
        (self.src / "_draft.md").write_text("# 草稿", encoding="utf-8")
        (self.src / ".hidden.md").write_text("# 隐藏", encoding="utf-8")

    def build(self, *args, **kwargs):
        return build_site(self.src, *args, **kwargs)

    def run_cli(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = main(list(args))
        return code, stdout.getvalue(), stderr.getvalue()


class BuilderTest(TempDocs):
    def test_pages_built_with_subdirs(self):
        report = self.build(out=str(self.src / "site"))
        files = set(report["files"])
        self.assertEqual(report["pages"], 3)
        self.assertIn("index.html", files)
        self.assertIn("guide.html", files)
        self.assertIn("sub/advance.html", files)
        self.assertTrue((self.src / "site" / "guide.html").is_file())
        # 草稿与隐藏文件不构建
        self.assertNotIn("_draft.html", files)
        self.assertNotIn(".hidden.html", files)

    def test_out_dir_inside_source_is_skipped(self):
        self.build(out=str(self.src / "site"))
        report = self.build(out=str(self.src / "site"))  # site 里已有 html
        self.assertEqual(report["pages"], 3)  # 不会把输出目录当源内容

    def test_title_from_h1_and_link_rewrite(self):
        report = self.build(out=str(self.src / "site"))
        guide = (self.src / "site" / "guide.html").read_text(encoding="utf-8")
        self.assertIn("<title>指南</title>", guide)
        # .md 链接被重写为 .html(含子目录)
        self.assertIn('href="index.html"', guide)
        self.assertIn('href="sub/advance.html"', guide)
        advance = (self.src / "site" / "sub" / "advance.html").read_text(encoding="utf-8")
        self.assertIn('href="../guide.html"', advance)  # 导航自动加 ../ 前缀

    def test_nav_active_marking(self):
        self.build(out=str(self.src / "site"))
        guide = (self.src / "site" / "guide.html").read_text(encoding="utf-8")
        self.assertIn('class="active"', guide)

    def test_theme_light(self):
        report = self.build(out=str(self.src / "site"), theme="light")
        self.assertEqual(report["theme"], "light")
        html = (self.src / "site" / "index.html").read_text(encoding="utf-8")
        self.assertIn("#ffffff", html)

    def test_auto_index_page(self):
        (self.src / "index.md").unlink()
        report = self.build(out=str(self.src / "site"))
        self.assertIn("index.html", report["files"])  # 自动生成目录页
        html = (self.src / "site" / "index.html").read_text(encoding="utf-8")
        self.assertIn("指南", html)  # 目录页列出所有页面

    def test_invalid_theme(self):
        with self.assertRaises(ValueError):
            self.build(out=str(self.src / "site"), theme="solarized")

    def test_missing_source(self):
        with self.assertRaises(NotADirectoryError):
            build_site(self.src / "ghost")

    def test_no_md_files(self):
        empty = self.src / "empty"
        empty.mkdir()
        with self.assertRaises(ValueError):
            build_site(empty, out=str(self.src / "site2"))

    def test_output_equal_to_source_is_rejected_without_deletion(self):
        sentinel = self.src / "sentinel.txt"
        sentinel.write_text("keep", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "不能与源目录相同"):
            self.build(out=str(self.src), clean=True)
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")

    def test_output_ancestor_is_rejected_without_deletion(self):
        sentinel = self.src / "sentinel.txt"
        sentinel.write_text("keep", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "不能是源目录的祖先"):
            self.build(out=str(self.src.parent), clean=True)
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")

    def test_output_file_is_rejected_without_overwrite(self):
        target = self.src / "output"
        target.write_text("keep", encoding="utf-8")
        with self.assertRaises(NotADirectoryError):
            self.build(out=str(target), clean=True)
        self.assertEqual(target.read_text(encoding="utf-8"), "keep")

    def test_empty_source_preserves_old_output_with_clean(self):
        empty = self.src / "empty"
        empty.mkdir()
        out_dir = self.src.parent / "old-site"
        out_dir.mkdir()
        stale = out_dir / "stale.html"
        stale.write_text("keep", encoding="utf-8")
        with self.assertRaises(ValueError):
            build_site(empty, out=str(out_dir), clean=True)
        self.assertEqual(stale.read_text(encoding="utf-8"), "keep")

    def test_conversion_failure_preserves_old_output_with_clean(self):
        out_dir = self.src / "site"
        out_dir.mkdir()
        stale = out_dir / "stale.html"
        stale.write_text("keep", encoding="utf-8")
        (self.src / "broken.md").write_bytes(b"\xff")
        with self.assertRaises(UnicodeDecodeError):
            self.build(out=str(out_dir), clean=True)
        self.assertEqual(stale.read_text(encoding="utf-8"), "keep")

    def test_site_title_is_escaped_in_title_nav_and_index(self):
        payload = '</title><script>alert("x")</script>'
        (self.src / "index.md").unlink()
        self.build(out=str(self.src / "site"), title=payload)
        page = (self.src / "site" / "index.html").read_text(encoding="utf-8")
        escaped = "&lt;/title&gt;&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;"
        self.assertIn(f"<title>{escaped}</title>", page)
        self.assertIn(f"<aside><h1>{escaped}</h1>", page)
        self.assertNotIn("<script>", page)

    def test_vendored_mdown_blocks_attribute_and_url_injection(self):
        (self.src / "guide.md").write_text(
            '# 安全\n\n[危险](`javascript:alert(1)`)\n\n'
            '![a`x" onerror="alert(1)`](image.png)\n', encoding="utf-8")
        self.build(out=str(self.src / "site"))
        guide = (self.src / "site" / "guide.html").read_text(encoding="utf-8")
        self.assertIn('<a href="#">危险</a>', guide)
        self.assertIn('alt="ax&quot; onerror=&quot;alert(1)"', guide)
        self.assertNotIn("javascript:", guide)


class CliTest(TempDocs):
    def test_build_report(self):
        out_dir = self.src / "site"
        code, out, err = self.run_cli(str(self.src), "-o", str(out_dir))
        self.assertEqual(code, 0, err)
        self.assertIn("已构建 3 页", out)
        self.assertIn("index.html", out)

    def test_json_report(self):
        code, out, _ = self.run_cli(str(self.src), "-o", str(self.src / "site"), "--json")
        self.assertEqual(code, 0)
        report = json.loads(out)
        self.assertEqual(report["pages"], 3)
        self.assertEqual(report["theme"], "dark")

    def test_clean_option(self):
        out_dir = self.src / "site"
        self.build(out=str(out_dir))
        stale = out_dir / "stale.html"
        stale.write_text("old", encoding="utf-8")
        code, _, err = self.run_cli(str(self.src), "-o", str(out_dir), "--clean")
        self.assertEqual(code, 0, err)
        self.assertFalse(stale.exists())  # --clean 清掉了遗留文件

    def test_missing_source_exit_code(self):
        code, _, err = self.run_cli(str(self.src / "ghost"))
        self.assertEqual(code, 1)
        self.assertIn("源目录不存在", err)


class LegacyEncodingCliTest(unittest.TestCase):
    def setUp(self):
        self.env = {**os.environ, "PYTHONIOENCODING": "cp1252", "PYTHONUTF8": "0"}
        self.cwd = Path(__file__).resolve().parents[1]

    def test_utf8_help_under_legacy_encoding(self):
        result = subprocess.run(
            [sys.executable, "-m", "msite", "--help"],
            cwd=self.cwd, capture_output=True, env=self.env,
        )
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8"))
        self.assertIn("静态文档站", result.stdout.decode("utf-8"))

    def test_utf8_json_stdout_under_legacy_encoding(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "中文文档"
            source.mkdir()
            (source / "index.md").write_text("# 中文标题\n\n正文。", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-m", "msite", str(source), "-o",
                 str(Path(tmp) / "站点"), "--title", "中文站点", "--json"],
                cwd=self.cwd, capture_output=True, env=self.env,
            )
            self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8"))
            report = json.loads(result.stdout.decode("utf-8"))
            self.assertEqual(report["title"], "中文站点")
            self.assertEqual(report["pages"], 1)

    def test_utf8_error_stderr_under_legacy_encoding(self):
        result = subprocess.run(
            [sys.executable, "-m", "msite", str(self.cwd / "不存在")],
            cwd=self.cwd, capture_output=True, env=self.env,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("源目录不存在", result.stderr.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
