from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from config import (
    BLOG_BUILD_DIR,
    BLOG_DIR,
    BLOG_COMPONENTS_GIT_PATH,
    BLOG_EDIT_PATHS,
    BLOG_GLOBAL_CSS_PATH,
    BLOG_GLOBAL_CSS_GIT_PATH,
    BLOG_REPO_DIR,
    LIGHTHOUSE_CATEGORIES,
    LIGHTHOUSE_URL,
    OPTIMIZER_AGENT,
    OPTIMIZER_TIMEOUT_SECONDS,
)


class BlogUIDomain:
    def read_policy(self) -> dict[str, object]:
        if not BLOG_GLOBAL_CSS_PATH.exists():
            raise FileNotFoundError(f"Expected stylesheet at {BLOG_GLOBAL_CSS_PATH}")

        css = BLOG_GLOBAL_CSS_PATH.read_text(encoding="utf-8")
        return {"css_hash": hash(css), "css_preview": css[:500]}

    def optimize(self, policy: dict[str, object], iteration: int) -> dict[str, object]:
        del policy
        prompt = f"""
UI autoresearch iteration {iteration}.
Read {BLOG_GLOBAL_CSS_GIT_PATH} and files in {BLOG_COMPONENTS_GIT_PATH}.
Make ONE focused improvement to readability or aesthetics.
Then run: cd {BLOG_BUILD_DIR} && npm run build
If build fails: git checkout {" ".join(BLOG_EDIT_PATHS)} and stop.
If build succeeds: output JSON summary:
{{"change": "what you changed", "reason": "why", "files": ["list"]}}
Output ONLY the JSON at the end.
"""
        if OPTIMIZER_AGENT == "claude":
            raw_output = self._run_claude(prompt)
        elif OPTIMIZER_AGENT == "codex":
            raw_output = self._run_codex(prompt)
        else:
            raise ValueError(
                f"Unsupported OPTIMIZER_AGENT={OPTIMIZER_AGENT!r}. Use 'claude' or 'codex'."
            )
        return self._parse_agent_output(raw_output)

    def evaluate(self, run_output: dict[str, object]) -> float:
        del run_output
        result = subprocess.run(
            [
                "npx",
                "lighthouse",
                LIGHTHOUSE_URL,
                "--output=json",
                "--quiet",
                f"--only-categories={LIGHTHOUSE_CATEGORIES}",
            ],
            capture_output=True,
            text=True,
            cwd=BLOG_DIR,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr or result.stdout or "Lighthouse failed")
        scores = json.loads(result.stdout)
        a11y = scores["categories"]["accessibility"]["score"]
        perf = scores["categories"]["performance"]["score"]
        return (a11y + perf) / 2

    def rollback(self) -> None:
        subprocess.run(["git", "checkout", *BLOG_EDIT_PATHS], cwd=BLOG_REPO_DIR, check=False)

    def commit(self, change_desc: str, iteration: int) -> None:
        subprocess.run(["git", "add", *BLOG_EDIT_PATHS], cwd=BLOG_REPO_DIR, check=False)
        subprocess.run(
            ["git", "commit", "-m", f"ui(autoresearch iter-{iteration}): {change_desc}"],
            cwd=BLOG_REPO_DIR,
            check=False,
        )

    def _run_claude(self, prompt: str) -> str:
        result = subprocess.run(
            [
                "claude",
                "--dangerously-skip-permissions",
                "-p",
                prompt,
            ],
            cwd=BLOG_REPO_DIR,
            capture_output=True,
            text=True,
            timeout=OPTIMIZER_TIMEOUT_SECONDS,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr or result.stdout or "Claude command failed")
        return result.stdout

    def _run_codex(self, prompt: str) -> str:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".txt", delete=False
        ) as output_file:
            output_path = output_file.name

        try:
            result = subprocess.run(
                [
                    "codex",
                    "exec",
                    "--full-auto",
                    "--output-last-message",
                    output_path,
                    prompt,
                ],
                cwd=BLOG_REPO_DIR,
                capture_output=True,
                text=True,
                timeout=OPTIMIZER_TIMEOUT_SECONDS,
                check=False,
            )
            if result.returncode != 0:
                raise RuntimeError(result.stderr or result.stdout or "Codex command failed")
            with open(output_path, encoding="utf-8") as handle:
                return handle.read()
        finally:
            Path(output_path).unlink(missing_ok=True)

    def _parse_agent_output(self, raw_output: str) -> dict[str, object]:
        payload = raw_output.strip()
        if not payload:
            raise RuntimeError(f"{OPTIMIZER_AGENT} returned empty output")

        candidates = [payload]
        if payload.startswith("```") and payload.endswith("```"):
            lines = payload.splitlines()
            if len(lines) >= 3:
                candidates.append("\n".join(lines[1:-1]).strip())

        for candidate in candidates:
            try:
                parsed = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed

        raise RuntimeError(
            f"{OPTIMIZER_AGENT} returned non-JSON output: {payload[:500]}"
        )
