from __future__ import annotations

from pathlib import Path

from .adapters import DomainRegistry, SyntheticDomainAdapter
from .models import (
    ExperimentCreateInput,
    ExperimentRecord,
    OptimizerContext,
    OptimizerProposalRecord,
    PolicyRecord,
    RunMetrics,
    RunRecord,
)
from .optimizers import OptimizerRegistry, RandomOptimizer
from .storage import FileStorage
from .utils import hash_policy_content, new_id, utc_now


class EngineService:
    def __init__(
        self,
        storage: FileStorage,
        domain_registry: DomainRegistry,
        optimizer_registry: OptimizerRegistry,
    ):
        self.storage = storage
        self.domain_registry = domain_registry
        self.optimizer_registry = optimizer_registry

    def list_domains(self):
        return self.domain_registry.list()

    def create_policy(self, domain_id: str, content: dict[str, object]) -> PolicyRecord:
        adapter = self.domain_registry.get(domain_id)
        adapter.validate_policy(content)
        policy = PolicyRecord(
            policy_id=new_id("pol"),
            domain_id=domain_id,
            schema_version=adapter.schema_version,
            content=content,
            created_at=utc_now(),
            content_hash=hash_policy_content(content),
        )
        self.storage.save_policy(policy)
        return policy

    def get_policy(self, policy_id: str) -> PolicyRecord:
        return self.storage.get_policy(policy_id)

    def list_policies(self, domain_id: str | None = None) -> list[PolicyRecord]:
        return self.storage.list_policies(domain_id=domain_id)

    def create_experiment(self, payload: ExperimentCreateInput) -> ExperimentRecord:
        self.domain_registry.get(payload.domain_id)
        self.optimizer_registry.get(payload.optimizer_id)
        baseline_policy = self.create_policy(payload.domain_id, payload.baseline_policy)
        experiment = ExperimentRecord(
            experiment_id=new_id("exp"),
            domain_id=payload.domain_id,
            baseline_policy_id=baseline_policy.policy_id,
            optimizer_id=payload.optimizer_id,
            objective=payload.objective,
            constraints=payload.constraints,
            window_config=payload.window_config,
            status="active",
            created_at=utc_now(),
        )
        self.storage.save_experiment(experiment)
        return experiment

    def get_experiment(self, experiment_id: str) -> ExperimentRecord:
        return self.storage.get_experiment(experiment_id)

    def list_experiments(self) -> list[ExperimentRecord]:
        return self.storage.list_experiments()

    def create_run_record(
        self,
        experiment: ExperimentRecord,
        policy_id: str,
        metadata: dict[str, object],
    ) -> RunRecord:
        run = RunRecord(
            run_id=new_id("run"),
            experiment_id=experiment.experiment_id,
            policy_id=policy_id,
            domain_id=experiment.domain_id,
            status="running",
            window_config=experiment.window_config,
            metadata=metadata,
            started_at=utc_now(),
        )
        self.storage.save_run(run)
        return run

    def complete_run(
        self,
        run_id: str,
        metrics: RunMetrics,
        metadata: dict[str, object],
    ) -> RunRecord:
        current = self.storage.get_run(run_id)
        if current.status == "completed":
            raise ValueError(f"run {run_id} is already completed")
        if current.status == "failed":
            raise ValueError(f"run {run_id} is already failed")
        updated = current.model_copy(
            update={
                "status": "completed",
                "metrics": metrics,
                "metadata": {**current.metadata, **metadata},
                "ended_at": utc_now(),
            }
        )
        self.storage.save_run(updated)
        return updated

    def run_experiment(self, experiment_id: str) -> RunRecord:
        experiment = self.get_experiment(experiment_id)
        adapter = self.domain_registry.get(experiment.domain_id)
        optimizer = self.optimizer_registry.get(experiment.optimizer_id)
        baseline_policy = self.storage.get_policy(experiment.baseline_policy_id)
        recent_runs = self.storage.list_runs(experiment_id=experiment.experiment_id)
        existing_policies = self.storage.list_policies(domain_id=experiment.domain_id)
        candidate = optimizer.propose(
            OptimizerContext(
                domain_id=experiment.domain_id,
                policy_schema=adapter.get_policy_schema(),
                baseline_policy=baseline_policy,
                recent_runs=recent_runs,
                existing_policies=existing_policies,
                objective=experiment.objective,
                constraints=experiment.constraints,
            )
        )
        candidate_policy = self.create_policy(experiment.domain_id, candidate.candidate_policy)
        proposal = OptimizerProposalRecord(
            proposal_id=new_id("prop"),
            experiment_id=experiment.experiment_id,
            optimizer_id=experiment.optimizer_id,
            candidate_policy_id=candidate_policy.policy_id,
            rationale=candidate.rationale,
            decision="accepted",
            metadata=candidate.metadata,
            created_at=utc_now(),
        )
        self.storage.save_optimizer_proposal(proposal)
        run = self.create_run_record(
            experiment=experiment,
            policy_id=candidate_policy.policy_id,
            metadata={
                "proposal_id": proposal.proposal_id,
                "optimizer_id": experiment.optimizer_id,
                "candidate_policy_id": candidate_policy.policy_id,
            },
        )
        evaluation = adapter.evaluate_policy(
            policy=candidate_policy,
            window_config=experiment.window_config,
            objective=experiment.objective,
            constraints=experiment.constraints,
        )
        return self.complete_run(run.run_id, evaluation.metrics, evaluation.metadata)

    def get_run(self, run_id: str) -> RunRecord:
        return self.storage.get_run(run_id)

    def list_runs(self, experiment_id: str | None = None) -> list[RunRecord]:
        return self.storage.list_runs(experiment_id=experiment_id)


def build_service(data_dir: Path | None = None) -> EngineService:
    storage_dir = data_dir or Path.cwd() / ".autoresearch"
    return EngineService(
        storage=FileStorage(storage_dir),
        domain_registry=DomainRegistry([SyntheticDomainAdapter()]),
        optimizer_registry=OptimizerRegistry([RandomOptimizer()]),
    )
