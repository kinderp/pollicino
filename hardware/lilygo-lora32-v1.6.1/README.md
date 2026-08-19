# HW-001 — LILYGO LoRa32 V1.6.1 transparent PollicinoNet bridge

HW-001 is the first real-radio lab for PollicinoNet. It is intentionally an **optional hardware adapter**: `pollicino.net` remains transport-agnostic and does not import Arduino, RadioLib, PlatformIO, LoRa or this firmware.

## Target hardware

Expected board for Amazon ASIN `B09FXHSS6P`:

- LILYGO / TTGO LoRa32 V1.6.1 family;
- ESP32-PICO-D4;
- SX1276 radio;
- 868 MHz variant;
- 4 MB flash;
- no PSRAM;
- SSD1306 OLED and microSD slot present on the board.

**Before flashing, visually verify the board marking and radio variant.** Marketplace listings can be revised. HW-001 is compiled specifically for the SX1276 V1.6.1 pinout.

### Frozen pinout

| Function | GPIO |
|---|---:|
| SX1276 SCK | 5 |
| SX1276 MISO | 19 |
| SX1276 MOSI | 27 |
| SX1276 CS | 18 |
| SX1276 DIO0 | 26 |
| SX1276 RESET | 23 |
| SX1276 DIO1 | 33 |
| User LED | 25 |
| OLED SDA/SCL | 21 / 22 |
| microSD CS/MOSI/MISO/SCK | 13 / 15 / 2 / 14 |

Vendor reference:
`https://github.com/Xinyuan-LilyGO/LilyGo-LoRa-Series/blob/master/docs/en/t3_v161_sx1276/t3_v161_sx1276_hw.md`

The firmware initialization mirrors LILYGO's own SX1276 LoRa32 example:
`https://github.com/Xinyuan-LilyGO/LilyGo-LoRa-Series/blob/master/examples/LoRa/T3_LoRa32/SX1276_PingPong/SX1276_PingPong.ino`

## Safety first

**Connect the correct 868 MHz antenna before any transmission.** LILYGO explicitly warns that transmitting without the antenna can damage the RF stage.

For the first bench test:

- keep the boards a few metres apart rather than touching antennas together;
- use the frozen low-power 10 dBm profile;
- send only short test packets;
- do not run a continuous transmitter;
- review current Italian/European SRD rules before longer outdoor or unattended tests.

The current CEPT SRD recommendation is ERC/REC 70-03 (5 June 2026). The RF constants in HW-001 are a conservative **lab profile**, not a declaration of regulatory compliance for every deployment.

## Frozen RF profile

The firmware explicitly configures:

- carrier: `868.100 MHz`;
- bandwidth: `125 kHz`;
- spreading factor: `SF7`;
- coding rate: `4/5`;
- sync word: `0x12` (private LoRa, not LoRaWAN's reserved `0x34`);
- output power: `10 dBm`;
- preamble: `8` symbols;
- maximum host TX payload: `240` bytes.

These values belong to this adapter only. PND1, PNF1, PNM1 and the rest of PollicinoNet do not know or require them.

## What the firmware does

The ESP32 is a transparent byte bridge:

```text
PC A
  |
  | USB serial: TX <hex>
  v
LILYGO A / SX1276
  |
  | raw LoRa packet
  v
LILYGO B / SX1276
  |
  | USB serial: RX <len> <RSSI> <SNR> <hex>
  v
PC B
```

The radio firmware does **not** parse DNA, manifests, hashes or codecs. It carries arbitrary bytes unchanged. That means the same firmware can transport:

- standalone PND1 discovery descriptors;
- PNF1 exact-transfer frames;
- DNA-derived PND1 descriptors through the optional integration;
- future PollicinoNet payloads that fit the radio-packet budget.

### Serial commands

Host -> board:

- `PING` -> health check;
- `INFO` -> frozen board/RF configuration;
- `TX <hex>` -> transmit 1..240 bytes.

Board -> host:

- `READY hw-001`;
- `INFO ...`;
- `PONG`;
- `TXOK <bytes>` or `TXERR <RadioLib code>`;
- `RX <bytes> <rssi_dbm> <snr_db> <hex>`;
- `RXERR ...` / `ERR ...`.

USB text/hex overhead is **not radio overhead** and must never be counted as PollicinoNet TRC.

## Build

PlatformIO Core 6.1.19 is the frozen host build tool for CI. The embedded environment follows LILYGO's current reference platform and library generation:

- `espressif32@6.13.0`;
- Arduino framework;
- RadioLib `7.6.0`.

From the repository root:

```bash
python -m pip install platformio==6.1.19
pio run -d hardware/lilygo-lora32-v1.6.1
```

## Flash the two boards

Flash each board separately so the serial port is unambiguous:

```bash
pio run -d hardware/lilygo-lora32-v1.6.1 -t upload --upload-port COM5
pio run -d hardware/lilygo-lora32-v1.6.1 -t upload --upload-port COM6
```

On Linux/macOS replace `COM5`/`COM6` with the actual `/dev/...` ports.

LILYGO documents a CH9102 USB bridge for this board family; install its driver if the board does not appear as a serial port. Remove a microSD card while flashing, as the vendor hardware notes recommend.

## Host tool

Install Pollicino in editable mode plus pyserial:

```bash
python -m pip install -e . pyserial
```

Pure host/protocol self-test, no hardware needed:

```bash
python hardware/lilygo-lora32-v1.6.1/host/bridge.py selftest
```

### First physical test with both boards on one computer

After both boards are flashed and have antennas attached:

```bash
python hardware/lilygo-lora32-v1.6.1/host/bridge.py loopback \
  --tx-port COM5 \
  --rx-port COM6
```

HW-001 automatically performs two transmissions:

1. a real standalone PND1 descriptor;
2. the same PND1 wrapped in a real frozen 64-byte-budget PNF1 frame.

Success requires byte-for-byte identity plus successful PND1/PNF1 decoding. The result also records RSSI and SNR for both packets.

Example shape:

```json
{
  "success": true,
  "pnd1": {"exact": true, "rssi_dbm": -70.0, "snr_db": 8.0},
  "pnf1": {"exact": true, "rssi_dbm": -70.0, "snr_db": 8.0}
}
```

The actual RSSI/SNR values are measurements, not success thresholds.

## What HW-001 does not claim

HW-001 is only the first physical transport proof. It does not yet validate:

- maximum range;
- real packet-loss curves;
- LoRa airtime/TRC model;
- duty-cycle scheduler;
- automatic ACK/retry on the physical boards;
- P2P chunk synchronization;
- Wi-Fi/BLE handover;
- store-and-forward;
- DNA consent on-device;
- cryptographic radio authentication.

Those belong to later hardware labs. The immediate scientific question is narrower:

> Can two real SX1276 boards carry unmodified PND1 and PNF1 bytes and report physical-link RSSI/SNR while keeping PollicinoNet core independent of LoRa?
