from __future__ import annotations

import copy
import random
from typing import Any

from ..models import CandidatePolicyProposal, OptimizerContext
from ..utils import canonical_json, hash_policy_content
from .base import Optimizer


class RandomOptimizer(Optimizer):
    optimizer_id = "random"

    def propose(self, context: OptimizerContext) -> CandidatePolicyProposal:
        schema = context.policy_schema
        baseline = context.baseline_policy.content
        numeric_fields = {
            name: definition
            for name, definition in schema.get("properties", {}).items()
            if definition.get("type") in {"number", "integer"}
        }
        if not numeric_fields:
            raise ValueError("random optimizer requires numeric policy fields")

        existing_hashes = {policy.content_hash for policy in context.existing_policies}
        seed_basis = canonical_json(
            {
                "baseline": baseline,
                "run_count": len(context.recent_runs),
                "policy_count": len(context.existing_policies),
            }
        )
        rng = random.Random(seed_basis)

        for attempt in range(1, 26):
            candidate = copy.deepcopy(baseline)
            mutated_fields: list[str] = []
            for field_name, definition in numeric_fields.items():
                minimum = float(definition.get("minimum", -10.0))
                maximum = float(definition.get("maximum", 10.0))
                range_width = max(maximum - minimum, 1.0)
                should_mutate = rng.random() < 0.75 or not mutated_fields
                if not should_mutate:
                    continue
                current_value = float(candidate[field_name])
                step = range_width * (0.15 + rng.random() * 0.35)
                proposed_value = current_value + rng.uniform(-step, step)
                proposed_value = max(minimum, min(maximum, proposed_value))
                if definition.get("type") == "integer":
                    candidate[field_name] = int(round(proposed_value))
                else:
                    candidate[field_name] = round(proposed_value, 4)
                mutated_fields.append(field_name)

            candidate_hash = hash_policy_content(candidate)
            if candidate_hash not in existing_hashes:
                rationale = (
                    "Random local search mutated "
                    + ", ".join(mutated_fields)
                    + f" on attempt {attempt}."
                )
                return CandidatePolicyProposal(
                    candidate_policy=candidate,
                    rationale=rationale,
                    metadata={"mutated_fields": mutated_fields, "attempt": attempt},
                )

        fallback = self._global_resample(numeric_fields, rng)
        return CandidatePolicyProposal(
            candidate_policy=fallback,
            rationale="Fallback global resample after duplicate local mutations.",
            metadata={"mutated_fields": sorted(numeric_fields), "attempt": 26},
        )

    def _global_resample(
        self,
        numeric_fields: dict[str, dict[str, Any]],
        rng: random.Random,
    ) -> dict[str, Any]:
        candidate: dict[str, Any] = {}
        for field_name, definition in numeric_fields.items():
            minimum = float(definition.get("minimum", -10.0))
            maximum = float(definition.get("maximum", 10.0))
            value = rng.uniform(minimum, maximum)
            if definition.get("type") == "integer":
                candidate[field_name] = int(round(value))
            else:
                candidate[field_name] = round(value, 4)
        return candidate
