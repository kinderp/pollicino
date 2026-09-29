# UC-133 — Fenced Control Lease and Monotonic Command-Epoch Courier

## Idea

Allow a disconnected controller to obtain a short-lived control lease for one harmless demo actuator or robot resource, while every accepted command carries a strictly increasing fencing epoch. The target remembers the highest accepted epoch and rejects commands from older controllers even if those commands arrive much later through store-and-forward.

## Problem solved

Delay-tolerant delivery makes stale control messages a real systems problem. Controller A may receive permission for a tabletop demo actuator, then lose that lease while controller B gets a newer one. Hours later an old relay can deliver A's delayed command. Signature verification alone would still say that the old message is authentic.

UC-133 adds a monotonic fencing value so the target can distinguish authentic-but-obsolete from current control state.

## Actors / nodes

Lease issuer/coordinator, low-risk demo actuator or robot, controller nodes, student relay/store-and-forward nodes, optional UC-019 trust source and UC-020/UC-123 time-quality source.

## Why PollicinoNet fits

Lease and command metadata are tiny, while logs or sensor evidence can travel later over richer bearers. Intermittent relay paths are exactly where delayed-but-valid commands can reappear.

LoRa can carry lease epoch, target ID, command ID and compact status. The frozen LoRa PHY is unchanged.

## Possible bearers

- LoRa: lease grant/revoke, fencing epoch, bounded demo command, accept/reject receipt.
- BLE: nearby controller-to-target exchange and diagnostics.
- Wi-Fi/LAN: detailed logs, telemetry and configuration.
- Internet: optional fast path to the lease issuer.
- Physical transport: a relay carries pending control state between islands.

## What we can test now in software

Build a deterministic actuator emulator with durable max_fencing_epoch. Test controller A at epoch 41 followed by controller B at epoch 42; delayed A/41 messages after B/42; duplicate/reordered commands; reboot before and after acceptance; lease expiry with uncertain time; issuer-key revocation; command cancellation; and two controllers that both believe they are current because of a partition.

Useful states include ACCEPTED, STALE_EPOCH, LEASE_EXPIRED, WRONG_TARGET, REPLAY, POLICY_DENIED and TIME_UNCERTAIN.

## What requires real hardware

Use 4–6 boards and a harmless target such as an LED, buzzer or small servo fixture. Deliberately partition two controllers, issue a newer lease to one side, then physically ferry the stale command from the other side and verify rejection after reboot.

Keep the experiment strictly low-risk and tabletop-only.

## Messina teaching scenario

Two student groups represent Rometta/Venetico and Spadafora, while a school coordinator issues control epochs. Group A first controls a tabletop servo. Group B later receives the newer epoch. A student relay then brings A's delayed command into B's island.

The target must reject the stale epoch even though signature and payload are otherwise valid.

## Privacy / security

Authenticate issuer, target and command; bind commands to lease/epoch; persist the greatest accepted fencing value; bound every parameter locally; make expiry uncertainty explicit; minimize identities in broadcast metadata; and never let network authorization override local device safety.

A fencing epoch is not a substitute for cryptographic authentication or local safeguards.

## Difficulty

High. The wire format is small; crash consistency, split-brain handling and safe local enforcement are the real challenge.

## Why this is distinct

UC-026 authorizes one bounded action; UC-053 tasks sensors; UC-075 allocates robot jobs; UC-132 handles alert supersession. UC-133 protects stateful control ownership against stale authenticated commands from an older lease holder.

## Research / implementation signal

Distributed systems commonly use fencing tokens because lease expiry alone cannot stop a delayed former holder from acting. The useful PollicinoNet experiment is to make that failure mode visible under real store-and-forward delay.

References:

- https://nalar.dev/fencing-tokens-block-stale-lease-holders/
- https://www.ogc.org/standards/sensorthings/
