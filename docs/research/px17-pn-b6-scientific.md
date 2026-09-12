# PX17-PN-B6 scientific report

## Question and result

Can the unchanged B4 frame contract cross a real ordered Unix byte stream
between independent processes without another framing protocol or persistent
transport state?

Yes, within the registered local limits.  The selected primary classification
is:

```text
POLLICINO_UNIX_STREAM_TRANSPORT_READY_WITH_LIMITS
```

Confidence is high because unit framing, real kernel sockets, fresh Python
processes, persistent roots, adversarial EOF/corruption, pressure, restart,
adaptive policy, exact fairness, and mule paths all agree.

## Evidence

- baseline: 704 passed, 5 skipped; focused PX14--PX16: 198 passed;
- final: 763 passed, 5 skipped;
- focused PX17: 59 passed;
- compileall: pass;
- executable B4 header: 52 bytes;
- stream-specific wire overhead: zero;
- frame ceilings: 53 through 4096 all pass;
- capacity-10 message: 797 bytes and unchanged B4 frame counts;
- maximum B2-family message: 29,245 bytes, 385 frames at ceiling 128;
- canonical mismatch versus Unix datagram: zero;
- partial-frame native mutations: zero;
- starved records in 105-record exact run: zero;
- direct peer-store reads/shared endpoint objects: zero.

## Falsification findings

Arbitrary stream segmentation did not affect B4 frame identity.  Corruption or
deletion did not motivate resynchronization: terminating the finite connection
and starting a fresh contact was sufficient.  Receiver/sender crashes did not
require stream-session persistence or ACK state.  A short read horizon exposed
real backpressure coupling between a large response batch and receiver
lifetime, but only as bounded transport failure; it did not corrupt state or
falsely converge.

## Historical evidence discipline

PX16 `adaptive-regression.json` labels 20 differences as
`capacity_failure_and_exact`, while the closed executable on the deterministic
PX17 set reports `DECODED`.  PX16's actual test asserted transport convergence
and `COMPACT_10`, not that status.  PX17 does not rewrite the artifact.  It uses
100 differences for executable capacity-failure/fallback evidence.  This
imprecision does not affect PX16's transport classification.

The earlier PX12 documentation discrepancy also remains untouched: its
preregistration described 128-bit fingerprints/64-bit checksums while the
closed executable uses 64-bit fingerprints/32-bit checksums.  PX17 exercises
the executable behavior and makes no new compact-format claim.

## Inherited limits

- experimental B2/B4 encodings, not stable public wire protocols;
- exact metadata disclosure and known compact fingerprint/checksum limits;
- configured rather than negotiated B4 ceiling;
- one incomplete B4 message per direction;
- finite contacts, partial progress, no global delivery guarantee;
- POSIX/macOS-tested persistence with inherited single-writer assumptions;
- no authentication, encryption, routing, discovery, ACK/ARQ, FEC, or custody;
- no TCP/IP, UDP/IP, LAN, Internet, BLE, LoRa, or RF evidence.

## New stream limits

- pathname length and filesystem lifecycle are platform-specific;
- exactly one accepted connection/contact in the experimental listener model;
- ordered byte stream required by this adapter;
- invalid framing terminates the connection; no within-stream resync;
- bounded large outbound batches can meet backpressure if the peer ends its
  receive horizon early;
- blocking sockets with finite timeout are tested, not nonblocking/event-loop
  integration;
- half-close is supported but not required by correctness;
- connection/address is not authenticated identity.

## Validity of inherited gates

PX3, PX5, PX6, PX8, PX9, PX10, PX11, PX12, PX13, PX14, PX15, and PX16 remain
valid unchanged.  No historical checkpoint content changed.  PX16's artifact
imprecision is recorded above without changing its core conclusion.

## Frontier

B4 is now supported over two materially different real local transport
families without upper-layer branches.  Further Unix-local abstraction work is
not justified.  The smallest next falsification boundary is a bounded UDP/IP
adapter experiment, initially on loopback with explicit configured addresses,
carrying one B4 frame per datagram.  That crosses the IP addressing/network
stack boundary while changing only the adapter; two-machine LAN evidence should
remain separately gated.
