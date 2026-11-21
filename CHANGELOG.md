# 更新日志

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 格式,
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.0.0] - 2026-11-21

### 新增
- 递归扫描源目录全部 `.md`(跳过 `.`/`_` 前缀与输出目录自身)
- 转换内核为同系列 [mdown](https://github.com/JAKE1266/mdown)(纯标准库)
- 侧边导航:index.md 置顶、按页面层级自动加 `../` 前缀、当前页高亮
- 页面间 `.md` 相对链接(含 `#锚点`)统一重写为 `.html`
- `--theme dark/light`、`--title` 站点名、`-o` 输出目录、`--clean` 清理、`--json` 报告
- 缺少 index.md 时自动生成目录页
- 13 个端到端测试(临时目录真实构建);GitHub Actions 三系统 × 三 Python 版本 CI
