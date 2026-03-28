# Examples

## CLI Walkthrough

Create an experiment from the bundled payload:

```bash
uv run autoresearch experiment create --file examples/synthetic/experiment.json
```

List experiments:

```bash
uv run autoresearch experiment list
```

Run one optimization step:

```bash
uv run autoresearch experiment run <experiment-id>
```

List runs:

```bash
uv run autoresearch run list
```

One real run payload is recorded in `examples/synthetic/expected-run.json`. The IDs and timestamps will differ on your machine.

## HTTP Walkthrough

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
- `examples/synthetic/expected-run.json` - snapshot of the example run response shape
