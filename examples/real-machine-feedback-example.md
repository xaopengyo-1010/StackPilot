# Real Machine Feedback Example

这个示例说明如何从“跑一次命令”整理成一条可用反馈。它不会安装软件，也不会修改系统。

## 1. 运行扫描

```bash
python -m stackpilot scan
```

重点看这些信息：

- OS、CPU、内存、磁盘空间
- GPU 列表
- `primary_gpu`
- `gpu_selection_reason`
- `vram_confidence`
- Python / Git / Docker / WSL 检测结果

## 2. 运行一次完整报告

```bash
python -m stackpilot doctor --goal comfyui_starter
```

如果你不是 AI 绘图用户，也可以换成：

```bash
python -m stackpilot doctor --goal coding_starter
```

## 3. 复制必要输出

只复制和问题有关的输出即可，例如：

- StackPilot 把哪张显卡识别成了主要 GPU；
- Python / Git / Docker / WSL 是否被正确检测；
- 推荐结果哪里看不懂或不合理；
- 安装计划哪里缺少风险说明。

## 4. 删除隐私信息

提交前请删除或打码：

- 用户名；
- 个人目录和绝对路径；
- 设备序列号；
- 账号、密钥、token；
- 私人文件名或截图里的私人内容。

## 5. 提交反馈

可以复制 `docs/feedback/feedback-template.md` 里的模板，然后通过 Issue 或交流群反馈。

如果是硬件识别问题，建议附上：

- OS；
- CPU；
- GPU 列表；
- RAM；
- Python / Git / Docker / WSL 状态；
- 实际输出；
- 你认为正确的结果。
