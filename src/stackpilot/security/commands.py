from __future__ import annotations

import re
from dataclasses import dataclass


FORBIDDEN_COMMAND_PATTERNS = [
    re.compile(r"invoke-webrequest\b.*\|\s*iex", re.IGNORECASE),
    re.compile(r"\bcurl\b.*\|\s*powershell", re.IGNORECASE),
    re.compile(r"\bcurl\b.*\|\s*(?:sh|bash|zsh)\b", re.IGNORECASE),
    re.compile(r"\bwget\b.*\|\s*(?:sh|bash|zsh)\b", re.IGNORECASE),
    re.compile(r"\birm\b.*\|\s*iex", re.IGNORECASE),
    re.compile(r"\biwr\b.*\|\s*iex", re.IGNORECASE),
    re.compile(r"\b(?:powershell|pwsh)\b.*-encodedcommand\b", re.IGNORECASE),
    re.compile(r"set-executionpolicy\s+bypass", re.IGNORECASE),
    re.compile(r"remove-item\s+-recurse\s+c:\\", re.IGNORECASE),
    re.compile(r"\brm\s+-rf\s+/(?:\s|$)", re.IGNORECASE),
    re.compile(r"\breg\s+add\b", re.IGNORECASE),
    re.compile(r"\breg\s+delete\b", re.IGNORECASE),
    re.compile(r"start-process\b.*\.exe", re.IGNORECASE),
    re.compile(r"\|\s*iex\b", re.IGNORECASE),
]

SAFE_TOKEN = r"[A-Za-z0-9_.-]+"
ALLOWED_WINGET_PATTERN = re.compile(
    rf"^winget\s+(?:install|uninstall)\s+(?:--id\s+)?{SAFE_TOKEN}(?:\s+--source\s+winget)?$",
    re.IGNORECASE,
)
ALLOWED_WHERE_PATTERN = re.compile(rf"^where\s+{SAFE_TOKEN}$", re.IGNORECASE)


@dataclass(frozen=True)
class CommandReview:
    """Result of reviewing a command preview string."""

    command: str
    allowed: bool
    blocked: bool
    message: str


def is_manual_plan_text(command: str | None) -> bool:
    """Return true when a command field is explicit non-executable plan text."""

    if command is None:
        return False
    text = command.strip().casefold()
    return text.startswith("manual:") or text.startswith("人工:")


def has_forbidden_pattern(command: str | None) -> bool:
    """Return true if command text contains a blocked shell pattern."""

    if not command:
        return False
    return any(pattern.search(command) for pattern in FORBIDDEN_COMMAND_PATTERNS)


def is_allowed_command_preview(command: str | None) -> bool:
    """Return true if command text is allowed to appear in an auditable plan."""

    if command is None:
        return True
    text = command.strip()
    if not text:
        return True
    if is_manual_plan_text(text):
        return True

    lowered = text.casefold()
    allowed_exact = {
        "python --version",
        "git --version",
        "node --version",
        "docker --version",
        "ffmpeg -version",
        "ollama --version",
    }
    return lowered in allowed_exact or bool(
        ALLOWED_WINGET_PATTERN.fullmatch(text) or ALLOWED_WHERE_PATTERN.fullmatch(text)
    )


def review_command(command: str | None) -> CommandReview:
    """Review one command preview according to StackPilot command policy."""

    text = command or ""
    if has_forbidden_pattern(text):
        return CommandReview(
            command=text,
            allowed=False,
            blocked=True,
            message="命令预览包含禁止的 shell 模式。",
        )
    if is_allowed_command_preview(text):
        return CommandReview(
            command=text,
            allowed=True,
            blocked=False,
            message="命令预览允许出现在计划中。",
        )
    return CommandReview(
        command=text,
        allowed=False,
        blocked=False,
        message="命令预览不在允许列表中，需要人工审查。",
    )
