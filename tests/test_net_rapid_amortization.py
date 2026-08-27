import runpy

from pollicino.net.rapid_amortization import (
    RapidAmortizationInput,
    rapid_amortization_point,
    sweep_rapid_amortization,
)
from pollicino.net.rapid_control_wire import (
    RapidControlWireProfile,
    RapidNodeReferenceMode,
    account_rapid_control_wire,
)


def _checkpoint_model(mode: RapidNodeReferenceMode) -> RapidAmortizationInput:
    ns = runpy.run_path("tests/test_net_rapid_schedule.py")
    _peers, _ledger, _item, _windows, rapid = ns["_run_rapid"]()
    control = account_rapid_control_wire(
        rapid,
        profile=RapidControlWireProfile(mode),
        node_count=4,
    )
    # The established 64-byte checkpoint compares RAPID's two governed copies
    # against Epidemic's three: 1260 B versus 1890 B.
    return RapidAmortizationInput.from_control_breakdown(
        rapid_transfer_wire_bytes_per_bundle=1260,
        baseline_wire_bytes_per_bundle=1890,
        control=control,
    )


def test_amortization_decomposition_recomposes_single_bundle_checkpoint() -> None:
    full = _checkpoint_model(RapidNodeReferenceMode.FULL_PSEUDONYM_128)
    indexed = _checkpoint_model(RapidNodeReferenceMode.SHARED_U16_INDEX)

    full_one = rapid_amortization_point(full, bundle_count=1)
    indexed_one = rapid_amortization_point(indexed, bundle_count=1)

    assert full_one.rapid_modeled_total_wire_bytes == 1958
    assert full_one.delta_vs_baseline_bytes == 68
    assert indexed_one.rapid_modeled_total_wire_bytes == 1768
    assert indexed_one.delta_vs_baseline_bytes == -122


def test_reusing_meeting_state_can_make_full_id_control_pay_for_itself() -> None:
    model = _checkpoint_model(RapidNodeReferenceMode.FULL_PSEUDONYM_128)
    sweep = sweep_rapid_amortization(model, (1, 2, 5, 10, 20))

    # Meeting knowledge is the only shared cost in full-ID mode. Once reused by
    # a second otherwise-similar object, avoided Epidemic replication outweighs
    # this checkpoint's bundle-specific control and governed transfer cost.
    assert sweep.points[0].delta_vs_baseline_bytes == 68
    assert sweep.first_cheaper_bundle_count == 2
    assert sweep.points[1].delta_vs_baseline_bytes < 0
    assert sweep.points[-1].delta_vs_baseline_bytes < sweep.points[1].delta_vs_baseline_bytes
    assert sweep.points[-1].shared_control_wire_bytes_per_bundle < sweep.points[0].shared_control_wire_bytes_per_bundle


def test_indexed_control_remains_optimistic_and_amortizes_bootstrap() -> None:
    model = _checkpoint_model(RapidNodeReferenceMode.SHARED_U16_INDEX)
    sweep = sweep_rapid_amortization(model, (1, 2, 5, 10, 20))

    assert sweep.first_cheaper_bundle_count == 1
    assert model.shared_control_wire_bytes > 0  # meeting state + dictionary representation
    assert sweep.points[-1].shared_control_wire_bytes_per_bundle < sweep.points[0].shared_control_wire_bytes_per_bundle


def test_amortization_rejects_invalid_counts() -> None:
    model = _checkpoint_model(RapidNodeReferenceMode.FULL_PSEUDONYM_128)
    try:
        rapid_amortization_point(model, bundle_count=0)
    except ValueError:
        pass
    else:
        raise AssertionError("zero bundle count must be rejected")

    try:
        sweep_rapid_amortization(model, (1, 1))
    except ValueError:
        pass
    else:
        raise AssertionError("duplicate bundle counts must be rejected")
