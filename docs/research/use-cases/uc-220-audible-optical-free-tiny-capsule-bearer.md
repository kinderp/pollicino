# UC-220 — Audible Tiny-Capsule Offline Bearer

## Problem
Two devices with speakers/microphones but no permitted network, camera or NFC reader still need to exchange a very small signed PollicinoNet object. A supervised audible transfer can act as a **human-initiated transport adapter**. It is not long-range networking or an emergency-alert service.

## Actors and Messina classroom
Two school-owned phones/laptops, two student testers, a teacher, and optional 2–4 relay boards and a gateway. Use an authorized quiet classroom, not unattended listening. One gateway acquires a token via sound and later passes its exact digest over LoRa.

## Why PollicinoNet and bearer choice
Envelopes, signatures, expiry and deduplication are independent of the delivery medium. **Audio:** short audible tones for tiny framed objects. **LoRa:** compact control when a next hop becomes available. **BLE/Wi-Fi:** later fetch of referenced content. **Internet:** optional. **Physical:** a person carries the audio-capable device; USB for larger objects. This does not change the LoRa PHY/MAC.

## Software now
Encode/decode a 20–100-byte synthetic token through WAV files using a test sound codec. Inject ambient noise, dropouts, clipping, replay and overlapping messages. First distinguish successful audio demodulation from authorized PollicinoNet ingestion: checksum, signature, expiry, message length and nonce must all be checked. A compact authenticated reference may be used where the complete signature is too large. No automatic actuation.

**Acceptance gate:** valid token round-trips in loopback; altered, expired or duplicated tokens are rejected at the application layer.

## Hardware later
Two supervised devices with audible volume limits and short transmissions; vary benign classroom noise while logging measured decode success, repetitions and duration. Optional follow-up with 2–4 LoRa boards for acoustic import followed by relay forwarding. Do not invent acoustic throughput or reliability.

## Privacy, security, accessibility and distinctness
Audible data can be overheard or recorded. Use nonpersonal tokens, encrypt private data, require a visible start gesture, never listen continuously, avoid ultrasound modes, and respect classroom noise and access needs. **Difficulty: medium-high.** UC-203 uses QR and UC-213 NFC; this separately validates speaker-to-mic transport.

Research reference: https://github.com/ggerganov/ggwave
