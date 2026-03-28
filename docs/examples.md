# Examples

## CLI Walkthrough

Install dependencies:

```bash
uv sync --dev
```

If your machine is configured to resolve packages from a private index, force PyPI:

```bash
UV_DEFAULT_INDEX=https://pypi.org/simple uv sync --dev
```

Use an isolated data directory for the demo:

```bash
export DEMO_DIR=/tmp/autoresearch-demo
```

Create an experiment from the bundled payload:

```bash
uv run autoresearch experiment create \
  --file examples/synthetic/experiment.json \
  --data-dir "$DEMO_DIR" \
  --json
```

That returns JSON containing an `experiment_id`. The shape looks like:

```json
{
  "experiment_id": "exp_...",
  "domain_id": "synthetic",
  "baseline_policy_id": "pol_...",
  "optimizer_id": "random",
  "status": "active"
}
```

Run one optimization step:

```bash
uv run autoresearch experiment run <experiment-id> \
  --data-dir "$DEMO_DIR" \
  --json
```

That returns a completed run with metrics:

```json
{
  "run_id": "run_...",
  "status": "completed",
  "metrics": {
    "primary_metric_name": "score",
    "primary_metric_value": -2.6995,
    "constraint_metrics": {
      "latency_ms": 69.4555,
      "error_rate": 0.0505
    }
  }
}
```

List persisted runs:

```bash
uv run autoresearch run list \
  --data-dir "$DEMO_DIR" \
  --json
```

One real run payload is recorded in `examples/synthetic/expected-run.json`. IDs and timestamps will differ on your machine.

## HTTP Walkthrough

Start the API:

```bash
uv run autoresearch serve --data-dir "$DEMO_DIR" --host 127.0.0.1 --port 8000
```

Create an experiment:

```bash
curl -X POST http://127.0.0.1:8000/experiments \
  -H 'content-type: application/json' \
  --data @examples/synthetic/experiment.json
```

Run an experiment:

```bash
curl -X POST http://127.0.0.1:8000/experiments/<experiment-id>/run
```

Fetch a run:

```bash
curl http://127.0.0.1:8000/runs/<run-id>
```

## Bundled Example Assets

- `examples/synthetic/experiment.json` - input payload for CLI and API creation
- `examples/synthetic/baseline-policy.json` - baseline policy used by the example
- `examples/synthetic/expected-run.json` - real snapshot of one example run response
