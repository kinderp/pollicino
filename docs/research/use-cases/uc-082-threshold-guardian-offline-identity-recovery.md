# UC-082 — Threshold Guardian Offline Identity Recovery

## Idea

Recover a lost/reset PollicinoNet identity without relying on one always-online administrator and without giving any single helper unilateral recovery power.

A small set of pre-enrolled **guardians** each holds or can produce one independent recovery approval/share. If the owner loses the device/key, a threshold such as `2-of-3` guardians can authorize binding a new key to the old logical identity. Their approvals may arrive at different times through store-and-forward relays.

The first experiments must use synthetic identities and worthless test keys only. This is not a cryptocurrency-wallet recovery service and not a production account-recovery mechanism.

## Problem solved

UC-068 handles initial enrollment and reset-device bootstrap. But a more difficult failure remains:

> what if the node/device containing the identity key is lost, destroyed or permanently wiped and the network still needs to recognize the same logical participant after recovery?

A single recovery administrator is easy but becomes a single point of compromise and availability. A threshold-guardian design can improve resilience, but introduces difficult questions:

- which recovery request are guardians approving exactly?
- what if approvals arrive days apart?
- what if the old key reappears after recovery?
- what if two conflicting recovery attempts are in flight?
- how is the old key revoked everywhere in an intermittently connected network?
- can a relay infer the user's social/guardian relationships?

## Actors / nodes

- owner logical identity;
- lost/old device identity key;
- replacement device/new key;
- 3+ pre-enrolled guardian nodes/persons for the experiment;
- relay/store-and-forward student nodes;
- optional school registrar/trust root;
- UC-019 revocation/trust-epoch distribution;
- UC-020 freshness/time checkpoints;
- UC-071 generic M-of-N approval semantics.

## Why PollicinoNet fits

Recovery approvals are small, independently generated objects that can tolerate delay.

- **DISCOVERY:** recovery request available, guardian approval pending/available, trust epoch changed;
- **EXACT:** logical identity ID, old key fingerprint, new key fingerprint, recovery-request hash, guardian ID/pseudonym, policy version, approval signature/share and resulting recovery certificate;
- **SEMANTIC:** labels such as `device-lost`, `factory-reset`, `key-compromise-suspected`, useful for operator display but not sufficient to authorize recovery.

LoRa can carry compact request/approval/revocation state. Richer bearers can carry detailed audit evidence or backup material. Physical presence/QR/NFC can optionally strengthen guardian verification without becoming mandatory to the basic store-and-forward experiment.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** recovery request digest, new-key fingerprint, guardian approval state, recovery certificate digest, trust-epoch/revocation notice;
- **BLE/NFC/QR:** optional close-range verification between owner/replacement device and a guardian;
- **Wi-Fi/LAN:** detailed audit bundle, encrypted recovery metadata and trust snapshots;
- **Internet:** optional synchronization with a registrar when available;
- **physical transport:** guardians or relay devices carry approvals between disconnected groups.

## What we can test now in software

Start with synthetic keypairs and a simple `2-of-3` policy.

Model a `RecoveryRequest` containing at least:

```text
logical_identity_id
old_key_fingerprint
new_key_fingerprint
recovery_policy_id
request_nonce
created_checkpoint
request_hash
```

Then model independent `GuardianApproval` objects bound to that exact request hash.

Test:

- normal 2-of-3 recovery;
- one guardian unavailable forever;
- duplicate approval delivery;
- approval replay against a different new key;
- stale approval after the recovery request is cancelled;
- two conflicting recovery requests for the same old identity;
- one malicious guardian approving the wrong request;
- old device comes back online after successful recovery;
- recovery certificate arrives before the newest UC-019 revocation state;
- replacement device loses power halfway through activation;
- guardian roster/policy itself changes while a recovery is pending;
- optional cooling-off period represented as a state transition rather than wall-clock certainty when trusted time is unavailable.

Useful post-recovery states should be explicit:

```text
RECOVERY_REQUESTED
PARTIALLY_APPROVED
RECOVERED_NEW_KEY_ACTIVE
OLD_KEY_REVOKED_KNOWN
OLD_KEY_REVOCATION_STALE
CONFLICTED_RECOVERY
CANCELLED
```

Important invariants:

- guardian approval must be cryptographically bound to the exact replacement key and recovery request;
- threshold success must not silently imply that every offline verifier already knows the old key is revoked;
- conflicting recovery histories must surface as a conflict, not last-write-wins.

Useful metrics include approval convergence time, time until old-key revocation is known by each verifier, duplicate/replay rejection, conflict-detection time and metadata overhead.

## What requires real hardware

A safe first experiment can use:

- 5–6 boards/devices;
- 1 owner/replacement device;
- 3 guardian nodes;
- 1–2 relays/verifiers;
- synthetic credentials only;
- one deliberately wiped owner board;
- guardians separated into groups with no simultaneous end-to-end path;
- recovery approvals ferried at different times;
- old device later reintroduced to verify revocation behavior.

Do not use real financial accounts, production credentials, school administrative identities or high-value secrets during the experiment.

## Messina teaching scenario

Create a synthetic identity `student-lab-node-17` whose private key is intentionally deleted. Three guardian roles live in separate controlled groups representing, for example, school/Messina, Rometta/Venetico and Spadafora.

A replacement board generates a new key and a recovery request. Two guardians approve the exact request at different times. Student relay nodes carry those approvals until the threshold is met. The recovered identity becomes active, and UC-019 then propagates the old-key revocation.

A final adversarial step reintroduces the supposedly lost old board. Nodes with fresh trust state must reject it; nodes with stale state must report that freshness is insufficient rather than silently asserting that both keys are valid.

## Privacy / security

Recovery is one of the highest-risk authentication paths because compromising recovery can defeat otherwise strong key security.

- use synthetic identities during teaching;
- do not broadcast human-readable guardian relationships;
- use opaque guardian IDs/pseudonyms on scarce public bearers;
- approvals must bind to old identity, new key, policy and unique request nonce;
- require independent guardian credentials and authenticated channels where appropriate;
- rate-limit recovery creation and surface concurrent requests;
- preserve an auditable recovery history;
- propagate old-key revocation explicitly via UC-019;
- allow guardians to refuse without revealing reasons publicly;
- consider a human-verifiable fingerprint/QR step before approval;
- never claim that M-of-N automatically protects against colluding guardians or compromised endpoints.

## Difficulty

**High.** The threshold check is simple. The hard part is the lifecycle around it: request binding, conflicting recoveries, stale revocation state, guardian privacy, post-recovery key migration and safe handling of a reappearing old device.

## Why this is distinct from nearby use cases

- **UC-021:** threshold-seals sensitive content so carriers cannot read it.
- **UC-068:** enrolls a new/reset device into the network.
- **UC-071:** provides generic M-of-N approval for one exact action.
- **UC-082:** applies threshold approval to the full **identity-loss recovery lifecycle**, including replacement-key binding and old-key revocation across partitions.

## Research signal

2026 work on peer-based recovery for decentralized/"grassroots" systems explicitly studies recovery from lost private keys and lost devices through designated identity/state custodians rather than a global recovery service. Recent key-recovery literature also emphasizes that recovery changes the trust model and must include post-recovery lifecycle handling. These are useful design signals, not a claim that this teaching prototype inherits their security guarantees.

References:

- https://arxiv.org/abs/2607.02304
- https://arxiv.org/abs/2608.07104
