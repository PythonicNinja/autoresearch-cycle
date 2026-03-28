from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..models import (
    ConstraintDefinition,
    DomainSummary,
    EvaluationResult,
    ObjectiveDefinition,
    PolicyRecord,
    WindowConfig,
)


class DomainAdapter(ABC):
    domain_id: str
    display_name: str
    schema_version: str

    @abstractmethod
    def describe(self) -> DomainSummary:
        raise NotImplementedError

    @abstractmethod
    def get_policy_schema(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def validate_policy(self, content: dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    def evaluate_policy(
        self,
        policy: PolicyRecord,
        window_config: WindowConfig,
        objective: ObjectiveDefinition,
        constraints: list[ConstraintDefinition],
    ) -> EvaluationResult:
        raise NotImplementedError


class DomainRegistry:
    def __init__(self, adapters: list[DomainAdapter]):
        self._adapters = {adapter.domain_id: adapter for adapter in adapters}

    def get(self, domain_id: str) -> DomainAdapter:
        try:
            return self._adapters[domain_id]
        except KeyError as exc:
            raise KeyError(f"domain {domain_id} is not registered") from exc

    def list(self) -> list[DomainSummary]:
        return [adapter.describe() for adapter in self._adapters.values()]
