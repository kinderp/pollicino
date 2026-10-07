# UC-177 — Delay-Tolerant Differential-Privacy Budget and Query-Admission Courier

## Problem solved
A privacy-preserving local analytics service may allow only a bounded sequence of differentially private queries. In a partitioned network, two disconnected gateways can each believe budget is still available and accidentally authorize more queries than intended.

UC-177 studies how a **privacy-budget policy and query-admission state** can remain conservative under disconnection without centralizing raw data.

## Actors / nodes
Local data holder, query issuer, budget authority/coordinator, relay nodes, DP analytics worker and auditor.

## Why PollicinoNet fits
PollicinoNet can move the query to the data and return only an approved aggregate. The private dataset stays local. Compact control state can carry dataset/policy epoch, query ID, mechanism class, reserved/consumed budget token, expiry and result status. The experiment focuses on avoiding conflicting offline budget admission, not on inventing a new DP mechanism.

## Bearers
- LoRa: query descriptor, budget token/reservation, epoch and admission/result status.
- BLE/Wi-Fi/LAN: larger query specification or aggregate result where needed.
- Internet: optional coordination/audit when available.
- Physical transport: controlled audit packs; raw personal data is not required for the initial experiment.

## Software test now
Use a synthetic dataset and a mature DP library. Simulate two or more disconnected query gateways and test concurrent budget reservations, duplicate queries, expired reservations, partition/rejoin, stale policy epoch, cancellation and retry after a lost result.

Compare naive local counters, a single online-authority baseline and a conservative offline reservation/token approach. Measure admitted/rejected queries, post-merge conflicts, accounted privacy loss under the chosen model and communication overhead.

## Real hardware
Use 4–6 boards plus 3 local analytics hosts with only synthetic/public data. Boards carry compact admission/query state; compute happens on the hosts. Real hardware validates delayed coordination and duplicate delivery, not the mathematical DP guarantee itself.

## Messina / provincial teaching scenario
Several school/public nodes hold separate synthetic environmental or classroom-demo datasets. A bounded aggregate query can travel through student relays to the node that holds the data, while raw records never need to cross LoRa or leave that host.

## Privacy / security
Use established DP implementations and an explicitly documented privacy model. Epsilon/delta, adjacency definition, composition/accounting and mechanism parameters are part of the policy. Budget state must be authenticated and versioned. Never claim privacy merely because raw data stayed local. Initial experiments should use synthetic/public data only. A partition that cannot prove safe remaining budget should defer or reject the query.

## Difficulty
**High.**

## Distinct from existing cases
UC-035 carries sketches/aggregates; UC-057 moves approved analysis toward local data; UC-094 moves historical sensor queries to archives; UC-137 limits relay traffic budgets. UC-177 focuses specifically on **privacy-loss/query-budget admission and reconciliation across disconnected analytics authorities**.

## Standards/guidance signal
NIST SP 800-226 provides guidance for evaluating differential-privacy guarantees and highlights deployment pitfalls that can invalidate informal privacy claims. UC-177 therefore treats privacy accounting as an explicit experiment contract rather than a checkbox.

## Validation boundary
The network experiment can validate budget-state convergence and conservative admission logic. It does not independently prove the mathematical correctness of the chosen DP library or privacy model.