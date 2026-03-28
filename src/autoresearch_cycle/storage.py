from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from .models import ExperimentRecord, OptimizerProposalRecord, PolicyRecord, RunRecord
from .utils import new_id, utc_now

RecordModel = TypeVar("RecordModel", bound=BaseModel)


class FileStorage:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.ensure_layout()

    def ensure_layout(self) -> None:
        for relative in (
            "policies",
            "experiments",
            "runs",
            "optimizer_proposals",
            "audit",
        ):
            (self.base_dir / relative).mkdir(parents=True, exist_ok=True)

    def save_policy(self, policy: PolicyRecord) -> None:
        self._save_record("policies", policy.policy_id, policy)
        self.append_audit(
            "policy.saved",
            {"policy_id": policy.policy_id, "domain_id": policy.domain_id},
        )

    def get_policy(self, policy_id: str) -> PolicyRecord:
        return self._get_record("policies", policy_id, PolicyRecord)

    def list_policies(self, domain_id: str | None = None) -> list[PolicyRecord]:
        policies = self._list_records("policies", PolicyRecord)
        if domain_id is None:
            return policies
        return [policy for policy in policies if policy.domain_id == domain_id]

    def save_experiment(self, experiment: ExperimentRecord) -> None:
        self._save_record("experiments", experiment.experiment_id, experiment)
        self.append_audit(
            "experiment.saved",
            {"experiment_id": experiment.experiment_id, "domain_id": experiment.domain_id},
        )

    def get_experiment(self, experiment_id: str) -> ExperimentRecord:
        return self._get_record("experiments", experiment_id, ExperimentRecord)

    def list_experiments(self) -> list[ExperimentRecord]:
        return self._list_records("experiments", ExperimentRecord)

    def save_run(self, run: RunRecord) -> None:
        self._save_record("runs", run.run_id, run)
        self.append_audit(
            "run.saved",
            {
                "run_id": run.run_id,
                "experiment_id": run.experiment_id,
                "status": run.status,
            },
        )

    def get_run(self, run_id: str) -> RunRecord:
        return self._get_record("runs", run_id, RunRecord)

    def list_runs(self, experiment_id: str | None = None) -> list[RunRecord]:
        runs = self._list_records("runs", RunRecord)
        if experiment_id is None:
            return runs
        return [run for run in runs if run.experiment_id == experiment_id]

    def save_optimizer_proposal(self, proposal: OptimizerProposalRecord) -> None:
        self._save_record("optimizer_proposals", proposal.proposal_id, proposal)
        self.append_audit(
            "optimizer_proposal.saved",
            {
                "proposal_id": proposal.proposal_id,
                "experiment_id": proposal.experiment_id,
                "optimizer_id": proposal.optimizer_id,
            },
        )

    def get_optimizer_proposal(self, proposal_id: str) -> OptimizerProposalRecord:
        return self._get_record("optimizer_proposals", proposal_id, OptimizerProposalRecord)

    def list_optimizer_proposals(
        self, experiment_id: str | None = None
    ) -> list[OptimizerProposalRecord]:
        proposals = self._list_records("optimizer_proposals", OptimizerProposalRecord)
        if experiment_id is None:
            return proposals
        return [proposal for proposal in proposals if proposal.experiment_id == experiment_id]

    def append_audit(self, event_type: str, payload: dict[str, object]) -> None:
        audit_path = self.base_dir / "audit" / "audit.jsonl"
        event = {
            "event_id": new_id("evt"),
            "event_type": event_type,
            "timestamp": utc_now().isoformat(),
            "payload": payload,
        }
        with audit_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True))
            handle.write("\n")

    def _save_record(self, collection: str, record_id: str, record: BaseModel) -> None:
        path = self._record_path(collection, record_id)
        tmp_path = path.with_name(f"{path.name}.tmp")
        tmp_path.write_text(
            json.dumps(record.model_dump(mode="json"), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        tmp_path.replace(path)

    def _get_record(self, collection: str, record_id: str, model: type[RecordModel]) -> RecordModel:
        path = self._record_path(collection, record_id)
        if not path.exists():
            raise KeyError(f"{collection[:-1]} {record_id} not found")
        return model.model_validate_json(path.read_text(encoding="utf-8"))

    def _list_records(self, collection: str, model: type[RecordModel]) -> list[RecordModel]:
        directory = self.base_dir / collection
        records: list[RecordModel] = []
        for path in sorted(directory.glob("*.json")):
            records.append(model.model_validate_json(path.read_text(encoding="utf-8")))
        return records

    def _record_path(self, collection: str, record_id: str) -> Path:
        return self.base_dir / collection / f"{record_id}.json"
