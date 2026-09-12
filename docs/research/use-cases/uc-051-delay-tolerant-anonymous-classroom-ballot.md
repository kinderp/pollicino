# UC-051 — Delay-Tolerant Anonymous Classroom Survey / Ballot

## Idea

Run a **low-stakes anonymous classroom poll** even when participants are not simultaneously connected, while keeping eligibility, ballot secrecy and duplicate prevention separate.

This is an educational distributed-systems/cryptography experiment only. It is **not** a design for public elections, legally binding votes or high-stakes governance.

## Problem solved

A normal online poll assumes every participant can reach one server before the deadline. In a partitioned student network, ballots may need to wait on relays and arrive later.

At the same time, we want different guarantees to remain distinct:

```text
Was this participant eligible?
Was at most one ballot accepted for that eligibility token?
Can relays read the vote?
Can a late/duplicate ballot change the final tally?
Can the tally be reproduced from the accepted exact ballot set?
```

This makes the scenario a compact way to teach store-and-forward, cryptographic envelopes, exact-set convergence and privacy.

## Actors / nodes

- poll issuer/teacher node;
- synthetic eligible voter nodes;
- student relay/store-and-forward nodes;
- one or more tally nodes;
- optional threshold key holders for an advanced variant;
- optional UC-048 credential/eligibility issuer and UC-020 trusted closing-time checkpoint.

## Why PollicinoNet fits

Ballots and receipts can be compact exact objects and do not require a continuous path.

- **DISCOVERY:** poll ID, closing epoch, supported ballot schema and rendezvous hints;
- **EXACT:** encrypted ballot envelope, unique one-use eligibility/nullifier token, ballot ID and accepted-set digest;
- **SEMANTIC:** human-readable question/options, which must never override the exact signed poll definition.

LoRa may carry a very small encrypted ballot or only the pending-ballot/control metadata depending on measured airtime. BLE/Wi-Fi can carry richer ballots or cryptographic proofs. Relays store ciphertext without needing to learn the choice.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** poll definition digest, close epoch, small ballot ciphertext where measurements justify it, ballot-set summaries and receipts;
- **BLE:** nearby ballot submission and reconciliation;
- **Wi-Fi/LAN:** larger proofs, tally synchronization or audit export;
- **Internet:** optional publication of the final teaching result;
- **physical transport:** a student device carries encrypted pending ballots between disconnected groups.

## What we can test now in software

Use synthetic voters and harmless questions.

- create a canonical poll definition with poll ID, options, opening/closing epoch and eligibility set;
- issue one-use synthetic eligibility tokens or UC-048 test credentials;
- encrypt ballot choices to a tally key;
- let relays store and duplicate ballot ciphertext without learning the vote;
- reject a second ballot using the same one-use/nullifier token;
- deliver ballots late, out of order and through multiple relays;
- make duplicate delivery idempotent;
- distinguish `submitted`, `accepted`, `rejected_late`, `duplicate` and `unknown` states;
- compute the tally only from the exact accepted ballot set;
- test a relay deleting ballots and quantify availability effects;
- test forged eligibility tokens and altered ciphertext;
- optional advanced experiment: threshold decryption so no single tally node can decrypt early;
- measure submission-to-acceptance delay, duplicate overhead, accepted-set convergence, late-ballot rate and metadata leakage.

A useful invariant is:

> network duplication may duplicate ciphertext packets, but it must never create a second logical vote from one eligibility right.

## What requires real hardware

- 5+ boards/devices split into two disconnected classroom groups;
- at least one moving courier;
- a tiny synthetic poll with pseudonymous participants;
- measured LoRa/control delivery and optional rich-bearer ballot transfer;
- deliberate duplicate, late and relay-loss cases;
- comparison of final accepted ballot sets across tally replicas.

Do not conduct a real student election or collect sensitive opinions during the prototype phase.

## Messina teaching scenario

Split the class into two synthetic islands, for example `Rometta` and `Messina`, with no direct path. Ask a harmless question such as which public-domain dataset should be used for the next networking lab.

Each test identity has one one-use eligibility token. Some ballots go directly to a tally node; others are carried by students through `Venetico/Spadafora` checkpoints. One ballot is intentionally duplicated and another intentionally arrives after the close epoch.

The exercise succeeds if all fully synchronized tally replicas eventually agree on:

- the same poll definition;
- the same exact accepted-ballot set;
- the same tally;
- explicit rejection reasons for duplicate/late/invalid ballots.

## Privacy / security

Voting systems are unusually subtle, so the teaching scope must remain narrow.

- use harmless synthetic polls only;
- do not infer that encryption alone provides coercion resistance, receipt-freeness or election-grade anonymity;
- separate voter eligibility from ballot content;
- minimize stable metadata that links a person to submission time/path;
- prevent relay nodes from decrypting ballots;
- make closing-time/freshness uncertainty explicit;
- preserve exact accepted-set auditability without exposing choices;
- never advertise this prototype for public elections, school governance, personnel decisions or any high-stakes vote.

## Difficulty

**High.** Store-and-forward is simple; meaningful ballot privacy, one-vote semantics, metadata minimization and verifiable tallying are not.

## Research signal

Contemporary privacy-preserving voting research and systems continue to use threshold cryptography, anonymous eligibility proofs and verifiable tallies. DAVINCI/Vocdoni, for example, describes threshold homomorphic encryption and verifiable ballot processing for its 2026 launch. PollicinoNet should not inherit claims from such systems; the useful teaching question is how a tiny exact encrypted ballot object behaves under delayed, duplicated and partitioned transport.

References:

- https://davinci.vote/
