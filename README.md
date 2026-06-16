<div align="center">
  <img src="assets/branding/stackpilot-logo.svg" alt="StackPilot logo" width="140" />
  <h1>StackPilot</h1>
  <p><strong>不知道新电脑该装什么？先让 StackPilot 看看你的电脑。</strong></p>
  <p>本地优先的电脑环境蓝图生成器：先扫描公开硬件和已有环境，再生成应用推荐、风险提示和可审查安装计划。</p>
  <p>
    <img src="https://img.shields.io/github/stars/xaopengyo-1010/StackPilot?style=flat&logo=github" alt="GitHub Repo stars" />
    <img src="https://img.shields.io/badge/License-MIT-blue" alt="License" />
    <img src="https://img.shields.io/badge/Python-%3E%3D%203.11-3776AB?logo=python&logoColor=white" alt="Python >= 3.11" />
    <img src="https://img.shields.io/badge/Windows-supported-0078D4?logo=windows&logoColor=white" alt="Windows supported" />
    <img src="https://img.shields.io/badge/Alpha_CLI-v0.4.0--alpha-7c3aed" alt="Alpha CLI v0.4.0 alpha" />
    <img src="https://img.shields.io/badge/local--first-report_on_your_machine-0f766e" alt="Local-first" />
    <img src="https://img.shields.io/badge/no_auto_install-human_review-0f766e" alt="No auto install" />
    <img src="https://img.shields.io/badge/output-Markdown%20%2F%20JSON-334155" alt="Markdown / JSON output" />
    <img src="https://img.shields.io/badge/GPU-aware-f97316" alt="GPU-aware" />
  </p>
  <p><strong>先看清楚，再决定怎么装。</strong></p>
  <p><sub>当前是早期命令行版本：不自动下载，不自动安装，不偷偷修改系统。</sub></p>
</div>

<p align="center">
  <img src="assets/branding/stackpilot-hero-banner.svg" alt="StackPilot 顶部品牌横幅" />
</p>

很多电脑环境问题，不是从“该装哪个软件”开始的，而是从“不知道这台电脑现在是什么状态”开始的。

我做 StackPilot，是因为之前给笔记本整理环境时发现：电脑对不太会折腾的人并不友好。哪怕只是装几个常用软件，也可能要找官网、看教程、分版本、选路径，还要担心广告、弹窗、捆绑安装和 C 盘空间。

StackPilot 想做的不是另一个软件管家，也不是一键帮你乱装东西。它现在更像一份本地电脑环境体检 + 推荐清单：先读取本机公开硬件和环境信息，再根据你的目标生成推荐报告、风险提示和可审查安装计划。

> [!NOTE]
> StackPilot 当前还是 Alpha CLI，也就是早期命令行版本。它更适合愿意用命令行测试的用户；真正面向纯小白的图形界面会作为后续方向探索。

## 先说清楚：它到底干什么？

StackPilot 现在主要做四件事：

1. 扫描：读取当前电脑的系统、CPU、内存、磁盘、GPU 和常用开发环境；
2. 推荐：根据目标模板生成应用推荐和风险提示；
3. 计划：输出可人工审查的安装计划；
4. 审计：标记不确定信息，比如虚拟显卡、共享显存、未知显存。

它不会自动安装软件，也不会替你修改系统。当前版本更像一个“先看清楚，再决定怎么装”的本地 CLI 工具。

### 几个英文词先翻译成人话

| 术语           | 人话解释                                             |
| -------------- | ---------------------------------------------------- |
| Local-first    | 本地优先，优先在你的电脑上运行，不把报告上传到云端。 |
| dry-run        | 只预览会做什么，不实际执行。                         |
| Auditable Plan | 生成可以人工检查的安装计划。                         |
| GPU-aware      | 会尽量识别核显、独显、虚拟显卡和不确定显卡信息。     |
| Alpha CLI      | 早期命令行版本，还不是图形界面软件。                 |

## StackPilot 和传统方案有什么不同？

