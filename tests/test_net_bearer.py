import hashlib

import pytest

from pollicino.net import (
    BearerGovernedContact,
    BearerKind,
    BearerProfile,
    CustodyLedger,
    EvidenceBasis,
    ForwardBundle,
    ForwardPeer,
    GovernedForwardContact,
    PollicinoStore,
    ScarceLinkProfile,
    run_per_bearer_governed_schedule,
    seed_bundle_custody,
    seed_forwarding_object,
)
from pollicino.net.wire import DiscoveryDescriptor


def clean_profile(seed: int) -> ScarceLinkProfile:
    return ScarceLinkProfile(
        max_frame_bytes=64,
        bitrate_bps=5000,
        ack_bytes=8,
        max_retries=3,
        seed=seed,
    )


def data_for_chunks(count: int, chunk_size: int = 64) -> bytes:
    pieces = []
    for index in range(count):
        seed = hashlib.sha256(f"bearer-{index}".encode()).digest()
        pieces.append((seed * ((chunk_size + 31) // 32))[:chunk_size])
    return b"".join(pieces)


def descriptor(*, hop_limit: int = 4) -> DiscoveryDescriptor:
    return DiscoveryDescriptor(
        object_class=1,
        rendezvous_key=b"bearer-demo",
        ttl_seconds=3600,
        nonce=123,
        hop_limit=hop_limit,
    )


def test_measured_profile_requires_provenance() -> None:
    with pytest.raises(ValueError, match="explicit provenance"):
        BearerProfile(
            bearer_id="lora-measured",
            kind=BearerKind.LORA,
            evidence_basis=EvidenceBasis.MEASURED,
            link_profile=clean_profile(1),
        )

    measured = BearerProfile(
        bearer_id="lora-measured",
        kind=BearerKind.LORA,
        evidence_basis=EvidenceBasis.MEASURED,
        link_profile=clean_profile(1),
        provenance="HW-006/example-checkpoint.json",
    )
    assert measured.provenance == "HW-006/example-checkpoint.json"


def test_four_bearers_are_accounted_separately() -> None:
    data = data_for_chunks(6)
    origin = ForwardPeer("origin", PollicinoStore())
    relay = ForwardPeer("relay", PollicinoStore())
    destination = ForwardPeer("destination", PollicinoStore())
    manifest = seed_forwarding_object(data, chunk_size=64, store=origin.store)

    desc = descriptor()
    bundle = ForwardBundle.from_descriptor(manifest, desc, created_at_s=100)
    ledger = CustodyLedger()
    seed_bundle_custody(bundle, manifest, origin=origin, ledger=ledger, now_s=100)

    bearers = {
        "lora-sim": BearerProfile(
            "lora-sim", BearerKind.LORA, EvidenceBasis.SYNTHETIC, clean_profile(1), "scenario:lora"
        ),
        "ble-sim": BearerProfile(
            "ble-sim", BearerKind.BLE, EvidenceBasis.SYNTHETIC, clean_profile(2), "scenario:ble"
        ),
        "wifi-sim": BearerProfile(
            "wifi-sim", BearerKind.WIFI, EvidenceBasis.SYNTHETIC, clean_profile(3), "scenario:wifi"
        ),
        "internet-sim": BearerProfile(
            "internet-sim", BearerKind.INTERNET, EvidenceBasis.SYNTHETIC, clean_profile(4), "scenario:internet"
        ),
    }
    contacts = (
        BearerGovernedContact(
            GovernedForwardContact("origin", "relay", 1000, 3, "c1", 110), "lora-sim"
        ),
        BearerGovernedContact(
            GovernedForwardContact("relay", "destination", 2000, 3, "c2", 120), "ble-sim"
        ),
        BearerGovernedContact(
            GovernedForwardContact("origin", "relay", 3000, 10, "c3", 130), "wifi-sim"
        ),
        BearerGovernedContact(
            GovernedForwardContact("relay", "destination", 4000, 10, "c4", 140), "internet-sim"
        ),
    )

    reconstructed, report = run_per_bearer_governed_schedule(
        bundle,
        manifest,
        peers={"origin": origin, "relay": relay, "destination": destination},
        contacts=contacts,
        destination_id="destination",
        ledger=ledger,
        bearers=bearers,
    )

    assert reconstructed == data
    assert report.destination_complete and report.destination_exact
    assert {line.kind for line in report.lines} == {
        BearerKind.LORA,
        BearerKind.BLE,
        BearerKind.WIFI,
        BearerKind.INTERNET,
    }
    assert report.contains_synthetic_profile
    assert not report.contains_measured_profile
    assert not report.fully_physical_replay
    assert report.total_wire_bytes == sum(line.total_wire_bytes for line in report.lines)
    for bearer_id in bearers:
        line = report.line_for(bearer_id)
        assert line.contact_count == 1
        assert line.forwarded_contact_count == 1
        assert line.model_contact_count == 1
        assert line.physical_replay_contact_count == 0
        assert line.total_wire_bytes > 0


def test_measured_parameters_do_not_turn_a_model_run_into_physical_evidence() -> None:
    data = data_for_chunks(1)
    origin = ForwardPeer("origin", PollicinoStore())
    destination = ForwardPeer("destination", PollicinoStore())
    manifest = seed_forwarding_object(data, chunk_size=64, store=origin.store)
    desc = descriptor(hop_limit=1)
    bundle = ForwardBundle.from_descriptor(manifest, desc, created_at_s=50)
    ledger = CustodyLedger()
    seed_bundle_custody(bundle, manifest, origin=origin, ledger=ledger, now_s=50)

    measured_profile = BearerProfile(
        bearer_id="lora-from-lab",
        kind=BearerKind.LORA,
        evidence_basis=EvidenceBasis.MEASURED,
        link_profile=clean_profile(9),
        provenance="physical-validation/HW-006/checkpoint-001.json",
    )
    reconstructed, report = run_per_bearer_governed_schedule(
        bundle,
        manifest,
        peers={"origin": origin, "destination": destination},
        contacts=(
            BearerGovernedContact(
                GovernedForwardContact("origin", "destination", 5000, 10, "measured-model", 60),
                "lora-from-lab",
            ),
        ),
        destination_id="destination",
        ledger=ledger,
        bearers={"lora-from-lab": measured_profile},
    )

    assert reconstructed == data
    line = report.line_for("lora-from-lab")
    assert line.profile_evidence_basis is EvidenceBasis.MEASURED
    assert line.profile_provenance.endswith("checkpoint-001.json")
    assert line.model_contact_count == 1
    assert line.physical_replay_contact_count == 0
    assert not line.fully_physical_replay
    assert report.contains_measured_profile
    assert not report.fully_physical_replay


def test_unknown_bearer_is_fail_closed() -> None:
    data = data_for_chunks(1)
    origin = ForwardPeer("origin", PollicinoStore())
    destination = ForwardPeer("destination", PollicinoStore())
    manifest = seed_forwarding_object(data, chunk_size=64, store=origin.store)
    desc = descriptor(hop_limit=1)
    bundle = ForwardBundle.from_descriptor(manifest, desc, created_at_s=1)
    ledger = CustodyLedger()
    seed_bundle_custody(bundle, manifest, origin=origin, ledger=ledger, now_s=1)

    with pytest.raises(KeyError, match="unknown bearer profile"):
        run_per_bearer_governed_schedule(
            bundle,
            manifest,
            peers={"origin": origin, "destination": destination},
            contacts=(
                BearerGovernedContact(
                    GovernedForwardContact("origin", "destination", 1, 1, "x", 2),
                    "missing",
                ),
            ),
            destination_id="destination",
            ledger=ledger,
            bearers={},
        )
