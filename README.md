# StackPilot (v0.6-Alpha)

Windows 本地硬件检测与环境配置规划工具。当前版本为核心数据解耦版（Core Data-Driven Edition）。

## 项目核心声明

1. **环境依赖**：当前版本未打包，必须在本地配置 Python 3.11+ 环境运行。
2. **功能边界**：本工具当前仅执行本地硬件拓扑扫描、已有依赖检索，并对比本地规则输出规划报告。**当前版本不执行、亦不包含任何实际的软件下载与自动安装逻辑。**
3. **安全保证**：全离线运行，无任何网络请求，不上传数据，不修改系统环境变量。

## 快速开始

### 1. 源码部署

确保你的电脑已安装 Git 和 Python 3.11+。打开 PowerShell 执行以下命令：

```powershell
# 克隆仓库
git clone [https://github.com/xaopengyo-1010/StackPilot.git](https://github.com/xaopengyo-1010/StackPilot.git)
cd StackPilot

# 创建并激活虚拟环境
python -m venv venv
.\venv\Scripts\activate

# 以本地可编辑模式安装
pip install -e .

```

### 2. 运行扫描与规划

执行以下命令，核心引擎将扫描本机配置，并输出标准结构化数据：

```powershell
# 执行流水线，获取纯数据化架构报告（JSON）
python src/stackpilot/main.py

```

> **注意（v0.6 变更）**：当前版本已完成表现层解耦。运行主入口将不再向控制台打印任何 Rich 彩色文本或 Markdown 渲染，而是直接输出标准化的数据结构（包含 `hardware_summary`, `scores`, `risk_alerts`, `recommendations`），为下阶段的 TUI（终端菜单界面）提供完全解耦的数据桩。

### 3. 单元测试验证

本地配置了完备的断言机制，执行以下命令运行 96 项数据契约测试：

```powershell
python -m pytest

```

## 内部测试重点（Bug 反馈）

当前底层扫描引擎正在全力优化针对复杂 Windows 环境的错误处理与健全性。如果参与内部测试，请重点协助验证以下边界场景：

1. **低权限/非管理员运行**：在非管理员终端运行程序，观察程序是否能稳定降级（预期表现：捕捉 PermissionError，在报告中记录相关项为可用性受限，但程序绝不发生静默闪退或崩溃，错误元数据将封装于 `risk_alerts` 中）。
2. **多显卡拓扑识别**：在同时存在核显、独立显卡（或多块独立显卡）的机器上运行，核对返回数据中的显存大小与分级标签（`detected/estimated/shared/unknown`）是否清洗准确。
3. **环境漏报/误报**：检查已安装的系统依赖（如 Node.js、Git、Docker、WSL2）是否被准确识别版本，或是否存在已配置 PATH 却提示 `command_not_found` 的情况。

若遇到程序中断、报错或数据严重不符，请直接在 GitHub 提交 Issue，并附带终端抛出的 Traceback 错误堆栈及你的实际物理配置。

## 后续发展路线

* **v0.6 (当前)**：完成核心层与表现层彻底解耦，通过 96 项数据断言测试，确立标准 JSON 数据契约。
* **v0.7 目标**：构建基于 1-2-3 数字菜单的交互式 TUI 界面，整合独立 Markdown 报告导出器，交付首个无需配置 Python 环境、双击即用的发布版单文件 `stackpilot.exe`。
* **v0.8 目标**：接入 LLM 大模型进行本地智能化诊断与配置建议。
* **v1.0 目标**：引入 Tauri 图形框架，交付纯原生、全渠道上架（微软商店、winget）的 Windows 图形端（GUI）桌面软件。

## 许可证

本项目基于 [MIT License](https://www.google.com/search?q=https://CHOOSEALICENSE.COM/LICENSES/MIT/) 协议开源
