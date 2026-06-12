# StackPilot examples

这些示例来自当前代码的真实 CLI 行为，用来帮助外部测试用户快速理解 StackPilot v0.4 的输出边界。

当前版本的重点不是自动安装软件，而是：

- 扫描本机公开系统信息；
- 基于目标模板生成推荐和风险提示；
- 生成可审查安装计划、审计报告、备份 / 回滚计划和 dry-run 预览；
- 对 GPU 做更保守的分类，区分核显、独显、虚拟显卡和未知显卡。

## 示例索引

- [scan-example.md](scan-example.md)：`python -m stackpilot scan` 的硬件扫描输出重点。
- [recommend-comfyui-example.md](recommend-comfyui-example.md)：`comfyui_starter` 推荐结果和规则提示。
- [install-plan-example.md](install-plan-example.md)：可审查安装计划、审计报告和 dry-run 预览。
- [gpu-detection-example.md](gpu-detection-example.md)：GPU 分类、primary GPU 和显存置信度的反馈方式。

## 反馈时请注意

请不要粘贴隐私信息。提交反馈前可以打码：

- 用户名和个人目录；
- 私有项目路径；
- 设备序列号；
- 账号、密钥、Token；
- 私人文档内容。

StackPilot 当前版本不会自动下载、自动安装或修改系统设置。
