from __future__ import annotations

from dataclasses import dataclass

from pollicino.bearer_runtime import BearerObservation, NodeBearerController
from pollicino.bearer_transport import (
    DeterministicGovernedBearerAdapter,
    NodeBearerTransport,
)
from pollicino.integrations.loramesher_pnf1 import (
    LoRaMesherGovernedBearerAdapter,
    LoRaMesherPnf1Receiver,
)
from pollicino.integrations.loramesher_runtime import (
    LoRaMesherBearerProbe,
    LoRaMesherRuntimeSnapshot,
)
from pollicino.integrations.loramesher_transport import InMemoryLoRaMesherBus
from pollicino.integrations.reference_mule import HomeReferenceResolver, PortableReference
from pollicino.net import DiscoveryDescriptor, ScarceLinkProfile
from pollicino.node_runtime import NodeMode, PollicinoNodeRuntime


@dataclass
class OffGridProbe:
    adapter_id: str = "raw-offgrid-model"
    mode: NodeMode = NodeMode.OPPORTUNISTIC_DTN

    def probe(self) -> BearerObservation:
        return BearerObservation(
            adapter_id=self.adapter_id,
            mode=self.mode,
            available=True,
            ready=True,
            detail="deterministic off-grid model",
        )


def _mesh_snapshot() -> LoRaMesherRuntimeSnapshot:
    return LoRaMesherRuntimeSnapshot(
        running=True,
        current_state="NORMAL_OPERATION",
        connected_nodes=1,
        is_synchronized=True,
        ready_to_send=True,
        time_since_last_sync_ms=5,
    )


def _mesh_profile() -> ScarceLinkProfile:
    return ScarceLinkProfile(
        max_frame_bytes=64,
        bitrate_bps=5000,
        max_retries=0,
        ack_bytes=0,
        seed=311,
    )


def _offgrid_profile() -> ScarceLinkProfile:
    return ScarceLinkProfile(
        max_frame_bytes=64,
        bitrate_bps=5000,
        max_retries=2,
        ack_bytes=8,
        seed=312,
    )


def test_school_loramesher_to_offgrid_to_home_reference_resolution(tmp_path) -> None:
    origin = PollicinoNodeRuntime(tmp_path / "origin", node_id="student-a")
    mule = PollicinoNodeRuntime(tmp_path / "mule", node_id="student-b")
    home = PollicinoNodeRuntime(tmp_path / "home", node_id="home-gateway")
    mule.transition(NodeMode.CONNECTED_MESH)
    home.transition(NodeMode.OPPORTUNISTIC_DTN)

    reference = PortableReference(
        provider_id="magnet",
        locator=(
            b"magnet:?xt=urn:btih:0123456789abcdef0123456789abcdef01234567"
            b"&dn=authorized-school-home-demo"
        ),
        label="authorized-school-home-demo",
        metadata=(
            ("purpose", "vertical-slice"),
            ("resolver", "authorized-home-handler"),
        ),
    )
    descriptor = DiscoveryDescriptor(
        object_class=1,
        rendezvous_key=b"school-home-ref",
        ttl_seconds=7200,
        hop_limit=4,
        nonce=2026082902,
    )
    manifest, bundle = origin.publish_governed(
        reference.encode(),
        chunk_size=48,
        descriptor=descriptor,
        created_at_s=1000,
        label="portable-reference",
    )

    # Morning: the controller detects a healthy LoRaMesher school context and
    # every governed PNF1 frame crosses the byte-oriented LoRaMesher port.
    bus = InMemoryLoRaMesherBus()
    origin_port = bus.attach(0x2001)
    mule_port = bus.attach(0x2002)
    mule_receiver = LoRaMesherPnf1Receiver(mule_port)
    school_controller = NodeBearerController(
        origin,
        (LoRaMesherBearerProbe(_mesh_snapshot),),
    )
    school_adapter = LoRaMesherGovernedBearerAdapter(
        origin_port,
        profile=_mesh_profile(),
        target_addresses={"student-b": 0x2002},
        receivers={0x2002: mule_receiver},
    )
    school_transport = NodeBearerTransport(
        origin,
        school_controller,
        {"loramesher": school_adapter},
    )
    morning = school_transport.send_governed(
        mule,
        bundle,
        manifest,
        transfer_id_base=16000,
        max_chunks=64,
        contact_id="school-loramesher-a-b-vertical",
        now_s=1010,
    )
    assert morning.adapter_id == "loramesher"
    assert morning.exact
    assert morning.contact.governance.accounting == "loramesher_host_application_bytes"
    assert mule.custody_record(bundle.bundle_id).hop_count == 1

    # Physical carry is represented only by time/mode/restart. No bytes or
    # bundle identity are rewritten while the student moves away from school.
    mule.transition(NodeMode.OPPORTUNISTIC_DTN)
    restarted_mule = PollicinoNodeRuntime(tmp_path / "mule", node_id="student-b")
    assert restarted_mule.mode is NodeMode.OPPORTUNISTIC_DTN
    assert restarted_mule.bundle(bundle.bundle_id) == bundle
    assert restarted_mule.custody_record(bundle.bundle_id).hop_count == 1
    assert PortableReference.decode(
        restarted_mule.reconstruct(manifest.fingerprint)
    ) == reference

    # Afternoon: the same governed object leaves through a different bearer
    # implementation. This remains a deterministic off-grid model until the
    # real raw-radio adapter/HW evidence is connected.
    offgrid_probe = OffGridProbe()
    offgrid_controller = NodeBearerController(restarted_mule, (offgrid_probe,))
    offgrid_adapter = DeterministicGovernedBearerAdapter(
        adapter_id=offgrid_probe.adapter_id,
        mode=NodeMode.OPPORTUNISTIC_DTN,
        profile=_offgrid_profile(),
    )
    offgrid_transport = NodeBearerTransport(
        restarted_mule,
        offgrid_controller,
        {offgrid_probe.adapter_id: offgrid_adapter},
    )
    afternoon = offgrid_transport.send_governed(
        home,
        restarted_mule.bundle(bundle.bundle_id),
        restarted_mule.manifest(manifest.fingerprint),
        transfer_id_base=17000,
        max_chunks=64,
        contact_id="territory-b-home-vertical",
        now_s=1100,
    )
    assert afternoon.adapter_id == "raw-offgrid-model"
    assert afternoon.exact
    assert home.custody_record(bundle.bundle_id).hop_count == 2
    assert PortableReference.decode(home.reconstruct(manifest.fingerprint)) == reference

    # Home resolution remains an explicit application action. The Pollicino
    # network core transports the opaque reference; it never executes a magnet.
    home.transition(NodeMode.RICH_HOME)
    recovered = PortableReference.decode(home.reconstruct(manifest.fingerprint))
    accepted: list[PortableReference] = []

    def authorized_handler(item: PortableReference) -> str:
        accepted.append(item)
        return "queued by authorized home resolver"

    resolver = HomeReferenceResolver({"magnet": authorized_handler})
    receipt = resolver.resolve(recovered)
    assert receipt.accepted
    assert receipt.detail == "queued by authorized home resolver"
    assert accepted == [reference]

    # Evidence labels remain intentionally different across the two contacts.
    assert morning.contact.governance.accounting == "loramesher_host_application_bytes"
    assert afternoon.contact.governance.accounting == "deterministic_model_exact"
    assert morning.total_wire_bytes > 0
    assert afternoon.total_wire_bytes > 0
