# Setup

## Requirements

- Python 3.10+
- `uv`

## Install

```bash
uv sync --dev
```

## Data Directory

The application stores local state in `.autoresearch/` under the current working directory by default.

Override it with:

```bash
export AUTORESEARCH_DATA_DIR=/absolute/path/to/data
```

The data directory contains:

- `policies/`
- `experiments/`
- `runs/`
- `optimizer_proposals/`
- `audit/audit.jsonl`

## Run the CLI

```bash
uv run autoresearch domain list
uv run autoresearch experiment create --file examples/synthetic/experiment.json
uv run autoresearch experiment list
uv run autoresearch experiment run <experiment-id>
uv run autoresearch run list
```

## Run the API

```bash
uv run autoresearch serve --host 127.0.0.1 --port 8000
```

Health check:

```bash
curl http://127.0.0.1:8000/healthz
```

## Development

Run tests:

```bash
uv run pytest
```

Run Ruff:

```bash
uv run ruff check .
```

## Notes

- v1 uses explicit synchronous execution. There is no scheduler or background worker yet.
- The synthetic adapter evaluates windows immediately instead of waiting in real time.
