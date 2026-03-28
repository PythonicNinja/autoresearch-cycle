from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ObjectiveDirection = Literal["maximize", "minimize"]
ConstraintOperator = Literal["<=", ">="]
ExperimentStatus = Literal["active", "completed", "failed"]
RunStatus = Literal["scheduled", "running", "completed", "failed"]
ProposalDecision = Literal["accepted", "rejected"]
WindowType = Literal["time", "sample"]


class ObjectiveDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    direction: ObjectiveDirection


class ConstraintDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    operator: ConstraintOperator
    threshold: float


class WindowConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: WindowType
    duration_seconds: int | None = None
    sample_count: int | None = None
    timeout_seconds: int = 60

    @model_validator(mode="after")
    def validate_budget(self) -> WindowConfig:
        if self.type == "time" and (self.duration_seconds is None or self.duration_seconds <= 0):
            raise ValueError("time windows require a positive duration_seconds")
        if self.type == "sample" and (self.sample_count is None or self.sample_count <= 0):
            raise ValueError("sample windows require a positive sample_count")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        return self


class DomainSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    domain_id: str
    display_name: str
    schema_version: str
    supported_metrics: list[str]
    default_objective: ObjectiveDefinition
    default_policy: dict[str, Any]


class PolicyRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy_id: str
    domain_id: str
    schema_version: str
    content: dict[str, Any]
    created_at: datetime
    content_hash: str


class ExperimentRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    experiment_id: str
    domain_id: str
    baseline_policy_id: str
    optimizer_id: str
    objective: ObjectiveDefinition
    constraints: list[ConstraintDefinition] = Field(default_factory=list)
    window_config: WindowConfig
    status: ExperimentStatus = "active"
    created_at: datetime


class RunMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    primary_metric_name: str
    primary_metric_value: float
    constraint_metrics: dict[str, float] = Field(default_factory=dict)


class RunRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    experiment_id: str
    policy_id: str
    domain_id: str
    status: RunStatus
    window_config: WindowConfig
    metrics: RunMetrics | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime
    ended_at: datetime | None = None


class OptimizerProposalRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal_id: str
    experiment_id: str
    optimizer_id: str
    candidate_policy_id: str
    rationale: str
    decision: ProposalDecision
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ExperimentCreateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    domain_id: str
    baseline_policy: dict[str, Any]
    optimizer_id: str = "random"
    objective: ObjectiveDefinition
    constraints: list[ConstraintDefinition] = Field(default_factory=list)
    window_config: WindowConfig


class OptimizerContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    domain_id: str
    policy_schema: dict[str, Any]
    baseline_policy: PolicyRecord
    recent_runs: list[RunRecord]
    existing_policies: list[PolicyRecord]
    objective: ObjectiveDefinition
    constraints: list[ConstraintDefinition]


class CandidatePolicyProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_policy: dict[str, Any]
    rationale: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvaluationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metrics: RunMetrics
    metadata: dict[str, Any] = Field(default_factory=dict)
