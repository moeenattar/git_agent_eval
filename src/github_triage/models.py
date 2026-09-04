"""Shared data contracts for inference and evaluation."""

from datetime import date
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class IssueType(StrEnum):
    BUG = "bug"
    ENHANCEMENT = "enhancement"
    DOCUMENTATION = "documentation"
    MAINTENANCE = "maintenance"
    OTHER = "other"


class Priority(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IssueInput(BaseModel):
    """The complete inference-time input contract."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=500)
    body: str = Field(default="", max_length=100_000)


class TriageDecision(BaseModel):
    """Structured output returned by the triage agent."""

    model_config = ConfigDict(extra="forbid")

    issue_type: IssueType
    priority: Priority
    needs_human_review: bool


class AgentTriageDecision(BaseModel):
    """Gemini-compatible response schema; service revalidates it strictly."""

    issue_type: IssueType
    priority: Priority
    needs_human_review: bool


class Annotation(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    reason: str = Field(min_length=1)
    annotator: str | None = None
    reviewed_by: str | None = None
    review_status: Literal["approved", "changed"] | None = None
    reviewed_on: date | None = None

    @field_validator("reviewed_by")
    @classmethod
    def nonempty_reviewer(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("reviewed_by cannot be blank")
        return value


class DatasetRecord(BaseModel):
    """Versioned evaluation example. Raw labels never enter IssueInput."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    source_url: str | None = None
    title: str = Field(min_length=1, max_length=500)
    body: str = Field(default="", max_length=100_000)
    gold: TriageDecision
    annotation: Annotation
    slices: list[str] = Field(min_length=1)
    dataset_version: str = Field(default="v1", min_length=1)

    @field_validator("slices")
    @classmethod
    def unique_slices(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("slices must not contain duplicates")
        return value

    def inference_input(self) -> IssueInput:
        return IssueInput(title=self.title, body=self.body)
