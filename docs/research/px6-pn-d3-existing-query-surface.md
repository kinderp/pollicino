# PX6-PN-D3 existing query surface

Audit base: Pollicino `2169489b766f84ad64920fd95cb8c9c075d879d0`; FARO read-only `44af3e4f0fbdd4f3373a9d464f54892481f0d891`.

Pollicino contained no implemented generic persistent asynchronous query/result primitive. Searches for `query`, `interest`, `want`, `result`, `request`, `response`, `search`, `discovery`, `async`, and `delayed` found use-case prose and application/experiment vocabulary, but no canonical D3 state contract to reuse.

The reusable substrate was:

| Surface | Module | PX6 use |
|---|---|---|
| bounded byte keys and opaque references | `pollicino.net.catalog` | result candidates use native catalog keys |
| exact identifier reconciliation and selected pull | `pollicino.net.catalog` | architectural pattern, not semantic query evaluation |
| dual-generation atomic snapshot | `pollicino.net.persistent_catalog` | durability guarantees extracted without changing the catalog contract |

FARO's real `RegistryQuery` is built by `faro_profiles.registry_protocol.build_registry_query`. `LocalRegistryMock.search` owns matching, pagination, registry metadata and ranking. `FAROPollicinoDiscoverySource` remains a D2 discovery source. PX6 therefore carries canonical FARO query bytes opaquely in a test adapter and invokes FARO's evaluator outside Pollicino.

No competing universal query vocabulary was found or introduced.
