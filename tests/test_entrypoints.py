from __future__ import annotations

import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_default_entrypoints_start_tui():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert pyproject["project"]["scripts"]["stackpilot"] == "stackpilot.main:main"
    assert (ROOT / "src" / "stackpilot" / "__main__.py").read_text(encoding="utf-8").strip().startswith(
        "from .main import main"
    )


def test_cli_entrypoint_is_still_available():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert pyproject["project"]["scripts"]["stackpilot-cli"] == "stackpilot.cli:main"
