# HW-006 — untethered responder checkpoints

HW-006 extends the validated HW-005/HW-003 path for physical distance and NLOS checkpoints where the responder cannot remain connected to the host PC.

## Roles

- Local node: HW-005 or HW-006, connected to the host over USB serial.
- Remote node: HW-006, powered independently (for example by a USB power bank) and not serially observed during the checkpoint.

The frozen H2 PING/PONG wire format and PHY remain unchanged. A valid PONG still carries the RSSI/SNR observed by the remote responder, while the local initiator measures RSSI/SNR for the return PONG.

## Remote boot contract

HW-006 starts the SX1276 directly at 2 dBm on PA_BOOST and immediately enters the event-driven receive path. INFO advertises:

- `lab=hw-006`
- `power_dbm=2`
- `boot_power_dbm=2`
- `power_path=pa_boost`
- `untethered_responder=1`
- `untethered_profile_version=1`

The responder therefore does not require a host serial command after power-up.

## Preflight

Before disconnecting the remote node, run the host preflight with both serial ports present. It verifies the local power-capable firmware, the HW-006 remote boot contract, fixed-PHY equality and matching time-on-air for the chosen frame size.

## Checkpoint measurement

During a physical checkpoint only the local serial port is opened. The runner sets the local transmitter to 2 dBm, applies explicit TX-airtime budgeting and occupancy pacing, and records MRESULT for each transaction.

For a successful transaction the result contains both:

- `remote_rssi_dbm` / `remote_snr_db`: remote observation of the PING, encoded in the valid PONG;
- `local_rssi_dbm` / `local_snr_db`: local observation of the returning PONG.

## Critical observability boundary

The remote serial stream and its H2RESP scheduler trace are intentionally unavailable during an untethered checkpoint. Therefore a timeout is ambiguous. It cannot by itself distinguish remote CRC/decode failure, missed return PONG, remote reset or power-bank shutdown, or another RF failure.

Remote RSSI/SNR are also unavailable for a transaction that does not return a valid PONG. Do not impute receiver values to failed attempts.

## Suggested progression

Start with a same-room checkpoint to validate one-port operation, then increase attenuation through reproducible geometry: greater separation, one wall, multiple walls, another floor, and only then outdoor distance. Keep antenna orientation and node placement documented. Use the same 42-byte frame and 2 dBm power until a transition region begins to appear.

Success fractions are descriptive for each named checkpoint and are not deployment packet-loss probabilities. No electrical energy measurement is made by this experiment.
