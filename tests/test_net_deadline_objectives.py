import hashlib

import pytest

from pollicino.net import PollicinoStore, ScarceLinkProfile
from pollicino.net.bearer import BearerKind, BearerProfile, EvidenceBasis
from pollicino.net.bundle import CustodyLedger, ForwardBundle, seed_bundle_custody
from pollicino.net.contact_windows import SyntheticContactWindow
from pollicino.net.deadline_objectives import (
    ApplicationDeadlineObjective,
    evaluate_application_deadlines,
)
from pollicino.net.fair_scheduling import BearerSchedulingPolicy, FairnessPolicy
from pollicino.net.routing_baselines import DirectDeliveryStrategy, EpidemicStrategy
from pollicino.net.routing_benchmark import RoutingBenchmarkScenario, run_synthetic_routing_benchmark
from pollicino.net.scheduling import BundlePriority, ContactSchedulingPolicy, ScheduledBundle
from pollicino.net.store_forward import ForwardPeer, seed_forwarding_object
from pollicino.net.wire import DiscoveryDescriptor


def _link(seed: int) -> ScarceLinkProfile:
    return ScarceLinkProfile(
        max_frame_bytes=64,
        bitrate_bps=5000,
        ack_bytes=8,
        max_retries=2,
        seed=seed,
    )


def _bearer() -> BearerProfile:
    return BearerProfile(
        bearer_id="lora",
        kind=BearerKind.LORA,
        evidence_basis=EvidenceBasis.SYNTHETIC,
        link_profile=_link(101),
    )


def _policy() -> BearerSchedulingPolicy:
    return BearerSchedulingPolicy(
        bearer_id="lora",
        contact_policy=ContactSchedulingPolicy(
            max_source_bytes=4096,
            max_bundles=8,
            max_chunks_per_bundle=8,
        ),
        fairness_policy=FairnessPolicy(
            starvation_seconds=100,
            max_rescue_bundles=1,
            rescue_chunks_per_bundle=1,
        ),
    )


def _content(label: str) -> bytes:
    digest = hashlib.sha256(label.encode()).digest()
    return digest * 2


def _bundle(origin: ForwardPeer, ledger: CustodyLedger, *, nonce: int) -> ScheduledBundle:
    manifest = seed_forwarding_object(
        _content(f"deadline-{nonce}"),
        chunk_size=64,
        store=origin.store,
    )
    descriptor = DiscoveryDescriptor(
        object_class=1,
        rendezvous_key=f"deadline-{nonce}".encode(),
        ttl_seconds=1000,
        hop_limit=8,
        nonce=nonce,
    )
    bundle = ForwardBundle.from_descriptor(manifest, descriptor, created_at_s=1000)
    seed_bundle_custody(bundle, manifest, origin=origin, ledger=ledger, now_s=1000)
    return ScheduledBundle(
        bundle=bundle,
        manifest=manifest,
        priority=BundlePriority.NORMAL,
        label=f"deadline-{nonce}",
    )


def _scenario(scenario_id: str, *, nonce: int, direct: bool) -> RoutingBenchmarkScenario:
    peer_ids = ("a", "d") if direct else ("a", "x", "d")
    peers = {
        peer_id: ForwardPeer(peer_id, PollicinoStore())
        for peer_id in peer_ids
    }
    ledger = CustodyLedger()
    item = _bundle(peers["a"], ledger, nonce=nonce)
    if direct:
        windows = (
            SyntheticContactWindow("a-d", "a", "d", "lora", 1010, 5, 64, 100),
        )
    else:
        windows = (
            SyntheticContactWindow("a-x", "a", "x", "lora", 1001, 5, 64, 100),
            SyntheticContactWindow("x-d", "x", "d", "lora", 1010, 5, 64, 200),
        )
    return RoutingBenchmarkScenario(
        scenario_id=scenario_id,
        strategies=(DirectDeliveryStrategy(("d",)), EpidemicStrategy()),
        bundles=(item,),
        peers=peers,
        ledger=ledger,
        windows=windows,
        bearers={"lora": _bearer()},
        scheduling_policies={"lora": _policy()},
        scheduler_states={},
        destination_ids=("d",),
    )


