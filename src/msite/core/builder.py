"""站点构建:扫描 .md → mdown 转 HTML → 导航与主题组装。

约定:

- ``index.md`` 映射为 ``index.html`` 并排在导航最前;没有它则自动生成目录页;
- 页面间链接直接写相对 ``.md`` 路径(如 ``[下一步](next.md)``),
  构建时统一重写为 ``.html``(含 ``#锚点``);
- 以 ``.`` 或 ``_`` 开头的文件/目录跳过;输出目录位于源目录内时自动排除;
- 导航链接按当前页面所在层级自动加 ``../`` 前缀。
"""

from __future__ import annotations

import html
import re
import shutil
from pathlib import Path

from msite._vendor.mdown import to_html

_MD_SUFFIX = ".md"
_H1_RE = re.compile(r"<h1>(.*?)</h1>", re.S)
_TAG_RE = re.compile(r"<[^>]+>")
_MD_HREF_RE = re.compile(r'href="([^"]*?)\.md(#[^"]*)?"')


def _themes() -> dict:
    """页面内嵌样式(侧边栏布局)。"""
    return {
        "dark": (
            "*{box-sizing:border-box}body{margin:0;display:flex;min-height:100vh;"
            "background:#0b1220;color:#e6ecff;font-family:'Segoe UI','Microsoft YaHei UI',system-ui,sans-serif}"
            "aside{width:230px;flex-shrink:0;padding:22px 16px;background:#111a2e;"
            "border-right:1px solid #223051;position:sticky;top:0;height:100vh;overflow-y:auto}"
            "aside h1{font-size:18px;margin:0 0 12px}"
            "aside a{display:block;color:#8ea0c6;text-decoration:none;padding:6px 10px;border-radius:8px;font-size:13px}"
            "aside a:hover{color:#e6ecff}aside a.active{color:#04121f;background:linear-gradient(135deg,#38bdf8,#34d399);font-weight:600}"
            "main{flex:1;padding:36px 34px 80px;max-width:860px}"
            "a{color:#38bdf8}code{background:#1a2440;padding:2px 6px;border-radius:5px;font-family:Consolas,monospace;font-size:.92em}"
            "pre{background:#111a2e;border:1px solid #223051;border-radius:10px;padding:14px;overflow-x:auto}"
            "pre code{background:none;padding:0}table{border-collapse:collapse;width:100%}"
            "th,td{border:1px solid #223051;padding:8px 12px}"
            "blockquote{margin:0;padding:4px 18px;border-left:3px solid #38bdf8;background:#111a2e;color:#8ea0c6}"
            "hr{border:none;border-top:1px solid #223051;margin:28px 0}img{max-width:100%}"
        ),
        "light": (
            "*{box-sizing:border-box}body{margin:0;display:flex;min-height:100vh;"
            "background:#ffffff;color:#1f2937;font-family:'Segoe UI','Microsoft YaHei UI',system-ui,sans-serif}"
            "aside{width:230px;flex-shrink:0;padding:22px 16px;background:#f8fafc;"
            "border-right:1px solid #e2e8f0;position:sticky;top:0;height:100vh;overflow-y:auto}"
            "aside h1{font-size:18px;margin:0 0 12px}"
            "aside a{display:block;color:#475569;text-decoration:none;padding:6px 10px;border-radius:8px;font-size:13px}"
            "aside a:hover{color:#1f2937}aside a.active{color:#ffffff;background:linear-gradient(135deg,#0ea5e9,#10b981);font-weight:600}"
            "main{flex:1;padding:36px 34px 80px;max-width:860px}"
            "a{color:#0369a1}code{background:#f1f5f9;padding:2px 6px;border-radius:5px;font-family:Consolas,monospace;font-size:.92em}"
            "pre{background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:14px;overflow-x:auto}"
            "pre code{background:none;padding:0}table{border-collapse:collapse;width:100%}"
            "th,td{border:1px solid #e2e8f0;padding:8px 12px}"
            "blockquote{margin:0;padding:4px 18px;border-left:3px solid #0369a1;background:#f8fafc;color:#475569}"
            "hr{border:none;border-top:1px solid #e2e8f0;margin:28px 0}img{max-width:100%}"
        ),
    }


def _collect_md_files(source: Path, out_dir: Path) -> list:
    """递归收集 .md 相对路径:index.md 优先,其余按路径排序。"""
    out_resolved = out_dir.resolve()
    pages: list = []
    for path in source.rglob("*.md"):
        if path.resolve().is_relative_to(out_resolved):
            continue
        rel = path.relative_to(source)
        parts = rel.parts
        if any(part.startswith((".", "_")) for part in parts):
            continue
        pages.append(rel)
    return sorted(pages, key=lambda p: (p.name.lower() != "index.md", p.as_posix().lower()))


