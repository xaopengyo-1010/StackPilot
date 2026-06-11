# StackPilot 架构说明

StackPilot v0.2 Alpha 采用兼容式分层迁移。当前仍保留原有模块入口，避免破坏 CLI，但核心链路已经按下面的方向收敛：

```text
硬件事实采集 -> 规则判断 -> 结构化推荐 -> 报告渲染 -> LLM prompt builder
```

## 分层职责

### Scanner

`src/stackpilot/scanner.py` 只负责采集本地公开系统事实，例如系统版本、CPU、内存、显卡、显存、磁盘空间，以及 Python、Node.js、Git、Docker、WSL 等工具状态。Scanner 不负责推荐应用、打分或渲染报告。

### Models

`src/stackpilot/models.py` 定义稳定数据结构，包括：

- `HardwareProfile`
- `EnvironmentStatus`
- `RuleFinding`
- `RecommendationResult`
- `AppRecommendation`
- `ReportData`

其中 `SystemProfile` 和 `TemplateRecommendation` 作为兼容别名保留，方便旧测试和旧调用继续工作。

### Rules

`src/stackpilot/rules/engine.py` 集中处理规则判断。规则输入是硬件事实和目标模板，输出是结构化 `RuleFinding` 列表。规则层不生成 Markdown，不打印 CLI，也不修改系统。

集中规则的原因是：硬件判断必须可测试、可审查、可解释。LLM 不能直接决定显存、内存、磁盘和工具缺失的风险级别，否则报告会变得不可复现。

### Recommender

`src/stackpilot/recommender.py` 负责把目标模板、应用目录、硬件事实和规则 findings 组合成 `RecommendationResult`。它不写文件、不渲染 Markdown，也不直接打印终端输出。

### Reports

`src/stackpilot/report.py` 只负责把结构化 `ReportData` 渲染为 Markdown 和 JSON。报告层不会重新判断硬件，也不会改写规则级别。

### LLM

`src/stackpilot/llm/prompt_builder.py` 只生成可审查的中文 prompt，不调用真实 LLM API，不要求 API Key，也不联网。

未来如果接入 LLM，应只把已采集事实、规则 findings 和推荐结果交给 LLM 做表达优化。LLM 不应编造硬件信息，不应覆盖 warning/critical 规则，不应生成自动安装脚本。

## 安全边界

StackPilot 当前版本不会自动下载软件，不会自动安装软件，不会修改系统设置，不会扫描私人文件，也不会上传数据。报告中的建议应引导用户从官方渠道手动确认和安装。
