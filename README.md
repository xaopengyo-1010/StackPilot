<div align="center">
  <img src="assets/LOGO1.png" alt="StackPilot Logo" width="180" />
</div>

<div align="center">
  
# StackPilot

</div>

<div align="center">

给小白用的电脑应用推荐助手。

不知道新电脑该装什么？告诉 StackPilot 你想做什么，它会根据你的电脑配置，推荐适合的应用组合、配置建议和注意事项。

</div>



## 🚀 简介

很多人拿到新电脑后，不知道该装什么软件，也不知道自己的电脑适合做什么。

StackPilot 会检测你的电脑配置，并根据你的使用目标生成应用推荐报告。

你可以告诉 StackPilot 你想：

* 写代码；
* 使用 AI 辅助写代码；
* 体验 AI 工具；
* 运行本地大模型；
* 办公生产力
* 做办公生产力
* 玩游戏；
* 做视频/内容创作。

StackPilot 会告诉你：

* 推荐安装哪些应用；
* 哪些是必装，哪些是可选；
* 为什么推荐这些应用；
* 你的电脑是否适合这个目标；
* 有哪些配置建议；
* 有哪些坑不要踩。

---

## ✨ 特点

- **根据电脑配置推荐**：读取本地公开系统信息，例如系统版本、CPU、内存、显卡、硬盘空间，以及 Python、Node.js、Git、Docker、WSL 等常用环境状态。

- **面向小白**：不用先懂依赖、Vibe Coding、LLM、Agent、DLSS 这些概念。你只需要选择自己想做什么，StackPilot 会给你一份推荐报告。

- **多种使用场景**：支持办公生产力、Coding、AI、游戏、内容创作等模板。

- **只生成报告**：当前版本不会自动下载软件，不会自动安装软件，也不会修改系统设置，只生成一份本地推荐报告。

- **开源透明**：项目代码开源，模板和推荐逻辑都可以查看、修改和贡献。

---

## 🧩 模板示例

| 模板             | 适合谁                          |
| -------------- | ---------------------------- |
| 写代码入门          | 想搭建基础编程环境                    |
| AI 辅助写代码       | 想使用 Cursor、Codex、Copilot 等工具 |
| AI 入门体验        | 想体验 AI 工具，但不知道电脑适不适合         |
| AI 绘图入门        | 想搭建 ComfyUI 环境               |
| 本地大模型          | 想运行 Ollama、LM Studio 等本地模型工具 |
| 游戏玩家常用软件       | 想准备游戏平台、驱动和性能监控工具            |
| 视频/内容创作        | 想做录屏、剪辑、音频和视频创作              |
| 办公生产力 | 想准备浏览器、文档、笔记、截图、PDF 等基础工具 |

---

## 📸 示例

### 🖥️ 检测电脑配置

### 📦 推荐应用组合

### 📄 生成推荐报告

### 🎬 演示 GIF

---

## 📥 下载 / 安装

### 从源码运行

```bash
git clone https://github.com/xaopengyo-1010/StackPilot.git
cd StackPilot
pip install -e .
```

---

## 📘 用户指南

### 检测电脑配置

```bash
python -m stackpilot scan
```

### 查看支持的模板

```bash
python -m stackpilot list-templates
```

### 根据目标生成推荐

```bash
python -m stackpilot recommend --goal coding_starter
python -m stackpilot recommend --goal comfyui_starter
python -m stackpilot recommend --goal minecraft_realism
```

### 生成报告

```bash
python -m stackpilot report --goal ai_beginner
```

### 一步完成检测、推荐和报告

```bash
python -m stackpilot doctor --goal vibe_coding
```

---

## 📋 报告内容

StackPilot 生成的报告包括：

* 当前电脑配置摘要；
* 选择的使用目标；
* 适合程度评分；
* 推荐应用组合；
* 每个应用的推荐原因；
* 配置建议；
* 风险提示；
* 当前电脑不推荐做的事情；
* 下一步操作建议。

---

## 🗺️ Roadmap（当前版本：v0.1 Alpha）

* [x] v0.1 本地电脑配置检测
* [x] v0.1 应用推荐模板
* [x] v0.1 Markdown / JSON 报告生成
* [ ] v0.2 生成可审查的安装脚本
* [ ] v0.3 安装后环境体检
* [ ] v0.4 自定义模板
* [ ] v0.5 Minecraft / ComfyUI / Vibe Coding 专项模板增强
* [ ] v1.0 社区模板分享

---

## 🛠️ 开发

### 安装开发依赖

```bash
git clone https://github.com/xaopengyo-1010/StackPilot.git
cd StackPilot
pip install -e .
```

### 运行测试

```bash
pytest
```

### 项目结构

```text
configs/              # 模板和应用目录
src/stackpilot/       # StackPilot 核心代码
outputs/reports/      # 生成的报告
tests/                # 测试
assets/               # Logo、截图、GIF、视频等资源
```

---

## 🤝 反馈与贡献

欢迎提交 Issue 或 Pull Request。

你可以帮助我们：

* 增加新的应用模板；
* 改进推荐逻辑；
* 修复电脑配置检测问题；
* 提供更好的配置建议；
* 改进 README、截图和文档；
* 提供真实电脑配置测试结果。

---

## ⭐ 支持项目

如果你觉得 StackPilot 有用，欢迎点一个 Star ⭐

这会帮助项目获得更多反馈和改进动力。

---

## 📄 版权说明

StackPilot 使用 MIT License 开源。

Logo、截图、演示图片等资源如果来自 AI 生成或第三方素材，应在这里注明来源。