def _first_title(fragment: str, fallback: str) -> str:
    match = _H1_RE.search(fragment)
    if match:
        return html.unescape(_TAG_RE.sub("", match.group(1))).strip() or fallback
    return fallback


def _rewrite_md_links(fragment: str) -> str:
    """``href="x.md#锚"`` → ``href="x.html#锚"``。"""
    return _MD_HREF_RE.sub(r'href="\1.html\2"', fragment)


def _nav_html(pages: list, titles: dict, current_rel: str, site_title: str) -> str:
    depth = current_rel.count("/")
    prefix = "../" * depth
    links = []
    for rel in pages:
        href = rel.with_suffix(".html").as_posix()
        target = prefix + href
        active = ' class="active"' if rel.as_posix() == current_rel else ""
        links.append(f'<a href="{html.escape(target, quote=True)}"{active}>'
                     f'{html.escape(titles[rel.as_posix()])}</a>')
    return (f"<aside><h1>{html.escape(site_title)}</h1><nav>" + "".join(links)
            + "</nav></aside>")


def _page(fragment: str, nav: str, theme: str, title: str) -> str:
    css = _themes()[theme]
    return (
        "<!doctype html>\n<html lang=\"zh-CN\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"<title>{html.escape(title)}</title>\n<style>{css}</style>\n"
        f"</head>\n<body>\n{nav}\n<main>\n{fragment}\n</main>\n</body>\n</html>\n"
    )


def _index_page(pages: list, titles: dict, nav: str, theme: str, title: str) -> str:
    links = "".join(
        f'<li><a href="{html.escape(rel.with_suffix(".html").as_posix(), quote=True)}">'
        f'{html.escape(titles[rel.as_posix()])}</a></li>' for rel in pages)
    fragment = f"<h1>{html.escape(title)}</h1>\n<ul>{links}</ul>"
    return _page(fragment, nav, theme, title)


def build_site(source, out: str = "site", theme: str = "dark",
               title: str | None = None, clean: bool = False) -> dict:
    """构建静态站点。

    :param source: 含 .md 的源目录
    :param out: 输出目录(默认 ``site/``;位于源目录内时自动排除)
    :param theme: ``dark`` 或 ``light``
    :param title: 站点名(默认源目录名)
    :param clean: 构建前清空输出目录
    :returns: 构建报告(页数、输出路径、生成文件列表)
    """
    if theme not in _themes():
        raise ValueError(f"主题只能是 dark/light:{theme!r}")
    source = Path(source).resolve()
    if not source.is_dir():
        raise NotADirectoryError(f"源目录不存在或不是文件夹:{source}")
    out_dir = Path(out).resolve()
    if out_dir == source:
        raise ValueError("输出目录不能与源目录相同")
    if source.is_relative_to(out_dir):
        raise ValueError("输出目录不能是源目录的祖先")
    if out_dir.exists() and not out_dir.is_dir():
        raise NotADirectoryError(f"输出路径不是文件夹:{out_dir}")

    pages = _collect_md_files(source, out_dir)
    if not pages:
        raise ValueError(f"源目录里没有找到任何 .md 文件:{source}")

    site_title = title or source.resolve().name
    titles: dict = {}
    fragments: dict = {}
    for rel in pages:
        fragment = to_html((source / rel).read_text(encoding="utf-8-sig"))
        fragment = _rewrite_md_links(fragment)
        fragments[rel.as_posix()] = fragment
        titles[rel.as_posix()] = _first_title(fragment, rel.stem)

    if clean and out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list = []
    for rel in pages:
        current = rel.as_posix()
        nav = _nav_html(pages, titles, current, site_title)
        page = _page(fragments[current], nav, theme, titles[current])
        target = out_dir / rel.with_suffix(".html")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(page, encoding="utf-8")
        written.append(target.relative_to(out_dir).as_posix())

    if "index.html" not in written:  # 没有 index.md:自动生成目录页
        nav = _nav_html(pages, titles, "index.html", site_title)
        (out_dir / "index.html").write_text(
            _index_page(pages, titles, nav, theme, site_title), encoding="utf-8")
        written.append("index.html")

    return {"source": str(source), "out": str(out_dir), "pages": len(pages),
            "files": sorted(written), "theme": theme, "title": site_title}
