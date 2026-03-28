from __future__ import annotations

from autoresearch_cycle.adapters.synthetic import SyntheticDomainAdapter
from autoresearch_cycle.models import ObjectiveDefinition, OptimizerContext, PolicyRecord
from autoresearch_cycle.optimizers.random_optimizer import RandomOptimizer
from autoresearch_cycle.utils import hash_policy_content, utc_now


def test_random_optimizer_returns_schema_valid_non_duplicate_policy() -> None:
    adapter = SyntheticDomainAdapter()
    baseline_content = {"x": 0.0, "y": 0.0, "noise": 0.1}
    baseline = PolicyRecord(
        policy_id="pol_base",
        domain_id="synthetic",
        schema_version="1.0",
        content=baseline_content,
        created_at=utc_now(),
        content_hash=hash_policy_content(baseline_content),
    )
    context = OptimizerContext(
        domain_id="synthetic",
        policy_schema=adapter.get_policy_schema(),
        baseline_policy=baseline,
        recent_runs=[],
        existing_policies=[baseline],
        objective=ObjectiveDefinition(name="score", direction="maximize"),
        constraints=[],
    )

    proposal = RandomOptimizer().propose(context)

    adapter.validate_policy(proposal.candidate_policy)
    assert hash_policy_content(proposal.candidate_policy) != baseline.content_hash
