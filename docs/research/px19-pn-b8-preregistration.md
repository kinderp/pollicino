# PX19-PN-B8 preregistration

Status: preregistered before implementation and before scientific two-host LAN
contacts.

`PX19-PN-B8` is the repository-owner candidate identifier derived from the
closed PX18 recommendation. No authoritative replacement exists in the exact
PX18 baseline tree. PX3--PX18 evidence and PILOT-014 remain untouched.

## Hypothesis

The unchanged PX18 UDP/B4 transport contract can synchronize independent
Pollicino endpoints across two physically distinct machines on one IPv4 LAN.
Moving from loopback to a real NIC/LAN path requires no semantic change above
the adapter and no persistent delivery authority.

## Registered physical model

- two physical hosts; containers, VMs, loopback aliases, overlays, VPNs and
  tunnels do not qualify;
- explicit numeric unicast IPv4 addresses and ports;
- direct UDP between peer LAN addresses, with connected UDP retained;
- separate filesystems, durable roots, processes and worktrees;
- identical committed PX19 implementation SHA and clean tree on both hosts;
- route proof must name a non-loopback interface and its MTU on each host;
- no shared state, clock-order assumption, discovery, routing, DNS, NAT,
  security, ACK/retry, FEC, PMTU protocol or MTU negotiation.

The local host observed before preregistration is macOS 15.7.9 arm64, Python
3.14.2, address `192.168.1.50`, interface `en0`, interface MTU 1500. A candidate
physical peer at `192.168.1.51` answered ICMP, but had no reachable SSH service;
this is environment discovery only and is not two-host Pollicino evidence.

## UDP and B4 contract

```text
one complete B4 frame = one UDP datagram
```

The implementation may generalize PX18's address validator from loopback-only
to explicit numeric IPv4 unicast. B4, D2/D3/D4, and the B2 family must not
change. The generic `max_frame_bytes`, `send_frame`, `receive_frame`, `close`
surface remains frozen. Transport coordinates remain non-authenticating.

## Registered ceilings and timing

Required physical-LAN B4 ceilings are 128, 512, 1024 and 1200 bytes. A fifth
near-path ceiling will be frozen in a supplemental preregistration commit only
after both interfaces/routes are recorded and before any final LAN contact.
The default scientific idle receive horizon is 2.0 seconds; orchestration has
a 20-second finite safety horizon. A timeout ends only the current opportunity.

The inherited 29,245-byte maximum B2 message is admitted at ceiling 128 or 512
if bounded runtime permits. No limit is enlarged.

## Path-MTU policy

Record both interface MTUs and route decisions. Use a non-privileged,
platform-appropriate diagnostic only if both hosts support it cleanly.
Otherwise record `PATH_MTU_BOUNDARY_INCONCLUSIVE`. Never infer absence of IP
fragmentation merely from delivery, and never add PMTU logic to Pollicino.

## Mandatory scenarios

Environment/route proof; A-to-B and reversed-role query; result and explicit
reference; PX11 105-record exact fairness; compact equality and small
difference; adaptive 0/1/10/100/1000; multi-frame B4 and registered ceilings;
crash before/after commit; sender exit; both-process restart; missing peer;
peer disappearance; MTU mismatch; and loopback/LAN/four-path canonical
comparison. Manual physical interruption is optional and never automated.

## Success invariants

```text
TWO_PHYSICAL_HOSTS = YES
LOOPBACK_INTERFACE_USED = NO
SAME_IMPLEMENTATION_SHA_BOTH_HOSTS = YES
DIRTY_SCIENTIFIC_WORKTREES = 0
REAL_LAN_CANONICAL_MISMATCHES = 0
LOOPBACK_LAN_CANONICAL_MISMATCHES = 0
FOUR_PATH_CANONICAL_MISMATCHES = 0
SHARED_ENDPOINT_OBJECTS = 0
SHARED_DURABLE_ROOTS = 0
DIRECT_REMOTE_STORE_READS = 0
B4_CHANGED = NO
UDP_EXTRA_FRAMING_BYTES = 0
PERSISTENT_LAN_SESSION_STATE = 0
PERSISTENT_ACK_STATE = 0
PERSISTENT_FRAGMENT_STATE = 0
APPLICATION_SPECIFIC_LAN_BRANCHES = 0
LAN_SPECIFIC_PROTOCOL_BRANCHES = 0
UDP_SPECIFIC_D4_BRANCHES = 0
UDP_SPECIFIC_B2_FAMILY_BRANCHES = 0
UDP_SPECIFIC_B4_BRANCHES = 0
FALSE_CONVERGENCE_AFTER_NETWORK_FAILURE = 0
STARVED_ELIGIBLE_RECORDS = 0
ORACLE_MISMATCHES = 0
UNDETECTED_FALSE_NEGATIVES = 0
```

## Kill and closure criteria

Any required semantic change above UDP, partial native mutation, false
convergence, oracle mismatch, or need for persistent session/ACK/fragment state
stops architectural expansion. Firewall, route, MTU, portability and physical
availability failures are classified separately.

No READY classification and no PX19 checkpoint may be created without evidence
from two actual physical machines. If Host B cannot be run, the only admissible
classification is `PX19_REAL_LAN_EVIDENCE_PENDING` or
`PX19_PN_B8_INCONCLUSIVE`.
