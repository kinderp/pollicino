import hashlib

from pollicino.net import PollicinoStore, ScarceLinkProfile
from pollicino.net.bundle import CustodyLedger, ForwardBundle, seed_bundle_custody
from pollicino.net.bundle_route import (
    GovernedForwardContact,
    run_governed_store_forward_schedule,
    summarize_governed_end_to_end_trc,
)
from pollicino.net.content import RetrievalSource, manifest_for_content
from pollicino.net.store_forward import ForwardPeer, seed_forwarding_object
from pollicino.net.wire import DiscoveryDescriptor


def profile() -> ScarceLinkProfile:
    return ScarceLinkProfile(
        max_frame_bytes=64,
        bitrate_bps=5000,
        ack_bytes=8,
        max_retries=3,
        seed=23,
    )


def payload(chunks: int, size: int = 64) -> bytes:
    pieces = []
    for index in range(chunks):
        digest = hashlib.sha256(f"route-bundle-{index}".encode()).digest()
        pieces.append((digest * ((size + 31) // 32))[:size])
    return b"".join(pieces)


def setup(*, ttl: int = 100, hops: int = 2, chunks: int = 3):
    data = payload(chunks)
    origin = ForwardPeer("origin", PollicinoStore())
    relay = ForwardPeer("relay", PollicinoStore())
    destination = ForwardPeer("destination", PollicinoStore())
    manifest = seed_forwarding_object(data, chunk_size=64, store=origin.store)
    descriptor = DiscoveryDescriptor(
        object_class=1,
        rendezvous_key=b"route-governance",
        ttl_seconds=ttl,
        hop_limit=hops,
        nonce=42,
    )
    bundle = ForwardBundle.from_descriptor(manifest, descriptor, created_at_s=1000)
    ledger = CustodyLedger()
    seed_bundle_custody(bundle, manifest, origin=origin, ledger=ledger, now_s=1000)
    return data, manifest, descriptor, bundle, ledger, {
        "origin": origin,
        "relay": relay,
        "destination": destination,
    }


def test_governed_schedule_delivers_over_two_hops() -> None:
    data, manifest, _descriptor, bundle, ledger, peers = setup()
    contacts = (
        GovernedForwardContact("origin", "relay", 100, 10, "c1", 1001),
        GovernedForwardContact("relay", "destination", 200, 10, "c2", 1002),
    )

    reconstructed, route = run_governed_store_forward_schedule(
        bundle,
        manifest,
        peers=peers,
        contacts=contacts,
        destination_id="destination",
        ledger=ledger,
        profile=profile(),
    )

    assert reconstructed == data
    assert route.destination_exact
    assert route.forwarded_contacts == 2
    assert route.bundle_primary_data_wire_bytes > 0
    assert route.custody_primary_data_wire_bytes > 0
    assert ledger.get(bundle.bundle_id, "destination").complete


def test_schedule_duplicate_contact_is_zero_wire_and_counted() -> None:
    _data, manifest, _descriptor, bundle, ledger, peers = setup(chunks=2)
    contacts = (
        GovernedForwardContact("origin", "relay", 300, 1, "same", 1001),
        GovernedForwardContact("origin", "relay", 400, 1, "same", 1002),
        GovernedForwardContact("origin", "relay", 500, 1, "new", 1003),
    )

    _, route = run_governed_store_forward_schedule(
        bundle,
        manifest,
        peers=peers,
        contacts=contacts,
        destination_id="relay",
        ledger=ledger,
        profile=profile(),
    )

    assert route.contacts[1].duplicate_suppressed
    assert route.contacts[1].total_wire_bytes == 0
    assert route.duplicate_suppressed_contacts == 1
    assert route.destination_exact


def test_schedule_can_expire_between_contacts() -> None:
    _data, manifest, _descriptor, bundle, ledger, peers = setup(ttl=2)
    contacts = (
        GovernedForwardContact("origin", "relay", 600, 10, "early", 1001),
        GovernedForwardContact("relay", "destination", 700, 10, "late", 1002),
    )

    reconstructed, route = run_governed_store_forward_schedule(
        bundle,
        manifest,
        peers=peers,
        contacts=contacts,
        destination_id="destination",
        ledger=ledger,
        profile=profile(),
    )

    assert reconstructed is None
    assert not route.destination_complete
    assert route.expired_contacts == 1
    assert route.contacts[1].total_wire_bytes == 0


def test_governed_trc_includes_bundle_and_custody_controls() -> None:
    data, manifest, descriptor, bundle, ledger, peers = setup()
    contacts = (
        GovernedForwardContact("origin", "relay", 800, 10, "h1", 1001),
        GovernedForwardContact("relay", "destination", 900, 10, "h2", 1002),
    )
    reconstructed, route = run_governed_store_forward_schedule(
        bundle,
        manifest,
        peers=peers,
        contacts=contacts,
        destination_id="destination",
        ledger=ledger,
        profile=profile(),
    )
    resolved = manifest_for_content(
        data,
        object_class=1,
        sources=(RetrievalSource(provider_id="p2p", locator=b"object"),),
    )
    trc = summarize_governed_end_to_end_trc(
        route,
        descriptor=descriptor,
        resolved_manifest=resolved,
        discovery_transmissions=2,
        rendezvous_transmissions=1,
    )

    assert reconstructed == data
    assert trc.exact
    assert trc.discovery_wire_bytes == len(descriptor.encode()) * 2
    assert trc.rendezvous_wire_bytes == len(resolved.encode())
    assert trc.bundle_primary_data_wire_bytes > 0
    assert trc.custody_primary_data_wire_bytes > 0
    assert trc.total_wire_bytes == (
        trc.primary_data_wire_bytes
        + trc.primary_ack_wire_bytes
        + trc.retransmission_wire_bytes
    )
    assert trc.total_bits == trc.total_wire_bytes * 8
