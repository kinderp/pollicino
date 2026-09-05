from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol

from .bearer_runtime import BearerEvaluationReport, NodeBearerController
from .net.bundle import ForwardBundle
from .net.link import ScarceLinkProfile
from .net.store import ChunkManifest
from .node_runtime import (
    NodeGovernedContactReport,
    NodeMode,
    PollicinoNodeRuntime,
)


class BearerDataPlaneUnavailable(RuntimeError):
    """Selected lifecycle bearer has no validated data-plane adapter."""


class GovernedBearerAdapter(Protocol):
    adapter_id: str
    mode: NodeMode

    def transfer_governed(
        self,
        *,
        source: PollicinoNodeRuntime,
        target: PollicinoNodeRuntime,
        bundle: ForwardBundle,
        manifest: ChunkManifest,
        transfer_id_base: int,
        max_chunks: int,
        contact_id: str,
        now_s: int,
    ) -> NodeGovernedContactReport:
        """Move one governed Pollicino bundle over this bearer."""


@dataclass(frozen=True, slots=True)
class DeterministicGovernedBearerAdapter:
    """Model-only bearer adapter around existing governed PNF1 transport.

    This adapter exists to prove that Pollicino state can cross different bearer
    implementations without changing the PNB1/PNC1/PCM1 core. Its profile is
    explicit synthetic/model input. It must not be named or cited as physical
    LoRaMesher/FreakWAN evidence.
    """

    adapter_id: str
    mode: NodeMode
    profile: ScarceLinkProfile

    def __post_init__(self) -> None:
        if not isinstance(self.adapter_id, str) or not self.adapter_id:
            raise ValueError("adapter_id must be a non-empty string")
        if not isinstance(self.mode, NodeMode):
            raise TypeError("mode must be NodeMode")
        if self.mode is NodeMode.DISCOVERING:
            raise ValueError("DISCOVERING has no data-plane adapter")
        if not isinstance(self.profile, ScarceLinkProfile):
            raise TypeError("profile must be ScarceLinkProfile")

    def transfer_governed(
        self,
        *,
        source: PollicinoNodeRuntime,
        target: PollicinoNodeRuntime,
        bundle: ForwardBundle,
        manifest: ChunkManifest,
        transfer_id_base: int,
        max_chunks: int,
        contact_id: str,
        now_s: int,
    ) -> NodeGovernedContactReport:
        if source.mode is not self.mode:
            raise ValueError(
                f"source mode {source.mode.value!r} does not match bearer mode {self.mode.value!r}"
            )
        if target.mode is not self.mode:
            raise ValueError(
                f"target mode {target.mode.value!r} does not match bearer mode {self.mode.value!r}"
            )
        return target.receive_governed_from(
            source,
            bundle,
            manifest,
            profile=self.profile,
            transfer_id_base=transfer_id_base,
            max_chunks=max_chunks,
            contact_id=contact_id,
            now_s=now_s,
        )


@dataclass(frozen=True, slots=True)
class BearerTransferReport:
    adapter_id: str
    mode: NodeMode
    evaluation: BearerEvaluationReport
    contact: NodeGovernedContactReport

    @property
    def total_wire_bytes(self) -> int:
        return self.contact.total_wire_bytes

    @property
    def exact(self) -> bool:
        return self.contact.exact


class NodeBearerTransport:
    """Dispatch governed transfer through the controller-selected adapter.

    Lifecycle probes and data-plane adapters are intentionally separate. A probe
    may prove that a context exists before its data-plane bridge is implemented.
    In that case dispatch fails closed instead of silently falling back or using
    an unrelated model transport under the same adapter name.
    """

    def __init__(
        self,
        source: PollicinoNodeRuntime,
        controller: NodeBearerController,
        adapters: Mapping[str, GovernedBearerAdapter],
    ) -> None:
        if not isinstance(source, PollicinoNodeRuntime):
            raise TypeError("source must be PollicinoNodeRuntime")
        if not isinstance(controller, NodeBearerController):
            raise TypeError("controller must be NodeBearerController")
        if controller.node is not source:
            raise ValueError("controller must belong to source runtime")
        normalized: dict[str, GovernedBearerAdapter] = {}
        for adapter_id, adapter in adapters.items():
            if not isinstance(adapter_id, str) or not adapter_id:
                raise ValueError("adapter map keys must be non-empty strings")
            if adapter.adapter_id != adapter_id:
                raise ValueError("adapter map key must match adapter.adapter_id")
            normalized[adapter_id] = adapter
        self.source = source
        self.controller = controller
        self.adapters = normalized

    def send_governed(
        self,
        target: PollicinoNodeRuntime,
        bundle: ForwardBundle,
        manifest: ChunkManifest,
        *,
        transfer_id_base: int,
        max_chunks: int,
        contact_id: str,
        now_s: int,
    ) -> BearerTransferReport:
        evaluation = self.controller.evaluate()
        adapter_id = evaluation.selected_adapter_id
        if adapter_id is None:
            raise BearerDataPlaneUnavailable("no usable bearer is selected")
        try:
            adapter = self.adapters[adapter_id]
        except KeyError as exc:
            raise BearerDataPlaneUnavailable(
                f"selected bearer {adapter_id!r} has no validated data-plane adapter"
            ) from exc
        if adapter.mode is not self.source.mode:
            raise BearerDataPlaneUnavailable(
                "selected data-plane adapter mode does not match source lifecycle mode"
            )
        contact = adapter.transfer_governed(
            source=self.source,
            target=target,
            bundle=bundle,
            manifest=manifest,
            transfer_id_base=transfer_id_base,
            max_chunks=max_chunks,
            contact_id=contact_id,
            now_s=now_s,
        )
        return BearerTransferReport(
            adapter_id=adapter_id,
            mode=adapter.mode,
            evaluation=evaluation,
            contact=contact,
        )
