# PX8-PN-D4 budget and bounds preregistration

D4 will accept an explicit item and encoded-byte budget. Both are hard positive
ceilings; there is no unlimited sentinel.

The item ceiling reuses D2/D3 `MAX_EXCHANGE_ITEMS = 100`.

The byte ceiling is derived from 100 times the largest complete lawful existing
record encoding:

| Record | Maximum encoded bytes |
|---|---:|
| query | 6-byte entry header + 128-byte ID + 4096-byte payload = 4230 |
| result | 6-byte entry header + two 128-byte IDs + 100 × (2-byte length + 256-byte key) = 26062 |
| reference | 6-byte entry header + 256-byte key + 4096-byte value = 4358 |

Therefore `MAX_CONTACT_BYTES = 100 * 26062 = 2,606,200`.

Accounting is `LOCAL_PROTOCOL_ACCOUNTING_ONLY`: complete-record canonical
entry sizes, not measured bandwidth, frames, latency, or bearer overhead.

Before applying a missing record, D4 checks that both remaining item and byte
budgets fit it. If either does not, the contact returns `BUDGET_EXHAUSTED` and
all earlier commits remain durable. Identifier reconciliation uses the existing
100-identifier page bound. Already-known identifiers may be scanned and
reported but do not consume transfer budget and are never counted as missing
record retransfers.

Observed: the 105-query run used exactly 100 items in Contact 1 and 5 in
Contact 2 after restart. A byte budget one byte below the next canonical entry
size applied zero bytes of that record. Both tests passed.
