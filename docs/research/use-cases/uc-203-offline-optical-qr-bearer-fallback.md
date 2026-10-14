# UC-203 — Screen-to-Camera and Printed-QR Offline Bearer Fallback

## Problem and concrete scenario
Two school islands cannot establish LoRa, BLE, Wi-Fi or Internet at a particular checkpoint, but a teacher may carry a printed QR sheet or display a signed token on a device screen. A very small payload such as an evidence receipt, manifest digest, revocation hint or message request can still move **without using the radio spectrum**. This is a supplementary bearer, not a replacement for radio or USB.

## Actors / nodes
School laptop or gateway, authorized teacher/courier carrying a screen or printed sheet, receiving camera-equipped phone/laptop, offline PollicinoNet storage and later student LoRa relays. Example: move a verified manifest from one supervised Messina school lab to a Rometta lab when no shared network is available.

## Why PollicinoNet fits and precise contract
Map an existing exact PollicinoNet application object to a small `optical_envelope` with version, object hash, expiry/policy epoch, signature and a bounded chunk count. QR is only the **bearer**; it does not imply identity, trust, freshness or successful delivery. The receiver validates the *whole reassembled object*, rejects incompatible or stale policy and emits a locally stored receipt for later carriage. A static printed QR is excellent for short signed digests; an animated sequence may be explored for larger objects but should enforce strict size and resource limits.

## Bearers
- **LoRa:** original/follow-on compact control or receipt delivery when contact is available; unchanged PHY.
- **BLE/Wi-Fi:** default rich bearer when available.
- **Internet:** optional publisher verification later.
- **Physical optical transport:** printed QR; one-device-screen-to-camera; optional animated QR for bounded objects; USB remains the better baseline for bulk.

## Software-only experiment (proposed; not run)
Use two isolated local processes and a QR encode/decode library, no network connection. Compare a single QR token with multipart frames on 1 KiB–100 KiB *synthetic* payloads. Inject missing, duplicated, reordered, corrupted and maliciously oversized frames; forged signatures and expired epochs. Metrics: exact verification success, recovery after frame loss, bytes/frame, encoded overhead, CPU and decode failures. The size range is a test input, not an achieved optical capacity.

## Physical test and measurements needed
Two laptops/phones and a printer initially; **no LoRa hardware is needed to prove optical exchange**. Then attach 4–6 LoRa boards to show a QR-imported exact object subsequently store-and-forwarded. Measure scan conditions (lighting/distance), transfer time, completion ratio and end-to-end object equality. Compare with Wi-Fi/USB where available; do not assume optical is faster.

## Privacy, security, difficulty
**Medium.** Public display/printed sheets reveal their content to bystanders: transmit only public signed data or authenticated ciphertext, not access secrets in plaintext. Reject replay, decompression bombs and unbounded multipart sequences; require user confirmation before import. Handle lost paper as an exposed medium and minimize metadata.

## Distinction from existing catalog
UC-151 treats removable storage as a bulk bearer, UC-005 uses mobile gateways, UC-167 explores one-way delivery, and UC-190 bridges heterogeneous networks. **UC-203 adds a deliberately simple optical control bearer**, with its own framing, human approval and end-to-end exact verification.

## Reference / guardrails
Optical file transfer implementations exist (e.g. https://github.com/qr-transfer/qrf ); no compatibility or throughput is assumed. Application/bearer work only. The frozen LoRa PHY and MAC remain untouched.