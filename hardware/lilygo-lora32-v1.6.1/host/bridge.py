#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
from typing import Any

from pollicino.net import DiscoveryDescriptor, FragmentFrame, fragment_payload

MAX_RADIO_PAYLOAD = 240


def tx_command(payload: bytes) -> bytes:
    if not isinstance(payload, bytes):
        raise TypeError("payload must be bytes")
    if not 1 <= len(payload) <= MAX_RADIO_PAYLOAD:
        raise ValueError(f"payload must contain 1..{MAX_RADIO_PAYLOAD} bytes")
    return b"TX " + payload.hex().encode("ascii") + b"\n"


def parse_rx_line(line: str) -> dict[str, Any] | None:
    if not line.startswith("RX "):
        return None
    parts = line.split(" ", 4)
    if len(parts) != 5:
        raise ValueError("malformed RX line")
    _, length_text, rssi_text, snr_text, payload_hex = parts
    payload = bytes.fromhex(payload_hex)
    expected = int(length_text)
    if len(payload) != expected:
        raise ValueError(f"RX length mismatch: expected {expected}, got {len(payload)}")
    return {
        "payload": payload,
        "length": expected,
        "rssi_dbm": float(rssi_text),
        "snr_db": float(snr_text),
    }


def demo_descriptor() -> DiscoveryDescriptor:
    return DiscoveryDescriptor(
        object_class=1,
        rendezvous_key=bytes.fromhex("102030405060708090a0b0c0"),
        ttl_seconds=300,
        nonce=1,
        capability_mask=0x0001,
        authenticator=b"hw001",
    )


def _serial_module():
    try:
        import serial  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "pyserial is required for hardware access. Install it with: "
            "python -m pip install pyserial"
        ) from exc
    return serial


def open_port(name: str):
    serial = _serial_module()
    port = serial.Serial(name, baudrate=115200, timeout=0.2, write_timeout=2)
    # Opening the ESP32 serial port can reset the board.
    time.sleep(1.5)
    port.reset_input_buffer()
    return port


def write_command(port, command: bytes) -> None:
    port.write(command)
    port.flush()


def read_line(port, deadline: float) -> str | None:
    while time.monotonic() < deadline:
        raw = port.readline()
        if not raw:
            continue
        return raw.decode("utf-8", errors="replace").strip()
    return None


def wait_prefix(port, prefix: str, timeout: float) -> str:
    deadline = time.monotonic() + timeout
    seen: list[str] = []
    while time.monotonic() < deadline:
        line = read_line(port, deadline)
        if line is None:
            break
        seen.append(line)
        if line.startswith(prefix):
            return line
    raise TimeoutError(f"did not receive {prefix!r}; seen={seen[-8:]}")


def send_payload(port, payload: bytes, timeout: float = 5.0) -> str:
    write_command(port, tx_command(payload))
    return wait_prefix(port, "TXOK ", timeout)


def receive_payload(port, timeout: float = 10.0) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    seen: list[str] = []
    while time.monotonic() < deadline:
        line = read_line(port, deadline)
        if line is None:
            break
        seen.append(line)
        parsed = parse_rx_line(line)
        if parsed is not None:
            return parsed
    raise TimeoutError(f"did not receive an RX frame; seen={seen[-8:]}")


