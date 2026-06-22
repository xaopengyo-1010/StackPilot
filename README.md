# StackPilot (v0.7-Alpha)

Windows 本地硬件检测与环境配置规划工具。当前版本为 **TUI exe 测试版**，已提供终端交互界面。

## 项目核心声明

1. **运行方式**：当前版本提供两种运行方式：

   * 下载 Release 中的 `StackPilot_TUI.exe` 直接运行
   * 通过源码部署，在本地配置 Python 3.11+ 环境运行

2. **功能边界**：本工具当前仅执行本地硬件拓扑扫描、已有依赖检索，并对比本地规则输出规划报告。
   **当前版本不执行、亦不包含任何实际的软件下载与自动安装逻辑。**

3. **安全保证**：程序运行时全离线，不主动发起网络请求，不上传数据，不修改系统环境变量、PATH 或注册表。

## 快速开始

### 1. TUI exe 下载

打开 [Release 页面](https://github.com/xaopengyo-1010/StackPilot/releases)，下载最新版本中的 `StackPilot_TUI.exe`。

下载后可直接双击运行。

如果双击后窗口一闪而过，建议在下载目录打开 PowerShell，执行以下命令：

```powershell
.\StackPilot_TUI.exe
```

这样可以看到终端输出和错误信息。

### 2. 源码部署

适合开发者、测试者和需要调试代码的人。

确保你的电脑已安装 Git 和 Python 3.11+。打开 PowerShell 执行：

```powershell
# 克隆项目
git clone https://github.com/xaopengyo-1010/StackPilot.git
cd StackPilot

# 建立虚拟环境
python -m venv venv
.\venv\Scripts\activate

# 安装所需依赖
python -m pip install -e .
```

启动 TUI：

```powershell
stackpilot
```

如果 `stackpilot` 命令不可用，可以尝试：

```powershell
python -m stackpilot
```

### 3. 单元测试验证

开发者可以运行测试：

```powershell
python -m pytest
```

## 内部测试重点（Bug 反馈）

当前底层扫描引擎正在优化复杂 Windows 环境下的错误处理与兼容性。如果参与测试，请重点协助验证以下场景：

1. **低权限 / 非管理员运行**
   在非管理员终端运行程序，观察程序是否能稳定降级。
   预期表现：即使部分硬件信息无法读取，程序也不应直接崩溃，而应记录相关失败项或风险提示。

2. **多显卡拓扑识别**
   在同时存在核显、独立显卡或多块显卡的机器上运行，核对 GPU 型号、显存大小与显存来源标签是否准确。
   重点关注：`detected` / `estimated` / `shared` / `unknown` 等分类是否合理。

3. **环境漏报 / 误报**
   检查已安装的系统依赖是否被准确识别，例如：

   * Python
   * Git
   * Node.js
   * pnpm
   * Docker
   * WSL / WSL2

4. **TUI 交互问题**
   检查菜单是否乱码、输入是否正常、退出是否正常、不同终端窗口大小下是否显示异常。

若遇到程序中断、报错或数据严重不符，请直接在 GitHub 提交 Issue，并尽量附带：

* Windows 版本
* CPU / GPU / 内存配置
* 是否使用管理员权限运行
* 运行方式：exe 或源码
* 报错截图或 Traceback 错误堆栈
* 生成的报告文件（提交前可自行打码用户名、路径和电脑名）

## 后续发展路线

* **v0.7.0（当前）**：TUI Developer Preview
  提供 TUI 终端交互界面，收集真实 Windows 机器上的硬件识别、权限降级、TUI 交互和报告输出反馈。

* **v0.7.5 目标**：GUI User Preview
  构建最小 GUI 测试版，验证普通用户是否能看懂、敢不敢用、流程是否直观。

* **v0.8 目标**：Shared Core Architecture
  正式整理 Core / Data / Schema / Pipeline，让 TUI、GUI、CLI 共用同一套内核代码和数据结构。

* **v0.9 目标**：LLM Explainer
  加入可选 AI 解释层，让 Core 输出更容易理解，但不让 LLM 接管硬件判断和安装决策。

* **v0.9.5 目标**：Native Core Migration Prep
  准备 Rust / C++ 内核迁移，优先处理安全层、计划层、schema 校验和底层探测模块。

* **v1.0 目标**：Stable Public Release
  GUI 面向普通用户，TUI 保留为开发者 / 测试者入口，两者共用同一套 StackPilot Core。

## 许可证

本项目基于 [MIT License](LICENSE) 协议开源。
