from __future__ import annotations

from pollicino.integrations.reference_mule import PortableReference
from pollicino.net import DiscoveryDescriptor, ScarceLinkProfile
from pollicino.node_runtime import NodeMode, PollicinoNodeRuntime


def _profile(seed: int) -> ScarceLinkProfile:
    return ScarceLinkProfile(
        max_frame_bytes=64,
        bitrate_bps=5000,
        ack_bytes=8,
        max_retries=2,
        seed=seed,
    )


def test_governed_reference_mule_keeps_node_local_custody_across_restart(tmp_path) -> None:
    origin = PollicinoNodeRuntime(tmp_path / "origin", node_id="student-a")
    mule = PollicinoNodeRuntime(tmp_path / "mule", node_id="student-b")
    home = PollicinoNodeRuntime(tmp_path / "home", node_id="home-gateway")
    origin.transition(NodeMode.CONNECTED_MESH)
    mule.transition(NodeMode.CONNECTED_MESH)
    home.transition(NodeMode.OPPORTUNISTIC_DTN)

    reference = PortableReference(
        provider_id="filesystem",
        locator=b"sha256:authorized-personal-document-demo",
        label="authorized-personal-document",
        metadata=(("resolver", "home-nas"),),
    )
    descriptor = DiscoveryDescriptor(
        object_class=1,
        rendezvous_key=b"ref-mule-demo",
        ttl_seconds=3600,
        hop_limit=4,
        nonce=2026082802,
    )
    manifest, bundle = origin.publish_governed(
        reference.encode(),
        chunk_size=64,
        descriptor=descriptor,
        created_at_s=1000,
        label="governed-reference",
    )

    origin_record = origin.custody_record(bundle.bundle_id)
    assert origin_record is not None
    assert origin_record.hop_count == 0
    assert origin_record.complete

    school = mule.receive_governed_from(
        origin,
        bundle,
        manifest,
        profile=_profile(211),
        transfer_id_base=5000,
        max_chunks=64,
        contact_id="school-a-b-001",
        now_s=1010,
    )
    assert school.governance.disposition == "forwarded"
    assert school.governance.target_hop_count == 1
    assert school.exact
    mule_record = mule.custody_record(bundle.bundle_id)
    assert mule_record is not None
    assert mule_record.peer_id == "student-b"
    assert mule_record.hop_count == 1
    assert mule_record.complete
    assert mule.knows_bundle(bundle.bundle_id)

    mule.transition(NodeMode.OPPORTUNISTIC_DTN)
    restarted_mule = PollicinoNodeRuntime(tmp_path / "mule", node_id="student-b")
    assert restarted_mule.mode is NodeMode.OPPORTUNISTIC_DTN
    assert restarted_mule.bundle(bundle.bundle_id) == bundle
    restarted_record = restarted_mule.custody_record(bundle.bundle_id)
    assert restarted_record == mule_record
    assert PortableReference.decode(
        restarted_mule.reconstruct(manifest.fingerprint)
    ) == reference

    afternoon = home.receive_governed_from(
        restarted_mule,
        restarted_mule.bundle(bundle.bundle_id),
        restarted_mule.manifest(manifest.fingerprint),
        profile=_profile(212),
        transfer_id_base=6000,
        max_chunks=64,
        contact_id="territory-b-home-001",
        now_s=1100,
    )
    assert afternoon.governance.disposition == "forwarded"
    assert afternoon.governance.target_hop_count == 2
    assert afternoon.exact
    home_record = home.custody_record(bundle.bundle_id)
    assert home_record is not None
    assert home_record.hop_count == 2
    assert home_record.complete
    assert PortableReference.decode(home.reconstruct(manifest.fingerprint)) == reference

    # The source of the second hop remembers only the contact it originated.
    # After another restart the exact same scheduled contact is suppressed with
    # zero wire, proving persistent idempotency without a global ledger.
    restarted_again = PollicinoNodeRuntime(tmp_path / "mule", node_id="student-b")
    replay = home.receive_governed_from(
        restarted_again,
        restarted_again.bundle(bundle.bundle_id),
        restarted_again.manifest(manifest.fingerprint),
        profile=_profile(213),
        transfer_id_base=7000,
        max_chunks=64,
        contact_id="territory-b-home-001",
        now_s=1110,
    )
    assert replay.governance.disposition == "duplicate_suppressed"
    assert replay.total_wire_bytes == 0


def test_hop_limit_is_preserved_by_node_local_runtime(tmp_path) -> None:
    origin = PollicinoNodeRuntime(tmp_path / "origin", node_id="a")
    relay = PollicinoNodeRuntime(tmp_path / "relay", node_id="b")
    third = PollicinoNodeRuntime(tmp_path / "third", node_id="c")

    reference = PortableReference(provider_id="http", locator=b"https://example.invalid/demo")
    descriptor = DiscoveryDescriptor(
        object_class=1,
        rendezvous_key=b"one-hop-only",
        ttl_seconds=3600,
        hop_limit=1,
        nonce=2026082803,
    )
    manifest, bundle = origin.publish_governed(
        reference.encode(),
        chunk_size=64,
        descriptor=descriptor,
        created_at_s=2000,
    )
    first = relay.receive_governed_from(
        origin,
        bundle,
        manifest,
        profile=_profile(214),
        transfer_id_base=8000,
        max_chunks=64,
        contact_id="a-b",
        now_s=2010,
    )
    assert first.exact

    blocked = third.receive_governed_from(
        relay,
        relay.bundle(bundle.bundle_id),
        relay.manifest(manifest.fingerprint),
        profile=_profile(215),
        transfer_id_base=9000,
        max_chunks=64,
        contact_id="b-c",
        now_s=2020,
    )
    assert blocked.governance.disposition == "hop_limit_exhausted"
    assert blocked.total_wire_bytes == 0
    assert third.custody_record(bundle.bundle_id) is None
