# PX15 generic MTU model

`MAX_FRAGMENT_FRAME_BYTES` is a synthetic, bearer-neutral frame ceiling. It is
not a claim about LoRa, BLE, Wi-Fi, UDP, or any other transport.

The B4 header is 52 bytes, so the minimum lawful frame ceiling is 53 bytes. The
registered sweep is 64, 128, 256, 512, 1024, 1500, and 4096 bytes. Usable
payload is `MTU - 52`. The inherited B2 maximum remains 29,245 bytes; B4 does
not expand it. At the smallest registered MTU, the maximum message requires
2,438 fragments.

Explicit limits are:

```text
message bytes                   29,245
frame bytes                     4,096
fragments/message               2,438
simultaneous incomplete messages 1
reassembly bytes                29,245
fragment metadata entries       2,438
fragments/contact               10,000
fragment bytes/contact          40,960,000 (derived ceiling)
```

The large contact-byte ceiling is only a hard memory/work bound. Existing B2
message and contact budgets continue to govern useful protocol progress.
Fragment counts and envelope bytes are accounted independently so physical
splitting cannot become hidden traffic.

The measured capacity-10 PX13 compact message is 797 encoded bytes. It requires
67, 11, 4, 2, 1, 1, and 1 fragments at the registered MTUs respectively. The
full measured matrix is retained in `artifacts/px15-pn-b4/mtu-matrix.json`.

