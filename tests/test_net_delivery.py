import pytest

from pollicino.net import (
    AdaptiveDeliveryError,
    AuthorizationError,
    DeliveryPolicy,
    DiscoveryDescriptor,
    InMemoryContentProvider,
    InMemoryResolver,
    RetrievalSource,
    ScarceLinkProfile,
    deliver_exact_adaptive,
    manifest_for_content,
)


class Gate:
    def __init__(self, allowed: bool) -> None:
        self.allowed = allowed
        self.calls: list[tuple[DiscoveryDescriptor, bytes]] = []

    def authorize(self, descriptor: DiscoveryDescriptor, context: bytes) -> bool:
        self.calls.append((descriptor, context))
        return self.allowed


class CountingResolver(InMemoryResolver):
    def __init__(self) -> None:
        super().__init__()
        self.resolve_calls = 0

    def resolve(self, coordinate: bytes) -> bytes:
        self.resolve_calls += 1
        return super().resolve(coordinate)


class CountingProvider(InMemoryContentProvider):
    def __init__(self) -> None:
        super().__init__()
        self.fetch_calls = 0

    def fetch(self, locator: bytes) -> bytes:
        self.fetch_calls += 1
        return super().fetch(locator)


def setup_object(content: bytes = b"exact authorized object"):
    coordinate = b"authorized-coordinate"
    locator = b"object/exact"
    resolver = CountingResolver()
    provider = CountingProvider()
    provider.put(locator, content)
    manifest = manifest_for_content(
        content,
        object_class=5,
        sources=(RetrievalSource(provider_id="rich", locator=locator),),
    )
    resolver.register(coordinate, manifest)
    descriptor = DiscoveryDescriptor(
        object_class=5,
        rendezvous_key=coordinate,
        ttl_seconds=300,
        nonce=7,
        authenticator=b"12345678",
    )
    return descriptor, resolver, provider, content, manifest


def clean_profile() -> ScarceLinkProfile:
    return ScarceLinkProfile(
        max_frame_bytes=64,
        bitrate_bps=5000,
        ack_bytes=8,
        max_retries=3,
        seed=1,
    )


def test_denial_happens_before_resolution_or_content_access() -> None:
    descriptor, resolver, provider, content, _ = setup_object()
    gate = Gate(False)

    with pytest.raises(AuthorizationError, match="denied"):
        deliver_exact_adaptive(
            descriptor,
            authorizer=gate,
            authorization_context=b"opaque-app-context",
            resolver=resolver,
            rich_providers={"rich": provider},
            source_content=content,
            scarce_profile=clean_profile(),
        )

    assert len(gate.calls) == 1
    assert gate.calls[0][1] == b"opaque-app-context"
    assert resolver.resolve_calls == 0
    assert provider.fetch_calls == 0


def test_rich_path_uses_only_discovery_bytes_on_scarce_link() -> None:
    descriptor, resolver, provider, content, manifest = setup_object()
    gate = Gate(True)

    reconstructed, report = deliver_exact_adaptive(
        descriptor,
        authorizer=gate,
        resolver=resolver,
        rich_providers={"rich": provider},
        source_content=content,
        scarce_profile=clean_profile(),
    )

    assert reconstructed == content
    assert report.path == "rich"
    assert report.scarce_discovery_bytes == len(descriptor.encode())
    assert report.total_scarce_wire_bytes == len(descriptor.encode())
    assert report.scarce_manifest_wire_bytes == 0
    assert report.scarce_content_wire_bytes == 0
    assert report.rich_manifest_bytes == len(manifest.encode())
    assert report.rich_content_bytes == len(content)
    assert report.exact


def test_scarce_fallback_sends_manifest_then_exact_content() -> None:
    content = bytes((index * 13 + 9) % 256 for index in range(300))
    descriptor, resolver, _provider, _, manifest = setup_object(content)
    gate = Gate(True)

    reconstructed, report = deliver_exact_adaptive(
        descriptor,
        authorizer=gate,
        resolver=resolver,
        rich_providers={},
        source_content=content,
        scarce_profile=clean_profile(),
        transfer_id=100,
    )

    assert reconstructed == content
    assert report.path == "scarce-exact"
    assert report.scarce_manifest_wire_bytes > len(manifest.encode())
    assert report.scarce_content_wire_bytes > len(content)
    assert report.total_scarce_wire_bytes == (
        report.scarce_discovery_bytes
        + report.scarce_manifest_wire_bytes
        + report.scarce_content_wire_bytes
    )
    assert report.rich_manifest_bytes == 0
    assert report.rich_content_bytes == 0
    assert report.fallback_manifest_retransmissions == 0
    assert report.fallback_content_retransmissions == 0
    assert report.exact


def test_lossy_scarce_fallback_remains_exact() -> None:
    content = bytes((index * 41 + 5) % 256 for index in range(512))
    descriptor, resolver, _provider, _, _manifest = setup_object(content)
    profile = ScarceLinkProfile(
        max_frame_bytes=64,
        bitrate_bps=5000,
        data_loss_ppm=200_000,
        ack_loss_ppm=100_000,
        max_retries=12,
        ack_bytes=8,
        seed=11,
    )

    reconstructed, report = deliver_exact_adaptive(
        descriptor,
        authorizer=Gate(True),
        resolver=resolver,
        rich_providers={},
        source_content=content,
        scarce_profile=profile,
        transfer_id=200,
    )

    assert reconstructed == content
    assert report.exact
    assert (
        report.fallback_manifest_retransmissions
        + report.fallback_content_retransmissions
        > 0
    )


def test_corrupt_rich_provider_can_fall_back_without_hiding_rich_bytes() -> None:
    descriptor, resolver, provider, content, manifest = setup_object()
    corrupt = CountingProvider()
    corrupt.put(b"object/exact", b"wrong")

    reconstructed, report = deliver_exact_adaptive(
        descriptor,
        authorizer=Gate(True),
        resolver=resolver,
        rich_providers={"rich": corrupt},
        source_content=content,
        scarce_profile=clean_profile(),
        transfer_id=300,
    )

    assert reconstructed == content
    assert report.path == "scarce-exact"
    assert report.exact
    assert report.rich_manifest_bytes == len(manifest.encode())
    assert report.rich_content_bytes == len(b"wrong")
    assert corrupt.fetch_calls == 1
    assert provider.fetch_calls == 0


def test_fallback_policy_and_source_verification_fail_closed() -> None:
    descriptor, resolver, _provider, content, _manifest = setup_object()

    with pytest.raises(AdaptiveDeliveryError, match="disabled"):
        deliver_exact_adaptive(
            descriptor,
            authorizer=Gate(True),
            resolver=resolver,
            rich_providers={},
            source_content=content,
            scarce_profile=clean_profile(),
            policy=DeliveryPolicy(prefer_rich_path=True, allow_scarce_fallback=False),
        )

    with pytest.raises(AdaptiveDeliveryError, match="does not match"):
        deliver_exact_adaptive(
            descriptor,
            authorizer=Gate(True),
            resolver=resolver,
            rich_providers={},
            source_content=b"tampered-at-sender",
            scarce_profile=clean_profile(),
        )
