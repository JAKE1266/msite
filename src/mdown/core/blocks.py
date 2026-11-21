"""块级解析:标题 / 段落 / 列表(嵌套)/ 引用 / 围栏代码块 / 表格 / 水平线。

支持的 Markdown 子集(有意保持简单、可测试):

- ATX 标题 ``# ~ ######``(允许结尾 #)
- 围栏代码块 `` ``` `` / ``~~~``(可选语言标注)
- 无序 / 有序列表(2 空格一层缩进,支持嵌套;空行结束列表)
- 引用 ``>``(可嵌套,内部递归解析)
- GFM 管道表格(第二行为对齐声明 ``:---:``)
- 水平线 ``---`` ``***`` ``___``
- 其余连续行为段落;所有行内文本经 :func:`mdown.core.inline.render_inline` 转义
"""

from __future__ import annotations

import re

from mdown.core.inline import render_inline

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)(?:\s+#+\s*)?$")
_FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})\s*([\w+-]*)\s*$")
_ITEM_RE = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
_TABLE_DELIM_RE = re.compile(r"^\s*\|?\s*:?-{1,}:?\s*(\|\s*:?-{1,}:?\s*)*\|?\s*$")
_QUOTE_RE = re.compile(r"^ {0,3}>")

# 水平线:三个以上相同符号(- 前两个之后允许空格分隔的重复)
_HR_RE = re.compile(r"^ {0,3}([-*_])(?: *\1){2,}\s*$")


def _escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _split_row(line: str) -> list:
    """拆分表格行,``\\|`` 视为字面竖线。"""
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    cells = [c.replace("\x00", "|").strip()
             for c in line.replace("\\|", "\x00").split("|")]
    return cells


def _parse_aligns(delim_line: str) -> list:
    aligns = []
    for cell in _split_row(delim_line):
        left, right = cell.startswith(":"), cell.endswith(":")
        if left and right:
            aligns.append("center")
        elif right:
            aligns.append("right")
        else:
            aligns.append("left")
    return aligns


def _render_table(header: list, aligns: list, rows: list) -> str:
    head_cells = "".join(
        f'<th style="text-align:{a}">{render_inline(h)}</th>'
        for h, a in zip(header, aligns))
    body_rows = []
    for row in rows:
        row = row[:len(aligns)] + [""] * max(0, len(aligns) - len(row))
        body_rows.append("<tr>" + "".join(
            f'<td style="text-align:{a}">{render_inline(c)}</td>'
            for c, a in zip(row, aligns)) + "</tr>")
    return ("<table>\n<thead>\n<tr>" + head_cells + "</tr>\n</thead>\n<tbody>\n"
            + "\n".join(body_rows) + "\n</tbody>\n</table>")


def _collect_list_item(lines: list, index: int) -> tuple:
    """从 ``index`` 收集一个列表块(含嵌套缩进行),返回 (行, 下一索引)。"""
    collected = [lines[index]]
    index += 1
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            break  # 空行结束列表(有意从简)
        if _ITEM_RE.match(line) or line[:2] == "  " or line[:2] == "\t":
            collected.append(line)
            index += 1
        else:
            break
    return collected, index


def _render_list(lines: list) -> str:
    """渲染一层列表;更深缩进的内容递归为嵌套列表。"""
    base = len(lines[0]) - len(lines[0].lstrip(" "))
    ordered = bool(re.match(r"^\s*\d", lines[0]))
    start = 1
    if ordered:
        start = int(re.match(r"^\s*(\d+)", lines[0]).group(1))

    items: list = []
    for line in lines:
        match = _ITEM_RE.match(line)
        indent = len(line) - len(line.lstrip(" "))
        if match and indent == base:
            items.append([match.group(3)])
        else:
            stripped = line[base + 2:] if len(line) > base + 2 else line.lstrip(" ")
            if items:
                items[-1].append(stripped)
            else:
                items.append([stripped])

    html_items = []
    for content in items:
        nested = [l for l in content if _ITEM_RE.match(l)]
        plain = [l for l in content if not _ITEM_RE.match(l)]
        inner = render_inline(" ".join(s.strip() for s in plain).strip())
        if nested:
            inner += "\n" + _render_list(nested)
        html_items.append(f"<li>{inner}</li>")

    tag = "ol" if ordered else "ul"
    start_attr = f' start="{start}"' if ordered and start != 1 else ""
    return f"<{tag}{start_attr}>\n" + "\n".join(html_items) + f"\n</{tag}>"


def to_html(text: str) -> str:
    """把 Markdown 文本渲染为 HTML 片段(不含 <html> 外壳)。"""
    if not isinstance(text, str):
        raise TypeError(f"text 必须是字符串,得到:{type(text).__name__}")
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out: list = []
    para: list = []

    def flush() -> None:
        if para:
            out.append("<p>" + render_inline("\n".join(para).strip()) + "</p>")
            para.clear()

    i = 0
    while i < len(lines):
        line = lines[i]

        if _FENCE_RE.match(line):  # 围栏代码块
            flush()
            fence = _FENCE_RE.match(line)
            marker, lang = fence.group(1), fence.group(2)
            i += 1
            code: list = []
            while i < len(lines) and not re.match(rf"^ {{0,3}}{re.escape(marker[0])}{{{len(marker)},}}\s*$", lines[i]):
                code.append(lines[i])
                i += 1
            i += 1  # 跳过闭合围栏(缺失则到文末)
            lang_attr = f' class="language-{lang}"' if lang else ""
            out.append(f"<pre><code{lang_attr}>{_escape_html(chr(10).join(code))}</code></pre>")
            continue

        if not line.strip():
            flush()
            i += 1
            continue

        heading = _HEADING_RE.match(line)
        if heading:
            flush()
            level = len(heading.group(1))
            out.append(f"<h{level}>{render_inline(heading.group(2).strip())}</h{level}>")
            i += 1
            continue

        if _HR_RE.match(line):
            flush()
            out.append("<hr />")
            i += 1
            continue

        if _QUOTE_RE.match(line):  # 引用(可嵌套)
            flush()
            quoted = []
            while i < len(lines) and _QUOTE_RE.match(lines[i]):
                quoted.append(re.sub(r"^ {0,3}> ?", "", lines[i]))
                i += 1
            out.append("<blockquote>\n" + to_html("\n".join(quoted)) + "\n</blockquote>")
            continue

        if _ITEM_RE.match(line):  # 列表
            flush()
            block, i = _collect_list_item(lines, i)
            out.append(_render_list(block))
            continue

        if (para and _TABLE_DELIM_RE.match(line)
                and "|" in para[-1]):  # 表格:段落尾行是表头
            header = _split_row(para.pop())
            aligns = _parse_aligns(line)
            rows = []
            i += 1
            while i < len(lines) and lines[i].strip() and "|" in lines[i]:
                rows.append(_split_row(lines[i]))
                i += 1
            out.append(_render_table(header, aligns, rows))
            continue

        para.append(line)
        i += 1

    flush()
    return "\n".join(out)
