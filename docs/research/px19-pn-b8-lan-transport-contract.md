# PX19-PN-B8 LAN transport contract

PX18 intentionally restricted its UDP validator to `127.0.0.1`. PX19 made the
smallest necessary adapter change: admit explicit numeric IPv4 unicast local
and peer addresses while rejecting unspecified, multicast, reserved and
non-numeric addresses. Connected UDP, bounded receive, timeout, accounting and
one-B4-frame/one-datagram behavior did not change.

The worker gained only experiment evidence fields: run ID, scenario, host role,
interface/MTU, expected SHA, clean-tree enforcement, timestamps, counters and
durable state digests. Evidence paths use exclusive creation so two hosts
cannot overwrite one file.

No changes were made to B4, D2/D3/D4 or B2/B2F/B2C/B2A. The generic adapter
surface remains:

```text
max_frame_bytes
send_frame
receive_frame
close
```

This contract remains a valid candidate, but PX19 produced no physical-LAN
contact capable of confirming it end-to-end.
