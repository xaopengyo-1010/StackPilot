from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SRC_DIR = ROOT / "src"
CONFIG_DIR = ROOT / "configs"
ENTRY_SCRIPT = SRC_DIR / "stackpilot" / "main.py"


def add_data_arg(source: Path, target: str) -> str:
    separator = ";" if os.name == "nt" else ":"
    return f"{source}{separator}{target}"


def build_command() -> list[str]:
    if not CONFIG_DIR.exists():
        raise FileNotFoundError(f"Missing config directory: {CONFIG_DIR}")
    if not ENTRY_SCRIPT.exists():
        raise FileNotFoundError(f"Missing entry script: {ENTRY_SCRIPT}")

    return [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--name=stackpilot",
        "--clean",
        "--paths",
        str(SRC_DIR),
        "--add-data",
        add_data_arg(CONFIG_DIR, "configs"),
        str(ENTRY_SCRIPT),
    ]


def main() -> None:
    subprocess.run(build_command(), cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