def _objective(scenario: RoutingBenchmarkScenario, deadline_s: int) -> ApplicationDeadlineObjective:
    return ApplicationDeadlineObjective(
        scenario_id=scenario.scenario_id,
        bundle_id=scenario.bundles[0].bundle.bundle_id.hex(),
        deadline_s=deadline_s,
    )


def test_deadline_evaluator_distinguishes_on_time_late_and_undelivered() -> None:
    relay_on_time = _scenario("relay-on-time", nonce=1, direct=False)
    relay_late = _scenario("relay-late", nonce=2, direct=False)
    direct_on_time = _scenario("direct-on-time", nonce=3, direct=True)
    scenarios = (relay_on_time, relay_late, direct_on_time)
    benchmark = run_synthetic_routing_benchmark(scenarios)

    deadline_report = evaluate_application_deadlines(
        benchmark,
        scenarios,
        (
            _objective(relay_on_time, 1015),
            _objective(relay_late, 1012),
            _objective(direct_on_time, 1015),
        ),
    )

    direct = deadline_report.strategy("direct-delivery")
    epidemic = deadline_report.strategy("epidemic")

    assert direct.deadline_opportunity_count == 3
    assert direct.delivered_before_deadline_count == 1
    assert direct.delivered_late_count == 0
    assert direct.undelivered_count == 2
    assert direct.on_time_delivery_rate == pytest.approx(1 / 3)

    assert epidemic.deadline_opportunity_count == 3
    assert epidemic.delivered_before_deadline_count == 2
    assert epidemic.delivered_late_count == 1
    assert epidemic.undelivered_count == 0
    assert epidemic.on_time_delivery_rate == pytest.approx(2 / 3)
    assert epidemic.eventual_delivery_count == 3
    assert epidemic.delivery_slack_samples_s == (-3, 0, 0)
    assert epidemic.mean_delivery_slack_s == -1.0
    assert deadline_report.evidence_class == "model_synthetic"

    # The evaluator is observational only; it cannot alter benchmark wire accounting.
    assert benchmark.strategy("epidemic").total_wire_bytes > 0


def test_application_deadline_is_independent_from_transport_ttl() -> None:
    scenario = _scenario("deadline-before-ttl", nonce=4, direct=False)
    item = scenario.bundles[0]
    transport_expiry = item.bundle.created_at_s + item.bundle.ttl_seconds
    assert transport_expiry == 2000

    benchmark = run_synthetic_routing_benchmark((scenario,))
    objective = _objective(scenario, 1012)
    report = evaluate_application_deadlines(benchmark, (scenario,), (objective,))

    epidemic = report.strategy("epidemic")
    assert epidemic.delivered_late_count == 1
    assert epidemic.undelivered_count == 0
    assert objective.deadline_s < transport_expiry


def test_deadline_objectives_fail_closed_on_invalid_references() -> None:
    scenario = _scenario("validation", nonce=5, direct=True)
    benchmark = run_synthetic_routing_benchmark((scenario,))
    bundle_id = scenario.bundles[0].bundle.bundle_id.hex()

    with pytest.raises(ValueError, match="precede bundle creation"):
        evaluate_application_deadlines(
            benchmark,
            (scenario,),
            (ApplicationDeadlineObjective("validation", bundle_id, 999),),
        )

    with pytest.raises(KeyError, match="unknown scenario"):
        evaluate_application_deadlines(
            benchmark,
            (scenario,),
            (ApplicationDeadlineObjective("missing", bundle_id, 1015),),
        )

    with pytest.raises(KeyError, match="unknown bundle"):
        evaluate_application_deadlines(
            benchmark,
            (scenario,),
            (ApplicationDeadlineObjective("validation", "00" * 32, 1015),),
        )

    objective = ApplicationDeadlineObjective("validation", bundle_id, 1015)
    with pytest.raises(ValueError, match="unique"):
        evaluate_application_deadlines(
            benchmark,
            (scenario,),
            (objective, objective),
        )
