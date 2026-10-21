from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from pollicino.bearer_runtime import BearerObservation
from pollicino.node_runtime import NodeMode


@dataclass(frozen=True, slots=True)
class LoRaMesherRuntimeSnapshot:
    """Host-side mirror of the LoRaMesher diagnostics needed by Pollicino.

    The current upstream LoRaMesher API exposes network status including
    ``current_state``, ``connected_nodes``, ``is_synchronized`` and
    ``time_since_last_sync_ms`` plus a separate ``IsReadyToSend()`` result.

    This snapshot is deliberately smaller than the upstream API. It does not
    import LoRaMesher, RadioLib or FreeRTOS and it carries no inferred contact
    capacity, RSSI-derived score or routing-table oracle.
    """

    running: bool
    current_state: str
    connected_nodes: int
    is_synchronized: bool
    ready_to_send: bool
    time_since_last_sync_ms: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.running, bool):
            raise TypeError("running must be bool")
        if not isinstance(self.current_state, str):
            raise TypeError("current_state must be a string")
        if (
            isinstance(self.connected_nodes, bool)
            or not isinstance(self.connected_nodes, int)
            or self.connected_nodes < 0
        ):
            raise ValueError("connected_nodes must be a non-negative integer")
        if not isinstance(self.is_synchronized, bool):
            raise TypeError("is_synchronized must be bool")
        if not isinstance(self.ready_to_send, bool):
            raise TypeError("ready_to_send must be bool")
        if self.time_since_last_sync_ms is not None and (
            isinstance(self.time_since_last_sync_ms, bool)
            or not isinstance(self.time_since_last_sync_ms, int)
            or self.time_since_last_sync_ms < 0
        ):
            raise ValueError(
                "time_since_last_sync_ms must be None or a non-negative integer"
            )

    @property
    def mesh_usable(self) -> bool:
        """Whether this snapshot can justify CONNECTED_MESH lifecycle mode.

        ``connected_nodes > 0`` is required because Pollicino's school-mesh
        lifecycle only has value when at least one other node is currently in
        the connected LoRa segment. A synchronized Network Manager alone is not
        treated as evidence of a useful peer path.
        """

        return (
            self.running
            and self.is_synchronized
            and self.ready_to_send
            and self.connected_nodes > 0
        )


SnapshotSource = Callable[[], LoRaMesherRuntimeSnapshot]


class LoRaMesherBearerProbe:
    """Map current LoRaMesher readiness into the generic node bearer runtime.

    An embedded bridge may populate ``LoRaMesherRuntimeSnapshot`` from
    ``GetNetworkStatus()`` and ``IsReadyToSend()``. This Python host prototype
    intentionally has no dependency on the C++ library.

    The probe answers only *lifecycle readiness*. It must never be used as proof
    of LoRa contact capacity, range, loss rate or physical reliability.
    """

    adapter_id = "loramesher"
    mode = NodeMode.CONNECTED_MESH

    def __init__(self, snapshot_source: SnapshotSource) -> None:
        if not callable(snapshot_source):
            raise TypeError("snapshot_source must be callable")
        self._snapshot_source = snapshot_source

    def probe(self) -> BearerObservation:
        snapshot = self._snapshot_source()
        if not isinstance(snapshot, LoRaMesherRuntimeSnapshot):
            raise TypeError("snapshot_source must return LoRaMesherRuntimeSnapshot")

        if not snapshot.running:
            reason = "stopped"
        elif not snapshot.is_synchronized:
            reason = "not synchronized"
        elif not snapshot.ready_to_send:
            reason = "not ready to send"
        elif snapshot.connected_nodes <= 0:
            reason = "no connected peers"
        else:
            reason = "mesh ready"

        detail = (
            f"state={snapshot.current_state};"
            f"connected_nodes={snapshot.connected_nodes};"
            f"synchronized={int(snapshot.is_synchronized)};"
            f"ready={int(snapshot.ready_to_send)};"
            f"reason={reason}"
        )
        return BearerObservation(
            adapter_id=self.adapter_id,
            mode=self.mode,
            available=snapshot.running,
            ready=snapshot.mesh_usable,
            detail=detail,
        )
