# PX18-PN-B7 transport comparison

| Property | Unix datagram | Unix stream | UDP/IP loopback |
|---|---:|---:|---:|
| Real kernel I/O | yes | yes | yes |
| Preserves message boundaries | yes | no | yes |
| Ordered byte stream | no | yes | no |
| Connection-oriented | no | yes | no (`connect()` is peer configuration) |
| Explicit peer address | pathname | pathname/contact | IPv4 tuple/contact |
| B4 changed | no | no | no |
| Adapter framing bytes | 0 | 0 | 0 |
| Persistent transport state | 0 | 0 | 0 |

Identical 10-query workloads ended with identical canonical D2/D3 state across
all three adapters. The minimal contract—bounded opaque frame send/receive,
configured maximum frame bytes, finite opportunity, and close—remains honest.
Connection establishment and addressing differ inside adapter setup and do not
need upper semantic capabilities.

The three materially different variants are enough to classify the minimal
generic adapter contract ready. This does not freeze OS lifecycle APIs or add an
automatic transport-selection policy.
