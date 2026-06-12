# GitHub 项目一句话简介

StackPilot 是一个本地优先、开源透明的电脑环境推荐与部署计划助手：先扫描公开硬件和环境信息，再生成应用推荐、风险提示、可审查安装计划、审计报告和 dry-run 预览。

这段简介适合放在外部测试邀请、项目简介或反馈帖开头。

短版：

```text
StackPilot: 本地优先的电脑环境推荐与可审查安装计划助手，当前版本只生成报告和 dry-run 计划，不自动安装软件。
```

v0.4 重点：

- GPU Detection Hardening；
- 区分核显、独显、虚拟显卡和未知显卡；
- 标记 `primary_gpu`、`gpu_selection_reason` 和 `vram_confidence`；
- 保持 dry-run first，不执行真实安装。
