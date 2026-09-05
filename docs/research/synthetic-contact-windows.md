# Synthetic multi-relay contact windows

## Purpose

This layer lets PollicinoNet model an intermittent network as a sequence of explicit encounters between peers.

Example:

```text
08:00  A -> B  LoRa   128 logical source bytes
12:00  B -> C  LoRa   128 logical source bytes
18:00  C -> D  Wi-Fi  512 logical source bytes
```

Origin and destination do not need a direct or simultaneous connection. Each encounter runs the existing governed, fair, per-bearer scheduler and therefore preserves TTL, hop limits, custody, duplicate suppression, priority, anti-starvation and exact chunk verification.

## Important evidence boundary

A synthetic contact window has two separate inputs:

- `duration_seconds`: scenario time;
- `logical_source_byte_budget`: how many authoritative source bytes the experiment allows the scheduler to advance.

The duration does **not** determine the budget in this layer.

Therefore:

```text
30-second synthetic LoRa window
+ 128-byte synthetic policy budget
!=
measured claim that LoRa carries 128 bytes in 30 seconds
```

The report exposes `duration_drives_budget = false` for this reason.

## Why this matters for the future student network

Before deploying many physical nodes, we can model a school/province-scale topology using pseudonymous peers and synthetic contacts:

```text
student-node-A
   -> student-node-B
   -> student-node-C
   -> school-gateway
   -> Internet
```

We can experiment with:

- different contact sequences;
- LoRa/BLE/Wi-Fi/Internet handoffs;
- bundle priorities;
- fairness and anti-starvation;
- relay storage limits;
- TTL and hop limits;
- data-mule scenarios;
- gateway placement hypotheses;
- delivery latency in scenario time;
- logical traffic budgets;
- which nodes eventually hold a complete verified object.

No student home address or precise personal location is needed for software experiments. Future physical mapping should use privacy-preserving node IDs and carefully scoped location data.

## Propagation report

At the end of a scenario, PollicinoNet reports for each bundle which peers possess a complete exact copy. Completeness requires the verified PCM1 manifest plus every SHA-256-addressed chunk; reconstruction is executed to confirm the object can actually be rebuilt.

This provides a simple answer to questions such as:

> Did the object reach the school gateway even though the origin never contacted it directly?

## Fair scheduling state per source

Each transmitting peer has its own `FairSchedulerState`. Waiting age and anti-starvation therefore follow the local relay that makes the scheduling decision. States can be persisted independently when scenarios are later moved to durable relay nodes.

## Future measured adapter

After HW-006 establishes real contact behaviour, a separate evidence-backed adapter may convert measurements such as:

```text
bearer + PHY + frame sizes + geometry + observed contact window
 -> supported useful scheduling budget
```

That adapter must record provenance and must not silently reuse 42-byte measurements for differently sized PNB1/PNC1/PCM1/PNA1/data frames.

Until then, all contact-window capacity inputs remain synthetic policy values even if the underlying bearer profile contains measured parameters.
