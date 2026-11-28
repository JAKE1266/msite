# msite

> 把一个目录的 Markdown 变成带侧边导航与主题的静态文档站。
> 一条命令,输出即 GitHub Pages。转换内核是同系列自研解析器 [mdown](https://github.com/JAKE1266/mdown)。

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Dependencies](https://img.shields.io/badge/dependencies-0-blue)
![Tests](https://img.shields.io/badge/tests-23%20passing-success)

## ✨ 特性

- 🌲 **递归扫描**:子目录里的 `.md` 全部构建,保持目录结构
- 🧭 **侧边导航**:`index.md` 置顶、当前页高亮、跨层级链接自动加 `../` 前缀
- 🔗 **链接重写**:页面间直接写 `[下一步](next.md)`,构建时统一改为 `.html`(支持 `#锚点`)
- 🎨 **双主题**:`--theme dark` / `light`,自包含 CSS,单文件页面
- 📄 **自动目录页**:没有 `index.md` 时自动生成站点目录
- 🚫 **约定排除**:`.` / `_` 前缀文件与输出目录自身不参与构建
- 🧹 **`--clean`**:全部页面转换成功后清空输出目录,不留陈旧文件
- 🛡 **安全边界**:拒绝把源目录或其祖先作为输出;站点名与标题按 HTML 上下文转义
- 📤 **`--json`**:构建报告结构化输出,方便接入脚本

## 📦 安装

```bash
git clone https://github.com/JAKE1266/msite.git
cd msite
pip install .
python -m msite --help
```

转换内核为同系列 [mdown](https://github.com/JAKE1266/mdown) 1.0.1,已私有化内嵌;
安装与运行不需要 Git,也没有第三方运行时依赖。

## 🚀 快速上手

```bash
msite docs/                          # docs/ → site/
msite docs/ -o public --theme light --title 我的文档
msite docs/ --clean --json           # 清理重建 + JSON 报告

# 本地预览
cd site && python -m http.server
```

页面之间直接写相对 Markdown 链接,构建时自动重写:

```markdown
# 指南

回[首页](index.md),继续阅读[进阶](sub/advance.md)。
```

## 🧰 参数一览

```
msite [源目录] [选项]
  -o 目录        输出目录(默认 site/)
  --theme        dark / light(默认 dark)
  --title 名称   站点名(默认源目录名)
  --clean        构建前清空输出目录
  --json         JSON 构建报告
```

## 📁 项目结构

```
msite/
├── .github/workflows/ci.yml   # CI:构建 + 三系统 × 四版本真实 wheel 测试
├── src/msite/
│   ├── _vendor/mdown/         # 私有内嵌 mdown 1.0.1
│   ├── core/builder.py        # 扫描 / 转换 / 导航 / 链接重写 / 主题
│   └── cli.py                 # 命令行入口
├── tests/                     # 23 项测试 + 已安装 wheel 冒烟
└── pyproject.toml
```

## 🧪 开发与测试

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

## 🗺 路线图

- [ ] 静态资源(.css/.png)复制
- [ ] 每页"上一篇 / 下一篇"
- [ ] 搜索(index.json + 前端过滤)

## 📄 许可证

[MIT](LICENSE) —— 可自由使用、修改与分发。

---

*同系列项目:[PyToolBox](https://github.com/JAKE1266/py-toolbox) 多功能工具箱 · [CashBook](https://github.com/JAKE1266/cashbook) 命令行记账本 · [gitdash](https://github.com/JAKE1266/gitdash) Git 终端仪表盘 · [DevBox](https://github.com/JAKE1266/devbox) 前端开发工具箱 · [csvq](https://github.com/JAKE1266/csvq) SQL 查 CSV · [cjktable](https://github.com/JAKE1266/cjktable) CJK 排版微库 · [duviz](https://github.com/JAKE1266/duviz) 磁盘占用可视化 · [httpoke](https://github.com/JAKE1266/httpoke) HTTP 调试工具 · [mdown](https://github.com/JAKE1266/mdown) Markdown→HTML · [crony](https://github.com/JAKE1266/crony) cron 表达式解析 · [pomo](https://github.com/JAKE1266/pomo) 番茄钟 · [termplot](https://github.com/JAKE1266/termplot) 终端数据图表 · [filewatch](https://github.com/JAKE1266/filewatch) 目录变更监控 · [packpeek](https://github.com/JAKE1266/packpeek) 压缩包检查与安全解压 · [statline](https://github.com/JAKE1266/statline) 统计摘要 · [difftool](https://github.com/JAKE1266/difftool) 文本差异 · [wordfreq](https://github.com/JAKE1266/wordfreq) 词频统计 · [hexview](https://github.com/JAKE1266/hexview) 十六进制查看器 · [quicktodo](https://github.com/JAKE1266/quicktodo) 待办清单 · [envcheck](https://github.com/JAKE1266/envcheck) .env 校验 · [ipcalc](https://github.com/JAKE1266/ipcalc) 子网计算器 · [quickjournal](https://github.com/JAKE1266/quickjournal) 速记日志 · [csv2md](https://github.com/JAKE1266/csv2md) CSV→Markdown · [namecase](https://github.com/JAKE1266/namecase) 命名风格转换 · [dirsinc](https://github.com/JAKE1266/dirsinc) 目录增量同步 · [stopwatch](https://github.com/JAKE1266/stopwatch) 正计时秒表 · [wordwrap](https://github.com/JAKE1266/wordwrap) 按显示宽度换行 · [mdtoc](https://github.com/JAKE1266/mdtoc) Markdown 目录生成 · [checksum](https://github.com/JAKE1266/checksum) 批量校验和 · [gitignore-gen](https://github.com/JAKE1266/gitignore-gen) .gitignore 模板 · [filefind](https://github.com/JAKE1266/filefind) 文件搜索 · [filedupe](https://github.com/JAKE1266/filedupe) 重复文件查找*
