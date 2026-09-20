# UC-092 — Opportunistic Internet Reachability and Backhaul Observatory

## Idea

Use PollicinoNet nodes as a privacy-conscious **distributed Internet reachability observatory**. Each node performs a very small, fixed measurement profile against known targets when permitted, stores the result locally, and later ferries compact summaries so the class can reconstruct where and when Internet access was healthy, degraded, partially reachable or unavailable.

PollicinoNet itself is a separate control/transport plane, so observations may still move after the Internet path being measured has failed.

## Problem solved

“Internet works / does not work” is too coarse. A node may have:

- local Wi-Fi but no upstream connectivity;
- DNS failure while HTTPS to an IP still works;
- access to one network but not another;
- intermittent or high-latency connectivity;
- a mobile uplink while fixed broadband is down;
- no Internet at all while LoRa relay paths still exist.

A distributed student network across the Messina area gives us many real vantage points, but we should not centralize browsing history or continuously track students.

## Actors / nodes

- measurement node at school/home/public checkpoint;
- student relay/store-and-forward nodes;
- collector/analysis node at school;
- fixed allow-listed measurement targets;
- optional Internet gateway nodes from UC-088.

## Why PollicinoNet fits

Reachability summaries are small, and the most interesting measurements may occur exactly when normal IP backhaul is missing.

- **DISCOVERY:** node has a recent reachability summary for a coarse area/network class;
- **EXACT:** measurement profile/version, target IDs, timestamps/epochs, result codes, resolver path, network class and signed batch hash;
- **SEMANTIC:** labels such as `healthy`, `dns-degraded`, `partial`, `offline` are derived interpretations and must remain traceable to exact measurements.

The network can therefore carry evidence about Internet failure without requiring the Internet to carry that evidence.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** compact health summary, profile ID, batch hash, coarse status and request for richer logs;
- **BLE:** nearby synchronization of measurement batches;
- **Wi-Fi/LAN:** detailed ping/DNS/TLS/HTTP timing records;
- **Internet:** used only as the thing being measured and optionally as a fast upload path when it works;
- **physical transport:** student devices carry batches from disconnected areas to school.

## What we can test now in software

Define a small versioned `ReachabilityProfile`, for example:

```text
profile_id
measurement_targets[]
checks = DNS | TCP/TLS | HTTPS_HEAD | optional_ping
max_frequency
privacy_class
```

and a `ReachabilityBatch`:

```text
node_pseudonym
coarse_area_id
network_class
profile_id
window_start
window_end
results[]
batch_hash
```

Then test:

- full connectivity;
- DNS failure with other reachability intact;
- one target unreachable while others work;
- captive portal simulation;
- gateway/default-route loss;
- intermittent availability;
- two nodes in the same coarse area seeing different results;
- stale batch arriving much later;
- clock uncertainty;
- missing measurements versus true failures;
- summary classification changing when new evidence arrives;
- deduplication of the same batch through several relays.

Useful metrics include observation-to-collector delay, number of independent vantage points, fraction of windows with evidence, disagreement rate between vantage points, bytes per summary, and agreement between compact classifications and full logs.

A key semantic rule is:

> “no measurement” is not the same as “Internet down”, and “one target failed” is not automatically a total outage.

## What requires real hardware

A first field experiment needs:

- 4–8 PollicinoNet nodes at controlled school/public checkpoints;
- Wi-Fi or mobile Internet on some nodes;
- a small fixed measurement profile;
- student relays that carry summaries when direct IP upload is disabled;
- a school collector.

Deliberately create benign failures in a lab first: disable DNS, disconnect WAN, block one test target, or switch between two uplinks. Only afterward observe natural connectivity changes in the field.

Any claims about outage frequency, partial reachability or geographic patterns require enough real repeated measurements to support them.

## Messina teaching scenario

Use coarse zones such as school/Messina, Villafranca, Rometta/Venetico and Spadafora rather than home addresses. Nodes periodically run the same minimal profile when connected to an authorized network. A student relay later delivers summaries to school over LoRa even if one zone temporarily lacked Internet.

A particularly useful experiment is to compare three independent states for every node/window:

```text
PollicinoNet reachable?
Internet reachable?
Internet partially reachable?
```

This creates a real dataset for deciding when UC-088 Internet fetch gateways are useful.

## Privacy / security

- never collect browsing history, SSIDs, BSSIDs or unrelated local traffic;
- use fixed allow-listed measurement targets only;
- record coarse network class rather than personally identifying ISP/account details unless explicitly needed for a controlled study;
- avoid precise home coordinates;
- cap frequency and bandwidth;
- sign/hash batches so relays cannot silently rewrite results;
- treat target blocking/firewall behavior as measurement evidence, not as authorization to bypass policy;
- do not infer a household’s availability or presence from measurement timing;
- publish only aggregated results when reporting class/territory findings.

## Difficulty

**Medium.** Individual checks are simple. The hard part is measurement semantics: distinguishing total outage, partial reachability, DNS/local failures, missing data and stale observations without overclaiming.

## Why this is distinct from nearby use cases

- **UC-008:** observes PollicinoNet contact opportunities and relay structure.
- **UC-063:** observes the RF/interference environment around the LoRa experiments.
- **UC-088:** uses an Internet gateway to fulfill a bounded remote fetch.
- **UC-092:** measures **Internet/backhaul reachability itself** from many intermittent vantage points and ferries the evidence over PollicinoNet.

## Research / implementation signal

RIPE Atlas already demonstrates the value of distributed vantage points using measurements such as ping, traceroute, DNS, NTP, TLS and HTTP. A 2026 study on partial reachability argues that Internet connectivity is not simply binary: persistent “peninsulas” and “islands” can produce partial views that ordinary outage logic may miss. That makes `healthy / partial / unknown / offline` a better experimental model than a single boolean.

References:

- https://www.ripe.net/analyse/internet-measurements/ripe-atlas/how-ripe-atlas-works/
- https://doi.org/10.4230/OASIcs.NINeS.2026.4
- https://arxiv.org/abs/2601.12196
