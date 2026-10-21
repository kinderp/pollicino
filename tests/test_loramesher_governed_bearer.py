from __future__ import annotations

import pytest

from pollicino.bearer_runtime import NodeBearerController
from pollicino.bearer_transport import NodeBearerTransport
from pollicino.integrations.loramesher_pnf1 import (
    LoRaMesherGovernedBearerAdapter,
    LoRaMesherPnf1Receiver,
    LoRaMesherPnf1Transmitter,
)
from pollicino.integrations.loramesher_runtime import (
    LoRaMesherBearerProbe,
    LoRaMesherRuntimeSnapshot,
)
from pollicino.integrations.loramesher_transport import InMemoryLoRaMesherBus
from pollicino.integrations.reference_mule import PortableReference
from pollicino.net import DiscoveryDescriptor, ScarceLinkProfile
from pollicino.node_runtime import NodeMode, PollicinoNodeRuntime


def _mesh_snapshot() -> LoRaMesherRuntimeSnapshot:
    return LoRaMesherRuntimeSnapshot(
        running=True,
        current_state="NORMAL_OPERATION",
        connected_nodes=1,
        is_synchronized=True,
        ready_to_send=True,
        time_since_last_sync_ms=5,
    )


def _profile() -> ScarceLinkProfile:
    return ScarceLinkProfile(
        max_frame_bytes=64,
        bitrate_bps=5000,
        data_loss_ppm=0,
        ack_loss_ppm=0,
        max_retries=0,
        ack_bytes=0,
        seed=301,
    )


def _publish(node: PollicinoNodeRuntime):
    reference = PortableReference(
        provider_id="magnet",
        locator=(
            b"magnet:?xt=urn:btih:0123456789abcdef0123456789abcdef01234567"
            b"&dn=authorized-pollicino-loramesher-demo"
        ),
        label="authorized-demo",
        metadata=(("purpose", "loramesher-governed-bridge"),),
    )
    descriptor = DiscoveryDescriptor(
        object_class=1,
        rendezvous_key=b"lora-mesh-bridge",
        ttl_seconds=3600,
        hop_limit=4,
        nonce=2026082901,
    )
    manifest, bundle = node.publish_governed(
        reference.encode(),
        chunk_size=48,
        descriptor=descriptor,
        created_at_s=1000,
        label="portable-reference",
    )
    return reference, manifest, bundle


def test_governed_reference_crosses_real_loramesher_application_port_boundary(tmp_path) -> None:
    source = PollicinoNodeRuntime(tmp_path / "source", node_id="student-a")
    target = PollicinoNodeRuntime(tmp_path / "target", node_id="student-b")
    target.transition(NodeMode.CONNECTED_MESH)

    bus = InMemoryLoRaMesherBus()
    source_port = bus.attach(0x1001)
    target_port = bus.attach(0x1002)
    target_receiver = LoRaMesherPnf1Receiver(target_port)

    probe = LoRaMesherBearerProbe(_mesh_snapshot)
    controller = NodeBearerController(source, (probe,))
    adapter = LoRaMesherGovernedBearerAdapter(
        source_port,
        profile=_profile(),
        target_addresses={"student-b": 0x1002},
        receivers={0x1002: target_receiver},
    )
    transport = NodeBearerTransport(
        source,
        controller,
        {"loramesher": adapter},
    )

    reference, manifest, bundle = _publish(source)
    result = transport.send_governed(
        target,
        bundle,
        manifest,
        transfer_id_base=14000,
        max_chunks=64,
        contact_id="school-loramesher-a-b-001",
        now_s=1010,
    )

    assert result.adapter_id == "loramesher"
    assert result.mode is NodeMode.CONNECTED_MESH
    assert source.mode is NodeMode.CONNECTED_MESH
    assert result.exact
    assert target.complete(manifest.fingerprint)
    assert PortableReference.decode(target.reconstruct(manifest.fingerprint)) == reference

    custody = target.custody_record(bundle.bundle_id)
    assert custody is not None
    assert custody.hop_count == 1
    assert custody.complete

    # Both governance and inner object transfer used the injected LoRaMesher
    # PNF1 transmitter. This is host application-byte evidence only, not RF.
    assert result.contact.governance.accounting == "loramesher_host_application_bytes"
    assert result.contact.governance.inner is not None
    assert (
        result.contact.governance.inner.accounting
        == "loramesher_host_application_bytes"
    )
    assert result.total_wire_bytes > 0


def test_pnf1_loramesher_bridge_rejects_unobservable_ack_or_synthetic_loss() -> None:
    bus = InMemoryLoRaMesherBus()
    source_port = bus.attach(1)
    target_port = bus.attach(2)
    receiver = LoRaMesherPnf1Receiver(target_port)
    transmitter = LoRaMesherPnf1Transmitter(
        source_port,
        destination=2,
        receiver=receiver,
    )

    with pytest.raises(ValueError, match="ACK bytes"):
        transmitter(
            b"payload",
            transfer_id=1,
            profile=ScarceLinkProfile(
                max_frame_bytes=64,
                bitrate_bps=5000,
                ack_bytes=8,
                max_retries=0,
            ),
        )

    with pytest.raises(ValueError, match="synthetic loss"):
        transmitter(
            b"payload",
            transfer_id=2,
            profile=ScarceLinkProfile(
                max_frame_bytes=64,
                bitrate_bps=5000,
                data_loss_ppm=1,
                ack_bytes=0,
                max_retries=0,
            ),
        )


def test_governed_adapter_fails_closed_without_target_mapping(tmp_path) -> None:
    source = PollicinoNodeRuntime(tmp_path / "source", node_id="student-a")
    target = PollicinoNodeRuntime(tmp_path / "target", node_id="student-b")
    source.transition(NodeMode.CONNECTED_MESH)
    target.transition(NodeMode.CONNECTED_MESH)

    bus = InMemoryLoRaMesherBus()
    source_port = bus.attach(10)
    target_port = bus.attach(11)
    receiver = LoRaMesherPnf1Receiver(target_port)
    adapter = LoRaMesherGovernedBearerAdapter(
        source_port,
        profile=_profile(),
        target_addresses={},
        receivers={11: receiver},
    )
    _reference, manifest, bundle = _publish(source)

    with pytest.raises(ValueError, match="no LoRaMesher address mapping"):
        adapter.transfer_governed(
            source=source,
            target=target,
            bundle=bundle,
            manifest=manifest,
            transfer_id_base=15000,
            max_chunks=64,
            contact_id="missing-mapping",
            now_s=1010,
        )

    assert target.custody_record(bundle.bundle_id) is None
    assert not target.knows_manifest(manifest.fingerprint)
