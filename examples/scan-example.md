# Scan example

## 命令

```bash
python -m stackpilot scan
```

## 当前真实输出摘录

以下摘录来自当前开发机运行结果：

```text
电脑配置摘要

系统             Windows 10.0.26200
架构             AMD64
平台类型         windows
默认安装后端     winget
CPU 核心数       16
内存             31.26 GB
检测到的 GPU     - AskLinkIddDriver Device（虚拟显卡 / 未能确认显存 / 显存置信度：unknown）
                 - OrayIddDriver Device（虚拟显卡 / 未能确认显存 / 显存置信度：unknown）
                 - MuMu Virtual Display Adapter（虚拟显卡 / 未能确认显存 / 显存置信度：unknown）
                 - AMD Radeon 780M Graphics（核显 / 0.5 GB 共享内存，不等于独立显存 / 显存置信度：shared）
主要性能判断 GPU AMD Radeon 780M Graphics
GPU 选择原因     未检测到独立显卡，当前主要性能判断基于集成显卡 AMD Radeon 780M Graphics。
Python           3.14.0
Node.js          v24.11.0
Git              git version 2.54.0.windows.1
Docker           未检测到
NVIDIA 驱动      未检测到
```

## 输出重点

- `检测到的 GPU` 会列出所有识别到的显示设备，不会把虚拟显卡当成主要性能 GPU。
- `主要性能判断 GPU` 是 StackPilot 用于推荐判断的 GPU。
- `显存置信度` 会说明显存值是检测到、共享、估算还是未知。
- `默认安装后端` 只是平台判断，不表示 StackPilot 会执行安装。

## 适合反馈什么

- GPU 名称是否识别正确。
- 核显、独显、虚拟显卡是否分类正确。
- 共享内存是否被误写成独立显存。
- 主要性能判断 GPU 是否选错。
- 系统、Python、Node.js、Git、Docker、WSL 等工具状态是否明显不准。
