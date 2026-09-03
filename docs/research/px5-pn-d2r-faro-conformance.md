# PX5 PN-D2R FARO conformance

FARO PX4 final `44af3e4f0fbdd4f3373a9d464f54892481f0d891`
was loaded read-only. Its exact
`FAROPollicinoDiscoverySource` attaches to the persistent subclass without any
FARO code copied into Pollicino.

Twelve focused cases pass: reference restart/reattach; A-to-B durable selected
pull and B restart; no knowledge/trust/Recommendation mutation; PX1 exact
fetch; no auto-import plus explicit import; identical catalog/different local
trust; compatible variant `REFERENCE_VARIANT_CONFLICT`; incompatible immutable
`REFERENCE_CONFLICT`; malformed opaque bytes persist then fail FARO decode;
catalog/reference/exact retrieval pass with invalid FARO signature still
failing; three holders confer no science; exact PX4 commit verification.

The persisted bytes contain only the generic PX3 key/value state and local
generation envelope. `EvidenceGrade`, `RegistryQuery`, publisher trust,
MachineProfile, `LocalKnowledgeStore`, `LocalTrustStore` and Recommendation do
not enter persistence. Pollicino remains a discovery source rather than a full
FARO registry backend.
