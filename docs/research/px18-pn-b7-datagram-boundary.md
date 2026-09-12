# PX18-PN-B7 datagram boundary

UDP preserves one application datagram boundary, so no PX17-style incremental
frame reader and no new wire prefix are necessary. B4 remains mandatory even
when a B2 message might fit a larger UDP payload:

```text
B2-family message -> B4 frame(s) -> UDP datagram(s)
```

All ceilings 53, 64, 128, 256, 512, 1024, 1500, and 4096 passed. The 797-byte
capacity-10 message retained closed B4 counts of 797, 67, 11, 4, 2, 1, 1, and
1 respectively. The 29,245-byte maximum lawful B2-family message reconstructed
byte-for-byte from 385 datagrams at ceiling 128.

Loss, duplication, delay, and reordering operate on whole datagrams. B4
reassembly remains duplicate-safe and unordered. A missing fragment leaves the
B2 message incomplete and causes zero partial native mutation. Corruption is
rejected by inherited B4 CRC/digest validation. UDP checksum behavior is not a
Pollicino authority and B4 integrity is not authentication.

Loopback may expose a large kernel path MTU. These results make no claim about
real IP fragmentation, PMTU, a NIC, Ethernet, Wi-Fi, LAN, router, or WAN path.