def run_loopback(tx_port_name: str, rx_port_name: str, timeout: float) -> dict[str, Any]:
    descriptor = demo_descriptor()
    pnd1 = descriptor.encode()
    pnf1_frames = fragment_payload(pnd1, transfer_id=0x1001, max_frame_bytes=64)
    if len(pnf1_frames) != 1:
        raise AssertionError("HW-001 demo PND1 should fit in one frozen 64-byte PNF1 frame")
    pnf1 = pnf1_frames[0].encode()

    tx_port = open_port(tx_port_name)
    rx_port = open_port(rx_port_name)
    try:
        write_command(tx_port, b"INFO\n")
        tx_info = wait_prefix(tx_port, "INFO ", timeout)
        write_command(rx_port, b"INFO\n")
        rx_info = wait_prefix(rx_port, "INFO ", timeout)

        send_payload(tx_port, pnd1, timeout)
        first = receive_payload(rx_port, timeout)
        if first["payload"] != pnd1:
            raise RuntimeError("PND1 radio payload changed in transit")
        decoded_pnd1 = DiscoveryDescriptor.decode(first["payload"])
        if decoded_pnd1 != descriptor:
            raise RuntimeError("received PND1 does not decode to the source descriptor")

        send_payload(tx_port, pnf1, timeout)
        second = receive_payload(rx_port, timeout)
        if second["payload"] != pnf1:
            raise RuntimeError("PNF1 radio payload changed in transit")
        decoded_frame = FragmentFrame.decode(second["payload"])
        decoded_nested = DiscoveryDescriptor.decode(decoded_frame.payload)
        if decoded_nested != descriptor:
            raise RuntimeError("received PNF1 payload does not contain the source descriptor")

        return {
            "success": True,
            "tx_info": tx_info,
            "rx_info": rx_info,
            "pnd1": {
                "bytes": len(pnd1),
                "rssi_dbm": first["rssi_dbm"],
                "snr_db": first["snr_db"],
                "exact": True,
            },
            "pnf1": {
                "bytes": len(pnf1),
                "rssi_dbm": second["rssi_dbm"],
                "snr_db": second["snr_db"],
                "exact": True,
            },
        }
    finally:
        tx_port.close()
        rx_port.close()


def selftest() -> dict[str, Any]:
    descriptor = demo_descriptor()
    payload = descriptor.encode()
    command = tx_command(payload)
    if not command.startswith(b"TX ") or not command.endswith(b"\n"):
        raise AssertionError("TX command framing failed")

    synthetic = f"RX {len(payload)} -71.5 8.25 {payload.hex()}"
    parsed = parse_rx_line(synthetic)
    assert parsed is not None
    if parsed["payload"] != payload:
        raise AssertionError("RX parser changed payload")
    if DiscoveryDescriptor.decode(parsed["payload"]) != descriptor:
        raise AssertionError("PND1 selftest round-trip failed")

    pnf1 = fragment_payload(payload, transfer_id=7, max_frame_bytes=64)
    if len(pnf1) != 1 or FragmentFrame.decode(pnf1[0].encode()).payload != payload:
        raise AssertionError("PNF1 selftest failed")

    return {
        "success": True,
        "pnd1_bytes": len(payload),
        "pnf1_bytes": len(pnf1[0].encode()),
        "serial_command_bytes": len(command),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="PollicinoNet HW-001 LILYGO serial/LoRa bridge")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("selftest")

    loopback = sub.add_parser("loopback", help="run PND1 and PNF1 exact tests across two connected boards")
    loopback.add_argument("--tx-port", required=True)
    loopback.add_argument("--rx-port", required=True)
    loopback.add_argument("--timeout", type=float, default=10.0)

    send_hex = sub.add_parser("send-hex")
    send_hex.add_argument("--port", required=True)
    send_hex.add_argument("hex")

    send_file = sub.add_parser("send-file")
    send_file.add_argument("--port", required=True)
    send_file.add_argument("path", type=Path)

    listen = sub.add_parser("listen")
    listen.add_argument("--port", required=True)

    args = parser.parse_args()

    if args.command == "selftest":
        print(json.dumps(selftest(), indent=2, sort_keys=True))
        return 0

    if args.command == "loopback":
        print(json.dumps(run_loopback(args.tx_port, args.rx_port, args.timeout), indent=2, sort_keys=True))
        return 0

    if args.command == "send-hex":
        payload = bytes.fromhex(args.hex)
        port = open_port(args.port)
        try:
            print(send_payload(port, payload))
        finally:
            port.close()
        return 0

    if args.command == "send-file":
        payload = args.path.read_bytes()
        port = open_port(args.port)
        try:
            print(send_payload(port, payload))
        finally:
            port.close()
        return 0

    if args.command == "listen":
        port = open_port(args.port)
        try:
            while True:
                event = receive_payload(port, timeout=3600.0)
                printable = dict(event)
                printable["payload_hex"] = printable.pop("payload").hex()
                print(json.dumps(printable, sort_keys=True), flush=True)
        except KeyboardInterrupt:
            return 0
        finally:
            port.close()

    return 2


if __name__ == "__main__":
    sys.exit(main())
