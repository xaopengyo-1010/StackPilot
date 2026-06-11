# StackPilot

StackPilot is an open-source environment blueprint generator.

It scans public local system information and recommends transparent setup templates for coding, AI, gaming, Minecraft, ComfyUI, local LLMs, and creator workflows.

## What StackPilot is not

StackPilot is not a software manager.
StackPilot does not install anything automatically.
StackPilot does not clean, optimize, monitor, or modify your system.
StackPilot does not upload your data.

It only generates an environment blueprint and recommendation report.

StackPilot 不是软件管家。
不会自动下载。
不会自动安装。
不会清理、优化或监控系统。
不会上传你的数据。
它只读取本地公开系统信息，并生成环境蓝图。

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
python -m stackpilot recommend --goal minecraft_realism
python -m stackpilot report --goal ai_beginner
python -m stackpilot doctor --goal vibe_coding
```

Reports are written to:

- `outputs/reports/stackpilot-report.md`
- `outputs/reports/stackpilot-report.json`

## Supported Templates

- `coding_starter`
- `vibe_coding`
- `ai_beginner`
- `comfyui_starter`
- `local_llm`
- `minecraft_realism`
- `gaming_setup`
- `creator_setup`

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
