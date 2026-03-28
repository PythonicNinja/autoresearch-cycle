from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
import uvicorn

from .api import create_app
from .models import ExperimentCreateInput
from .services import build_service

app = typer.Typer(no_args_is_help=True)
domain_app = typer.Typer(no_args_is_help=True)
experiment_app = typer.Typer(no_args_is_help=True)
run_app = typer.Typer(no_args_is_help=True)

app.add_typer(domain_app, name="domain")
app.add_typer(experiment_app, name="experiment")
app.add_typer(run_app, name="run")


def _service(data_dir: Path | None):
    return build_service(data_dir)


def _dump(value: Any) -> str:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    elif isinstance(value, list):
        value = [
            item.model_dump(mode="json") if hasattr(item, "model_dump") else item
            for item in value
        ]
    return json.dumps(value, indent=2, sort_keys=True)


def _echo_json(value: Any) -> None:
    typer.echo(_dump(value))


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8000, "--port"),
    data_dir: Path | None = typer.Option(None, "--data-dir"),
) -> None:
    uvicorn.run(create_app(data_dir=data_dir), host=host, port=port, reload=False)


@domain_app.command("list")
def list_domains(
    data_dir: Path | None = typer.Option(None, "--data-dir"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    domains = _service(data_dir).list_domains()
    if as_json:
        _echo_json(domains)
        return
    for domain in domains:
        typer.echo(f"{domain.domain_id}: {domain.display_name} (schema {domain.schema_version})")


@experiment_app.command("create")
def create_experiment(
    file: Path = typer.Option(..., "--file", exists=True, dir_okay=False, readable=True),
    data_dir: Path | None = typer.Option(None, "--data-dir"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    payload = ExperimentCreateInput.model_validate_json(file.read_text(encoding="utf-8"))
    experiment = _service(data_dir).create_experiment(payload)
    if as_json:
        _echo_json(experiment)
        return
    typer.echo(f"created experiment {experiment.experiment_id} for domain {experiment.domain_id}")


@experiment_app.command("list")
def list_experiments(
    data_dir: Path | None = typer.Option(None, "--data-dir"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    experiments = _service(data_dir).list_experiments()
    if as_json:
        _echo_json(experiments)
        return
    for experiment in experiments:
        typer.echo(
            f"{experiment.experiment_id}: {experiment.domain_id} "
            f"[{experiment.status}] optimizer={experiment.optimizer_id}"
        )


@experiment_app.command("run")
def run_experiment(
    experiment_id: str,
    data_dir: Path | None = typer.Option(None, "--data-dir"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    run = _service(data_dir).run_experiment(experiment_id)
    if as_json:
        _echo_json(run)
        return
    primary = run.metrics.primary_metric_value if run.metrics is not None else "n/a"
    typer.echo(f"completed run {run.run_id} for {experiment_id} with score {primary}")


@run_app.command("list")
def list_runs(
    experiment_id: str | None = typer.Option(None, "--experiment-id"),
    data_dir: Path | None = typer.Option(None, "--data-dir"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    runs = _service(data_dir).list_runs(experiment_id=experiment_id)
    if as_json:
        _echo_json(runs)
        return
    for run in runs:
        primary = run.metrics.primary_metric_value if run.metrics else "n/a"
        typer.echo(f"{run.run_id}: {run.experiment_id} [{run.status}] score={primary}")


def main() -> None:
    app()
