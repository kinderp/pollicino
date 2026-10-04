# UC-159 — Priority Preemption and Resumable Bulk-Interruption Courier

## Problem solved
A relay may already be moving a large low-priority object during a short Wi-Fi/BLE contact when a small high-priority drill message, maintenance command or sensor event appears. Letting the bulk transfer continue can delay the small item; aborting it can waste verified progress.

UC-159 studies bounded priority preemption: higher-priority work may temporarily interrupt lower-priority bulk work, while the interrupted transfer remains resumable.

## Actors / nodes
Sender applications, student relay/store-and-forward nodes, destination/gateway, transfer worker, optional policy service and experiment collector.

## Why PollicinoNet fits
Priority class, expiry, progress digest, preemption reason and resume state are compact. LoRa can carry that control state while the payload remains on BLE/Wi-Fi/LAN or physical transport. The frozen LoRa PHY remains unchanged.

## Bearers
- LoRa: priority, preempt/resume state and compact progress.
- BLE/Wi-Fi/LAN: payload transfer.
- Internet: optional destination/policy source.
- Physical transport: continuation of very large bulk work.

## Software test now
Compare FIFO, strict priority, bounded preemption, anti-starvation scheduling and priority combined with UC-112 resumable transfer. Inject repeated high-priority arrivals, expiry, reboot and contact loss. Measure delay by class, retransmitted bytes, starvation and completion rate.

## Real hardware
Use 4–6 LoRa boards plus two rich-bearer devices. Start a large public file transfer, inject a small high-priority TEST item, and compare restart-from-zero with resume-from-verified-progress under the same contact script.

## Messina scenario
A student relay is moving a public model or course pack from Rometta/Venetico toward Messina. During the contact window a small TEST/EXERCISE bulletin appears. The experiment checks whether the small item passes first while the large transfer can later continue through Villafranca or Spadafora.

## Privacy / security
Priority is authorization-sensitive. Use a small fixed experiment policy; do not let every sender mark traffic urgent. Bound consecutive preemptions or reserve service for lower classes to prevent starvation.

## Difficulty
**Medium–High.**

## Distinct from existing cases
UC-095 handles fair-share budgets, UC-108 queue pressure, UC-128 future capacity and UC-112 resumable transfer. UC-159 focuses on priority inversion during an already-running rich-bearer transfer.

## Standards signal
The DTN architecture has long defined relative delivery priorities. UC-159 evaluates application/transfer scheduling above the bearer and does not modify the frozen PHY.
