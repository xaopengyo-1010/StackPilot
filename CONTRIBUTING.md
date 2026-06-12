# Contributing to StackPilot

感谢参与 StackPilot。这个项目面向普通电脑用户，所有改动都应保持安全、可解释、可审计、可测试。

## 本地开发

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

常用手动验证：

```bash
python -m stackpilot list-templates
python -m stackpilot recommend --goal comfyui_starter
python -m stackpilot doctor --goal comfyui_starter
python -m stackpilot plan --goal comfyui_starter
```

## 新增模板

模板位于 `configs/templates/`，应用目录位于 `configs/app_catalog.json`。

新增模板时请确认：

- `template_id` 使用稳定英文 ID。
- 面向用户的 `display_name`、说明、风险和下一步建议使用中文。
- 模板引用的每个 `app_id` 都存在于 `app_catalog.json`。
- 不写自动下载、自动安装或修改系统设置的步骤。
- 为新模板补充测试。

## 新增 app_catalog 安装元数据

v0.3 计划系统需要应用目录提供可审查安装元数据。新增或修改应用时尽量补充：

- `winget_id`
- `official_url`
- `install_source`
- `verify_commands`
- `rollback_command`
- `requires_admin`
- `estimated_disk_mb`
- `risk_note`
- `notes`

如果无法确认可靠的 `winget_id`，请使用 `manual` 或 `official_url`，不要猜测可执行命令。未知来源必须保持 blocked 或需要人工确认。

## 新增安全策略

安全策略集中在 `src/stackpilot/security/` 和 `src/stackpilot/plans/policy.py`。新增策略时请补充测试，并确认：

- 不把危险命令放进可执行路径。
- unknown source 会 blocked。
- 缺少 rollback 会产生 warning。
- forbidden command pattern 会 blocked。
- 策略输出可以被审计报告解释。

## 新增安装计划测试

计划相关测试应覆盖：

- `InstallSource`、`InstallStep`、`InstallPlan` 序列化。
- source risk 分类。
- command policy。
- planner 从 `RecommendationResult` 生成步骤。
- Markdown/JSON renderer 不出现 `None`。
- dry-run executor 不调用 subprocess。
- CLI `plan` 生成完整文件。

## 禁止提交的改动

StackPilot 当前不接受以下改动：

- 默认执行真实安装。
- 下载软件或安装包。
- 静默运行安装器。
- 修改 PATH、环境变量、注册表或用户文件。
- 执行 `Invoke-WebRequest | iex`、`curl | powershell` 等危险管道。
- 执行未知来源脚本。
- 要求 API Key。
- 调用真实 LLM API。
- 上传本机数据。
- 宣称“绝对安全”或“100% 完美回滚”。

## 新增规则

规则集中在 `src/stackpilot/rules/engine.py`。新增规则时请输出 `RuleFinding`，并包含：

- `id`
- `level`: `info` / `warning` / `critical`
- `title`
- `message`
- `related_goal`
- `related_component`
- `evidence`

规则必须可以单独测试。不要把硬件判断写到 CLI、report renderer 或 scanner 中。

## 提交 Issue

提交 bug、模板请求或错误推荐时，请尽量提供：

- 系统版本
- CPU
- 内存
- 显卡和显存
- 磁盘剩余空间
- 选择的目标模板
- 实际输出
- 期望输出

不要提交包含隐私文件路径、账号、密钥或私人文档内容的报告。

## Pull Request

PR 请包含：

- 用户可见变化说明
- 修改的主要模块
- 新增或更新的测试
- 已运行的命令，例如 `python -m pytest`
