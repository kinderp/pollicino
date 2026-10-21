# Bundle priority and contact scheduling

PollicinoNet relays may hold many bundles at the same time, while an intermittent contact can be short. The relay therefore needs a deterministic answer to a simple question:

> If I cannot send everything, what should I send first?

## Current local priority classes

The first scheduling policy intentionally uses four simple local classes:

1. `EMERGENCY`
2. `HIGH`
3. `NORMAL`
4. `BULK`

Priority is currently local relay policy. It is **not** encoded into PNB1 and it is not part of the immutable bundle identity. This lets us compare policies without changing the frozen bundle wire contract. A future authenticated/authoritative priority field, if needed, should be designed separately.

## Ordering inside one contact

Candidates are ordered deterministically by:

1. higher local priority;
2. less time remaining before bundle TTL expiry;
3. when enabled, a bundle the source can finish at the target;
4. fewer remaining source bytes;
5. stable bundle ID as the final tie-breaker.

Expired bundles and bundles for which the source has no custody are skipped before any scheduling traffic is generated.

## Logical contact budget

`ContactSchedulingPolicy.max_source_bytes` is a **logical authoritative-content budget**. It limits source chunk bytes selected during the encounter.

It is deliberately not called a LoRa contact capacity. For example:

```text
max_source_bytes = 512
```

means:

> The scheduler may choose at most 512 bytes of authoritative chunk content in this experiment.

It does **not** mean:

> A real LoRa contact can carry 512 bytes before disappearing.

Control frames, PNF1 framing, ACKs and retries remain separately visible in the resulting wire accounting. The scheduler never exceeds the logical source-byte budget just to fit one more chunk.

## Example

Suppose a relay has:

```text
emergency message       64 B   EMERGENCY
sensor report          128 B   HIGH
ordinary document      512 B   NORMAL
software update       4096 B   BULK
```

and the logical encounter budget is 192 source bytes.

The current policy tries the emergency bundle first. It then considers HIGH-priority work before NORMAL/BULK work. If only 32 bytes remain but the next transferable chunk is 64 bytes, the relay leaves the 32 bytes unused rather than silently exceeding the budget.

## Why completion preference exists

Within the same priority and comparable urgency, completing a small object can be more useful than sending one fragment of a much larger object. Completion preference is therefore an explicit policy switch rather than a hidden rule.

This is especially useful for future student-network experiments: a short encounter could finish a small alert or sensor record instead of spending the whole opportunity on the first chunk of a large file.

## Current boundary

The current scheduler is deterministic protocol/software work. No physical board is required to validate:

- priority ordering;
- TTL-aware ordering;
- completion preference;
- logical byte budgets;
- skipping expired/no-custody bundles;
- reproducibility and TRC accounting.

Physical HW-006 evidence becomes necessary when we want to derive the logical budget from a statement such as:

> At this distance/NLOS condition and PHY, a typical usable contact window carries approximately N verified bytes/chunks.

That requires measured contact duration, loss/retry behaviour and the actual PNB1/PNC1/PCM1/PNA1/data frame sizes. Until then, scheduling-policy comparisons must label contact budgets as synthetic inputs.

## Next scheduling work

The current ordering is intentionally simple. Useful next experiments include:

- starvation protection/aging for low-priority bundles;
- explicit deadlines distinct from protocol TTL;
- per-bearer scheduling policies;
- energy-aware scheduling;
- value-per-byte / completion-per-byte policies;
- multi-relay coordination;
- synthetic mobility/contact-window traces;
- measured contact-capacity adapters after HW-006.
