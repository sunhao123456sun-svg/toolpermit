"""Versioned strict YAML policy schema."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, RootModel, model_validator

from toolpermit.domain.models import Decision


class ExactCondition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    exact: Any


class GlobCondition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    glob: str = Field(min_length=1, max_length=2048)


class PathUnderCondition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    path_under: str = Field(min_length=1, max_length=4096)


Condition = ExactCondition | GlobCondition | PathUnderCondition


class ArgumentConditions(RootModel[dict[str, Condition]]):
    model_config = ConfigDict(frozen=True)


class Match(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    tool: str | None = Field(default=None, min_length=1, max_length=512)
    arguments: ArgumentConditions = Field(default_factory=lambda: ArgumentConditions({}))


class Rule(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
    action: Decision
    match: Match
    explanation: str = Field(min_length=1, max_length=2048)


class Policy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    version: Literal[1]
    default: Decision
    rules: tuple[Rule, ...] = ()

    @model_validator(mode="after")
    def unique_rule_ids(self) -> Policy:
        rule_ids = [rule.id for rule in self.rules]
        if len(rule_ids) != len(set(rule_ids)):
            raise ValueError("policy rule IDs must be unique")
        return self
