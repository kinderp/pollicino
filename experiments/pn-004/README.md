# PN-004 — Authorization-gated adaptive EXACT delivery

PN-004 adds policy gating and path selection without making DNA, identity or consent semantics part of PollicinoNet core.

## Architectural rule

The application owns authorization. PollicinoNet exposes only an `AuthorizationGate` port:

```text
application-specific policy
        |
        v
AuthorizationGate
        |
        +-- deny -> stop before manifest/content access
        |
        +-- allow
              |
              +-- rich path available -> verified retrieval
              |
              +-- otherwise, if policy permits -> PNM1 + exact content over PNF1
```

A DNA adapter may later implement the gate using `ConsentGrant`; another application may use ACLs, local policy, a capability token or another mechanism. The core imports none of them.

## Accounting invariant

A failed rich-path attempt must not disappear when fallback occurs. If a provider returns bytes that fail full-hash verification, the final adaptive-delivery report retains:

- rich manifest bytes already resolved;
- rich content bytes already fetched;
- scarce-link manifest/content bytes subsequently sent;
- retransmissions on the scarce fallback.

This prevents fallback from making Transmission Reconstruction Cost look artificially cheap.

## Frozen object

- deterministic 4096-byte application-agnostic binary object;
- 12-byte opaque rendezvous coordinate;
- 8-byte PND1 authenticator;
- one `memory-rich` retrieval source in the PNM1 manifest.

## Frozen cases

1. `rich-valid`: authorization allows and rich provider returns exact content;
2. `fallback-clean`: authorization allows, no rich provider is available, clean PN-002 scarce profile carries PNM1 + content;
3. `fallback-lossy`: same fallback under the frozen 20% data / 10% ACK-loss profile;
4. `corrupt-rich-then-fallback`: rich provider returns hash-invalid bytes; the attempt is counted and exact scarce fallback follows;
5. `denied`: application gate rejects before resolver/provider access.

## Success criteria

PN-004 succeeds technically if:

1. the root/scientific suite remains green;
2. every allowed case reconstructs the exact 4096-byte source and SHA-256;
3. the rich-valid case sends only the PND1 discovery descriptor on the scarce link;
4. clean and lossy scarce fallbacks send the PNM1 manifest before content and remain exact;
5. the lossy fallback exercises retransmission;
6. the corrupt-rich case records the failed rich-path bytes instead of hiding them, then reconstructs exactly through fallback;
7. denial occurs before manifest resolution or provider fetch;
8. disabling fallback fails closed when no rich path is available;
9. sender content that does not match the resolved manifest fails closed before fallback transmission;
10. `pollicino.net` retains zero DNA/radio-SDK/application-policy runtime dependencies.

PN-004 still uses reference in-memory rich-path adapters and the PN-002 abstract scarce-link simulator. It does not claim real Internet or LoRa behavior.
