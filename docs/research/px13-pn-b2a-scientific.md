# PX13-PN-B2A scientific report

PX13 tested whether a deployable selector can retain compact wins without
knowing peer difference size and without persisting peer history.

The preregistered two-probe cost-aware candidate `(10, 100, exact)` failed its
large-difference ceiling: at 10,000 missing records it cost 2,134,044 control
bytes, 1.2735 times PX11 exact. That failure was not hidden. The simpler
registered policy—one capacity-10 probe then exact—cost 1,763,556 bytes, 1.0524
times exact, and became the selected policy.

At 10,000/1 missing it retained 98.0% of PX12's absolute saving; at 10 missing
it retained 100%. It remained exact for every tested topology and difference.
Across the registered hindsight comparison its median regret was 1.196875 and
maximum 1.462385, below the 1.50 threshold.

Anti-thrashing follows from policy structure, not history: after one delivered
decode failure the unchanged exact path runs within the same cumulative budget.
Exact progress changes durable state, so a fresh contact starts from a smaller
missing set. When the contact is too small to reserve exact work, the compact
probe is skipped.

No oracle inputs, persistent ACK, peer policy, escalation, session, or cursor
state were introduced. No historical production module was modified.
