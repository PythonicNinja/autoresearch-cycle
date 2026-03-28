from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import CandidatePolicyProposal, OptimizerContext


class Optimizer(ABC):
    optimizer_id: str

    @abstractmethod
    def propose(self, context: OptimizerContext) -> CandidatePolicyProposal:
        raise NotImplementedError


class OptimizerRegistry:
    def __init__(self, optimizers: list[Optimizer]):
        self._optimizers = {optimizer.optimizer_id: optimizer for optimizer in optimizers}

    def get(self, optimizer_id: str) -> Optimizer:
        try:
            return self._optimizers[optimizer_id]
        except KeyError as exc:
            raise KeyError(f"optimizer {optimizer_id} is not registered") from exc
