# UC-021 — Threshold-Sealed Sensitive Courier

## Idea

Move a sensitive exact object through several untrusted or semi-trusted carriers so that **no single relay holds enough information to recover the plaintext**. The destination reconstructs the protected key/material only after receiving a required threshold of independent shares.

This can combine ordinary encrypted content with threshold key sharing: the large ciphertext may travel through normal PollicinoNet content distribution, while the decryption secret is split across `k-of-n` shares carried by different nodes.

## Problem solved

Data mule systems are useful because people/devices physically bridge disconnected areas, but a relay may be lost, inspected or simply not be authorized to read the content it carries. Full replication of a sensitive file onto every student node would therefore be a poor privacy model.

Threshold transport separates **availability** from **read authority**: several relays can contribute to delivery without any one of them being able to decrypt the protected object.

## Actors / nodes

- authorized sender/origin creating the encrypted exact object;
- threshold-share generator bound to an explicit policy;
- multiple student relay/store-and-forward nodes carrying different shares or ciphertext fragments;
- authorized destination able to combine the required threshold;
- optional school/server/NAS holding an audit/reference copy under separate policy.

## Why PollicinoNet fits

PollicinoNet already treats content and manifests as exact content-addressed objects and can move metadata over LoRa while bulk bytes use richer bearers or physical carry. A signed `ThresholdManifest` can bind:

- ciphertext object hash;
- threshold scheme/version;
- `k` and `n`;
- share IDs/hashes;
- authorized recipient/key identity;
- expiry/revocation policy;
- provenance.

LoRa can advertise share availability or need without exposing the secret itself. Student nodes become useful carriers without becoming readers.

This is an application-layer confidentiality experiment and does not modify the frozen PHY.

## Possible bearers

- **LoRa:** manifest hash, share IDs, availability/need summaries, authorization/rendezvous metadata;
- **BLE/Wi-Fi/LAN:** encrypted object and secret shares when peers meet;
- **Internet:** optional authority/key-management synchronization when available;
- **physical transport:** different students carry different protected shares across disconnected areas.

Putting actual key shares on LoRa is not required and should only be considered after a threat model and payload analysis.

## What we can test now in software

- encrypt a synthetic/public test document with a random content key;
- split that key using a well-reviewed threshold secret-sharing library;
- create a signed exact manifest binding ciphertext and shares;
- distribute shares across 3–7 virtual carriers;
- prove that fewer than `k` shares cannot reconstruct the key through the intended API;
- reconstruct successfully with any valid threshold set and verify the plaintext hash;
- inject duplicate, corrupt, wrong-object and stale shares;
- test share revocation/re-issuance by creating a new manifest/version rather than silently mutating old shares;
- simulate compromised relay nodes and verify that they never receive plaintext authority;
- compare availability against a single-key courier under the same synthetic contact trace.

A key invariant is:

> carrying a share or ciphertext does not grant permission to decrypt the protected Knowledge Object.

## What requires real hardware

- 3–5 real relay devices carrying disjoint synthetic shares;
- a destination that receives the threshold through multiple separate contacts;
- one deliberate lost/absent carrier while the threshold still succeeds when policy allows;
- measurement of contact/transfer completion, not cryptographic "security strength";
- optional richer-bearer handover of the ciphertext while shares arrive through separate paths.

All early trials should use harmless synthetic documents or public data.

## Messina teaching scenario

Create a synthetic "sealed field packet" at school. The encrypted packet is cached on one or more nodes, while its decryption key is split among four student relays with a `3-of-4` policy. The destination in another controlled group must meet enough independent relays before opening it.

A second experiment can deliberately remove one carrier and verify that the destination still succeeds, while two carriers alone remain insufficient. This makes threshold concepts visible without handling real sensitive student or emergency data.

## Privacy / security

This use case requires mature cryptographic libraries and a clear threat model; do not implement ad-hoc secret sharing. Shares must be bound to the exact ciphertext/version and protected against substitution. Metadata can still leak that a sensitive transfer exists, so object names, stable identities and location details should be minimized.

Threshold secrecy does not solve endpoint compromise: an authorized destination that reconstructs the key can read the content. Revocation after shares have already been copied is also non-trivial and must be handled through new key/material versions and policy.

## Difficulty

**High.** The data-plane mechanics are straightforward, but correct key lifecycle, manifest binding, endpoint authorization and misuse-resistant cryptographic integration require careful design.

## Research signal

Threshold cryptography and secret sharing are established techniques; the interesting PollicinoNet research question is operational rather than inventing new cryptography: whether opportunistic multi-carrier mobility can improve availability while keeping plaintext authority off intermediate student/data-mule nodes.