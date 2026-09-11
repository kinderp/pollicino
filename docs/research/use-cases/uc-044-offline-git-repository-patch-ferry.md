# UC-044 — Offline Git Repository and Patch Ferry

## Idea

Let students exchange **Git commits, refs, patches and repository updates through PollicinoNet even when no forge/server is simultaneously reachable**.

LoRa carries only compact repository/ref/need metadata. Actual Git objects move later through BLE/Wi-Fi/LAN, Internet when available, or by physical carry on a student device.

This is intentionally different from building a new source-control system: Git already gives exact object identities and mature merge semantics. PollicinoNet supplies delay-tolerant discovery, rendezvous and transport opportunities.

## Problem solved

A programming group may work in several disconnected places:

- one student develops at home;
- another works in the school lab;
- a third has the latest tests or documentation;
- GitHub/GitLab/Internet is temporarily unavailable;
- the machines do not meet directly.

The useful question becomes:

> "Who has commits/refs for repository R that I do not have, and when can those exact objects reach me?"

Git already supports offline transfer through `git bundle`; PollicinoNet can make the discovery and courier process opportunistic rather than manual.

## Actors / nodes

- student developer laptops;
- school lab/server repository cache;
- student relay/store-and-forward nodes;
- optional local Radicle/Git peer;
- optional Internet forge used only when reachable;
- CI/test node that can consume an exact commit later.

## Why PollicinoNet fits

Git objects are already content-addressed and incremental updates can be represented exactly.

- **DISCOVERY:** repository ID, advertised refs, compact commit/frontier summary, bundle availability;
- **EXACT:** commit SHA/object IDs, bundle hash, prerequisite refs and signatures;
- **SEMANTIC:** human labels such as branch name, issue/task description or "latest classroom exercise", never a replacement for exact commit identity.

A moving student node can carry a `RepoNeed` from one island, encounter a peer with the requested commit set, obtain an incremental bundle over Wi-Fi and deliver it later.

The frozen LoRa PHY is unchanged.

## Possible bearers

- **LoRa:** repo ID, desired ref/commit, frontier summary, bundle offer, status/receipt and rendezvous token;
- **BLE:** small patches or bundle transfer when measured size is suitable;
- **Wi-Fi/LAN:** Git bundle/pack transfer, repository synchronization and code-review artifacts;
- **Internet:** optional ordinary Git/Radicle/GitHub path when available;
- **physical transport:** student device, USB storage or laptop physically carries an exact bundle between disconnected groups.

## What we can test now in software

Create 3–5 synthetic Git repositories sharing an initial history and then partition them.

Test:

- independent commits on different nodes;
- exact commit/ref discovery through compact advertisements;
- incremental `git bundle` generation with prerequisites;
- `git bundle verify` before import;
- duplicate bundle arrival;
- stale branch advertisements;
- missing prerequisites and request of the missing base;
- two diverged branches that must remain two branches until a human/normal Git merge resolves them;
- signed commit/ref verification where configured;
- bundle corruption and exact hash rejection;
- delayed code-review/comment metadata as a separate small object;
- compare full-repository transfer with incremental object/bundle transfer;
- integrate UC-024 for `RepoNeed` and UC-033 for rich-bearer handoff.

Useful metrics include bytes transferred, commits delivered, prerequisite misses, time-to-ref-convergence, duplicate transfer overhead and manual merge/conflict count.

## What requires real hardware

A first classroom experiment needs only 3–4 laptops plus LoRa nodes:

1. all laptops start from the same small teaching repository;
2. two groups make different commits while disconnected;
3. LoRa exchanges only repo/ref metadata;
4. a moving student relay discovers that one group needs a specific commit range;
5. the Git bundle moves over Wi-Fi/BLE or physical carry;
6. the destination verifies and imports it;
7. a divergent branch remains explicit rather than being silently overwritten.

Measure actual metadata airtime and rich-link transfer time separately.

## Messina teaching scenario

Use a programming assignment repository distributed among students in different coarse zones. A group in `Rometta/Venetico` has commit `A`; a school-lab node has tests at commit `B`; a group in `Messina` has documentation at commit `C`.

No central forge is assumed during the exercise. Student relays carry compact "I have/I need" state and later exact incremental Git bundles. At the next school session every group reconstructs the expected commit graph and compares it with the authoritative exercise state.

This can later become a practical companion to `python-docente` or other teaching repositories without coupling PollicinoNet to one project.

## Privacy / security

Repository metadata can reveal project names, branch names or collaboration relationships.

- use opaque repo IDs on broad discovery when appropriate;
- encrypt private bundle contents and restrict who may request them;
- verify Git/bundle integrity before import;
- never automatically execute received code;
- never auto-run untrusted hooks/scripts;
- keep code-signing/authorship separate from transport identity;
- make branch divergence visible instead of resolving it with last-write-wins;
- do not advertise private repository names globally.

## Difficulty

**Medium.** Git already solves object identity and merge history. The main PollicinoNet work is discovery, incremental need calculation, delayed transfer, privacy and avoiding accidental code execution.

## Why this is distinct from existing use cases

UC-028 handles generic collaborative documents with CRDT/op-log semantics. UC-029 distributes software dependencies. UC-044 handles **source-control history itself**, preserving Git's DAG, prerequisites and branch semantics across delay-tolerant contacts.

## Research / standards signal

Git officially documents `git bundle` specifically for offline transfer of Git objects without an active server, including incremental bundles and prerequisite verification. Radicle provides a modern local-first peer-to-peer Git collaboration model with signed identities and repository replication. These are strong implementation references, not performance claims for PollicinoNet.

References:

- https://git-scm.com/docs/git-bundle
- https://radicle.dev/
