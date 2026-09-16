from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from ..bearer_transport import GovernedBearerAdapter
from ..net.bundle import ForwardBundle
from ..net.link import (
    DeliveryError,
    FragmentFrame,
    ScarceLinkProfile,
    fragment_payload,
    reassemble_frames,
)
from ..net.store import ChunkManifest
from ..node_runtime import NodeGovernedContactReport, NodeMode, PollicinoNodeRuntime
from .loramesher_transport import (
    LoRaMesherAddress,
    LoRaMesherApplicationPort,
)


@dataclass(frozen=True, slots=True)
class LoRaMesherHostTransferReport:
    """PNF1 bytes accepted by a host-side LoRaMesher application port.

    This report deliberately counts only the encoded PNF1 application payloads
    handed to LoRaMesher. It does not include LoRaMesher headers, TDMA/control,
    retries, radio airtime or an application delivery ACK, because the narrow
    application API used by this prototype does not expose those quantities.
    """

    source_bytes: int
    reconstructed_bytes: int
    frame_count: int
    data_transmissions: int
    data_wire_bytes: int
    ack_wire_bytes: int = 0
    success: bool = True
    wire_accounting: str = "loramesher_host_application_bytes"

    @property
    def total_wire_bytes(self) -> int:
        return self.data_wire_bytes + self.ack_wire_bytes


class LoRaMesherPnf1Receiver:
    """Collect and reassemble PNF1 frames arriving on one LoRaMesher port."""

    def __init__(self, port: LoRaMesherApplicationPort) -> None:
        self.port = port
        self._frames: dict[tuple[LoRaMesherAddress, int], dict[int, FragmentFrame]] = {}
        port.set_receive_callback(self._receive)

    @property
    def local_address(self) -> LoRaMesherAddress:
        return self.port.local_address

    def _receive(self, source: LoRaMesherAddress, payload: bytes) -> None:
        frame = FragmentFrame.decode(payload)
        key = (source, frame.transfer_id)
        received = self._frames.setdefault(key, {})
        previous = received.get(frame.sequence)
        if previous is not None and previous.payload != frame.payload:
            raise ValueError("conflicting duplicate PNF1 frame over LoRaMesher")
        received[frame.sequence] = frame

    def take_complete(self, source: LoRaMesherAddress, transfer_id: int) -> bytes:
        key = (source, transfer_id)
        received = self._frames.get(key)
        if not received:
            raise DeliveryError("LoRaMesher receiver observed no PNF1 frames")
        frames = list(received.values())
        first = frames[0]
        if len(received) != first.total:
            missing = [index for index in range(first.total) if index not in received]
            raise DeliveryError(
                f"LoRaMesher PNF1 transfer is incomplete; missing sequences: {missing}"
            )
        reconstructed = reassemble_frames(frames)
        del self._frames[key]
        return reconstructed


class LoRaMesherPnf1Transmitter:
    """Synchronous host research transmitter using LoRaMesher's byte API.

    The current in-memory LoRaMesher application-port test double delivers a
    callback synchronously. A future embedded bridge may provide the same
    callable contract after waiting for its own bounded receive/session event.
    No such timing or RF behavior is inferred here.
    """

    def __init__(
        self,
        source_port: LoRaMesherApplicationPort,
        *,
        destination: LoRaMesherAddress,
        receiver: LoRaMesherPnf1Receiver,
    ) -> None:
        self.source_port = source_port
        self.destination = destination
        self.receiver = receiver
        if receiver.local_address != destination:
            raise ValueError("receiver address must match destination")
        if source_port.local_address == destination:
            raise ValueError("source and destination LoRaMesher addresses must differ")

    def __call__(
        self,
        data: bytes,
        *,
        transfer_id: int,
        profile: ScarceLinkProfile,
    ) -> tuple[bytes, LoRaMesherHostTransferReport]:
        if not isinstance(profile, ScarceLinkProfile):
            raise TypeError("profile must be ScarceLinkProfile")
        if profile.ack_bytes != 0:
            raise ValueError(
                "LoRaMesher application-port prototype cannot claim Pollicino ACK bytes"
            )
        if profile.data_loss_ppm or profile.ack_loss_ppm:
            raise ValueError(
                "LoRaMesher application-port prototype does not apply synthetic loss"
            )
        if not self.source_port.ready_to_send(self.destination):
            raise DeliveryError("LoRaMesher destination is not ready to send")

        frames = fragment_payload(
            data,
            transfer_id=transfer_id,
            max_frame_bytes=profile.max_frame_bytes,
        )
        data_wire_bytes = 0
        for frame in frames:
            encoded = frame.encode()
            result = self.source_port.send(self.destination, encoded)
            if not result.accepted:
                raise DeliveryError(
                    "LoRaMesher application API rejected PNF1 frame: " + result.detail
                )
            data_wire_bytes += len(encoded)

        reconstructed = self.receiver.take_complete(
            self.source_port.local_address,
            transfer_id,
        )
        if reconstructed != data:
            raise AssertionError("LoRaMesher PNF1 reconstruction mismatch")

        return reconstructed, LoRaMesherHostTransferReport(
            source_bytes=len(data),
            reconstructed_bytes=len(reconstructed),
            frame_count=len(frames),
            data_transmissions=len(frames),
            data_wire_bytes=data_wire_bytes,
        )


class LoRaMesherGovernedBearerAdapter(GovernedBearerAdapter):
    """Host-side governed Pollicino adapter over a LoRaMesher application port.

    It exercises the real Pollicino PNB1/PNC1/PCM1/PNA1 path with a transmitter
    that sends every PNF1 frame through the LoRaMesher application boundary.
    It is still host/model evidence: the application port does not expose the
    physical LoRaMesher wire/control cost or RF delivery evidence.
    """

    adapter_id = "loramesher"
    mode = NodeMode.CONNECTED_MESH

    def __init__(
        self,
        source_port: LoRaMesherApplicationPort,
        *,
        profile: ScarceLinkProfile,
        target_addresses: Mapping[str, LoRaMesherAddress],
        receivers: Mapping[LoRaMesherAddress, LoRaMesherPnf1Receiver],
    ) -> None:
        if not isinstance(profile, ScarceLinkProfile):
            raise TypeError("profile must be ScarceLinkProfile")
        if profile.ack_bytes != 0:
            raise ValueError("LoRaMesher governed host profile must use ack_bytes=0")
        if profile.data_loss_ppm or profile.ack_loss_ppm:
            raise ValueError("LoRaMesher governed host profile must not add synthetic loss")
        self.source_port = source_port
        self.profile = profile
        self.target_addresses = dict(target_addresses)
        self.receivers = dict(receivers)

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
        if source.mode is not NodeMode.CONNECTED_MESH:
            raise ValueError("source runtime is not in connected-mesh mode")
        if target.mode is not NodeMode.CONNECTED_MESH:
            raise ValueError("target runtime is not in connected-mesh mode")
        try:
            address = self.target_addresses[target.node_id]
        except KeyError as exc:
            raise ValueError("target runtime has no LoRaMesher address mapping") from exc
        try:
            receiver = self.receivers[address]
        except KeyError as exc:
            raise ValueError("target LoRaMesher address has no PNF1 receiver") from exc

        transmitter = LoRaMesherPnf1Transmitter(
            self.source_port,
            destination=address,
            receiver=receiver,
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
            transmitter=transmitter,
        )
