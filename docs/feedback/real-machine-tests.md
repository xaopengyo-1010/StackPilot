# Real Machine Tests

This file tracks real-world hardware and environment test results for StackPilot.

本文件用于记录真实机器测试结果，帮助 v0.5 持续修正 GPU 检测、环境检测、推荐规则和安装计划说明。

## Test Matrix

| Date       | OS      | CPU     | GPU Setup | RAM     | Python | Git     | Docker  | WSL     | Result           | Notes                     |
| ---------- | ------- | ------- | --------- | ------- | ------ | ------- | ------- | ------- | ---------------- | ------------------------- |
| YYYY-MM-DD | Pending | Pending | Pending   | Pending | 未填写 | 未填写  | 未填写  | 未填写  | 待补充真实测试结果 | Placeholder only.         |

## What to Check

- OS detection
- CPU detection
- RAM detection
- Disk capacity and free space
- GPU list
- `primary_gpu`
- `gpu_selection_reason`
- `vram_confidence`
- Python / Git / Docker / WSL detection
- Recommendation output
- Install plan output

## Suggested Result Values

- `pass`: 输出符合测试者预期。
- `partial`: 大部分正确，但有字段不清楚或需要修正。
- `fail`: 关键检测错误或影响推荐结论。
- `blocked`: 命令无法运行，需要先解决安装或环境问题。

## Privacy Rule

Only record hardware class and test result. Do not record personal usernames, absolute personal paths, device serial numbers, or private identifiers.

只记录硬件类型、环境状态和测试结论。不要记录个人用户名、绝对私人路径、设备序列号或其它私有标识。
