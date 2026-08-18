import pytest

from pollicino.net import DiscoveryDescriptor, MAGIC, MAX_KEY_BYTES


def make_descriptor() -> DiscoveryDescriptor:
    return DiscoveryDescriptor(
        object_class=7,
        rendezvous_key=bytes.fromhex("0011223344556677"),
        ttl_seconds=900,
        nonce=42,
        capability_mask=0b101,
        flags=0b10,
        hop_limit=3,
        metadata=b"generic-app-data",
        authenticator=bytes.fromhex("aabbccddeeff0011"),
    )


def test_standalone_descriptor_round_trips() -> None:
    descriptor = make_descriptor()
    encoded = descriptor.encode()

    assert encoded.startswith(MAGIC)
    assert len(encoded) == descriptor.encoded_size
    assert DiscoveryDescriptor.decode(encoded) == descriptor


def test_wire_encoding_is_deterministic() -> None:
    first = make_descriptor().encode()
    second = make_descriptor().encode()
    assert first == second


def test_metadata_is_application_opaque() -> None:
    descriptor = DiscoveryDescriptor(
        object_class=255,
        rendezvous_key=b"file-ref",
        ttl_seconds=3600,
        nonce=1,
        metadata=b"\x00\xffnot-a-domain-schema",
    )
    assert DiscoveryDescriptor.decode(descriptor.encode()).metadata == descriptor.metadata


def test_decode_rejects_wrong_magic_and_trailing_bytes() -> None:
    encoded = make_descriptor().encode()

    with pytest.raises(ValueError, match="magic"):
        DiscoveryDescriptor.decode(b"FAIL" + encoded[4:])

    with pytest.raises(ValueError, match="length mismatch"):
        DiscoveryDescriptor.decode(encoded + b"\x00")


def test_decode_rejects_truncated_descriptor() -> None:
    encoded = make_descriptor().encode()
    with pytest.raises(ValueError):
        DiscoveryDescriptor.decode(encoded[:-1])


def test_bounds_are_enforced() -> None:
    with pytest.raises(ValueError, match="rendezvous_key"):
        DiscoveryDescriptor(object_class=1, rendezvous_key=b"", ttl_seconds=1, nonce=1)

    with pytest.raises(ValueError, match="rendezvous_key"):
        DiscoveryDescriptor(
            object_class=1,
            rendezvous_key=b"x" * (MAX_KEY_BYTES + 1),
            ttl_seconds=1,
            nonce=1,
        )

    with pytest.raises(ValueError, match="object_class"):
        DiscoveryDescriptor(object_class=256, rendezvous_key=b"x", ttl_seconds=1, nonce=1)
