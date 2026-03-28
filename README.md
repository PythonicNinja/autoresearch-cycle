# autoresearch-cycle

`autoresearch-cycle` is a local-first reference implementation of the autoresearch pattern: define a policy, constrain how an optimizer can change it, evaluate candidate policies in fixed windows, and persist the resulting run history for inspection.

This repository currently ships a Python scaffold with:

- a shared engine and service layer
- a Typer CLI
- a FastAPI control plane
- file-backed JSON storage with an audit log
- a synthetic domain adapter and random optimizer for end-to-end demos

## Quickstart

```bash
uv sync --dev
uv run autoresearch experiment create --file examples/synthetic/experiment.json
uv run autoresearch experiment list
uv run autoresearch experiment run <experiment-id>
uv run autoresearch run list
uv run autoresearch serve --port 8000
```

By default the app stores state in `.autoresearch/` under the current working directory. Override it with `AUTORESEARCH_DATA_DIR=/path/to/data`.

## Repository Map

- `docs/prd.md` - full product requirements document
- `docs/setup.md` - local setup, development, and runtime notes
- `docs/interfaces.md` - core models, storage layout, CLI, and HTTP interfaces
- `docs/examples.md` - runnable walkthroughs for the synthetic demo
- `examples/synthetic/` - example payloads and output snapshots
- `src/autoresearch_cycle/` - package source
- `tests/` - unit and integration tests

## Main Commands

```bash
uv run autoresearch domain list
uv run autoresearch experiment create --file examples/synthetic/experiment.json
uv run autoresearch experiment list
uv run autoresearch experiment run <experiment-id>
uv run autoresearch run list
uv run autoresearch serve
```

## Current Scope

This is an MVP scaffold. It focuses on explicit local execution, file-backed persistence, and one synthetic reference domain. It does not yet include scheduling, auth, distributed execution, or production hardening.
