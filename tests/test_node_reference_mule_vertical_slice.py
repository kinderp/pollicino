from __future__ import annotations

from pollicino.integrations.reference_mule import (
    HomeReferenceResolver,
    PortableReference,
)
from pollicino.net import ScarceLinkProfile
from pollicino.node_runtime import NodeMode, PollicinoNodeRuntime


def _profile(seed: int) -> ScarceLinkProfile:
    return ScarceLinkProfile(
        max_frame_bytes=64,
        bitrate_bps=5000,
        ack_bytes=8,
        max_retries=2,
        seed=seed,
    )


def test_portable_reference_round_trip_is_canonical_and_opaque() -> None:
    reference = PortableReference(
        provider_id="magnet",
        locator=b"magnet:?xt=urn:btih:0123456789abcdef0123456789abcdef01234567",
        label="authorized-demo-content",
        metadata=(("topic", "books"), ("source", "peer")),
    )
    decoded = PortableReference.decode(reference.encode())
    assert decoded == reference
    assert decoded.sha256_digest == reference.sha256_digest
    assert decoded.locator.startswith(b"magnet:?")


def test_school_mesh_carry_restart_home_resolution_vertical_slice(tmp_path) -> None:
    school = PollicinoNodeRuntime(tmp_path / "school-a", node_id="student-a")
    mule = PollicinoNodeRuntime(tmp_path / "student-b", node_id="student-b")
    home = PollicinoNodeRuntime(tmp_path / "home", node_id="home-gateway")

    school.transition(NodeMode.CONNECTED_MESH)
    mule.transition(NodeMode.CONNECTED_MESH)
    home.transition(NodeMode.OPPORTUNISTIC_DTN)

    reference = PortableReference(
        provider_id="magnet",
        locator=b"magnet:?xt=urn:btih:0123456789abcdef0123456789abcdef01234567",
        label="authorized-demo-content",
        metadata=(("purpose", "reference-mule-test"),),
    )
    manifest = school.publish_exact(
        reference.encode(),
        chunk_size=64,
        label="portable-reference",
    )

    school_contact = mule.receive_from(
        school,
        manifest,
        profile=_profile(201),
        transfer_id_base=1000,
        max_chunks=64,
    )
    assert school_contact.source_mode is NodeMode.CONNECTED_MESH
    assert school_contact.target_mode is NodeMode.CONNECTED_MESH
    assert school_contact.exact
    assert mule.complete(manifest.fingerprint)
    assert PortableReference.decode(mule.reconstruct(manifest.fingerprint)) == reference

    # The student leaves school. Mode changes must not touch object identity or
    # cached bytes, and the state survives a fresh process/runtime instance.
    mule.transition(NodeMode.OPPORTUNISTIC_DTN)
    restarted_mule = PollicinoNodeRuntime(tmp_path / "student-b", node_id="student-b")
    assert restarted_mule.mode is NodeMode.OPPORTUNISTIC_DTN
    assert restarted_mule.knows_manifest(manifest.fingerprint)
    assert restarted_mule.complete(manifest.fingerprint)
    assert PortableReference.decode(restarted_mule.reconstruct(manifest.fingerprint)) == reference

    territorial_contact = home.receive_from(
        restarted_mule,
        manifest,
        profile=_profile(202),
        transfer_id_base=2000,
        max_chunks=64,
    )
    assert territorial_contact.source_mode is NodeMode.OPPORTUNISTIC_DTN
    assert territorial_contact.target_mode is NodeMode.OPPORTUNISTIC_DTN
    assert territorial_contact.exact
    assert home.complete(manifest.fingerprint)

    # Rich connectivity is an explicit mode transition. The network core still
    # does not interpret or execute the provider-specific locator.
    home.transition(NodeMode.RICH_HOME)
    recovered = PortableReference.decode(home.reconstruct(manifest.fingerprint))
    seen = []

    def handle(reference: PortableReference) -> str:
        seen.append(reference)
        return "queued by authorized test handler"

    resolver = HomeReferenceResolver({"magnet": handle})
    receipt = resolver.resolve(recovered)
    assert receipt.accepted
    assert receipt.provider_id == "magnet"
    assert receipt.detail == "queued by authorized test handler"
    assert seen == [reference]

    # Both scarce contacts are real executions in the deterministic model, not
    # free state copying.
    assert school_contact.total_wire_bytes > 0
    assert territorial_contact.total_wire_bytes > 0


def test_partial_carried_object_survives_mode_change_and_restart(tmp_path) -> None:
    source = PollicinoNodeRuntime(tmp_path / "source", node_id="source")
    mule = PollicinoNodeRuntime(tmp_path / "mule", node_id="mule")
    source.transition(NodeMode.CONNECTED_MESH)
    mule.transition(NodeMode.CONNECTED_MESH)

    reference = PortableReference(
        provider_id="filesystem",
        locator=b"sha256:4f6f70617175652d66696c652d7265666572656e6365",
        label="local-authorized-file",
        metadata=(("device", "home-nas"),),
    )
    manifest = source.publish_exact(reference.encode(), chunk_size=32, label="file-reference")
    assert len(manifest.chunks) > 1

    first = mule.receive_from(
        source,
        manifest,
        profile=_profile(203),
        transfer_id_base=3000,
        max_chunks=1,
    )
    assert not first.exact
    assert mule.knows_manifest(manifest.fingerprint)
    assert not mule.complete(manifest.fingerprint)

    mule.transition(NodeMode.OPPORTUNISTIC_DTN)
    restarted = PollicinoNodeRuntime(tmp_path / "mule", node_id="mule")
    assert restarted.knows_manifest(manifest.fingerprint)
    assert not restarted.complete(manifest.fingerprint)

    second = restarted.receive_from(
        source,
        manifest,
        profile=_profile(204),
        transfer_id_base=4000,
        max_chunks=64,
    )
    assert second.exact
    assert PortableReference.decode(restarted.reconstruct(manifest.fingerprint)) == reference
