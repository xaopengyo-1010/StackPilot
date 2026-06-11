# Contributing to StackPilot

感谢参与 StackPilot。这个项目面向电脑小白，所有改动都应该保持安全、可解释、可测试。

## 本地开发

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

## 新增模板

模板位于 `configs/templates/`，应用目录位于 `configs/app_catalog.json`。

新增模板时请确认：

- `template_id` 使用稳定英文 ID。
- 面向用户的 `display_name`、说明、风险和下一步建议使用中文。
- 模板引用的每个 `app_id` 都存在于 `app_catalog.json`。
- 不写自动下载、自动安装或修改系统设置的步骤。
- 为新模板补充测试。

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

## 不接受的改动

StackPilot 当前版本不接受会自动下载软件、自动安装软件、修改系统设置、要求 API Key、调用真实 LLM API 或上传本机数据的逻辑。
