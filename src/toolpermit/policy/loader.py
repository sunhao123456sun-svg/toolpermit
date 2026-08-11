"""Safe YAML loading with closed validation errors."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from toolpermit.policy.models import Policy


class PolicyLoadError(ValueError):
    """The policy cannot be used for enforcement."""


def parse_policy(text: str) -> Policy:
    try:
        raw = yaml.safe_load(text)
    except yaml.YAMLError as error:
        raise PolicyLoadError(f"invalid YAML: {error}") from error
    if not isinstance(raw, dict):
        raise PolicyLoadError("policy document must be a mapping")
    try:
        return Policy.model_validate(raw)
    except ValidationError as error:
        raise PolicyLoadError(str(error)) from error


def load_policy(path: Path) -> Policy:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise PolicyLoadError(f"cannot read policy {path}: {error}") from error
    return parse_policy(text)

