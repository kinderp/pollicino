from __future__ import annotations

from dataclasses import dataclass

from pollicino.bearer_runtime import BearerObservation, NodeBearerController
from pollicino.integrations.loramesher_runtime import (
    LoRaMesherBearerProbe,
    LoRaMesherRuntimeSnapshot,
)
from pollicino.node_runtime import NodeMode, PollicinoNodeRuntime


@dataclass
class OffGridProbe:
    available: bool = True
    ready: bool = True
    adapter_id: str = "raw-offgrid"
    mode: NodeMode = NodeMode.OPPORTUNISTIC_DTN

    def probe(self) -> BearerObservation:
        return BearerObservation(
            adapter_id=self.adapter_id,
            mode=self.mode,
            available=self.available,
            ready=self.ready,
            detail="raw/off-grid model",
        )


class SnapshotBox:
    def __init__(self, snapshot: LoRaMesherRuntimeSnapshot) -> None:
        self.snapshot = snapshot

    def __call__(self) -> LoRaMesherRuntimeSnapshot:
        return self.snapshot


def _snapshot(
    *,
    running: bool = True,
    state: str = "NORMAL_OPERATION",
    connected: int = 1,
    synchronized: bool = True,
    ready: bool = True,
) -> LoRaMesherRuntimeSnapshot:
    return LoRaMesherRuntimeSnapshot(
        running=running,
        current_state=state,
        connected_nodes=connected,
        is_synchronized=synchronized,
        ready_to_send=ready,
        time_since_last_sync_ms=10 if synchronized else None,
    )


def test_probe_requires_running_sync_send_readiness_and_peer() -> None:
    cases = (
        (_snapshot(running=False), False, False, "stopped"),
        (_snapshot(synchronized=False), True, False, "not synchronized"),
        (_snapshot(ready=False), True, False, "not ready to send"),
        (_snapshot(connected=0), True, False, "no connected peers"),
        (_snapshot(), True, True, "mesh ready"),
    )

    for snapshot, expected_available, expected_ready, detail in cases:
        probe = LoRaMesherBearerProbe(SnapshotBox(snapshot))
        observation = probe.probe()
        assert observation.adapter_id == "loramesher"
        assert observation.mode is NodeMode.CONNECTED_MESH
        assert observation.available is expected_available
        assert observation.ready is expected_ready
        assert observation.usable is (expected_available and expected_ready)
        assert detail in observation.detail


def test_loramesher_probe_enters_mesh_and_hysteresis_handles_transient_loss(tmp_path) -> None:
    node = PollicinoNodeRuntime(tmp_path / "node", node_id="student")
    offgrid = OffGridProbe()
    box = SnapshotBox(_snapshot(synchronized=False, connected=0, ready=False))
    mesh = LoRaMesherBearerProbe(box)
    controller = NodeBearerController(node, (offgrid, mesh))

    controller.evaluate()
    assert node.mode is NodeMode.OPPORTUNISTIC_DTN

    box.snapshot = _snapshot()
    joined = controller.evaluate()
    assert joined.changed
    assert joined.selected_adapter_id == "loramesher"
    assert node.mode is NodeMode.CONNECTED_MESH

    # One temporary loss of IsReadyToSend/synchronization is not enough to
    # throw the node out of the school mesh lifecycle context.
    box.snapshot = _snapshot(synchronized=False, ready=False)
    transient = controller.evaluate()
    assert not transient.changed
    assert node.mode is NodeMode.CONNECTED_MESH
    assert transient.pending_loss_mode is NodeMode.OPPORTUNISTIC_DTN
    assert transient.pending_loss_count == 1

    box.snapshot = _snapshot()
    recovered = controller.evaluate()
    assert not recovered.changed
    assert node.mode is NodeMode.CONNECTED_MESH
    assert recovered.pending_loss_mode is None

    # Repeated loss permits fallback to the always-ready raw DTN bearer.
    box.snapshot = _snapshot(running=False, synchronized=False, ready=False, connected=0)
    controller.evaluate()
    fallback = controller.evaluate()
    assert fallback.changed
    assert fallback.selected_adapter_id == "raw-offgrid"
    assert node.mode is NodeMode.OPPORTUNISTIC_DTN


def test_snapshot_does_not_encode_or_infer_contact_capacity() -> None:
    snapshot = _snapshot()
    assert not hasattr(snapshot, "capacity_bytes")
    assert not hasattr(snapshot, "bitrate_bps")
    assert not hasattr(snapshot, "rssi")
    assert not hasattr(snapshot, "snr")
