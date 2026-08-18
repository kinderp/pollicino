# Standalone contract

Pollicino and PollicinoNet are standalone projects. Application integrations are optional consumers, never prerequisites.

## Invariants

1. `pollicino.compression` must remain usable without PollicinoNet.
2. `pollicino.net` must remain usable without DNA, Travel DNA, LoRa hardware, Internet services, IPFS, BitTorrent or a learned checkpoint.
3. Core wire types contain only generic fields. Application meaning belongs to adapters.
4. Physical-radio details belong to transport adapters, not content descriptors.
5. An integration may import Pollicino; Pollicino core must not import the integration.
6. DNA is the first concrete PollicinoNet application fixture, not the canonical data model of PollicinoNet.
7. EXACT, DISCOVERY and SEMANTIC contracts remain meaningful for arbitrary applications and arbitrary byte content.

Dependency direction:

```text
optional application (DNA, future app, CLI, service)
                    |
                    v
              PollicinoNet
                    |
          +---------+---------+
          |                   |
          v                   v
   Pollicino Codec       transport ports
                              |
                              v
                  LoRa / BLE / Wi-Fi / Internet
```

Forbidden direction:

```text
Pollicino core ---> DNA domain model
Pollicino core ---> LoRa SDK
Pollicino core ---> hosted resolver
```

## First proof: PN-001

PN-001 introduces `PND1`, a deterministic discovery descriptor whose application-specific material is opaque bytes. Generic file, message and service fixtures are tested before any DNA mapping is introduced.

A DNA adapter can later encode a `DNATrace` into PND1 fields and metadata, but removing that adapter must leave all PollicinoNet core tests and standalone examples functional.
