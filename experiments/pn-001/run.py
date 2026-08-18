from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import zlib

from pollicino.net import DiscoveryDescriptor


CASES = {
    "file-coordinate": DiscoveryDescriptor(
        object_class=1,
        rendezvous_key=bytes.fromhex("0123456789abcdef"),
        ttl_seconds=3600,
        nonce=1,
        capability_mask=0b0000_0000_0000_0011,
        authenticator=bytes.fromhex("a1a2a3a4a5a6a7a8"),
    ),
    "message-coordinate": DiscoveryDescriptor(
        object_class=2,
        rendezvous_key=b"topic-7f3a2c",
        ttl_seconds=600,
        nonce=2,
        capability_mask=0b0000_0000_0000_0101,
        metadata=b"v1\x00\x11\x00",
        authenticator=bytes.fromhex("b1b2b3b4b5b6b7b8"),
    ),
    "service-coordinate": DiscoveryDescriptor(
        object_class=3,
        rendezvous_key=bytes.fromhex("00112233445566778899aabbccddeeff"),
        ttl_seconds=120,
        nonce=3,
        capability_mask=0b0000_0000_0000_1111,
        flags=1,
        hop_limit=2,
        metadata=b"service-resource",
        authenticator=bytes.fromhex("00112233445566778899aabbccddeeff"),
    ),
}


def json_ready(descriptor: DiscoveryDescriptor) -> dict[str, object]:
    result = asdict(descriptor)
    for field in ("rendezvous_key", "metadata", "authenticator"):
        result[field] = result[field].hex()
    return result


def canonical_json_bytes(descriptor: DiscoveryDescriptor) -> bytes:
    return json.dumps(
        json_ready(descriptor),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def main() -> None:
    rows: list[dict[str, object]] = []
    for name, descriptor in CASES.items():
        pnd1 = descriptor.encode()
        assert DiscoveryDescriptor.decode(pnd1) == descriptor

        json_payload = canonical_json_bytes(descriptor)
        zlib_payload = zlib.compress(json_payload, level=9)

        rows.append(
            {
                "case": name,
                "pnd1_bytes": len(pnd1),
                "canonical_json_bytes": len(json_payload),
                "zlib9_json_bytes": len(zlib_payload),
                "pnd1_vs_json_reduction_fraction": 1.0 - len(pnd1) / len(json_payload),
                "pnd1_vs_zlib9_reduction_fraction": 1.0 - len(pnd1) / len(zlib_payload),
                "round_trip": True,
            }
        )

    result = {
        "experiment": "PN-001",
        "protocol": "PND1",
        "standalone_core": True,
        "external_runtime_dependencies": [],
        "application_dependencies": [],
        "cases": rows,
        "mean_pnd1_bytes": sum(row["pnd1_bytes"] for row in rows) / len(rows),
        "mean_json_bytes": sum(row["canonical_json_bytes"] for row in rows) / len(rows),
        "mean_zlib9_bytes": sum(row["zlib9_json_bytes"] for row in rows) / len(rows),
    }

    output = Path(__file__).with_name("results.json")
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
