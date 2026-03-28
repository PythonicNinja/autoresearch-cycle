from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient
from typer.testing import CliRunner

from autoresearch_cycle.api import create_app
from autoresearch_cycle.cli import app
from autoresearch_cycle.models import ExperimentCreateInput, ObjectiveDefinition, WindowConfig
from autoresearch_cycle.services import build_service


def test_service_run_persists_proposal_and_rejects_duplicate_completion(tmp_path: Path) -> None:
    service = build_service(tmp_path / ".autoresearch")
    experiment = service.create_experiment(
        ExperimentCreateInput(
            domain_id="synthetic",
            baseline_policy={"x": 0.0, "y": 0.0, "noise": 0.1},
            objective=ObjectiveDefinition(name="score", direction="maximize"),
            constraints=[],
            window_config=WindowConfig(type="sample", sample_count=50, timeout_seconds=5),
        )
    )

    run = service.run_experiment(experiment.experiment_id)

    assert run.status == "completed"
    assert run.metrics is not None
    assert run.metadata["proposal_id"].startswith("prop_")
    assert len(service.storage.list_optimizer_proposals(experiment.experiment_id)) == 1

    try:
        service.complete_run(run.run_id, run.metrics, {})
    except ValueError as exc:
        assert "already completed" in str(exc)
    else:
        raise AssertionError("expected duplicate completion to fail")


def test_api_and_cli_share_persisted_state(tmp_path: Path) -> None:
    data_dir = tmp_path / ".autoresearch"
    client = TestClient(create_app(data_dir))
    runner = CliRunner()
    payload = {
        "domain_id": "synthetic",
        "baseline_policy": {"x": 0.0, "y": 0.0, "noise": 0.1},
        "optimizer_id": "random",
        "objective": {"name": "score", "direction": "maximize"},
        "constraints": [],
        "window_config": {"type": "sample", "sample_count": 25, "timeout_seconds": 5},
    }

    create_response = client.post("/experiments", json=payload)
    assert create_response.status_code == 200
    experiment_id = create_response.json()["experiment_id"]

    run_response = client.post(f"/experiments/{experiment_id}/run")
    assert run_response.status_code == 200
    run_id = run_response.json()["run_id"]

    cli_result = runner.invoke(
        app,
        ["run", "list", "--data-dir", str(data_dir), "--json"],
    )
    assert cli_result.exit_code == 0
    runs = json.loads(cli_result.stdout)
    assert runs[0]["run_id"] == run_id


def test_cli_can_create_experiment_from_file(tmp_path: Path) -> None:
    data_dir = tmp_path / ".autoresearch"
    payload_file = tmp_path / "experiment.json"
    payload_file.write_text(
        json.dumps(
            {
                "domain_id": "synthetic",
                "baseline_policy": {"x": 0.0, "y": 0.0, "noise": 0.1},
                "optimizer_id": "random",
                "objective": {"name": "score", "direction": "maximize"},
                "constraints": [],
                "window_config": {"type": "sample", "sample_count": 20, "timeout_seconds": 5},
            }
        ),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        app,
        [
            "experiment",
            "create",
            "--file",
            str(payload_file),
            "--data-dir",
            str(data_dir),
            "--json",
        ],
    )

    assert result.exit_code == 0
    experiment = json.loads(result.stdout)
    assert experiment["domain_id"] == "synthetic"
