"""行内元素解析:实体转义、反斜杠转义、代码段、图片、链接、强调。

处理顺序(关键,决定语义):

1. HTML 实体转义 ``& < >``(先转义,防 XSS);
2. 反斜杠转义压栈(占位符保护);
3. 行内代码压栈(代码内容不再参与后续解析);
4. 图片压栈(属性值转义,URL 方案白名单);
5. 粗斜体 ``***x***`` → 粗体 → 斜体(链接在后,文本内可嵌强调);
6. 链接渲染(属性值转义,URL 方案白名单);
7. 还原占位符。
"""

from __future__ import annotations

import re

_CODE_RE = re.compile(r"`([^`\n]+)`", re.S)
_IMAGE_RE = re.compile(r'!\[([^\]]*)\]\(([^)\s]+)(?:\s+"([^"]*)")?\)')
_TRIPLE_RE = re.compile(r"\*\*\*(.+?)\*\*\*", re.S)
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*", re.S)
_ITALIC_RE = re.compile(r"\*([^*\n]+)\*")
_BOLD_UNDERSCORE_RE = re.compile(r"(?<!\w)__(.+?)__(?!\w)", re.S)
_ITALIC_UNDERSCORE_RE = re.compile(r"(?<![\w\\])_([^_\n]+)_(?!\w)")
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)(?:\s+\"([^\"]*)\")?\)")
_SCHEME_RE = re.compile(r"^([a-z][a-z0-9+.-]*):", re.I)
_ALLOWED_SCHEMES = frozenset({"http", "https", "mailto", "tel"})


def _safe_url(url: str) -> str:
    match = _SCHEME_RE.match(url)
    if match and match.group(1).lower() not in _ALLOWED_SCHEMES:
        return "#"
    return url


def render_inline(text: str) -> str:
    """把一行/一段 Markdown 行内文本渲染为 HTML 片段。"""
    if not isinstance(text, str):
        raise TypeError(f"text 必须是字符串,得到:{type(text).__name__}")

    # 1) 基础实体转义(先于一切解析,XSS 防线)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    stash: dict[str, tuple[str, str]] = {}

    def keep(html: str, literal=None) -> str:
        token = f"\x00{len(stash)}\x00"
        stash[token] = (html, html if literal is None else literal)
        return token

    def resolve_literal(text: str) -> str:
        for _ in range(len(stash) + 1):
            for token, (_, literal) in stash.items():
                text = text.replace(token, literal)
        return text

    def attribute(text: str) -> str:
        return resolve_literal(text).replace('"', "&quot;")

    # 2) 反斜杠转义:任意标点按字面量保留
    text = re.sub(r"\\([\\`*_{}\[\]()#+\-.!>])",
                  lambda m: keep(m.group(1)), text)

    # 3) 行内代码(先剥出,内容不再处理)
    def code(m: re.Match) -> str:
        content = m.group(1).strip()
        return keep(f"<code>{content}</code>", resolve_literal(content))

    text = _CODE_RE.sub(code, text)

    # 4) 图片
    def image(m: re.Match) -> str:
        title = f' title="{attribute(m.group(3))}"' if m.group(3) else ""
        src = attribute(_safe_url(resolve_literal(m.group(2))))
        alt = attribute(m.group(1))
        return keep(f'<img src="{src}" alt="{alt}"{title} />')
    text = _IMAGE_RE.sub(image, text)

    # 5) 强调(先三连,再双星,再单星;下划线要求词边界)
    text = _TRIPLE_RE.sub(r"<strong><em>\1</em></strong>", text)
    text = _BOLD_RE.sub(r"<strong>\1</strong>", text)
    text = _BOLD_UNDERSCORE_RE.sub(r"<strong>\1</strong>", text)
    text = _ITALIC_RE.sub(r"<em>\1</em>", text)
    text = _ITALIC_UNDERSCORE_RE.sub(r"<em>\1</em>", text)

    # 6) 链接(此时链接文本里可能已包含强调结果)
    def link(m: re.Match) -> str:
        title = f' title="{attribute(m.group(3))}"' if m.group(3) else ""
        href = attribute(_safe_url(resolve_literal(m.group(2))))
        return f'<a href="{href}"{title}>{m.group(1)}</a>'
    text = _LINK_RE.sub(link, text)

    # 7) 还原占位符(嵌套占位符需要多轮)
    for _ in range(len(stash) + 1):
        previous = text
        for token, (html, _) in stash.items():
            text = text.replace(token, html)
        if text == previous:
            break
    return text
