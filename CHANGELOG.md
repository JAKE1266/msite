# 更新日志

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 格式,
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.0.1] - 2026-11-28

### 修复
- `--clean` 不再删除源目录或其祖先;空源目录、读取或转换失败时保留旧输出
- 输出路径为文件时明确拒绝,避免覆盖或清理异常
- 站点名、页面标题、导航与自动目录文本按 HTML 上下文转义
- 私有化内嵌 mdown 1.0.1,移除 Git 运行时依赖及同名顶级包冲突
- 命令行标准流统一 UTF-8,兼容旧编码终端

### 新增
- 23 项回归测试,覆盖数据保护、HTML/URL 安全、vendor 与旧编码 CLI
- 已安装 wheel 冒烟;三系统 × Python 3.9/3.10/3.12/3.13 真实 wheel CI
- sdist 包含更新日志与完整测试源码

## [1.0.0] - 2026-11-21

### 新增
- 递归扫描源目录全部 `.md`(跳过 `.`/`_` 前缀与输出目录自身)
- 转换内核为同系列 [mdown](https://github.com/JAKE1266/mdown)(纯标准库)
- 侧边导航:index.md 置顶、按页面层级自动加 `../` 前缀、当前页高亮
- 页面间 `.md` 相对链接(含 `#锚点`)统一重写为 `.html`
- `--theme dark/light`、`--title` 站点名、`-o` 输出目录、`--clean` 清理、`--json` 报告
- 缺少 index.md 时自动生成目录页
- 13 个端到端测试(临时目录真实构建);GitHub Actions 三系统 × 三 Python 版本 CI
