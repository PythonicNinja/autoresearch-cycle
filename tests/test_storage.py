from __future__ import annotations

from pathlib import Path

from autoresearch_cycle.models import (
    PolicyRecord,
    RunMetrics,
    RunRecord,
    WindowConfig,
)
from autoresearch_cycle.storage import FileStorage
from autoresearch_cycle.utils import hash_policy_content, utc_now


def test_storage_persists_policy_and_audit_log(tmp_path: Path) -> None:
    storage = FileStorage(tmp_path / ".autoresearch")
    content = {"x": 0.0, "y": 0.0, "noise": 0.1}
    policy = PolicyRecord(
        policy_id="pol_test",
        domain_id="synthetic",
        schema_version="1.0",
        content=content,
        created_at=utc_now(),
        content_hash=hash_policy_content(content),
    )

    storage.save_policy(policy)

    loaded = storage.get_policy("pol_test")
    assert loaded == policy
    audit_path = tmp_path / ".autoresearch" / "audit" / "audit.jsonl"
    assert audit_path.exists()
    assert "policy.saved" in audit_path.read_text(encoding="utf-8")


def test_storage_lists_runs_by_experiment(tmp_path: Path) -> None:
    storage = FileStorage(tmp_path / ".autoresearch")
    window = WindowConfig(type="sample", sample_count=10, timeout_seconds=5)
    run = RunRecord(
        run_id="run_test",
        experiment_id="exp_1",
        policy_id="pol_1",
        domain_id="synthetic",
        status="completed",
        window_config=window,
        metrics=RunMetrics(primary_metric_name="score", primary_metric_value=1.0),
        started_at=utc_now(),
        ended_at=utc_now(),
    )
    storage.save_run(run)

    assert storage.list_runs(experiment_id="exp_1") == [run]
    assert storage.list_runs(experiment_id="exp_2") == []
