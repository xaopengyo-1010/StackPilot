# Recommend ComfyUI example

## 命令

```bash
python -m stackpilot recommend --goal comfyui_starter
```

## 当前真实输出摘录

```text
推荐结果：AI 绘图入门

适配度评分：60 / 100

推荐应用：
- Git（必装）：用于下载和管理开源 AI 绘图项目。
- Python（必装）：运行 ComfyUI 和相关 Python 工具。
- ComfyUI（必装）：本地 AI 图像生成工作流核心。
- FFmpeg（可选）：处理图片序列、视频和部分节点依赖时有用。
- NVIDIA App（可选）：NVIDIA 显卡用户可用于驱动和设置管理。 未检测到 NVIDIA 显卡，因此这个项目可以跳过。
- CUDA/PyTorch 兼容提醒（可选）：用于提醒 CUDA/PyTorch 版本兼容关系，不自动安装。 未检测到 NVIDIA 显卡，因此不要按 CUDA 必装路径处理。

规则判断与风险提示：
- [提醒] 模板风险提示：低显存设备不适合运行重型图像生成工作流。
- [提醒] 模板风险提示：ComfyUI 依赖较多，新手容易遇到节点缺失问题。
- [提醒] 模板风险提示：StackPilot 当前版本只生成推荐报告，不会自动安装 ComfyUI。
- [提醒] 当前主要 GPU 是核显：当前主要性能判断基于集成显卡和共享内存，不推荐用于较重的本地 AI 绘图工作流。
```

## 输出重点

- `适配度评分` 是规则判断后的参考分，不是安装成功率。
- 推荐应用会区分 `必装` 和 `可选`，但当前版本只输出建议，不会安装。
- 没有 NVIDIA 独显时，NVIDIA App 和 CUDA 路径会被标记为可跳过或不要按必装路径处理。
- 核显设备会收到较保守的本地 AI 绘图提示。

## 适合反馈什么

- 对当前硬件的 ComfyUI 建议是否过于激进或过于保守。
- 没有 NVIDIA 显卡时，CUDA / NVIDIA 文案是否清楚。
- 风险提示是否能让普通用户理解限制。
- `comfyui_starter` 是否缺少必要的人工审查提醒。
