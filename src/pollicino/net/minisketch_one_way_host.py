from __future__ import annotations

from dataclasses import dataclass
import os

from .minisketch_host import (
    HostMinisketchReconciliation,
    reconcile_partial_caches_with_minisketch,
)
from .store import AvailabilitySummary


@dataclass(frozen=True, slots=True)
class HostMinisketchOneWayAvailability:
    """Receiver-to-source sketch result for one-way chunk transfer.

    ``source_only_indices`` are exactly the chunks the source can offer that the
    receiver lacks. ``receiver_only_indices`` are chunks present only at the
    receiver and need no request/response action for this transfer direction.
    """

    serialized_receiver_sketch: bytes
    source_only_indices: tuple[int, ...]
    receiver_only_indices: tuple[int, ...]
    native: HostMinisketchReconciliation
    evidence_class: str = "host_optional_native"

    @property
    def serialized_sketch_bytes(self) -> int:
        return len(self.serialized_receiver_sketch)


def reconcile_receiver_availability_at_source(
    source: AvailabilitySummary,
    receiver: AvailabilitySummary,
    *,
    capacity: int,
    library_path: str | os.PathLike[str] | None = None,
) -> HostMinisketchOneWayAvailability:
    """Have the receiver describe availability with one minisketch.

    This mirrors current PNA semantics: the receiver advertises what it already
    has so the source can avoid retransmitting those chunks. The receiver sketch
    is merged against the source's local set. The source can then classify the
    decoded symmetric difference using its own membership:

    - present at source -> source-only -> useful to send;
    - absent at source  -> receiver-only -> irrelevant for source->receiver.

    No second request message is needed merely to classify the difference.
    """

    native = reconcile_partial_caches_with_minisketch(
        receiver,
        source,
        capacity=capacity,
        library_path=library_path,
    )
    # In the underlying LEFT=receiver / RIGHT=source call:
    # LEFT-only = receiver-only; RIGHT-only = source-only.
    return HostMinisketchOneWayAvailability(
        serialized_receiver_sketch=native.serialized_sketch,
        source_only_indices=native.right_only_indices,
        receiver_only_indices=native.left_only_indices,
        native=native,
    )
