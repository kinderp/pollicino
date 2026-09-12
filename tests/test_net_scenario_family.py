from pollicino.net.bearer import BearerKind, BearerProfile, EvidenceBasis
from pollicino.net.fair_scheduling import BearerSchedulingPolicy, FairnessPolicy
from pollicino.net.link import ScarceLinkProfile
from pollicino.net.scenario_family import (
    SyntheticBearerTemplate,
    SyntheticScenarioFamilyConfig,
    generate_synthetic_scenario_family,
)
from pollicino.net.scheduling import ContactSchedulingPolicy


def link(seed: int) -> ScarceLinkProfile:
    return ScarceLinkProfile(
        max_frame_bytes=64,
        bitrate_bps=5000,
        ack_bytes=8,
        max_retries=3,
        seed=seed,
    )


def template(
    bearer_id: str,
    kind: BearerKind,
    *,
    seed: int,
    weight: int,
    duration: tuple[int, int],
    budget: tuple[int, int],
) -> SyntheticBearerTemplate:
    profile = BearerProfile(
        bearer_id=bearer_id,
        kind=kind,
        evidence_basis=EvidenceBasis.SYNTHETIC,
        link_profile=link(seed),
    )
    policy = BearerSchedulingPolicy(
        bearer_id=bearer_id,
        contact_policy=ContactSchedulingPolicy(
            max_source_bytes=4096,
            max_bundles=16,
            max_chunks_per_bundle=16,
        ),
        fairness_policy=FairnessPolicy(
            starvation_seconds=100,
            max_rescue_bundles=1,
            rescue_chunks_per_bundle=1,
        ),
    )
    return SyntheticBearerTemplate(
        profile=profile,
        scheduling_policy=policy,
        selection_weight=weight,
        min_duration_seconds=duration[0],
        max_duration_seconds=duration[1],
        min_logical_source_byte_budget=budget[0],
        max_logical_source_byte_budget=budget[1],
    )


def templates() -> tuple[SyntheticBearerTemplate, ...]:
    return (
        template(
            "lora",
            BearerKind.LORA,
            seed=61,
            weight=7,
            duration=(5, 20),
            budget=(64, 128),
        ),
        template(
            "wifi",
            BearerKind.WIFI,
            seed=62,
            weight=3,
            duration=(3, 15),
            budget=(128, 512),
        ),
    )


def config(*, seed: int = 1234) -> SyntheticScenarioFamilyConfig:
    return SyntheticScenarioFamilyConfig(
        family_id="messina-student-network-long-family-name",
        seed=seed,
        scenario_count=3,
        peer_count=7,
        gateway_count=2,
        bundle_count=3,
        windows_per_scenario=24,
        start_s=1000,
        horizon_seconds=600,
        chunk_size=64,
        min_bundle_chunks=1,
        max_bundle_chunks=3,
        min_ttl_seconds=120,
        max_ttl_seconds=900,
        hop_limit=8,
        priority_weights=(1, 5, 2, 2),
    )


def signature(family):
    result = []
    for scenario, summary in zip(family.scenarios, family.summaries):
        windows = tuple(
            (
                item.encounter_id,
                item.source_id,
                item.target_id,
                item.bearer_id,
                item.start_s,
                item.duration_seconds,
                item.logical_source_byte_budget,
                item.transfer_id_base,
            )
            for item in scenario.windows
        )
        bundles = tuple(
            (
                item.bundle.bundle_id.hex(),
                int(item.priority),
                item.manifest.object_size,
                item.bundle.ttl_seconds,
            )
            for item in scenario.bundles
        )
        result.append(
            (
                scenario.scenario_id,
                summary.scenario_seed,
                summary.gateway_ids,
                summary.static_gateway_rank,
                windows,
                bundles,
            )
        )
    return tuple(result)


def test_same_seed_generates_identical_family() -> None:
    first = generate_synthetic_scenario_family(config(), bearer_templates=templates())
    second = generate_synthetic_scenario_family(config(), bearer_templates=templates())

    assert signature(first) == signature(second)


def test_different_seed_changes_generated_family() -> None:
    first = generate_synthetic_scenario_family(config(seed=1234), bearer_templates=templates())
    second = generate_synthetic_scenario_family(config(seed=1235), bearer_templates=templates())

    assert signature(first) != signature(second)


def test_generated_ids_are_pseudonymous_and_gateway_rank_is_synthetic() -> None:
    family = generate_synthetic_scenario_family(config(), bearer_templates=templates())

    for scenario, summary in zip(family.scenarios, family.summaries):
        assert all(peer_id.startswith("node-") for peer_id in scenario.peers)
        assert all(gateway_id.startswith("node-") for gateway_id in summary.gateway_ids)
        assert all(summary.rank_for(gateway_id) == 0 for gateway_id in summary.gateway_ids)
        assert scenario.destination_ids == summary.gateway_ids
        assert all("latitude" not in tag and "longitude" not in tag for tag in scenario.tags)


def test_long_family_id_still_builds_valid_pnd1_descriptors() -> None:
    family = generate_synthetic_scenario_family(config(), bearer_templates=templates())

    for scenario in family.scenarios:
        for item in scenario.bundles:
            # ForwardBundle creation only succeeds after the bounded PND1 descriptor
            # has been validated and encoded into the immutable bundle identity.
            assert len(item.bundle.discovery_sha256) == 32
            assert len(item.bundle.bundle_id) == 32


def test_generated_family_runs_multi_scenario_benchmark() -> None:
    family = generate_synthetic_scenario_family(config(), bearer_templates=templates())
    report = family.run_benchmark()

    assert len(report.scenarios) == 3
    assert {item.strategy_id for item in report.strategies} == {
        "flood-all",
        "gateway-progress",
        "emergency-flood-progress",
    }
    assert all(item.scenario_count == 3 for item in report.strategies)
    assert all(item.bundle_opportunity_count == 9 for item in report.strategies)


def test_duration_and_budget_are_explicit_independent_synthetic_inputs() -> None:
    fixed_duration_templates = (
        template(
            "lora",
            BearerKind.LORA,
            seed=63,
            weight=1,
            duration=(10, 10),
            budget=(64, 192),
        ),
    )
    family = generate_synthetic_scenario_family(
        SyntheticScenarioFamilyConfig(
            family_id="independent-inputs",
            seed=99,
            scenario_count=1,
            peer_count=5,
            gateway_count=1,
            bundle_count=1,
            windows_per_scenario=20,
            start_s=1000,
            horizon_seconds=200,
            chunk_size=64,
            min_bundle_chunks=1,
            max_bundle_chunks=1,
            min_ttl_seconds=500,
            max_ttl_seconds=500,
        ),
        bearer_templates=fixed_duration_templates,
    )
    windows = family.scenarios[0].windows

    assert {item.duration_seconds for item in windows} == {10}
    assert len({item.logical_source_byte_budget for item in windows}) > 1
