# StackPilot 安全说明

StackPilot v0.5 当前只生成推荐报告、可审查计划和 dry-run 预览，不会自动安装软件或修改系统设置。

## 安全原则

- 先生成计划，再审计，再 dry-run。
- 不默认执行真实安装。
- 不下载软件。
- 不运行来自网络的脚本。
- 不修改 PATH、环境变量、注册表或用户文件。
- 不承诺绝对无病毒。
- 不承诺 100% 完美回滚。
- 不让 LLM 参与硬件事实判断。
- 不把 GPU 当成独立显卡的同义词。

## 硬件事实安全边界

StackPilot 的推荐、规则和安装计划依赖硬件事实。GPU 检测必须区分：

- GPU：图形处理器总称。
- integrated GPU / 核显：通常使用共享内存。
- dedicated GPU / 独显：可能有独立显存。
- virtual GPU：远程、虚拟或基础显示设备，不作为真实性能判断 GPU。
- unknown GPU：无法确认类型，必须保守提示。

共享内存不能写成独立显存。只有 `vram_confidence == "detected"` 时，报告才可以把数值描述为检测到的独立显存。`shared`、`estimated`、`unknown` 都必须明确说明边界。

Microsoft Basic Display、Remote Display、VMware、VirtualBox、Parallels、IDD 远程显示驱动等不能作为真实性能 GPU。

## 为什么不让 LLM 做硬件判断

LLM 可以帮助解释报告，但不能替代 scanner、parser、classifier、selector 和规则测试。硬件判断必须来自可审计代码和 fixtures，不允许把“看起来像”的 GPU 名称交给 LLM 猜测。

架构原则：别让 LLM 给错误硬件诊断写诗。

## 可信来源策略

来源风险等级：

- `winget`: low
- `microsoft_store`: low
- `official_url`: low 或 medium
- `github_release`: medium
- `pypi`: medium
- `npm`: medium
- `docker_official`: medium
- `manual`: medium
- `unknown`: blocked

如果 `source.trusted == false`，风险至少为 medium。`unknown` 来源必须 blocked。

## 命令审计策略

计划中允许出现少量命令预览，例如：

- `winget install`
- `winget uninstall`
- `python --version`
- `git --version`
- `node --version`
- `docker --version`
- `where`
- `ffmpeg -version`
- `ollama --version`

以下模式会被阻止：

- `Invoke-WebRequest | iex`
- `curl | powershell`
- `irm | iex`
- `iwr | iex`
- `Set-ExecutionPolicy Bypass`
- `Remove-Item -Recurse C:\`
- `reg add`
- `reg delete`
- 未审查的 `Start-Process *.exe`

命令字段只是计划文本。StackPilot v0.3 不执行这些命令。

## 安装前审查

在允许任何真实执行前，用户应审查：

- 应用来源是否可信。
- package id 是否匹配目标软件。
- 是否需要管理员权限。
- 是否可能修改 PATH、环境变量、驱动、服务或注册表。
- 验证命令是否清晰。
- 回滚命令是否存在。
- 是否存在 blocked 或 unknown source 步骤。

## 备份 / 快照计划

StackPilot 会生成备份 / 快照计划，建议记录：

- PATH 环境变量
- 用户级环境变量
- 系统级环境变量
- 已安装软件列表
- StackPilot 安装计划
- StackPilot dry-run 和执行日志
- 关键配置文件路径

当前版本只生成备份计划，不会创建真实系统还原点。

## 回滚限制

软件安装可能写入注册表、用户目录、缓存、驱动、服务或云同步目录。StackPilot 可以规划回滚步骤，但不能保证 100% 完全恢复到安装前状态。

## 为什么当前版本不自动安装

自动安装会把推荐工具变成系统修改工具。v0.3 的目标是先建立可审查、可测试、可导出的计划内核，让用户在执行前理解每一步的来源、风险、验证方式和回滚限制。

## 为什么不执行未知脚本

未知脚本可能修改系统、下载额外程序、隐藏执行逻辑或绕过用户审查。StackPilot 禁止下载即执行和危险 shell 管道；任何真实执行能力都必须保持这一边界。
