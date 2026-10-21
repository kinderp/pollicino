from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol


LoRaMesherAddress = int
LoRaMesherReceiveCallback = Callable[[LoRaMesherAddress, bytes], None]


@dataclass(frozen=True, slots=True)
class LoRaMesherSendResult:
    """Minimal result mirror for the LoRaMesher application Send() boundary.

    This is a host-side integration contract, not a LoRaMesher wire format and
    not physical evidence. ``accepted`` means the application API accepted the
    payload for delivery/queueing; it does not claim RF delivery.
    """

    accepted: bool
    detail: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.accepted, bool):
            raise TypeError("accepted must be bool")
        if not isinstance(self.detail, str):
            raise TypeError("detail must be a string")


class LoRaMesherApplicationPort(Protocol):
    """Port shaped after the current upstream LoRaMesher application API.

    Upstream exposes roughly:

    - IsReadyToSend(destination)
    - Send(destination, vector<uint8_t>)
    - SetDataCallback(source, vector<uint8_t>)

    Pollicino deliberately depends only on this narrow byte-oriented surface.
    The port carries no route table, RSSI/SNR, inferred contact capacity or
    future-topology knowledge.
    """

    @property
    def local_address(self) -> LoRaMesherAddress:
        ...

    def ready_to_send(self, destination: LoRaMesherAddress) -> bool:
        ...

    def send(self, destination: LoRaMesherAddress, payload: bytes) -> LoRaMesherSendResult:
        ...

    def set_receive_callback(self, callback: LoRaMesherReceiveCallback) -> None:
        ...


class InMemoryLoRaMesherBus:
    """Deterministic host-only bus for validating the application-port boundary.

    It is intentionally *not* a mesh/radio simulator. Delivery is immediate and
    byte-exact. Its only purpose is to prove that Pollicino can sit above the
    current LoRaMesher application API without giving LoRaMesher knowledge of
    Pollicino object/bundle semantics.
    """

    def __init__(self) -> None:
        self._ports: dict[LoRaMesherAddress, InMemoryLoRaMesherPort] = {}

    def attach(self, address: LoRaMesherAddress) -> InMemoryLoRaMesherPort:
        _require_address(address)
        if address in self._ports:
            raise ValueError("LoRaMesher address is already attached")
        port = InMemoryLoRaMesherPort(address, self)
        self._ports[address] = port
        return port

    def _has_peer(self, address: LoRaMesherAddress) -> bool:
        return address in self._ports

    def _deliver(
        self,
        *,
        source: LoRaMesherAddress,
        destination: LoRaMesherAddress,
        payload: bytes,
    ) -> LoRaMesherSendResult:
        target = self._ports.get(destination)
        if target is None:
            return LoRaMesherSendResult(False, "destination not attached")
        target._receive(source, payload)
        return LoRaMesherSendResult(True, "accepted by host application bus")


class InMemoryLoRaMesherPort:
    """Host test double implementing ``LoRaMesherApplicationPort``."""

    def __init__(self, address: LoRaMesherAddress, bus: InMemoryLoRaMesherBus) -> None:
        _require_address(address)
        if not isinstance(bus, InMemoryLoRaMesherBus):
            raise TypeError("bus must be InMemoryLoRaMesherBus")
        self._address = address
        self._bus = bus
        self._callback: LoRaMesherReceiveCallback | None = None

    @property
    def local_address(self) -> LoRaMesherAddress:
        return self._address

    def ready_to_send(self, destination: LoRaMesherAddress) -> bool:
        _require_address(destination)
        return destination != self._address and self._bus._has_peer(destination)

    def send(self, destination: LoRaMesherAddress, payload: bytes) -> LoRaMesherSendResult:
        _require_address(destination)
        if not isinstance(payload, bytes):
            raise TypeError("payload must be bytes")
        if not payload:
            raise ValueError("payload must not be empty")
        if destination == self._address:
            return LoRaMesherSendResult(False, "self-send rejected")
        if not self.ready_to_send(destination):
            return LoRaMesherSendResult(False, "destination not ready")
        return self._bus._deliver(
            source=self._address,
            destination=destination,
            payload=payload,
        )

    def set_receive_callback(self, callback: LoRaMesherReceiveCallback) -> None:
        if not callable(callback):
            raise TypeError("callback must be callable")
        self._callback = callback

    def _receive(self, source: LoRaMesherAddress, payload: bytes) -> None:
        callback = self._callback
        if callback is None:
            return
        callback(source, bytes(payload))


def _require_address(value: LoRaMesherAddress) -> None:
    # Current upstream AddressType is integer-like. Keep the prototype bounded
    # to uint16 because LoRaMesher's documented on-wire addresses are 16-bit;
    # this remains an adapter constraint, not a Pollicino node-identity format.
    if isinstance(value, bool) or not isinstance(value, int) or not (0 <= value <= 0xFFFF):
        raise ValueError("LoRaMesher address must be a uint16 integer")
