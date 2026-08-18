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

A failed rich-path attempt must not disappear when fallback occurs. If a provider returns bytes that fail full-hash verification, the final adaptive-delivery report retains rich manifest/content bytes already consumed as well as subsequent scarce-link traffic.

## Frozen object and cases

The object is a deterministic 4096-byte application-agnostic binary value with a 12-byte opaque coordinate, 8-byte PND1 authenticator and one `memory-rich` PNM1 source.

Frozen cases:

1. `rich-valid`;
2. `fallback-clean`;
3. `fallback-lossy` under 20% data / 10% ACK loss;
4. `corrupt-rich-then-fallback`;
5. `denied` before resolver/provider access.

## Scientific result

Successful GitHub Actions run `32185787384`, scientific head `1c8f0a05fd11337a0c207a0a9c63f852980f19ed`:

- **115 root/scientific tests passed in 6.04 s**;
- every allowed case reconstructed the exact 4096-byte source and SHA-256;
- denial occurred before manifest resolution or provider fetch;
- artifact `9342397186` (`pn-004-results`);
- artifact digest `sha256:47a0a532a7a11a69b690da24d43d68c12be96d8b661fa1c4f40e878d0daab339`.

| Case | Path | Scarce bytes | Rich manifest | Rich content | Fallback retransmissions |
| --- | --- | ---: | ---: | ---: | ---: |
| rich-valid | rich | **45 B** | 80 B | 4096 B | 0 |
| fallback-clean | scarce-exact | **6613 B** | 0 | 0 | 0 |
| fallback-lossy | scarce-exact | **9773 B** | 0 | 0 | 48 |
| corrupt-rich-then-fallback | scarce-exact | **6613 B** | 80 B | 22 B | 0 |

The clean fallback sends 132 B of framed manifest traffic plus 6436 B of framed content traffic, in addition to the 45 B discovery descriptor. Under the frozen lossy profile those become 564 B + 9164 B, with 7 manifest and 41 content retransmissions.

The corrupt-rich case is intentionally important for accounting: the failed attempt consumed an 80 B manifest and 22 B corrupt provider response before exact fallback. Those bytes remain visible instead of being erased by path switching.

## Success criteria

All frozen criteria passed: exact allowed delivery, rich-path scarce minimization, clean/lossy exact fallback, retry exercise, failed-rich accounting, pre-access denial, fail-closed policy/source validation and zero DNA/radio-SDK/application-policy dependency in the core.

## Conclusion and boundary

**PN-004 is a positive technical result.** PollicinoNet now has an application-independent authorization boundary plus adaptive exact delivery. DNA can later implement the authorization port, but PollicinoNet remains independently usable.

The experiment still uses in-memory rich-path adapters and the PN-002 abstract scarce-link simulator; it does not claim real Internet or LoRa behavior.
