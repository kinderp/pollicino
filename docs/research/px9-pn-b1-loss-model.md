# PX9-PN-B1 deterministic loss model

`ScriptedInMemoryLink` consumes an explicit action sequence independently in
each direction. Default actions apply after a sequence is exhausted, making
permanent and repeated loss finite and reproducible at the contact-call level.

| Action | Receiver presentation | Sender observation | Contact behavior |
|---|---:|---:|---|
| `DELIVER` | one exact complete unit | yes | continue |
| `DROP` | none | yes | continue, partial if still missing |
| `DUPLICATE` | two identical complete units | yes | native idempotence |
| `DISCONNECT` | none | no | stop immediately |
| `DELAY_DELIVER` | one after a bounded temporary hold | yes | continue |
| `DELIVER_UNCERTAIN` | one exact complete unit | no | commit, then stop |

There is no random scheduler, wall-clock timeout, fragmentation, corrupted
partial value, automatic retransmission, or ACK. “Delay” is a deterministic
logical impairment, not a latency or reordering model.

The critical ambiguity is intentionally asymmetric. Under
`DELIVER_UNCERTAIN`, the sender-side report cannot affirm observation, but the
receiver's state is exact and durable. A fresh contact reconciles that state
and performs zero new attempts for the committed record. Under `DROP`, the
receiver remains unchanged and a later contact still identifies the record as
missing.

Loss is charged before the attempt. Therefore an always-dropping link returns
control when either the D4 budget or B1 attempt/trace budget is exhausted. It
never spins until success and never reports convergence while work is missing.
