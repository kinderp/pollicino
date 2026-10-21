from __future__ import annotations

from dataclasses import dataclass

import pytest

from pollicino.bearer_runtime import BearerObservation, NodeBearerController
from pollicino.bearer_transport import (
    BearerDataPlaneUnavailable,
    DeterministicGovernedBearerAdapter,
    NodeBearerTransport,
)
from pollicino.integrations.loramesher_runtime import (
    LoRaMesherBearerProbe,
    LoRaMesherRuntimeSnapshot,
)
from pollicino.integrations.reference_mule import PortableReference
from pollicino.net import DiscoveryDescriptor, ScarceLinkProfile
from pollicino.node_runtime import NodeMode, PollicinoNodeRuntime


@dataclass
class StaticProbe:
    adapter_id: str
    mode: NodeMode
    available: bool
    ready: bool

    def probe(self) -> BearerObservation:
        return BearerObservation(
            adapter_id=self.adapter_id,
            mode=self.mode,
            available=self.available,
            ready=self.ready,
            detail="deterministic test probe",
        )


def _profile(seed: int) -> ScarceLinkProfile:
    return ScarceLinkProfile(
        max_frame_bytes=64,
        bitrate_bps=5000,
        ack_bytes=8,
        max_retries=2,
        seed=seed,
    )


def _publish(node: PollicinoNodeRuntime):
    reference = PortableReference(
        provider_id="filesystem",
        locator=b"sha256:bearer-data-plane-demo",
        label="authorized-demo",
    )
    descriptor = DiscoveryDescriptor(
        object_class=1,
        rendezvous_key=b"bearer-data-plane",
        ttl_seconds=7200,
        hop_limit=4,
        nonce=2026082805,
    )
    manifest, bundle = node.publish_governed(
        reference.encode(),
        chunk_size=64,
        descriptor=descriptor,
        created_at_s=1000,
        label="portable-reference",
    )
    return reference, manifest, bundle


def test_same_governed_bundle_crosses_school_model_then_raw_offgrid_model(tmp_path) -> None:
    origin = PollicinoNodeRuntime(tmp_path / "origin", node_id="student-a")
    mule = PollicinoNodeRuntime(tmp_path / "mule", node_id="student-b")
    home = PollicinoNodeRuntime(tmp_path / "home", node_id="home")

    school_probe = StaticProbe(
        "school-mesh-model", NodeMode.CONNECTED_MESH, True, True
    )
    origin_controller = NodeBearerController(origin, (school_probe,))
    mule.transition(NodeMode.CONNECTED_MESH)

    school_adapter = DeterministicGovernedBearerAdapter(
        adapter_id="school-mesh-model",
        mode=NodeMode.CONNECTED_MESH,
        profile=_profile(221),
    )
    origin_transport = NodeBearerTransport(
        origin,
        origin_controller,
        {school_adapter.adapter_id: school_adapter},
    )

    reference, manifest, bundle = _publish(origin)
    school = origin_transport.send_governed(
        mule,
        bundle,
        manifest,
        transfer_id_base=10000,
        max_chunks=64,
        contact_id="school-model-a-b",
        now_s=1010,
    )
    assert school.adapter_id == "school-mesh-model"
    assert school.mode is NodeMode.CONNECTED_MESH
    assert school.exact
    mule_record = mule.custody_record(bundle.bundle_id)
    assert mule_record is not None and mule_record.hop_count == 1

    # Physical carry / process restart. The next transport has a completely
    # different adapter implementation and lifecycle mode, but the same PNB1
    # bundle and PNC1 custody state remain authoritative.
    mule.transition(NodeMode.OPPORTUNISTIC_DTN)
    restarted = PollicinoNodeRuntime(tmp_path / "mule", node_id="student-b")
    home.transition(NodeMode.OPPORTUNISTIC_DTN)

    offgrid_probe = StaticProbe(
        "raw-offgrid-model", NodeMode.OPPORTUNISTIC_DTN, True, True
    )
    mule_controller = NodeBearerController(restarted, (offgrid_probe,))
    offgrid_adapter = DeterministicGovernedBearerAdapter(
        adapter_id="raw-offgrid-model",
        mode=NodeMode.OPPORTUNISTIC_DTN,
        profile=_profile(222),
    )
    mule_transport = NodeBearerTransport(
        restarted,
        mule_controller,
        {offgrid_adapter.adapter_id: offgrid_adapter},
    )

    territorial = mule_transport.send_governed(
        home,
        restarted.bundle(bundle.bundle_id),
        restarted.manifest(manifest.fingerprint),
        transfer_id_base=11000,
        max_chunks=64,
        contact_id="offgrid-model-b-home",
        now_s=1100,
    )
    assert territorial.adapter_id == "raw-offgrid-model"
    assert territorial.mode is NodeMode.OPPORTUNISTIC_DTN
    assert territorial.exact
    home_record = home.custody_record(bundle.bundle_id)
    assert home_record is not None and home_record.hop_count == 2
    assert PortableReference.decode(home.reconstruct(manifest.fingerprint)) == reference

    assert school.total_wire_bytes > 0
    assert territorial.total_wire_bytes > 0


def test_real_loramesher_lifecycle_probe_without_data_bridge_fails_closed(tmp_path) -> None:
    source = PollicinoNodeRuntime(tmp_path / "source", node_id="source")
    target = PollicinoNodeRuntime(tmp_path / "target", node_id="target")
    target.transition(NodeMode.CONNECTED_MESH)
    reference, manifest, bundle = _publish(source)

    snapshot = LoRaMesherRuntimeSnapshot(
        running=True,
        current_state="NORMAL_OPERATION",
        connected_nodes=3,
        is_synchronized=True,
        ready_to_send=True,
        time_since_last_sync_ms=5,
    )
    probe = LoRaMesherBearerProbe(lambda: snapshot)
    controller = NodeBearerController(source, (probe,))

    # There is deliberately NO `loramesher` data-plane adapter registered yet.
    transport = NodeBearerTransport(source, controller, {})
    with pytest.raises(BearerDataPlaneUnavailable, match="no validated data-plane"):
        transport.send_governed(
            target,
            bundle,
            manifest,
            transfer_id_base=12000,
            max_chunks=64,
            contact_id="must-not-fake-loramesher",
            now_s=1010,
        )

    assert source.mode is NodeMode.CONNECTED_MESH
    assert target.custody_record(bundle.bundle_id) is None
    assert not target.knows_manifest(manifest.fingerprint)
    assert PortableReference.decode(source.reconstruct(manifest.fingerprint)) == reference


def test_data_plane_refuses_target_in_incompatible_lifecycle_mode(tmp_path) -> None:
    source = PollicinoNodeRuntime(tmp_path / "source", node_id="source")
    target = PollicinoNodeRuntime(tmp_path / "target", node_id="target")
    probe = StaticProbe("school-model", NodeMode.CONNECTED_MESH, True, True)
    controller = NodeBearerController(source, (probe,))
    adapter = DeterministicGovernedBearerAdapter(
        "school-model", NodeMode.CONNECTED_MESH, _profile(223)
    )
    transport = NodeBearerTransport(source, controller, {"school-model": adapter})
    _reference, manifest, bundle = _publish(source)

    # Controller enters school mode, but the target is still DISCOVERING; the
    # model must not silently bridge unrelated contexts.
    with pytest.raises(ValueError, match="target mode"):
        transport.send_governed(
            target,
            bundle,
            manifest,
            transfer_id_base=13000,
            max_chunks=64,
            contact_id="incompatible-target-mode",
            now_s=1010,
        )
