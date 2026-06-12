# GPU detection example

## 相关命令

```bash
python -m stackpilot scan
python -m stackpilot recommend --goal comfyui_starter
python -m stackpilot plan --goal comfyui_starter
```

## 当前真实行为摘录

当前开发机检测到多个虚拟显示设备和一个 AMD 核显。StackPilot 没有把虚拟显示设备当作主要性能 GPU，而是选择了 AMD Radeon 780M Graphics：

```text
检测到的 GPU：
- AskLinkIddDriver Device（虚拟显卡 / 未能确认显存 / 显存置信度：unknown）
- OrayIddDriver Device（虚拟显卡 / 未能确认显存 / 显存置信度：unknown）
- MuMu Virtual Display Adapter（虚拟显卡 / 未能确认显存 / 显存置信度：unknown）
- AMD Radeon 780M Graphics（核显 / 0.5 GB 共享内存，不等于独立显存 / 显存置信度：shared）

主要性能判断 GPU：AMD Radeon 780M Graphics
GPU 选择原因：未检测到独立显卡，当前主要性能判断基于集成显卡 AMD Radeon 780M Graphics。
```

在 `comfyui_starter` 推荐里，规则层给出保守提示：

```text
[提醒] 当前主要 GPU 是核显：
当前主要性能判断基于集成显卡和共享内存，不推荐用于较重的本地 AI 绘图工作流。
```

## StackPilot v0.4 期望保持的判断

- 虚拟显卡、远程显示设备和基础显示设备不能作为主要性能 GPU。
- Intel / AMD 核显可以作为 primary GPU，但要说明共享内存不是独立显存。
- NVIDIA 独显可以触发 ComfyUI 的独显提示，但仍要看显存容量和置信度。
- 未知 GPU 名称要保守处理，不能猜测成高性能独显。
- `vram_confidence` 必须显示为 `detected`、`shared`、`estimated` 或 `unknown` 之一。

## 适合反馈什么

- 你的电脑上 GPU 列表是否完整。
- 核显 / 独显 / 虚拟显卡 / 未知显卡分类是否正确。
- 如果有多块 GPU，primary GPU 是否选对。
- 显存是否被标为正确的置信度。
- 推荐结果是否因为 GPU 判断而变得不合理。

提交反馈时可以附上 `python -m stackpilot scan` 的输出，并打码用户名、路径、序列号和任何私人信息。
