from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Mapping, Protocol

from .content import (
    ContentManifest,
    ContentProvider,
    ManifestResolver,
    RetrievalError,
    retrieve_exact,
)
from .link import ScarceLinkProfile, transmit_exact
from .wire import DiscoveryDescriptor


class AuthorizationGate(Protocol):
    """Application-supplied authorization decision.

    PollicinoNet deliberately does not define consent, identity, roles or
    business rules. An application adapter decides whether a descriptor may
    progress beyond discovery.
    """

    def authorize(self, descriptor: DiscoveryDescriptor, context: bytes) -> bool:
        ...


@dataclass(frozen=True, slots=True)
class DeliveryPolicy:
    prefer_rich_path: bool = True
    allow_scarce_fallback: bool = True


@dataclass(frozen=True, slots=True)
class AdaptiveDeliveryReport:
    path: str
    scarce_discovery_bytes: int
    scarce_manifest_wire_bytes: int
    scarce_content_wire_bytes: int
    total_scarce_wire_bytes: int
    rich_manifest_bytes: int
    rich_content_bytes: int
    fallback_manifest_retransmissions: int
    fallback_content_retransmissions: int
    exact: bool
    sha256: str


class AuthorizationError(PermissionError):
    pass


class AdaptiveDeliveryError(RuntimeError):
    pass


def _verify_content(manifest: ContentManifest, content: bytes) -> bytes:
    if not isinstance(content, bytes):
        raise TypeError("content must be bytes")
    digest = hashlib.sha256(content).digest()
    if len(content) != manifest.size_bytes or digest != manifest.sha256_digest:
        raise AdaptiveDeliveryError("source content does not match the resolved manifest")
    return digest


def deliver_exact_adaptive(
    descriptor: DiscoveryDescriptor,
    *,
    authorizer: AuthorizationGate,
    authorization_context: bytes = b"",
    resolver: ManifestResolver,
    rich_providers: Mapping[str, ContentProvider],
    source_content: bytes | None = None,
    scarce_profile: ScarceLinkProfile | None = None,
    transfer_id: int = 1,
    policy: DeliveryPolicy = DeliveryPolicy(),
) -> tuple[bytes, AdaptiveDeliveryReport]:
    """Deliver one exact object using a rich path or scarce-link fallback.

    Authorization is evaluated before manifest resolution or content access.
    This keeps identity/consent policy outside PollicinoNet while ensuring a
    denied request does not progress to data exchange.

    The fallback path sends the complete PNM1 manifest first and then the exact
    content using PN-002 PNF1 framing. The receiver verifies the reconstructed
    bytes against the manifest's full SHA-256 and declared length.
    """

    if not isinstance(authorization_context, bytes):
        raise TypeError("authorization_context must be bytes")
    if not isinstance(transfer_id, int) or not 0 <= transfer_id <= 0xFFFFFFFE:
        raise ValueError("transfer_id must leave room for the manifest/content pair")

    if not authorizer.authorize(descriptor, authorization_context):
        raise AuthorizationError("application authorization denied data exchange")

    descriptor_wire = descriptor.encode()

    if policy.prefer_rich_path and rich_providers:
        try:
            content, rich_report = retrieve_exact(
                descriptor,
                resolver=resolver,
                providers=rich_providers,
            )
        except (LookupError, RetrievalError):
            pass
        else:
            return content, AdaptiveDeliveryReport(
                path="rich",
                scarce_discovery_bytes=len(descriptor_wire),
                scarce_manifest_wire_bytes=0,
                scarce_content_wire_bytes=0,
                total_scarce_wire_bytes=len(descriptor_wire),
                rich_manifest_bytes=rich_report.manifest_bytes,
                rich_content_bytes=rich_report.content_bytes,
                fallback_manifest_retransmissions=0,
                fallback_content_retransmissions=0,
                exact=True,
                sha256=rich_report.reconstructed_sha256,
            )

    if not policy.allow_scarce_fallback:
        raise AdaptiveDeliveryError("rich path unavailable and scarce fallback is disabled")
    if scarce_profile is None:
        raise AdaptiveDeliveryError("scarce fallback requires a ScarceLinkProfile")
    if source_content is None:
        raise AdaptiveDeliveryError("scarce fallback requires exact source_content")

    manifest_wire = resolver.resolve(descriptor.rendezvous_key)
    sender_manifest = ContentManifest.decode(manifest_wire)
    digest = _verify_content(sender_manifest, source_content)

    received_manifest_wire, manifest_report = transmit_exact(
        manifest_wire,
        transfer_id=transfer_id,
        profile=scarce_profile,
    )
    receiver_manifest = ContentManifest.decode(received_manifest_wire)

    received_content, content_report = transmit_exact(
        source_content,
        transfer_id=transfer_id + 1,
        profile=scarce_profile,
    )
    receiver_digest = _verify_content(receiver_manifest, received_content)
    if receiver_digest != digest:
        raise AdaptiveDeliveryError("sender/receiver digest mismatch after fallback transfer")

    scarce_manifest_bytes = manifest_report.total_wire_bytes
    scarce_content_bytes = content_report.total_wire_bytes
    total_scarce_bytes = len(descriptor_wire) + scarce_manifest_bytes + scarce_content_bytes

    return received_content, AdaptiveDeliveryReport(
        path="scarce-exact",
        scarce_discovery_bytes=len(descriptor_wire),
        scarce_manifest_wire_bytes=scarce_manifest_bytes,
        scarce_content_wire_bytes=scarce_content_bytes,
        total_scarce_wire_bytes=total_scarce_bytes,
        rich_manifest_bytes=0,
        rich_content_bytes=0,
        fallback_manifest_retransmissions=manifest_report.retransmissions,
        fallback_content_retransmissions=content_report.retransmissions,
        exact=True,
        sha256=receiver_digest.hex(),
    )
