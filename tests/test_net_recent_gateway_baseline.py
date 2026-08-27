import runpy

from pollicino.net.rapid_control_wire import (
    RapidControlWireProfile,
    RapidNodeReferenceMode,
    account_rapid_control_wire,
    rapid_modeled_total_wire_bytes,
)
from pollicino.net.rapid_schedule import RapidPriorMeetingObservation, run_rapid_deadline_schedule
from pollicino.net.recent_gateway_baseline import (
    PriorGatewayEncounter,
    RecentGatewayControlProfile,
    RecentGatewayEncounterStrategy,
    recent_gateway_control_wire_bytes,
)
from pollicino.net.routing_baselines import EpidemicStrategy
from pollicino.net.routing_compare import compare_synthetic_routing_strategies


def _scenario():
    ns = runpy.run_path("tests/test_net_edu_deadline_discrimination.py")
    scenario, item, _spray, _prophet = ns["_scenario"]()
    return scenario, item


def test_recent_gateway_baseline_matches_on_time_path_with_tiny_control_model() -> None:
    scenario, item = _scenario()
    simple = RecentGatewayEncounterStrategy(
        ("d",),
        prior_encounters=(
            PriorGatewayEncounter("a", "d", 0),
            PriorGatewayEncounter("b", "d", 40),
        ),
    )

    comparison = compare_synthetic_routing_strategies(
        (simple, EpidemicStrategy()),
        scenario.bundles,
        peers=scenario.peers,
        ledger=scenario.ledger,
        windows=scenario.windows,
        bearers=scenario.bearers,
        scheduling_policies=scenario.scheduling_policies,
        scheduler_states=scenario.scheduler_states,
        destination_ids=scenario.destination_ids,
    )
    recent = comparison.strategy("recent-gateway-encounter")
    epidemic = comparison.strategy("epidemic")

    outcome = recent.outcome_for_label("edu-resource")
    assert outcome.delivered
    assert outcome.first_delivery_s == 1025
    assert recent.windows[1].scheduling is None  # A->X: X has no gateway history
    assert recent.windows[2].scheduling is not None  # A->B: B has fresher direct history
    assert recent.used_source_bytes == 128
    assert epidemic.used_source_bytes == 192
    assert recent.total_wire_bytes < epidemic.total_wire_bytes

    # Only A-X and A-B need recency-score exchange. The first B-D window and
    # later final-delivery windows target D directly.
    control = recent_gateway_control_wire_bytes(
        non_destination_encounter_count=2,
        profile=RecentGatewayControlProfile(),
    )
    assert control == 44
    assert recent.total_wire_bytes + control < epidemic.total_wire_bytes


def test_simple_baseline_is_far_cheaper_than_rapid_control_on_same_behavioral_case() -> None:
    scenario, item = _scenario()
    simple = RecentGatewayEncounterStrategy(
        ("d",),
        prior_encounters=(
            PriorGatewayEncounter("a", "d", 0),
            PriorGatewayEncounter("b", "d", 40),
        ),
    )
    recent = compare_synthetic_routing_strategies(
        (simple,),
        scenario.bundles,
        peers=scenario.peers,
        ledger=scenario.ledger,
        windows=scenario.windows,
        bearers=scenario.bearers,
        scheduling_policies=scenario.scheduling_policies,
        scheduler_states=scenario.scheduler_states,
        destination_ids=scenario.destination_ids,
    ).strategy("recent-gateway-encounter")
    simple_total = recent.total_wire_bytes + recent_gateway_control_wire_bytes(
        non_destination_encounter_count=2
    )

    rapid = run_rapid_deadline_schedule(
        scenario.bundles,
        peers=scenario.peers,
        ledger=scenario.ledger,
        windows=scenario.windows,
        bearers=scenario.bearers,
        scheduling_policies=scenario.scheduling_policies,
        scheduler_states=scenario.scheduler_states,
        destination_id="d",
        application_deadlines={item.bundle.bundle_id: 1030},
        prior_meetings=(
            RapidPriorMeetingObservation("a", "d", 0, opportunity_bytes_a_to_b=64),
            RapidPriorMeetingObservation("b", "d", 0, opportunity_bytes_a_to_b=64),
            RapidPriorMeetingObservation("b", "d", 40, opportunity_bytes_a_to_b=64),
            RapidPriorMeetingObservation("a", "d", 100, opportunity_bytes_a_to_b=64),
        ),
    )
    full_control = account_rapid_control_wire(
        rapid,
        profile=RapidControlWireProfile(RapidNodeReferenceMode.FULL_PSEUDONYM_128),
        node_count=4,
    )
    indexed_control = account_rapid_control_wire(
        rapid,
        profile=RapidControlWireProfile(RapidNodeReferenceMode.SHARED_U16_INDEX),
        node_count=4,
    )

    assert recent.outcomes[0].first_delivery_s == rapid.routing.outcomes[0].first_delivery_s == 1025
    assert simple_total < rapid_modeled_total_wire_bytes(rapid, control=full_control)
    assert simple_total < rapid_modeled_total_wire_bytes(rapid, control=indexed_control)


def test_prior_gateway_history_must_precede_windows() -> None:
    scenario, _item = _scenario()
    strategy = RecentGatewayEncounterStrategy(
        ("d",),
        prior_encounters=(PriorGatewayEncounter("b", "d", 1005),),
    )
    try:
        compare_synthetic_routing_strategies(
            (strategy,),
            scenario.bundles,
            peers=scenario.peers,
            ledger=scenario.ledger,
            windows=scenario.windows,
            bearers=scenario.bearers,
            scheduling_policies=scenario.scheduling_policies,
            scheduler_states=scenario.scheduler_states,
            destination_ids=scenario.destination_ids,
        )
    except ValueError as exc:
        assert "precede routing windows" in str(exc)
    else:
        raise AssertionError("future prior history must be rejected")
