from __future__ import annotations

from pollicino.integrations.loramesher_transport import (
    InMemoryLoRaMesherBus,
    LoRaMesherSendResult,
)
from pollicino.integrations.reference_mule import PortableReference
from pollicino.net.wire import DiscoveryDescriptor


def test_application_port_delivers_opaque_bytes_with_source_address() -> None:
    bus = InMemoryLoRaMesherBus()
    a = bus.attach(0x1001)
    b = bus.attach(0x1002)
    received: list[tuple[int, bytes]] = []
    b.set_receive_callback(lambda source, payload: received.append((source, payload)))

    payload = b"pollicino-opaque-application-payload"
    assert a.ready_to_send(0x1002)
    result = a.send(0x1002, payload)

    assert result == LoRaMesherSendResult(True, "accepted by host application bus")
    assert received == [(0x1001, payload)]


def test_portable_reference_crosses_loramesher_port_byte_exact() -> None:
    bus = InMemoryLoRaMesherBus()
    source = bus.attach(1)
    target = bus.attach(2)
    received: list[bytes] = []
    target.set_receive_callback(lambda _source, payload: received.append(payload))

    reference = PortableReference(
        provider_id="magnet",
        locator=b"magnet:?xt=urn:btih:0123456789abcdef0123456789abcdef01234567",
        label="authorized-demo",
        metadata=(("purpose", "loramesher-port-gate"),),
    )
    encoded = reference.encode()
    assert source.send(2, encoded).accepted
    assert received == [encoded]
    assert PortableReference.decode(received[0]) == reference


def test_discovery_descriptor_crosses_port_without_semantic_translation() -> None:
    bus = InMemoryLoRaMesherBus()
    source = bus.attach(7)
    target = bus.attach(8)
    received: list[bytes] = []
    target.set_receive_callback(lambda _source, payload: received.append(payload))

    descriptor = DiscoveryDescriptor(
        object_class=1,
        rendezvous_key=b"school-mesh-demo",
        ttl_seconds=3600,
        hop_limit=4,
        nonce=20260829,
    )
    wire = descriptor.encode()
    assert source.send(8, wire).accepted
    assert received == [wire]
    assert DiscoveryDescriptor.decode(received[0]) == descriptor


def test_port_fails_closed_for_unknown_destination_and_self_send() -> None:
    bus = InMemoryLoRaMesherBus()
    port = bus.attach(0x1234)

    assert not port.ready_to_send(0x9999)
    unknown = port.send(0x9999, b"x")
    assert not unknown.accepted

    self_send = port.send(0x1234, b"x")
    assert not self_send.accepted
    assert "self-send" in self_send.detail


def test_callback_registration_does_not_imply_delivery_acknowledgement() -> None:
    bus = InMemoryLoRaMesherBus()
    source = bus.attach(10)
    bus.attach(11)  # no application callback registered

    # API acceptance is deliberately weaker than application-level delivery or
    # RF evidence. The host port mirrors that distinction instead of inventing
    # a Pollicino ACK from LoRaMesher queue acceptance.
    result = source.send(11, b"opaque")
    assert result.accepted
