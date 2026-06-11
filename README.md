# StackPilot

StackPilot is an open-source environment blueprint generator.

It scans public local system information and recommends transparent setup templates for coding, AI-assisted coding, AI beginner workflows, ComfyUI, local LLMs, gaming, creator workflows, and office productivity.

## What StackPilot is not

StackPilot is not a software manager.
StackPilot does not install anything automatically.
StackPilot does not clean, optimize, monitor, or modify your system.
StackPilot does not upload your data.

It only generates an environment blueprint and recommendation report.

StackPilot 不是软件管家，不会自动下载、安装、清理、优化或监控系统，也不会上传你的数据。它只读取本地公开系统信息，并生成环境蓝图。

## Current Features

- Scans local public system information: OS, CPU, RAM, disk, GPU, common developer tools, WSL, and NVIDIA driver signals.
- Loads transparent setup templates from JSON files.
- Recommends apps, configuration notes, risk warnings, and next steps for a selected goal.
- Generates Markdown and JSON reports.
- Provides a Typer CLI with Rich terminal output.

## Installation

Use Python 3.11 or newer.

```powershell
python -m pip install -e .[dev]
```

If your shell treats brackets specially, quote the package spec:

```powershell
python -m pip install -e ".[dev]"
```

## Usage

```powershell
python -m stackpilot scan
python -m stackpilot list-templates
python -m stackpilot recommend --goal coding_starter
python -m stackpilot recommend --goal comfyui_starter
python -m stackpilot recommend --goal office_productivity
python -m stackpilot report --goal ai_beginner
python -m stackpilot doctor --goal vibe_coding
```

Reports are written to:

- `outputs/reports/stackpilot-report.md`
- `outputs/reports/stackpilot-report.json`

## Supported Templates

| Goal | Display name |
|---|---|
| `coding_starter` | 写代码入门 |
| `vibe_coding` | AI 辅助写代码 |
| `ai_beginner` | AI 入门体验 |
| `comfyui_starter` | AI 绘图入门 |
| `local_llm` | 本地大模型 |
| `gaming_setup` | 游戏玩家常用软件 |
| `creator_setup` | 视频/内容创作 |
| `office_productivity` | 办公生产力 |

## Safety Notes

StackPilot v0.1 only reads public local system information and local JSON configuration files. It does not download software, install software, modify system settings, clean files, optimize the system, monitor in the background, upload data, or execute install scripts.

Recommended app sources are displayed for user review. StackPilot does not open those sources or contact the internet.

## Roadmap

- Better hardware-specific recommendation rules.
- More templates and app catalog entries.
- Optional localized report output.
- Export presets for sharing environment blueprints.

## License

MIT License. See `LICENSE`.
