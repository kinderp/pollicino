import hashlib

import pytest

from pollicino.net import (
    DirectoryPollicinoStore,
    DiscoveryDescriptor,
    ForwardContact,
    ForwardPeer,
    InMemoryContentProvider,
    PollicinoStore,
    RetrievalSource,
    ScarceLinkProfile,
    forward_contact,
    manifest_for_content,
    run_store_forward_schedule,
    seed_forwarding_object,
    summarize_end_to_end_trc,
)


def clean_profile() -> ScarceLinkProfile:
    return ScarceLinkProfile(
        max_frame_bytes=64,
        bitrate_bps=5000,
        ack_bytes=8,
        max_retries=3,
        seed=23,
    )


def unique_chunks(count: int, chunk_size: int = 64) -> bytes:
    pieces = []
    for index in range(count):
        seed = hashlib.sha256(f"forward-chunk-{index}".encode()).digest()
        pieces.append((seed * ((chunk_size + 31) // 32))[:chunk_size])
    return b"".join(pieces)


def test_two_hop_store_forward_without_permanent_end_to_end_path() -> None:
    data = unique_chunks(6)
    origin = ForwardPeer("origin", PollicinoStore())
    relay = ForwardPeer("relay", PollicinoStore())
    destination = ForwardPeer("destination", PollicinoStore())
    manifest = seed_forwarding_object(data, chunk_size=64, store=origin.store)

    reconstructed, route = run_store_forward_schedule(
        manifest,
        peers={
            "origin": origin,
            "relay": relay,
            "destination": destination,
        },
        contacts=(
            ForwardContact("origin", "relay", transfer_id_base=100, max_chunks=3),
            ForwardContact("relay", "destination", transfer_id_base=200, max_chunks=3),
            ForwardContact("origin", "relay", transfer_id_base=300, max_chunks=10),
            ForwardContact("relay", "destination", transfer_id_base=400, max_chunks=10),
        ),
        destination_id="destination",
        profile=clean_profile(),
    )

    assert reconstructed == data
    assert route.destination_complete and route.destination_exact
    assert all(
        not (item.source_id == "origin" and item.target_id == "destination")
        for item in route.contacts
    )
    assert route.contacts[0].manifest_sent
    assert route.contacts[0].transferred_chunk_indices == (0, 1, 2)
    assert route.contacts[1].manifest_sent
    assert route.contacts[1].transferred_chunk_indices == (0, 1, 2)
    assert not route.contacts[2].manifest_sent
    assert route.contacts[2].cached_chunk_count_before == 3
    assert route.contacts[2].transferred_chunk_indices == (3, 4, 5)
    assert not route.contacts[3].manifest_sent
    assert route.contacts[3].cached_chunk_count_before == 3
    assert route.contacts[3].transferred_chunk_indices == (3, 4, 5)


def test_relay_can_forward_only_chunks_it_actually_possesses() -> None:
    data = unique_chunks(5)
    origin = ForwardPeer("origin", PollicinoStore())
    relay = ForwardPeer("relay", PollicinoStore())
    destination = ForwardPeer("destination", PollicinoStore())
    manifest = seed_forwarding_object(data, chunk_size=64, store=origin.store)

    _, first = forward_contact(
        manifest,
        source=origin,
        target=relay,
        profile=clean_profile(),
        transfer_id_base=10,
        max_chunks=2,
    )
    assert first.transferred_chunk_indices == (0, 1)

    reconstructed, second = forward_contact(
        manifest,
        source=relay,
        target=destination,
        profile=clean_profile(),
        transfer_id_base=20,
        max_chunks=99,
    )
    assert reconstructed is None
    assert second.source_available_missing_count == 2
    assert second.transferred_chunk_indices == (0, 1)
    assert second.remaining_chunk_count == 3
    assert not second.target_complete


def test_durable_relay_survives_restart_between_contacts(tmp_path) -> None:
    data = unique_chunks(4)
    origin_root = tmp_path / "origin"
    relay_root = tmp_path / "relay"
    destination_root = tmp_path / "destination"

    origin = ForwardPeer("origin", DirectoryPollicinoStore(origin_root))
    relay = ForwardPeer("relay", DirectoryPollicinoStore(relay_root))
    destination = ForwardPeer("destination", DirectoryPollicinoStore(destination_root))
    manifest = seed_forwarding_object(data, chunk_size=64, store=origin.store)

    _, first = forward_contact(
        manifest,
        source=origin,
        target=relay,
        profile=clean_profile(),
        transfer_id_base=1000,
        max_chunks=2,
    )
    assert first.transferred_chunk_indices == (0, 1)

    # Simulate process/device restart: all peer wrapper objects are recreated.
    restarted_relay = ForwardPeer("relay", DirectoryPollicinoStore(relay_root))
    restarted_destination = ForwardPeer(
        "destination", DirectoryPollicinoStore(destination_root)
    )
    reconstructed, second = forward_contact(
        manifest,
        source=restarted_relay,
        target=restarted_destination,
        profile=clean_profile(),
        transfer_id_base=2000,
        max_chunks=10,
    )
    assert reconstructed is None
    assert second.transferred_chunk_indices == (0, 1)
    assert second.remaining_chunk_count == 2

    # Origin meets relay again; relay later completes delivery without origin->destination.
    restarted_origin = ForwardPeer("origin", DirectoryPollicinoStore(origin_root))
    _, third = forward_contact(
        manifest,
        source=restarted_origin,
        target=restarted_relay,
        profile=clean_profile(),
        transfer_id_base=3000,
        max_chunks=10,
    )
    assert third.cached_chunk_count_before == 2
    assert third.transferred_chunk_indices == (2, 3)

    final, fourth = forward_contact(
        manifest,
        source=ForwardPeer("relay", DirectoryPollicinoStore(relay_root)),
        target=ForwardPeer("destination", DirectoryPollicinoStore(destination_root)),
        profile=clean_profile(),
        transfer_id_base=4000,
        max_chunks=10,
    )
    assert final == data
    assert fourth.cached_chunk_count_before == 2
    assert fourth.transferred_chunk_indices == (2, 3)
    assert fourth.target_complete and fourth.target_exact


def test_corrupt_durable_relay_chunk_is_not_advertised_or_forwarded(tmp_path) -> None:
    data = unique_chunks(3)
    origin = ForwardPeer("origin", DirectoryPollicinoStore(tmp_path / "origin"))
    relay_store = DirectoryPollicinoStore(tmp_path / "relay")
    relay = ForwardPeer("relay", relay_store)
    destination = ForwardPeer("destination", DirectoryPollicinoStore(tmp_path / "destination"))
    manifest = seed_forwarding_object(data, chunk_size=64, store=origin.store)

    _, first = forward_contact(
        manifest,
        source=origin,
        target=relay,
        profile=clean_profile(),
        transfer_id_base=10,
        max_chunks=3,
    )
    assert first.target_complete

    bad_ref = manifest.chunks[1]
    relay_store.path_for_digest(bad_ref.sha256_digest).write_bytes(b"corrupt")
    assert not relay_store.has(bad_ref.sha256_digest)

    reconstructed, report = forward_contact(
        manifest,
        source=ForwardPeer("relay", DirectoryPollicinoStore(tmp_path / "relay")),
        target=destination,
        profile=clean_profile(),
        transfer_id_base=20,
        max_chunks=10,
    )
    assert reconstructed is None
    assert report.source_available_missing_count == 2
    assert report.transferred_chunk_indices == (0, 2)
    assert report.remaining_chunk_count == 1


def test_end_to_end_trc_includes_discovery_rendezvous_and_route_without_overlap() -> None:
    data = unique_chunks(2)
    origin = ForwardPeer("origin", PollicinoStore())
    destination = ForwardPeer("destination", PollicinoStore())
    chunk_manifest = seed_forwarding_object(data, chunk_size=64, store=origin.store)

    reconstructed, route = run_store_forward_schedule(
        chunk_manifest,
        peers={"origin": origin, "destination": destination},
        contacts=(ForwardContact("origin", "destination", 50, 10),),
        destination_id="destination",
        profile=clean_profile(),
    )
    assert reconstructed == data

    descriptor = DiscoveryDescriptor(
        object_class=3,
        rendezvous_key=b"route-coordinate",
        ttl_seconds=600,
        nonce=7,
        hop_limit=4,
    )
    content_manifest = manifest_for_content(
        data,
        object_class=3,
        sources=(
            RetrievalSource(
                provider_id="pollicino-store",
                locator=chunk_manifest.fingerprint,
            ),
        ),
    )
    trc = summarize_end_to_end_trc(
        route,
        descriptor=descriptor,
        resolved_manifest=content_manifest,
        discovery_transmissions=2,
        rendezvous_transmissions=1,
    )

    assert trc.exact
    assert trc.discovery_wire_bytes == len(descriptor.encode()) * 2
    assert trc.rendezvous_wire_bytes == len(content_manifest.encode())
    assert trc.chunk_manifest_primary_data_wire_bytes == route.manifest_primary_data_wire_bytes
    assert trc.availability_primary_data_wire_bytes == route.availability_primary_data_wire_bytes
    assert trc.payload_primary_data_wire_bytes == route.payload_primary_data_wire_bytes
    assert trc.total_wire_bytes == (
        trc.discovery_wire_bytes
        + trc.rendezvous_wire_bytes
        + trc.chunk_manifest_primary_data_wire_bytes
        + trc.availability_primary_data_wire_bytes
        + trc.payload_primary_data_wire_bytes
        + trc.primary_ack_wire_bytes
        + trc.retransmission_data_wire_bytes
        + trc.retransmission_ack_wire_bytes
        + trc.fec_wire_bytes
    )
    assert trc.total_bits == trc.total_wire_bytes * 8


def test_contact_rejects_source_without_verified_manifest() -> None:
    data = unique_chunks(1)
    seed = PollicinoStore()
    manifest = seed_forwarding_object(data, chunk_size=64, store=seed)
    source = ForwardPeer("source", PollicinoStore())
    target = ForwardPeer("target", PollicinoStore())

    with pytest.raises(ValueError, match="does not possess"):
        forward_contact(
            manifest,
            source=source,
            target=target,
            profile=clean_profile(),
            transfer_id_base=1,
            max_chunks=1,
        )
