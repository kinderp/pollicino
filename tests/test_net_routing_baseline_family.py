from pollicino.net import ScarceLinkProfile
from pollicino.net.bearer import BearerKind, BearerProfile, EvidenceBasis
from pollicino.net.fair_scheduling import BearerSchedulingPolicy, FairnessPolicy
from pollicino.net.routing_baseline_factory import canonical_dtn_strategy_factory
from pollicino.net.scenario_family import (
    SyntheticBearerTemplate,
    SyntheticScenarioFamilyConfig,
    generate_synthetic_scenario_family,
)
from pollicino.net.scheduling import ContactSchedulingPolicy


def _template() -> SyntheticBearerTemplate:
    profile = BearerProfile(
        bearer_id="synthetic-lora",
        kind=BearerKind.LORA,
        evidence_basis=EvidenceBasis.SYNTHETIC,
        link_profile=ScarceLinkProfile(
            max_frame_bytes=64,
            bitrate_bps=5000,
            ack_bytes=8,
            max_retries=2,
            seed=91,
        ),
    )
    policy = BearerSchedulingPolicy(
        bearer_id="synthetic-lora",
        contact_policy=ContactSchedulingPolicy(
            max_source_bytes=256,
            max_bundles=8,
            max_chunks_per_bundle=4,
        ),
        fairness_policy=FairnessPolicy(
            starvation_seconds=120,
            max_rescue_bundles=1,
            rescue_chunks_per_bundle=1,
        ),
    )
    return SyntheticBearerTemplate(
        profile=profile,
        scheduling_policy=policy,
        selection_weight=1,
        min_duration_seconds=5,
        max_duration_seconds=20,
        min_logical_source_byte_budget=64,
        max_logical_source_byte_budget=128,
    )


def _config() -> SyntheticScenarioFamilyConfig:
    return SyntheticScenarioFamilyConfig(
        family_id="canonical-dtn-family",
        seed=20260827,
        scenario_count=4,
        peer_count=8,
        gateway_count=2,
        bundle_count=2,
        windows_per_scenario=40,
        start_s=1000,
        horizon_seconds=900,
        chunk_size=64,
        min_bundle_chunks=1,
        max_bundle_chunks=1,
        min_ttl_seconds=600,
        max_ttl_seconds=1800,
        hop_limit=12,
    )


def test_seeded_family_runs_all_canonical_dtn_baselines_on_same_scenarios() -> None:
    family = generate_synthetic_scenario_family(
        _config(),
        bearer_templates=(_template(),),
        strategy_factory=canonical_dtn_strategy_factory,
    )
    report = family.run_benchmark()

    expected = {
        "direct-delivery",
        "epidemic",
        "binary-spray-and-wait",
        "prophet",
    }
    assert {item.strategy_id for item in report.strategies} == expected
    assert report.evidence_class == "model_synthetic"
    for strategy_id in expected:
        strategy = report.strategy(strategy_id)
        assert strategy.scenario_count == 4
        assert strategy.bundle_opportunity_count == 8
        assert strategy.total_window_count == 160


def test_canonical_dtn_family_is_reproducible_for_same_seed() -> None:
    first = generate_synthetic_scenario_family(
        _config(),
        bearer_templates=(_template(),),
        strategy_factory=canonical_dtn_strategy_factory,
    ).run_benchmark()
    second = generate_synthetic_scenario_family(
        _config(),
        bearer_templates=(_template(),),
        strategy_factory=canonical_dtn_strategy_factory,
    ).run_benchmark()

    for strategy_id in (
        "direct-delivery",
        "epidemic",
        "binary-spray-and-wait",
        "prophet",
    ):
        left = first.strategy(strategy_id)
        right = second.strategy(strategy_id)
        assert left.delivered_bundle_count == right.delivered_bundle_count
        assert left.delivery_latency_samples_s == right.delivery_latency_samples_s
        assert left.used_source_bytes == right.used_source_bytes
        assert left.total_wire_bytes == right.total_wire_bytes
        assert left.forwarding_decision_count == right.forwarding_decision_count
