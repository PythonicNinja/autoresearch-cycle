from __future__ import annotations

import hashlib
import random
from typing import Any

from jsonschema import validate

from ..models import (
    ConstraintDefinition,
    DomainSummary,
    EvaluationResult,
    ObjectiveDefinition,
    PolicyRecord,
    RunMetrics,
    WindowConfig,
)
from ..utils import canonical_json
from .base import DomainAdapter


class SyntheticDomainAdapter(DomainAdapter):
    domain_id = "synthetic"
    display_name = "Synthetic Function"
    schema_version = "1.0"

    def describe(self) -> DomainSummary:
        return DomainSummary(
            domain_id=self.domain_id,
            display_name=self.display_name,
            schema_version=self.schema_version,
            supported_metrics=["score", "latency_ms", "error_rate"],
            default_objective=ObjectiveDefinition(name="score", direction="maximize"),
            default_policy=self.default_policy(),
        )

    def get_policy_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "additionalProperties": False,
            "required": ["x", "y", "noise"],
            "properties": {
                "x": {"type": "number", "minimum": -10.0, "maximum": 10.0},
                "y": {"type": "number", "minimum": -10.0, "maximum": 10.0},
                "noise": {"type": "number", "minimum": 0.0, "maximum": 1.0},
            },
        }

    def default_policy(self) -> dict[str, Any]:
        return {"x": 0.0, "y": 0.0, "noise": 0.1}

    def validate_policy(self, content: dict[str, Any]) -> None:
        validate(instance=content, schema=self.get_policy_schema())

    def evaluate_policy(
        self,
        policy: PolicyRecord,
        window_config: WindowConfig,
        objective: ObjectiveDefinition,
        constraints: list[ConstraintDefinition],
    ) -> EvaluationResult:
        del constraints
        sample_budget = (
            window_config.sample_count
            if window_config.type == "sample"
            else max((window_config.duration_seconds or 1) * 10, 10)
        )
        seed_payload = {
            "policy": policy.content,
            "window": window_config.model_dump(mode="json"),
            "objective": objective.model_dump(mode="json"),
        }
        seed_hash = hashlib.sha256(canonical_json(seed_payload).encode("utf-8")).hexdigest()
        seed_value = int(seed_hash[:16], 16)
        rng = random.Random(seed_value)

        x = float(policy.content["x"])
        y = float(policy.content["y"])
        noise = float(policy.content["noise"])

        base_score = 100.0 - (((x - 2.5) ** 2) * 6.0 + ((y + 1.5) ** 2) * 8.0 + noise * 35.0)
        total_score = 0.0
        for _ in range(sample_budget):
            total_score += base_score + rng.uniform(-1.5, 1.5) * max(noise, 0.05)

        primary_value = round(total_score / sample_budget, 4)
        latency = round(55.0 + abs(x) * 3.5 + abs(y) * 2.0 + noise * 40.0, 4)
        error_rate = round(min(1.0, 0.01 + noise * 0.15 + abs(y) / 100.0), 4)

        metrics = RunMetrics(
            primary_metric_name=objective.name,
            primary_metric_value=primary_value,
            constraint_metrics={
                "latency_ms": latency,
                "error_rate": error_rate,
            },
        )
        return EvaluationResult(
            metrics=metrics,
            metadata={
                "sample_budget": sample_budget,
                "seed": str(seed_value),
            },
        )
