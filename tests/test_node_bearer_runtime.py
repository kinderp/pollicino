from __future__ import annotations

from dataclasses import dataclass

from pollicino.bearer_runtime import (
    BearerObservation,
    BearerSelectionPolicy,
    NodeBearerController,
)
from pollicino.integrations.reference_mule import PortableReference
from pollicino.net import DiscoveryDescriptor
from pollicino.node_runtime import NodeMode, PollicinoNodeRuntime


@dataclass
class MutableProbe:
    adapter_id: str
    mode: NodeMode
    available: bool = False
    ready: bool = False
    detail: str = ""

    def probe(self) -> BearerObservation:
        return BearerObservation(
            adapter_id=self.adapter_id,
            mode=self.mode,
            available=self.available,
            ready=self.ready,
            detail=self.detail,
        )


def _controller(tmp_path):
    node = PollicinoNodeRuntime(tmp_path / "node", node_id="student-node")
    offgrid = MutableProbe("raw-offgrid", NodeMode.OPPORTUNISTIC_DTN, True, True)
    mesh = MutableProbe("loramesher-model", NodeMode.CONNECTED_MESH, False, False)
    home = MutableProbe("home-rich", NodeMode.RICH_HOME, False, False)
    controller = NodeBearerController(
        node,
        (offgrid, mesh, home),
        policy=BearerSelectionPolicy(loss_confirmations=2),
    )
    return node, offgrid, mesh, home, controller


def test_daily_mode_sequence_uses_hysteresis_on_mesh_loss(tmp_path) -> None:
    node, offgrid, mesh, home, controller = _controller(tmp_path)
    assert node.mode is NodeMode.DISCOVERING

    first = controller.evaluate()
    assert first.changed
    assert node.mode is NodeMode.OPPORTUNISTIC_DTN
    assert first.selected_adapter_id == "raw-offgrid"

    # School appears: positive higher-priority evidence is accepted immediately.
    mesh.available = mesh.ready = True
    school = controller.evaluate()
    assert school.changed
    assert node.mode is NodeMode.CONNECTED_MESH
    assert school.selected_adapter_id == "loramesher-model"

    # One missed mesh observation is not enough to flap into off-grid mode.
    mesh.available = mesh.ready = False
    one_loss = controller.evaluate()
    assert not one_loss.changed
    assert node.mode is NodeMode.CONNECTED_MESH
    assert one_loss.pending_loss_mode is NodeMode.OPPORTUNISTIC_DTN
    assert one_loss.pending_loss_count == 1

    # Mesh returns and clears the pending fallback.
    mesh.available = mesh.ready = True
    recovered = controller.evaluate()
    assert not recovered.changed
    assert node.mode is NodeMode.CONNECTED_MESH
    assert recovered.pending_loss_mode is None
    assert recovered.pending_loss_count == 0

    # Two consecutive losses now permit the fallback.
    mesh.available = mesh.ready = False
    controller.evaluate()
    fallback = controller.evaluate()
    assert fallback.changed
    assert node.mode is NodeMode.OPPORTUNISTIC_DTN
    assert fallback.selected_adapter_id == "raw-offgrid"

    # Arriving home is richer than either LoRa context and is entered immediately.
    home.available = home.ready = True
    rich = controller.evaluate()
    assert rich.changed
    assert node.mode is NodeMode.RICH_HOME
    assert rich.selected_adapter_id == "home-rich"


def test_no_usable_bearer_falls_back_to_discovering_after_confirmation(tmp_path) -> None:
    node, offgrid, _mesh, _home, controller = _controller(tmp_path)
    controller.evaluate()
    assert node.mode is NodeMode.OPPORTUNISTIC_DTN

    offgrid.available = offgrid.ready = False
    first = controller.evaluate()
    assert not first.changed
    assert node.mode is NodeMode.OPPORTUNISTIC_DTN
    assert first.pending_loss_mode is NodeMode.DISCOVERING

    second = controller.evaluate()
    assert second.changed
    assert node.mode is NodeMode.DISCOVERING
    assert second.selected_adapter_id is None


def test_mode_switches_do_not_change_exact_object_bundle_or_local_custody(tmp_path) -> None:
    node, _offgrid, mesh, home, controller = _controller(tmp_path)
    controller.evaluate()  # initial off-grid

    reference = PortableReference(
        provider_id="filesystem",
        locator=b"sha256:mode-switch-invariant-demo",
        label="mode-switch-invariant",
    )
    descriptor = DiscoveryDescriptor(
        object_class=1,
        rendezvous_key=b"mode-switch-demo",
        ttl_seconds=3600,
        hop_limit=4,
        nonce=2026082804,
    )
    manifest, bundle = node.publish_governed(
        reference.encode(),
        chunk_size=64,
        descriptor=descriptor,
        created_at_s=1000,
        label="portable-reference",
    )

    expected_payload = node.reconstruct(manifest.fingerprint)
    expected_bundle = node.bundle(bundle.bundle_id)
    expected_custody = node.custody_record(bundle.bundle_id)
    assert expected_custody is not None

    mesh.available = mesh.ready = True
    controller.evaluate()
    assert node.mode is NodeMode.CONNECTED_MESH

    mesh.available = mesh.ready = False
    controller.evaluate()
    controller.evaluate()
    assert node.mode is NodeMode.OPPORTUNISTIC_DTN

    home.available = home.ready = True
    controller.evaluate()
    assert node.mode is NodeMode.RICH_HOME

    # Restart in the final mode to prove all invariants are durable, not merely
    # in-memory identities surviving a controller call.
    restarted = PollicinoNodeRuntime(tmp_path / "node", node_id="student-node")
    assert restarted.mode is NodeMode.RICH_HOME
    assert restarted.manifest(manifest.fingerprint) == manifest
    assert restarted.reconstruct(manifest.fingerprint) == expected_payload
    assert restarted.bundle(bundle.bundle_id) == expected_bundle
    assert restarted.custody_record(bundle.bundle_id) == expected_custody
    assert PortableReference.decode(expected_payload) == reference