| 方案           | 优点                         | 可能遇到的问题                                               | StackPilot 的选择                          |
| -------------- | ---------------------------- | ------------------------------------------------------------ | ------------------------------------------ |
| 传统软件管家   | 操作简单，上手快。           | 可能有广告、弹窗、捆绑安装，推荐逻辑也不一定透明。           | 不做捆绑安装，先输出可审查计划。           |
| winget / Scoop | 官方或开源，适合熟练用户。   | 对小白有命令行门槛，也不会主动判断这台电脑适合什么。         | 先扫描电脑，再给推荐和计划。               |
| 跟教程手动装   | 灵活，能按自己的需求调整。   | 很多教程默认你已经懂 Python、CUDA、Docker、WSL、驱动和路径。 | 把硬件状态、风险和步骤写清楚。             |
| StackPilot     | 本地扫描、透明推荐、可审查。 | 当前还是 Alpha CLI，暂时不是成熟 GUI 软件。                  | 先保证透明和可审查，再逐步探索自动化体验。 |

## 适合谁？

StackPilot 现在适合：

- 想整理新电脑环境，但不知道该装什么的人；
- 想体验 AI 绘图、本地 LLM、AI 编程工具的人；
- 想检查电脑有没有 Python、Git、Docker、WSL 等环境的人；
- 愿意用命令行测试早期版本的开发者、学生或折腾玩家。

暂时不太适合：

- 完全不想碰命令行的人；
- 想要一键自动安装所有软件的人；
- 想要成熟 GUI 软件管家的用户。

这些会是后续 GUI / 桌面版本的探索方向，但当前版本先保证报告、风险提示和计划能被看见、能被审查。

> [!TIP]
> 第一次测试可以直接跑 `python -m stackpilot doctor --goal comfyui_starter`。这条命令只生成报告和计划，不会安装 ComfyUI 或其它软件。

**15 秒看看它怎么跑：**

（当前录屏展示的是早期 CLI 流程，新版演示会后续替换。）

https://github.com/user-attachments/assets/5a50b36c-ec9f-494f-af9f-0c6ae95452f6

<a id="quickstart"></a>

<p align="center">
  <img src="assets/branding/readme-section-quickstart.svg" alt="快速开始 · Command Deck" />
</p>

### 运行前准备

| 需要什么              | 用来做什么          | 怎么检查                  |
| --------------------- | ------------------- | ------------------------- |
| Python >= 3.11        | 运行 StackPilot CLI | `python --version`        |
| pip                   | 安装本地项目        | `python -m pip --version` |
| Git                   | 克隆仓库            | `git --version`           |
| PowerShell / Terminal | 执行命令            | Windows 推荐 PowerShell   |

### 如果你还没有 Python

