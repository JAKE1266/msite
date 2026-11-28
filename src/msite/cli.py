"""msite 命令行入口。

::

    msite docs/                          # 构建 docs/ → site/
    msite docs/ -o public --theme light
    msite docs/ --clean                  # 转换成功后清空输出目录再构建
"""

from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from .core.builder import build_site


def _configure_standard_streams() -> None:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def cmd_build(args) -> int:
    try:
        report = build_site(args.source, out=args.output, theme=args.theme,
                            title=args.title, clean=args.clean)
    except (ValueError, NotADirectoryError, OSError) as exc:
        print(f"错误:{exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    print(f"[OK] 已构建 {report['pages']} 页 → {report['out']}"
          f"(主题:{report['theme']},站点:{report['title']})")
    for name in report["files"]:
        print(f"  {name}")
    print("提示:本地预览可在输出目录运行 python -m http.server。")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="msite",
        description="msite —— 把一个目录的 Markdown 构建成带侧边导航与主题的静态文档站"
                    "(转换内核为同系列 mdown)",
    )
    parser.add_argument("--version", action="version", version=f"msite {__version__}")
    parser.add_argument("source", nargs="?", default=".", help="含 .md 的源目录(默认当前目录)")
    parser.add_argument("-o", "--output", default="site", help="输出目录(默认 site/)")
    parser.add_argument("--theme", choices=("dark", "light"), default="dark", help="主题(默认 dark)")
    parser.add_argument("--title", default=None, help="站点名(默认源目录名)")
    parser.add_argument("--clean", action="store_true", help="转换成功后清空输出目录")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出构建报告")
    return parser


def main(argv=None) -> int:
    _configure_standard_streams()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return cmd_build(args)
    except KeyboardInterrupt:
        print("\n已取消。")
        return 130
    except BrokenPipeError:
        return 0
    except (ValueError, NotADirectoryError, OSError) as exc:
        print(f"错误:{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
