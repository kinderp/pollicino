# PX6-PN-D3 FARO conformance

FARO was read-only at exact closure `44af3e4f0fbdd4f3373a9d464f54892481f0d891`. The production FARO code was not changed.

The PX6 test adapter serializes a real `faro.registry-query.v0` with FARO's canonical JSON function. Pollicino stores and exchanges those bytes without parsing them. After restart, the harness reattaches a FARO-side evaluator which decodes the query and calls the real `LocalRegistryMock.search`. Returned FARO package IDs use PX4's `package_id_to_logical_key` mapping and become generic result keys.

Positive and zero-match queries pass. A requester accepts a result key before its catalog contains the corresponding reference. Only explicit selection invokes D2/PX5 pull; only a later explicit PX1 operation retrieves exact package bytes; only explicit FARO import mutates `LocalKnowledgeStore`.

The conformance slice also preserves:

- no knowledge, trust or Recommendation mutation during query/result/discovery;
- local UNKNOWN versus TRUSTED interpretation for the same result/reference;
- invalid signature as a FARO failure after query, result, catalog and exact retrieval success;
- PX4 `REFERENCE_VARIANT_CONFLICT` for compatible-but-byte-different references;
- no popularity or multi-responder scientific escalation.

Classification: `FARO_D3_CONFORMANCE_READY_TEST_ADAPTER_ONLY`. A production adapter belongs in `RG3-PX7`; Pollicino remains application-neutral.
