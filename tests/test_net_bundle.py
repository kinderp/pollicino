import hashlib

import pytest

from pollicino.net import PollicinoStore, ScarceLinkProfile
from pollicino.net.bundle import (
    CustodyLedger,
    ForwardBundle,
    governed_forward_contact,
    load_custody_ledger,
    save_custody_ledger,
    seed_bundle_custody,
)
from pollicino.net.store_forward import ForwardPeer, seed_forwarding_object
from pollicino.net.wire import DiscoveryDescriptor


def profile() -> ScarceLinkProfile:
    return ScarceLinkProfile(
        max_frame_bytes=64,
        bitrate_bps=5000,
        ack_bytes=8,
        max_retries=3,
        seed=19,
    )


def descriptor(*, ttl: int = 100, hops: int = 2, nonce: int = 7) -> DiscoveryDescriptor:
    return DiscoveryDescriptor(
        object_class=1,
        rendezvous_key=b"bundle-test",
        ttl_seconds=ttl,
        hop_limit=hops,
        nonce=nonce,
    )


def data_for_chunks(count: int, size: int = 64) -> bytes:
    pieces = []
    for index in range(count):
        digest = hashlib.sha256(f"bundle-chunk-{index}".encode()).digest()
        pieces.append((digest * ((size + 31) // 32))[:size])
    return b"".join(pieces)


def seeded(*, ttl: int = 100, hops: int = 2, chunks: int = 4):
    data = data_for_chunks(chunks)
    origin = ForwardPeer("origin", PollicinoStore())
    manifest = seed_forwarding_object(data, chunk_size=64, store=origin.store)
    discovery = descriptor(ttl=ttl, hops=hops)
    bundle = ForwardBundle.from_descriptor(manifest, discovery, created_at_s=1000)
    ledger = CustodyLedger()
    seed_bundle_custody(bundle, manifest, origin=origin, ledger=ledger, now_s=1000)
    return data, origin, manifest, bundle, ledger


def test_bundle_wire_round_trip_and_identity_binds_discovery() -> None:
    _data, _origin, manifest, bundle, _ledger = seeded()
    encoded = bundle.encode_forward(1)
    decoded, hop = ForwardBundle.decode_forward(encoded)

    assert decoded == bundle
    assert hop == 1
    assert len(bundle.bundle_id) == 32

    changed = ForwardBundle.from_descriptor(
        manifest, descriptor(nonce=8), created_at_s=1000
    )
    assert changed.bundle_id != bundle.bundle_id


def test_ttl_expiry_blocks_before_any_wire() -> None:
    _data, origin, manifest, bundle, ledger = seeded(ttl=10)
    relay = ForwardPeer("relay", PollicinoStore())

    reconstructed, report = governed_forward_contact(
        bundle,
        manifest,
        source=origin,
        target=relay,
        ledger=ledger,
        profile=profile(),
        transfer_id_base=10,
        max_chunks=4,
        contact_id="expired-contact",
        now_s=1010,
    )

    assert reconstructed is None
    assert report.disposition == "expired"
    assert report.total_wire_bytes == 0
    assert len(relay.store) == 0


def test_hop_limit_and_partial_custody_are_enforced() -> None:
    _data, origin, manifest, bundle, ledger = seeded(hops=1, chunks=4)
    relay = ForwardPeer("relay", PollicinoStore())
    destination = ForwardPeer("destination", PollicinoStore())

    _, first = governed_forward_contact(
        bundle,
        manifest,
        source=origin,
        target=relay,
        ledger=ledger,
        profile=profile(),
        transfer_id_base=100,
        max_chunks=2,
        contact_id="origin-relay-1",
        now_s=1001,
    )
    relay_custody = ledger.get(bundle.bundle_id, "relay")

    assert first.disposition == "forwarded"
    assert first.target_hop_count == 1
    assert relay_custody is not None
    assert relay_custody.hop_count == 1
    assert relay_custody.verified_chunk_count == 2
    assert not relay_custody.complete

    _, blocked = governed_forward_contact(
        bundle,
        manifest,
        source=relay,
        target=destination,
        ledger=ledger,
        profile=profile(),
        transfer_id_base=200,
        max_chunks=4,
        contact_id="relay-destination-1",
        now_s=1002,
    )
    assert blocked.disposition == "hop_limit_exhausted"
    assert blocked.total_wire_bytes == 0
    assert ledger.get(bundle.bundle_id, "destination") is None


def test_duplicate_contact_id_is_zero_wire_but_new_contact_uses_pna1() -> None:
    _data, origin, manifest, bundle, ledger = seeded(chunks=4)
    relay = ForwardPeer("relay", PollicinoStore())

    _, first = governed_forward_contact(
        bundle,
        manifest,
        source=origin,
        target=relay,
        ledger=ledger,
        profile=profile(),
        transfer_id_base=300,
        max_chunks=2,
        contact_id="encounter-1",
        now_s=1001,
    )
    _, duplicate = governed_forward_contact(
        bundle,
        manifest,
        source=origin,
        target=relay,
        ledger=ledger,
        profile=profile(),
        transfer_id_base=400,
        max_chunks=2,
        contact_id="encounter-1",
        now_s=1002,
    )
    _, second = governed_forward_contact(
        bundle,
        manifest,
        source=origin,
        target=relay,
        ledger=ledger,
        profile=profile(),
        transfer_id_base=500,
        max_chunks=2,
        contact_id="encounter-2",
        now_s=1003,
    )

    assert first.inner is not None
    assert first.inner.transferred_chunk_indices == (0, 1)
    assert duplicate.duplicate_suppressed
    assert duplicate.total_wire_bytes == 0
    assert second.inner is not None
    assert second.inner.cached_chunk_count_before == 2
    assert second.inner.transferred_chunk_indices == (2, 3)
    assert ledger.get(bundle.bundle_id, "relay").complete


def test_two_hop_delivery_records_custody_and_exact_destination() -> None:
    data, origin, manifest, bundle, ledger = seeded(hops=2, chunks=3)
    relay = ForwardPeer("relay", PollicinoStore())
    destination = ForwardPeer("destination", PollicinoStore())

    _, first = governed_forward_contact(
        bundle,
        manifest,
        source=origin,
        target=relay,
        ledger=ledger,
        profile=profile(),
        transfer_id_base=600,
        max_chunks=10,
        contact_id="hop-1",
        now_s=1001,
    )
    reconstructed, second = governed_forward_contact(
        bundle,
        manifest,
        source=relay,
        target=destination,
        ledger=ledger,
        profile=profile(),
        transfer_id_base=700,
        max_chunks=10,
        contact_id="hop-2",
        now_s=1002,
    )

    assert first.inner is not None and first.inner.target_exact
    assert reconstructed == data
    assert second.inner is not None and second.inner.target_exact
    destination_custody = ledger.get(bundle.bundle_id, "destination")
    assert destination_custody is not None
    assert destination_custody.hop_count == 2
    assert destination_custody.complete
    assert second.total_wire_bytes > 0


def test_custody_ledger_persistence_preserves_duplicate_suppression(tmp_path) -> None:
    _data, origin, manifest, bundle, ledger = seeded(chunks=2)
    relay = ForwardPeer("relay", PollicinoStore())

    _, first = governed_forward_contact(
        bundle,
        manifest,
        source=origin,
        target=relay,
        ledger=ledger,
        profile=profile(),
        transfer_id_base=800,
        max_chunks=1,
        contact_id="persisted-contact",
        now_s=1001,
    )
    assert first.disposition == "forwarded"

    checkpoint = tmp_path / "custody.json"
    save_custody_ledger(checkpoint, ledger)
    restored = load_custody_ledger(checkpoint)

    assert restored.get(bundle.bundle_id, "origin") is not None
    assert restored.get(bundle.bundle_id, "relay") is not None
    _, duplicate = governed_forward_contact(
        bundle,
        manifest,
        source=origin,
        target=relay,
        ledger=restored,
        profile=profile(),
        transfer_id_base=900,
        max_chunks=1,
        contact_id="persisted-contact",
        now_s=1002,
    )
    assert duplicate.duplicate_suppressed
    assert duplicate.total_wire_bytes == 0


def test_custody_ledger_checksum_fails_closed(tmp_path) -> None:
    _data, _origin, _manifest, _bundle, ledger = seeded()
    checkpoint = tmp_path / "custody.json"
    save_custody_ledger(checkpoint, ledger)
    raw = checkpoint.read_text(encoding="utf-8")
    checkpoint.write_text(raw.replace('"hop_count":0', '"hop_count":1'), encoding="utf-8")

    with pytest.raises(ValueError, match="checksum"):
        load_custody_ledger(checkpoint)
