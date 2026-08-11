"""Immutable domain models shared by every interface."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Decision(StrEnum):
    ALLOW = "allow"
    ASK = "ask"
    DENY = "deny"


class ApprovalState(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    EXECUTING = "executing"
    EXECUTED = "executed"
    FAILED = "failed"
    UNKNOWN = "unknown"


class ToolDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(min_length=1, max_length=512)
    input_schema: dict[str, Any]
    schema_fingerprint: str = Field(min_length=64, max_length=64)


class ToolCall(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    event_id: str = Field(min_length=1, max_length=128)
    run_id: str = Field(min_length=1, max_length=128)
    connection_id: str = Field(min_length=1, max_length=128)
    request_id: str | int
    tool_name: str = Field(min_length=1, max_length=512)
    schema_fingerprint: str = Field(min_length=64, max_length=64)
    arguments: dict[str, Any]


class DecisionResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    decision: Decision
    rule_id: str
    explanation: str
    policy_digest: str = Field(min_length=64, max_length=64)
    indeterminate: bool = False
    diagnostics: tuple[str, ...] = ()

