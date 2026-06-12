# Install plan example

## 命令

```bash
python -m stackpilot plan --goal comfyui_starter
```

## 当前真实 CLI 输出摘录

```text
正在检测电脑配置...
正在生成推荐：AI 绘图入门...
正在生成可审查安装计划...
安装计划已生成：
D:\StackPilot\outputs\plans\install-plan.md
D:\StackPilot\outputs\plans\install-plan.json

审计报告已生成：
D:\StackPilot\outputs\plans\install-audit.md
D:\StackPilot\outputs\plans\install-audit.json

备份、回滚和 dry-run 预览已生成：
D:\StackPilot\outputs\plans\snapshot-plan.md
D:\StackPilot\outputs\plans\rollback-plan.md
D:\StackPilot\outputs\plans\dry-run.md

当前版本只生成计划，不会自动安装软件或修改系统设置。
```

## 安装计划摘录

```text
## 总览

- 目标: `comfyui_starter` / AI 绘图入门
- 仅 dry-run: `是`

当前版本只生成可审查安装计划，不会自动安装软件或修改系统设置。

## 安装步骤

### install-1-git - Git

- 来源: winget (`winget`) / Git
- 命令预览: `winget install --id Git.Git --source winget`
- 回滚命令预览: `winget uninstall Git.Git`
- 验证命令: git --version

### install-3-comfyui - ComfyUI

- 操作: 人工处理 (`manual`)
- 命令预览: `人工: 请审查 ComfyUI 的官方说明；当前不会生成自动安装命令。`
- 风险等级: `medium`
- 回滚命令预览: `未检测到`
```

## Dry-run 摘录

```text
install-1-git / Git：would_run=True, skipped=False, risk=low
install-3-comfyui / ComfyUI：would_run=False, skipped=True, skip_reason=需要人工审查, risk=medium
```

## 输出重点

- `plan` 会写入 `outputs/plans/`，这些文件是生成物，不应该提交。
- `winget install` 等命令只是计划文本和 dry-run 预览，不会被 StackPilot 执行。
- `manual` 步骤表示需要用户自己查看官方文档并人工判断。
- 审计报告会列出缺少回滚信息、medium/high 风险和需要人工确认的步骤。

## 适合反馈什么

- 安装来源和 package id 是否可信、准确。
- 风险等级是否合理。
- 回滚命令是否缺失或不准确。
- dry-run 的 `would_run` / `skipped` 是否符合预期。
