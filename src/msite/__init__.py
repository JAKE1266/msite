"""msite —— 把一个目录的 Markdown 构建成静态文档站(基于同系列 mdown)。

::

    from msite import build_site

    report = build_site("docs", out="site", theme="dark")
"""

from msite.core.builder import build_site

__version__ = "1.0.0"

__all__ = ["build_site", "__version__"]
