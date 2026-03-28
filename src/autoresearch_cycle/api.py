from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException

from .models import DomainSummary, ExperimentCreateInput, ExperimentRecord, RunRecord
from .services import build_service


def create_app(data_dir: Path | None = None) -> FastAPI:
    service = build_service(data_dir)
    app = FastAPI(title="autoresearch-cycle", version="0.1.0")

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/domains", response_model=list[DomainSummary])
    def list_domains() -> list[DomainSummary]:
        return service.list_domains()

    @app.post("/experiments", response_model=ExperimentRecord)
    def create_experiment(payload: ExperimentCreateInput) -> ExperimentRecord:
        return _handle_request(lambda: service.create_experiment(payload))

    @app.get("/experiments", response_model=list[ExperimentRecord])
    def list_experiments() -> list[ExperimentRecord]:
        return service.list_experiments()

    @app.get("/experiments/{experiment_id}", response_model=ExperimentRecord)
    def get_experiment(experiment_id: str) -> ExperimentRecord:
        return _handle_request(lambda: service.get_experiment(experiment_id))

    @app.post("/experiments/{experiment_id}/run", response_model=RunRecord)
    def run_experiment(experiment_id: str) -> RunRecord:
        return _handle_request(lambda: service.run_experiment(experiment_id))

    @app.get("/runs", response_model=list[RunRecord])
    def list_runs(experiment_id: str | None = None) -> list[RunRecord]:
        return service.list_runs(experiment_id=experiment_id)

    @app.get("/runs/{run_id}", response_model=RunRecord)
    def get_run(run_id: str) -> RunRecord:
        return _handle_request(lambda: service.get_run(run_id))

    return app


def _handle_request(operation):
    try:
        return operation()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
