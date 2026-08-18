import hashlib

import pytest

from pollicino.net import (
    ContentManifest,
    DiscoveryDescriptor,
    InMemoryContentProvider,
    InMemoryResolver,
    RetrievalError,
    RetrievalSource,
    manifest_for_content,
    retrieve_exact,
)


def test_manifest_round_trip_is_deterministic_and_fail_closed() -> None:
    manifest = ContentManifest(
        object_class=7,
        size_bytes=1234,
        sha256_digest=bytes(range(32)),
        sources=(
            RetrievalSource(provider_id="memory", locator=b"object-a"),
            RetrievalSource(provider_id="backup", locator=b"object-b"),
        ),
        metadata=b"application-opaque",
    )

    encoded = manifest.encode()
    assert ContentManifest.decode(encoded) == manifest
    assert ContentManifest.decode(encoded).encode() == encoded

    with pytest.raises(ValueError, match="truncated|shorter"):
        ContentManifest.decode(encoded[:-1])
    with pytest.raises(ValueError, match="trailing"):
        ContentManifest.decode(encoded + b"x")


def test_opaque_coordinate_resolves_exact_content() -> None:
    content = b"PollicinoNet retrieves exact bytes through a richer path."
    coordinate = bytes.fromhex("102030405060708090a0b0c0")
    locator = b"fixture/exact"

    resolver = InMemoryResolver()
    provider = InMemoryContentProvider()
    provider.put(locator, content)
    manifest = manifest_for_content(
        content,
        object_class=1,
        sources=(RetrievalSource(provider_id="memory", locator=locator),),
    )
    resolver.register(coordinate, manifest)

    descriptor = DiscoveryDescriptor(
        object_class=1,
        rendezvous_key=coordinate,
        ttl_seconds=300,
        nonce=17,
        capability_mask=1,
        authenticator=b"12345678",
    )

    reconstructed, report = retrieve_exact(
        descriptor,
        resolver=resolver,
        providers={"memory": provider},
    )

    assert reconstructed == content
    assert report.exact
    assert report.scarce_link_bytes == len(descriptor.encode())
    assert report.manifest_bytes == len(manifest.encode())
    assert report.content_bytes == len(content)
    assert report.expected_sha256 == hashlib.sha256(content).hexdigest()
    assert report.reconstructed_sha256 == report.expected_sha256


def test_coordinate_is_not_content_identity_and_can_rotate() -> None:
    content = b"same-content-under-two-rendezvous-coordinates"
    manifest = manifest_for_content(
        content,
        object_class=4,
        sources=(RetrievalSource(provider_id="memory", locator=b"same"),),
    )
    resolver = InMemoryResolver()
    resolver.register(b"epoch-coordinate-A", manifest)
    resolver.register(b"epoch-coordinate-B", manifest)

    provider = InMemoryContentProvider()
    provider.put(b"same", content)

    reports = []
    for nonce, coordinate in enumerate((b"epoch-coordinate-A", b"epoch-coordinate-B"), start=1):
        descriptor = DiscoveryDescriptor(
            object_class=4,
            rendezvous_key=coordinate,
            ttl_seconds=60,
            nonce=nonce,
        )
        reconstructed, report = retrieve_exact(
            descriptor,
            resolver=resolver,
            providers={"memory": provider},
        )
        assert reconstructed == content
        reports.append(report)

    assert b"epoch-coordinate-A" != manifest.sha256_digest[: len(b"epoch-coordinate-A")]
    assert b"epoch-coordinate-B" != manifest.sha256_digest[: len(b"epoch-coordinate-B")]
    assert reports[0].expected_sha256 == reports[1].expected_sha256


def test_tampered_content_fails_full_hash_verification() -> None:
    good = b"authoritative exact bytes"
    coordinate = b"opaque-key"
    locator = b"object"

    resolver = InMemoryResolver()
    resolver.register(
        coordinate,
        manifest_for_content(
            good,
            object_class=2,
            sources=(RetrievalSource(provider_id="memory", locator=locator),),
        ),
    )
    provider = InMemoryContentProvider()
    provider.put(locator, b"tampered bytes")

    descriptor = DiscoveryDescriptor(
        object_class=2,
        rendezvous_key=coordinate,
        ttl_seconds=60,
        nonce=1,
    )
    with pytest.raises(RetrievalError, match="matching the resolved manifest"):
        retrieve_exact(descriptor, resolver=resolver, providers={"memory": provider})


def test_bad_provider_can_fall_back_to_verified_provider() -> None:
    content = b"verified fallback"
    resolver = InMemoryResolver()
    manifest = manifest_for_content(
        content,
        object_class=9,
        sources=(
            RetrievalSource(provider_id="bad", locator=b"x"),
            RetrievalSource(provider_id="good", locator=b"y"),
        ),
    )
    resolver.register(b"coord", manifest)

    bad = InMemoryContentProvider()
    bad.put(b"x", b"corrupt")
    good = InMemoryContentProvider()
    good.put(b"y", content)

    descriptor = DiscoveryDescriptor(
        object_class=9,
        rendezvous_key=b"coord",
        ttl_seconds=60,
        nonce=2,
    )
    reconstructed, report = retrieve_exact(
        descriptor,
        resolver=resolver,
        providers={"bad": bad, "good": good},
    )

    assert reconstructed == content
    assert report.provider_attempts == 2
    assert report.failed_verification_attempts == 1
    assert report.selected_provider_id == "good"


def test_resolver_rejects_coordinate_rebinding_and_missing_coordinate() -> None:
    resolver = InMemoryResolver()
    first = ContentManifest(
        object_class=1,
        size_bytes=1,
        sha256_digest=hashlib.sha256(b"a").digest(),
        sources=(RetrievalSource(provider_id="memory", locator=b"a"),),
    )
    second = ContentManifest(
        object_class=1,
        size_bytes=1,
        sha256_digest=hashlib.sha256(b"b").digest(),
        sources=(RetrievalSource(provider_id="memory", locator=b"b"),),
    )

    resolver.register(b"coord", first)
    resolver.register(b"coord", first)
    with pytest.raises(ValueError, match="different manifest"):
        resolver.register(b"coord", second)
    with pytest.raises(LookupError, match="not resolved"):
        resolver.resolve(b"missing")
