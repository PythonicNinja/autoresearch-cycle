from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from config import (
    BLOG_DIR,
    DATA_DIR,
    DOMAIN_ID,
    EVAL_THRESHOLD,
    EXPERIMENT_NAME,
    MAX_ITERATIONS,
    OPTIMIZER_AGENT,
)
from domain import BlogUIDomain


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_experiment() -> dict[str, object]:
    return {
        "id": f"exp_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "name": EXPERIMENT_NAME,
        "domain": DOMAIN_ID,
        "optimizer_agent": OPTIMIZER_AGENT,
        "max_iterations": MAX_ITERATIONS,
        "eval_threshold": EVAL_THRESHOLD,
        "created_at": utc_now(),
    }


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def append_run(path: Path, run: dict[str, object]) -> list[dict[str, object]]:
    if path.exists():
        runs = json.loads(path.read_text(encoding="utf-8"))
    else:
        runs = []
    runs.append(run)
    write_json(path, runs)
    return runs


def main() -> None:
    print("Start the blog dev server in another terminal:")
    print(f'  cd "{BLOG_DIR}" && npm run dev\n')
    print(f"Optimizer agent: {OPTIMIZER_AGENT}")

    domain = BlogUIDomain()
    experiment = build_experiment()
    runs_path = DATA_DIR / f"{experiment['id']}.runs.json"
    experiment_path = DATA_DIR / f"{experiment['id']}.experiment.json"
    write_json(experiment_path, experiment)

    runs: list[dict[str, object]] = []
    for iteration in range(1, MAX_ITERATIONS + 1):
        print(f"\n=== ITERATION {iteration} ===")

        run_output = domain.optimize(domain.read_policy(), iteration)
        print(f"Change: {run_output.get('change')}")

        score = domain.evaluate(run_output)
        print(f"Score: {score:.2f}")

        accepted = score >= EVAL_THRESHOLD
        run_record = {
            "iteration": iteration,
            "output": run_output,
            "score": score,
            "accepted": accepted,
            "created_at": utc_now(),
        }
        runs = append_run(runs_path, run_record)

        if accepted:
            domain.commit(str(run_output["change"]), iteration)
            print("Accepted and committed")
        else:
            domain.rollback()
            print("Rejected, rollback")

    print("\n=== HISTORY ===")
    print(json.dumps(runs, indent=2))


if __name__ == "__main__":
    main()
