# PX18-PN-B7 address model

PX18 deliberately admits only numeric `127.0.0.1` and explicit UDP ports.
Tests use already-bound port-zero sockets inherited by fresh endpoint workers,
which removes free-port races without adding discovery.

Connected UDP was selected over unconnected `sendto/recvfrom`: the contact has
one configured peer, so kernel filtering is smaller and less error-prone than
reimplementing source checks. A foreign socket's valid-looking B4 datagram was
not emitted by the adapter and caused no mutation. This is filtering, not
authentication; source tuples can never be Pollicino identity or trust.

Exclusive bind is retained: no `SO_REUSEADDR` or `SO_REUSEPORT`. An active bind
collision fails. Closing an adapter releases the port for rebinding. Sending to
an unused port may succeed; on the tested macOS host the subsequent receive on
the connected socket reported `ECONNREFUSED` (errno 61). Correctness does not
depend on that platform feedback.

PX18 introduces no IPv6, hostnames, DNS, multicast, broadcast, NAT traversal,
routing, peer discovery, or address negotiation.
