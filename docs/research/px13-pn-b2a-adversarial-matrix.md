# PX13-PN-B2A adversarial matrix

- zero difference terminates with one compact summary;
- compact decode failure alone advances the finite ladder;
- summary/request/reveal/record loss returns partial state and never escalates;
- duplicate and delayed delivery remain safe through native idempotence;
- corrupt compact control returns an error and never triggers exact by guessing;
- disconnect returns control finitely;
- sender uncertainty is resolved by fresh durable-state reconciliation;
- a 105-record persistent reopen resumes with a fresh selector;
- a 100-record workload with only eight attempts per contact chooses exact
  immediately and converges in 33 contacts rather than repeating probes;
- differences 1,001, 2,000, 5,000, and 10,000 fall back finitely;
- 1,000 records converge in 11 contacts with no persistent escalation state;
- query, result, and explicitly selected reference paths remain generic;
- a semantic-blind mule carries query and result state.

Loss is not treated as capacity evidence. The policy escalates only after a
delivered compact decode reports `FALLBACK_REQUIRED`.
