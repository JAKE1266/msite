"""mdown —— 零依赖的 Markdown → HTML 转换器(自研解析器)。

::

    from mdown import to_html, render_inline

    to_html("# 标题\\n\\n正文 **加粗**")
"""

from mdown.core.blocks import to_html
from mdown.core.inline import render_inline

__version__ = "1.0.0"

__all__ = ["render_inline", "to_html", "__version__"]
