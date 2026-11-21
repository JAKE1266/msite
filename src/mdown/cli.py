"""mdown 命令行入口。

::

    mdown README.md                      # 自包含 HTML 输出到 stdout
    mdown README.md -o out.html --theme dark
    mdown doc.md --fragment              # 仅输出 <body> 片段
"""

from __future__ import annotations

import argparse
import html
import sys
from pathlib import Path

from . import __version__
from .core.blocks import to_html

_THEMES = {
    "dark": (
        "body{margin:0 auto;max-width:820px;padding:40px 20px 80px;line-height:1.75;"
        "font-family:'Segoe UI','Microsoft YaHei UI',system-ui,sans-serif;"
        "background:#0b1220;color:#e6ecff}"
        "h1,h2,h3{line-height:1.3}"
        "a{color:#38bdf8}"
        "code{background:#1a2440;padding:2px 6px;border-radius:5px;"
        "font-family:Consolas,monospace;font-size:.92em}"
        "pre{background:#111a2e;border:1px solid #223051;border-radius:10px;"
        "padding:14px;overflow-x:auto}"
        "pre code{background:none;padding:0}"
        "table{border-collapse:collapse;width:100%}"
        "th,td{border:1px solid #223051;padding:8px 12px}"
        "blockquote{margin:0;padding:4px 18px;border-left:3px solid #38bdf8;"
        "background:#111a2e;color:#8ea0c6}"
        "hr{border:none;border-top:1px solid #223051;margin:28px 0}"
        "img{max-width:100%}"
    ),
    "light": (
        "body{margin:0 auto;max-width:820px;padding:40px 20px 80px;line-height:1.75;"
        "font-family:'Segoe UI','Microsoft YaHei UI',system-ui,sans-serif;"
        "background:#ffffff;color:#1f2937}"
        "h1,h2,h3{line-height:1.3}"
        "a{color:#0369a1}"
        "code{background:#f1f5f9;padding:2px 6px;border-radius:5px;"
        "font-family:Consolas,monospace;font-size:.92em}"
        "pre{background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;"
        "padding:14px;overflow-x:auto}"
        "pre code{background:none;padding:0}"
        "table{border-collapse:collapse;width:100%}"
        "th,td{border:1px solid #e2e8f0;padding:8px 12px}"
        "blockquote{margin:0;padding:4px 18px;border-left:3px solid #0369a1;"
        "background:#f8fafc;color:#475569}"
        "hr{border:none;border-top:1px solid #e2e8f0;margin:28px 0}"
        "img{max-width:100%}"
    ),
}


def _document(body: str, theme: str, title: str) -> str:
    css = _THEMES.get(theme, _THEMES["dark"])
    return (
        "<!doctype html>\n<html lang=\"zh-CN\">\n<head>\n<meta charset=\"utf-8\">\n"
        f"<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"<title>{html.escape(title)}</title>\n<style>{css}</style>\n"
        f"</head>\n<body>\n{body}\n</body>\n</html>\n"
    )


def _guess_title(body: str, source: Path) -> str:
    for line in body.splitlines():
        if line.startswith("<h1>"):
            return line[4:-5] or source.stem
    return source.stem


def cmd_convert(args) -> int:
    source = Path(args.input)
    if not source.is_file():
        print(f"错误:文件不存在:{source}", file=sys.stderr)
        return 1
    text = source.read_text(encoding="utf-8-sig")
    fragment = to_html(text)

    if args.fragment:
        output = fragment
    else:
        output = _document(fragment, args.theme, args.title or _guess_title(fragment, source))

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"[OK] 已生成 {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mdown",
        description="mdown —— 零依赖的 Markdown → HTML 转换器(自研解析器,纯标准库)",
    )
    parser.add_argument("--version", action="version", version=f"mdown {__version__}")
    parser.add_argument("input", help="输入的 Markdown 文件")
    parser.add_argument("-o", "--output", default=None, help="输出 HTML 文件(缺省打印到 stdout)")
    parser.add_argument("--theme", choices=tuple(_THEMES), default="dark",
                        help="内嵌主题(默认 dark)")
    parser.add_argument("--title", default=None, help="页面标题(默认取第一个一级标题或文件名)")
    parser.add_argument("-f", "--fragment", action="store_true",
                        help="只输出 HTML 片段(不包 <html> 外壳与样式)")
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return cmd_convert(args)
    except KeyboardInterrupt:
        print("\n已取消。")
        return 130
    except (ValueError, OSError) as exc:
        print(f"错误:{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
