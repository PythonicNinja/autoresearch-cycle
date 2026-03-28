# Interfaces

## Core Records

### Policy

```json
{
  "policy_id": "pol_...",
  "domain_id": "synthetic",
  "schema_version": "1.0",
  "content": {
    "x": 0.0,
    "y": 0.0,
    "noise": 0.1
  },
  "created_at": "2026-03-28T18:00:00Z",
  "content_hash": "..."
}
```

### Experiment

```json
{
  "experiment_id": "exp_...",
  "domain_id": "synthetic",
  "baseline_policy_id": "pol_...",
  "optimizer_id": "random",
  "objective": {
    "name": "score",
    "direction": "maximize"
  },
  "constraints": [
    {
      "name": "latency_ms",
      "operator": "<=",
      "threshold": 120.0
    }
  ],
  "window_config": {
    "type": "sample",
    "sample_count": 250,
    "timeout_seconds": 60
  },
  "status": "active",
  "created_at": "2026-03-28T18:00:00Z"
}
```

### Run

```json
{
  "run_id": "run_...",
  "experiment_id": "exp_...",
  "policy_id": "pol_...",
  "domain_id": "synthetic",
  "status": "completed",
  "window_config": {
    "type": "sample",
    "sample_count": 250,
    "timeout_seconds": 60
  },
  "metrics": {
    "primary_metric_name": "score",
    "primary_metric_value": 78.4,
    "constraint_metrics": {
      "latency_ms": 71.2,
      "error_rate": 0.03
    }
  },
  "metadata": {
    "proposal_id": "prop_...",
    "optimizer_id": "random"
  },
  "started_at": "2026-03-28T18:00:01Z",
  "ended_at": "2026-03-28T18:00:01Z"
}
```

## Storage Layout

```text
.autoresearch/
  policies/
  experiments/
  runs/
  optimizer_proposals/
  audit/
    audit.jsonl
```

Each entity is stored as a JSON file named `<id>.json`.

## CLI

```bash
autoresearch serve
autoresearch domain list
autoresearch experiment create --file examples/synthetic/experiment.json
autoresearch experiment list
autoresearch experiment run <experiment-id>
autoresearch run list
```

## HTTP API

- `GET /healthz`
- `GET /domains`
- `POST /experiments`
- `GET /experiments`
- `GET /experiments/{experiment_id}`
- `POST /experiments/{experiment_id}/run`
- `GET /runs`
- `GET /runs/{run_id}`

## POST /experiments Request

```json
{
  "domain_id": "synthetic",
  "baseline_policy": {
    "x": 0.0,
    "y": 0.0,
    "noise": 0.1
  },
  "optimizer_id": "random",
  "objective": {
    "name": "score",
    "direction": "maximize"
  },
  "constraints": [
    {
      "name": "latency_ms",
      "operator": "<=",
      "threshold": 120.0
    }
  ],
  "window_config": {
    "type": "sample",
    "sample_count": 250,
    "timeout_seconds": 60
  }
}
```
