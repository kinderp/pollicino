# UC-213 — NFC/NDEF tap-to-carry bearer

Problem: a small signed manifest needs to cross a disconnected site without an available radio link or QR display.

Actors: two authorized school workstations, NFC phones or readers, an untrusted NFC tag, a relay cache, and optionally two LoRa boards.

Why PollicinoNet: an NFC tag can physically carry a compact object reference, digest and authorization envelope. Store-carry-forward continues when the receiving workstation imports it into the local cache.

Bearers: NFC/NDEF and physical movement for the tiny envelope; LoRa for later announcement; BLE, Wi-Fi or Internet for full objects; USB as another fallback.

Software now: implement strict NDEF size and field validation, signed envelope parsing, duplicate suppression and revoked or unknown authorization outcomes. Test corrupted, replayed, cloned and truncated records.

Hardware later: two compatible readers and writable tags, then two LoRa gateways. Measure successful read/write and import, not radio coverage.

Privacy/security: never treat the tag UID as a trustworthy identity. Store no private keys or personal details on a public writable tag. Verify signatures, freshness status and exact object hash before acceptance.

Difficulty: medium. Distinct from UC-203 optical QR and UC-151 high-capacity storage. Reference: https://nfc-forum.org/build/specifications/data-exchange-format-ndef-technical-specification/ . No PHY changes or measured results.
