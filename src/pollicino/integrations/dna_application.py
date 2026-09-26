from __future__ import annotations

from .dna import DNATraceV01
from .dna_subscription import (
    DNAGovernedForward,
    DNAGovernedPublication,
    forward_governed_trace_if_subscribed,
    publish_governed_trace_if_subscribed,
)
from .dna_subscription_store import DNASubscriptionRegistry
from pollicino.bearer_transport import NodeBearerTransport
from pollicino.net.bundle import ForwardBundle
from pollicino.net.store import ChunkManifest
from pollicino.node_runtime import PollicinoNodeRuntime


class DNAApplicationCoordinator:
    """Bind one Pollicino node to its persisted local DNA subscription policy.

    The coordinator is deliberately application-layer glue. It owns no network
    protocol and adds no DNA wire fields. Instead it resolves the node's active
    subscription from ``DNASubscriptionRegistry`` and delegates accepted work to
    the already validated DNA integration, governed object runtime and bearer
    transport.

    Incoming offers are evaluated by the *target* coordinator. This keeps
    subscription ownership local: a source does not invent or persist another
    node's interests merely to decide whether to transfer an object.
    """

    def __init__(
        self,
        node: PollicinoNodeRuntime,
        subscriptions: DNASubscriptionRegistry,
    ) -> None:
        if not isinstance(node, PollicinoNodeRuntime):
            raise TypeError("node must be PollicinoNodeRuntime")
        if not isinstance(subscriptions, DNASubscriptionRegistry):
            raise TypeError("subscriptions must be DNASubscriptionRegistry")
        if subscriptions.node_id != node.node_id:
            raise ValueError("subscription registry belongs to a different node")
        self.node = node
        self.subscriptions = subscriptions

    def publish_active(
        self,
        trace: DNATraceV01,
        *,
        coordinate: bytes,
        chunk_size: int,
        created_at_s: int,
        label: str = "dna-trace",
        prefer_inline: bool = True,
        radio_authenticator: bytes | None = None,
        hop_limit: int = 0,
    ) -> DNAGovernedPublication:
        """Publish only when the node's current local subscription accepts it."""

        return publish_governed_trace_if_subscribed(
            self.node,
            trace,
            self.subscriptions.require_active(),
            coordinate=coordinate,
            chunk_size=chunk_size,
            created_at_s=created_at_s,
            label=label,
            prefer_inline=prefer_inline,
            radio_authenticator=radio_authenticator,
            hop_limit=hop_limit,
        )

    def accept_offer(
        self,
        transport: NodeBearerTransport,
        bundle: ForwardBundle,
        manifest: ChunkManifest,
        *,
        transfer_id_base: int,
        max_chunks: int,
        contact_id: str,
        now_s: int,
    ) -> DNAGovernedForward:
        """Apply this target node's active subscription before any transfer."""

        return forward_governed_trace_if_subscribed(
            transport,
            self.node,
            bundle,
            manifest,
            self.subscriptions.require_active(),
            transfer_id_base=transfer_id_base,
            max_chunks=max_chunks,
            contact_id=contact_id,
            now_s=now_s,
        )

    def offer_to(
        self,
        target: DNAApplicationCoordinator,
        transport: NodeBearerTransport,
        bundle: ForwardBundle,
        manifest: ChunkManifest,
        *,
        transfer_id_base: int,
        max_chunks: int,
        contact_id: str,
        now_s: int,
    ) -> DNAGovernedForward:
        """Offer one governed DNA trace; the target owns the acceptance policy."""

        if not isinstance(target, DNAApplicationCoordinator):
            raise TypeError("target must be DNAApplicationCoordinator")
        if not isinstance(transport, NodeBearerTransport):
            raise TypeError("transport must be NodeBearerTransport")
        if transport.source is not self.node:
            raise ValueError("transport source does not belong to this DNA application")
        return target.accept_offer(
            transport,
            bundle,
            manifest,
            transfer_id_base=transfer_id_base,
            max_chunks=max_chunks,
            contact_id=contact_id,
            now_s=now_s,
        )
