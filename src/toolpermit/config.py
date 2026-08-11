"""Strict, local-only ToolPermit configuration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

DEFAULT_CONFIG_NAME = "toolpermit.config.yaml"


class UISettings(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    host: Literal["127.0.0.1", "localhost", "::1"] = "127.0.0.1"
    port: int = Field(default=8765, ge=1, le=65535)


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    version: Literal[1] = 1
    database: Path = Path(".toolpermit/audit.db")
    policy: Path = Path("toolpermit.yaml")
    approval_ttl: float = Field(default=300.0, gt=0, le=86400)
    ui: UISettings = Field(default_factory=UISettings)


class ConfigError(ValueError):
    """The configuration cannot be used safely."""


def load_settings(path: Path | None = None, *, require: bool = False) -> Settings:
    config_path = path or Path(DEFAULT_CONFIG_NAME)
    if not config_path.exists():
        if require or path is not None:
            raise ConfigError(f"configuration file not found: {config_path}")
        settings = Settings()
        return _resolve_paths(settings, Path.cwd())
    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise ConfigError(f"cannot read configuration {config_path}: {error}") from error
    if not isinstance(raw, dict):
        raise ConfigError("configuration document must be a mapping")
    try:
        settings = Settings.model_validate(raw)
    except ValidationError as error:
        raise ConfigError(str(error)) from error
    return _resolve_paths(settings, config_path.resolve().parent)


def _resolve_paths(settings: Settings, base: Path) -> Settings:
    database = settings.database
    policy = settings.policy
    return settings.model_copy(
        update={
            "database": database if database.is_absolute() else base / database,
            "policy": policy if policy.is_absolute() else base / policy,
        }
    )


def starter_config(*, policy: str = "toolpermit.yaml") -> str:
    return (
        "# ToolPermit local configuration. Unknown keys are rejected.\n"
        "version: 1\n"
        "database: .toolpermit/audit.db\n"
        f"policy: {json.dumps(policy, ensure_ascii=False)}\n"
        "approval_ttl: 300\n"
        "ui:\n"
        "  host: 127.0.0.1\n"
        "  port: 8765\n"
    )


def starter_policy() -> str:
    return (
        "# Safe starter policy: every tool call requires local approval.\n"
        "version: 1\n"
        "default: ask\n"
        "rules: []\n"
    )
