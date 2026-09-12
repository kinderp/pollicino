# PX18-PN-B7 UDP contract

## Selected model

PX18 uses connected numeric-IPv4 loopback UDP:

```text
AF_INET / SOCK_DGRAM / 127.0.0.1
```

Each bounded contact configures one local `(address, port)` and one peer tuple.
`connect()` performs no handshake; it selects a default destination and lets
the kernel filter non-peer source tuples. The tuple remains a transport
coordinate, not peer identity, trust, or possession evidence.

The public experimental surface is deliberately the same small surface tested
by the Unix transports: `max_frame_bytes`, `send_frame(bytes)`,
`receive_frame()`, and `close()`. Address/bind setup surrounds that surface.

## Frame mapping and bounds

```text
one complete B4 frame = one UDP payload = one datagram
```

The adapter adds zero bytes. It rejects an outgoing frame larger than the
configured B4 ceiling before `send()`. A receive requests ceiling plus one byte;
an observed extra byte proves oversize and rejects the whole candidate. Empty
datagrams are rejected. Short opaque datagrams are returned to B4, which rejects
them structurally.

The tested B4 range is 53--4096 bytes. MTU is configured, not negotiated. The
adapter has no queue, retry, ACK, NACK, FEC, PMTU, discovery, routing, or DNS.

## Outcome semantics

Send success only means the local kernel accepted the datagram. Timeout,
`ECONNREFUSED`, absence of ICMP feedback, and buffer pressure end or impair the
current transport opportunity; none establishes reconciliation facts. Durable
receiver state remains the later possession authority.