Windows 用户可以从 [Python 官网](https://www.python.org/downloads/) 安装 Python。安装时建议勾选 `Add python.exe to PATH`，安装完成后重新打开 PowerShell。

检查 Python 和 pip：

```powershell
python --version
python -m pip --version
```

如果 `python` 不可用，可以试试：

```powershell
py --version
py -m pip --version
```

如果你的电脑只能用 `py`，后面的 `python -m ...` 可以替换成 `py -m ...`。

### 第一次怎么跑？

Windows PowerShell：

```powershell
# 1. 克隆项目
git clone https://github.com/xaopengyo-1010/StackPilot.git

# 2. 进入项目目录
cd StackPilot

# 3. 安装当前项目到本地 Python 环境
python -m pip install -e .

# 4. 检测当前电脑配置
python -m stackpilot scan

# 5. 一步生成推荐报告
python -m stackpilot doctor --goal comfyui_starter
```

macOS / Linux：

```bash
git clone https://github.com/xaopengyo-1010/StackPilot.git
cd StackPilot
python3 -m pip install -e .
python3 -m stackpilot scan
python3 -m stackpilot doctor --goal comfyui_starter
```

### 命令是什么意思？

| 命令                                                    | 作用                           |
| ------------------------------------------------------- | ------------------------------ |
| `python -m stackpilot scan`                             | 检测当前电脑配置和环境。       |
| `python -m stackpilot list-templates`                   | 查看支持的目标模板。           |
| `python -m stackpilot recommend --goal comfyui_starter` | 根据目标生成推荐结果。         |
| `python -m stackpilot plan --goal comfyui_starter`      | 生成可审查安装计划。           |
| `python -m stackpilot doctor --goal comfyui_starter`    | 一步完成检测、推荐和报告生成。 |

### 第一次建议用哪个 goal？

如果只是想快速测试，我建议先用：

```powershell
python -m stackpilot doctor --goal comfyui_starter
```

`comfyui_starter` 比较适合首次测试，因为它能明显看出硬件 / GPU 判断、推荐报告和风险提示。如果你不是 AI 绘图用户，也可以试：

- `coding_starter`
- `vibe_coding`
- `local_llm`

这些命令都只是生成报告和计划，不会自动安装对应工具。

<a id="why"></a>

<p align="center">
  <img src="assets/branding/readme-section-why.svg" alt="为什么做 StackPilot？ · Why it exists" />
</p>

我最开始想做 StackPilot，是因为整理笔记本环境时被装机流程折腾过。

对熟悉电脑的人来说，装软件可能只是几条命令。对小白来说，问题会变成一串连锁反应：Python 版本要选哪个、CUDA 能不能装、Docker 和 WSL 是什么、驱动要不要更新、安装路径放哪里、C 盘空间够不够。

一些软件管家确实方便，但也可能遇到广告、弹窗、捆绑安装，或者推荐逻辑不透明的问题。去看教程又常常默认你已经懂 Python、Node、CUDA、Docker、WSL、驱动和路径这些东西。

所以 StackPilot 先不急着做自动安装。自动执行之前，至少应该先让每一步能被看见。

- 有些电脑没有独显，却照着高配 AI 绘图教程折腾；
- 有些工具会把缓存、模型或依赖塞进 C 盘；
- AI 绘图、本地模型、编程环境、游戏工具、内容创作工具混在一起时，很容易越装越乱；
- 小白真正缺的不是又一个安装脚本，而是一份先看清电脑状态后的推荐和计划。

StackPilot 当前强调的是透明、可审查、无广告、无捆绑、不偷偷改系统。它先看清电脑状态，再告诉你当前机器更适合装什么、哪里有风险、哪些步骤需要人工确认。

<a id="workflow"></a>

<p align="center">
  <img src="assets/branding/readme-section-workflow.svg" alt="工作流程 · Scan Recommend Plan Audit" />
</p>

![StackPilot 任务控制台](assets/branding/stackpilot-mission-control.svg)

```text
扫描电脑 → 匹配目标模板 → 生成推荐报告 → 输出可审查安装计划 → 标记风险和不确定信息
```

<a id="preview"></a>

<p align="center">
  <img src="assets/branding/readme-section-preview.svg" alt="真实截图预览 · Real CLI output" />
</p>

| 硬件扫描                                                              | 推荐报告                                                                 | 可审查安装计划                                                              |
| --------------------------------------------------------------------- | ------------------------------------------------------------------------ | --------------------------------------------------------------------------- |
| ![StackPilot GPU 检测扫描](assets/screenshots/scan-gpu-detection.png) | ![StackPilot ComfyUI 推荐报告](assets/screenshots/recommend-comfyui.png) | ![StackPilot 生成的安装计划](assets/screenshots/install-plan-generated.png) |
| 读取真实本机环境。                                                    | 生成推荐和风险提示。                                                     | 输出可人工审查的计划文本。                                                  |

<a id="capabilities"></a>

<p align="center">
  <img src="assets/branding/readme-section-capabilities.svg" alt="当前能做什么？ · Capability Matrix" />
</p>

| 阶段      | 能力           | StackPilot 做什么                                                 |
| --------- | -------------- | ----------------------------------------------------------------- |
| Scan      | 硬件与环境扫描 | 读取系统、CPU、内存、磁盘、GPU、Python、Git、Docker、WSL 等状态。 |
| Recommend | 规则推荐       | 基于目标模板生成应用推荐、适配评分和风险提示。                    |
| Plan      | 可审查安装计划 | 输出安装计划、审计报告、备份 / 回滚计划和 dry-run 预览。          |
| Audit     | 风险与不确定性 | 标记虚拟显卡、共享显存、未知显存等不确定信息。                    |

<a id="release"></a>

<p align="center">
  <img src="assets/branding/readme-section-release.svg" alt="v0.4 更新 · GPU Radar Upgrade" />
</p>

### v0.4.0-alpha · GPU Radar Upgrade

v0.4 增强了 GPU 检测链路，可以区分核显、独显、虚拟显卡和未知显卡。

| Upgrade              | Meaning                                   |
| -------------------- | ----------------------------------------- |
| GPU list             | 保留完整 GPU 列表，避免只看单一显卡名称。 |
| primary_gpu          | 标记主要性能判断 GPU。                    |
| gpu_selection_reason | 解释为什么这样判断。                      |
| vram_confidence      | 标记显存可信度。                          |
| shared / unknown     | 不把共享内存伪装成独立显存。              |

它不会承诺显存识别完全准确。如果无法确认显存来源，就明确告诉你不确定，而不是假装知道。

![GPU 检测预览](assets/screenshots/scan-gpu-detection.png)

## Roadmap

- [x] v0.4：GPU 检测增强，区分核显、独显、虚拟显卡和未知显卡。
- [ ] v0.5：收集真实机器反馈，修正推荐规则和 README 上手路径。
- [ ] v0.6：扩充软件目录和模板说明。
- [ ] v0.7：生成更清晰的可审查安装脚本草稿。
- [ ] v1.0：稳定 CLI 版本。
- [ ] v1.x：探索图形界面，让不熟悉命令行的用户也能使用。
- [ ] README_EN.md：补充英文 README，方便海外开发者理解项目。

<a id="templates"></a>

<p align="center">
  <img src="assets/branding/readme-section-templates.svg" alt="支持的模板 · Template Signals" />
</p>

| Template              | 适合谁             |
| --------------------- | ------------------ |
| `coding_starter`      | 写代码入门         |
| `vibe_coding`         | AI 辅助写代码      |
| `ai_beginner`         | AI 入门体验        |
| `comfyui_starter`     | AI 绘图入门        |
| `local_llm`           | 本地大模型环境规划 |
| `gaming_setup`        | 游戏玩家常用软件   |
| `creator_setup`       | 视频 / 内容创作    |
| `office_productivity` | 办公生产力         |

<a id="outputs"></a>

<p align="center">
  <img src="assets/branding/readme-section-outputs.svg" alt="跑完以后看哪里？ · Output Files" />
</p>

如果你执行的是 `doctor`，推荐报告默认写到：

```text
outputs/reports/stackpilot-report.md
outputs/reports/stackpilot-report.json
```

如果你执行的是 `plan`，安装计划和审计材料默认写到：

```text
outputs/plans/install-plan.md
outputs/plans/install-plan.json
outputs/plans/install-audit.md
outputs/plans/install-audit.json
outputs/plans/snapshot-plan.md
outputs/plans/snapshot-plan.json
outputs/plans/rollback-plan.md
outputs/plans/rollback-plan.json
outputs/plans/dry-run.md
outputs/plans/dry-run.json
```

这些文件是给你打开阅读和审查的。StackPilot 当前不会自动执行里面的安装命令。

<a id="safety"></a>

<p align="center">
  <img src="assets/branding/readme-section-safety.svg" alt="安全边界 · No auto install Human review" />
</p>

我现在没有急着做自动安装，原因很简单：自动执行之前，先要让每一步能被看见。

StackPilot 当前只生成报告、计划和 dry-run 预览，不会自动安装软件，也不会直接修改系统。这样做可能慢一点，但更适合早期版本，也更适合让用户和贡献者一起检查推荐逻辑。

> [!IMPORTANT]
> StackPilot 当前只生成报告、风险提示、dry-run 预览和可审查安装计划。它不会自动下载软件，不会执行安装命令，也不会直接修改你的系统。

> [!WARNING]
> README 里的命令用于运行 StackPilot 本身和生成报告，不代表 StackPilot 会替你安装目标软件。计划里的安装步骤需要你自己阅读、确认和执行。

| 当前版本会做            | 当前版本不会做                     |
| ----------------------- | ---------------------------------- |
| 生成推荐报告            | 自动安装软件                       |
| 生成可审查安装计划      | 自动下载安装包                     |
| 生成安装审计说明        | 执行 `winget install`              |
| 生成 dry-run 预览       | 执行安装脚本或 PowerShell 安装脚本 |
| 生成备份 / 回滚计划文档 | 修改 PATH / 环境变量 / 注册表      |
| 标记风险和不确定信息    | 自动创建真实系统还原点             |
| 保持本地 CLI 工作流     | 自动回滚系统或删除用户文件         |
| 输出 Markdown / JSON    | 调用真实 LLM API                   |
| 给出可人工审查的计划    | 承诺绝对安全或自动回滚             |

StackPilot 的目标是降低风险，而不是假装风险不存在。如果某一步不确定，就应该把不确定写出来，而不是包装成“智能推荐”。

<a id="faq"></a>

<p align="center">
  <img src="assets/branding/readme-section-faq.svg" alt="常见问题 · FAQ" />
</p>

### 这个 StackPilot 是做什么方向的？

这个项目面向个人电脑环境检测、应用推荐和可审查安装计划，不是服务器运维平台，也不是代码脚手架工具。

### StackPilot 会自动安装软件吗？

不会。当前版本只生成报告、计划和 dry-run 预览，计划里的命令需要你自己阅读和判断。

### 没有独显还能用吗？

可以。StackPilot 会尽量区分核显、独显、虚拟显卡和未知显卡。如果显存来源不确定，它会标记不确定，而不是假装知道。

### 推荐结果一定正确吗？

不保证。StackPilot 现在是早期版本，推荐逻辑还需要更多真实机器反馈。你可以把不合理的推荐、识别错误或文档看不懂的地方提到 Issue。

<a id="dev"></a>

<p align="center">
  <img src="assets/branding/readme-section-dev.svg" alt="开发 · Local Dev Loop" />
</p>

安装开发依赖并运行测试：

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

常用验证命令：

```bash
python -m stackpilot scan
python -m stackpilot list-templates
python -m stackpilot recommend --goal comfyui_starter
python -m stackpilot doctor --goal comfyui_starter
python -m stackpilot plan --goal comfyui_starter
```

<a id="feedback"></a>

<p align="center">
  <img src="assets/branding/readme-section-feedback.svg" alt="反馈与贡献 · Feedback Signals" />
</p>

StackPilot 还是早期项目，现在最需要真实机器测试。尤其欢迎你拿自己的电脑跑一下，看看检测结果、推荐结果和命令输出是否正常。

| 反馈类型 | 什么最有帮助                                 |
| -------- | -------------------------------------------- |
| GPU 识别 | 核显、独显、虚拟显卡、未知显卡是否识别合理。 |
| 环境检测 | Python / Git / Docker / WSL 检测是否准确。   |
| 推荐结果 | 推荐是否合理，风险解释是否能看懂。           |
| 安装计划 | 步骤、来源、风险和回滚信息是否需要补充。     |
| README   | 第一次看是否能理解，命令是否能跑起来。       |
| 新模板   | 你希望增加的目标、软件目录或规则建议。       |

欢迎提交 Issue，把机器信息、命令输出、截图或你看不懂的地方说清楚就很有帮助。

如果你觉得这个方向有用，欢迎点一个 Star。Star 不只是数字，它会让我知道这个项目值得继续做下去。

## 许可证

StackPilot 使用 [MIT License](LICENSE) 发布。
