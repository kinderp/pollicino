from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .rapid_inference import RapidDeadlineInferenceReport


@dataclass(frozen=True, slots=True)
class RapidDeadlineSelectionItem:
    bundle_id: bytes
    application_deadline_s: int
    transfer_bytes: int
    marginal_utility: float
    marginal_utility_per_byte: float


@dataclass(frozen=True, slots=True)
class RapidDeadlineSelectionDecision:
    candidate_id: str
    destination_id: str
    now_s: int
    ranked_items: tuple[RapidDeadlineSelectionItem, ...]

    @property
    def selected(self) -> RapidDeadlineSelectionItem | None:
        return None if not self.ranked_items else self.ranked_items[0]

    @property
    def selected_bundle_id(self) -> bytes | None:
        return None if self.selected is None else self.selected.bundle_id


def select_rapid_deadline_candidate(
    inferences: Sequence[RapidDeadlineInferenceReport],
) -> RapidDeadlineSelectionDecision:
    """Select at most one replication by RAPID marginal utility per byte.

    All reports must describe the same candidate encounter. Incomplete,
    delivered, expired, already-replicated or zero-benefit inferences are not
    eligible. This is the minimal selection kernel needed before integrating a
    RAPID strategy with the routing comparator.
    """

    if not inferences:
        raise ValueError("at least one RAPID inference is required")
    if not all(isinstance(item, RapidDeadlineInferenceReport) for item in inferences):
        raise TypeError("inferences must contain RapidDeadlineInferenceReport values")

    first = inferences[0]
    context = (first.candidate_id, first.destination_id, first.now_s)
    seen_bundle_ids: set[bytes] = set()
    ranked: list[RapidDeadlineSelectionItem] = []

    for inference in inferences:
        if (inference.candidate_id, inference.destination_id, inference.now_s) != context:
            raise ValueError(
                "all RAPID inferences must describe the same candidate/destination/encounter time"
            )
        if inference.bundle_id in seen_bundle_ids:
            raise ValueError("RAPID inferences must have unique bundle IDs")
        seen_bundle_ids.add(inference.bundle_id)
        if not inference.usable_for_replication_ranking or inference.utility is None:
            continue
        if inference.utility.marginal_utility <= 0:
            continue
        ranked.append(
            RapidDeadlineSelectionItem(
                bundle_id=inference.bundle_id,
                application_deadline_s=inference.application_deadline_s,
                transfer_bytes=inference.transfer_bytes,
                marginal_utility=inference.utility.marginal_utility,
                marginal_utility_per_byte=inference.utility.marginal_utility_per_byte,
            )
        )

    ranked.sort(
        key=lambda item: (
            -item.marginal_utility_per_byte,
            item.application_deadline_s,
            item.transfer_bytes,
            item.bundle_id,
        )
    )
    return RapidDeadlineSelectionDecision(
        candidate_id=context[0],
        destination_id=context[1],
        now_s=context[2],
        ranked_items=tuple(ranked),
    )
