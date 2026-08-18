from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path

from pollicino.net import DiscoveryDescriptor, ScarceLinkProfile, transmit_exact


def descriptor_bundle() -> bytes:
    descriptors = (
        DiscoveryDescriptor(
            object_class=1,
            rendezvous_key=bytes.fromhex("0123456789abcdef"),
            ttl_seconds=3600,
            nonce=1,
            capability_mask=0b11,
            authenticator=bytes.fromhex("a1a2a3a4a5a6a7a8"),
        ),
        DiscoveryDescriptor(
            object_class=2,
            rendezvous_key=b"topic-7f3a2c",
            ttl_seconds=600,
            nonce=2,
            capability_mask=0b101,
            metadata=b"v1\x00\x11\x00",
            authenticator=bytes.fromhex("b1b2b3b4b5b6b7b8"),
        ),
        DiscoveryDescriptor(
            object_class=3,
            rendezvous_key=bytes.fromhex("00112233445566778899aabbccddeeff"),
            ttl_seconds=120,
            nonce=3,
            capability_mask=0b1111,
            flags=1,
            hop_limit=2,
            metadata=b"service-resource",
            authenticator=bytes.fromhex("00112233445566778899aabbccddeeff"),
        ),
    )
    return b"".join(descriptor.encode() for descriptor in descriptors)


PAYLOADS = {
    "descriptor-bundle": descriptor_bundle(),
    "synthetic-512": bytes((index * 37 + 11) % 256 for index in range(512)),
}

PROFILES = {
    "clean-64": ScarceLinkProfile(
        max_frame_bytes=64,
        bitrate_bps=5000,
        data_loss_ppm=0,
        ack_loss_ppm=0,
        max_retries=3,
        ack_bytes=8,
        seed=1,
    ),
    "lossy-64": ScarceLinkProfile(
        max_frame_bytes=64,
        bitrate_bps=5000,
        data_loss_ppm=200_000,
        ack_loss_ppm=100_000,
        max_retries=12,
        ack_bytes=8,
        seed=11,
    ),
    "narrow-48": ScarceLinkProfile(
        max_frame_bytes=48,
        bitrate_bps=2400,
        data_loss_ppm=100_000,
        ack_loss_ppm=50_000,
        max_retries=12,
        ack_bytes=8,
        seed=23,
    ),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    rows: list[dict[str, object]] = []

    for payload_index, (payload_name, payload) in enumerate(PAYLOADS.items(), start=1):
        for profile_index, (profile_name, profile) in enumerate(PROFILES.items(), start=1):
            transfer_id = payload_index * 100 + profile_index
            reconstructed, report = transmit_exact(payload, transfer_id=transfer_id, profile=profile)
            repeated_reconstructed, repeated_report = transmit_exact(
                payload,
                transfer_id=transfer_id,
                profile=profile,
            )

            exact = reconstructed == repeated_reconstructed == payload
            deterministic = repeated_report == report
            if not exact:
                raise AssertionError(f"{payload_name}/{profile_name}: exact reconstruction failed")
            if not deterministic:
                raise AssertionError(f"{payload_name}/{profile_name}: deterministic replay failed")

            row = {
                "payload": payload_name,
                "profile": profile_name,
                "source_sha256": sha256(payload),
                "reconstructed_sha256": sha256(reconstructed),
                "exact": exact,
                "deterministic_replay": deterministic,
                "profile_parameters": asdict(profile),
                **asdict(report),
                "wire_over_source_ratio": report.total_wire_bytes / max(1, len(payload)),
            }
            rows.append(row)

    clean_rows = [row for row in rows if row["profile"] == "clean-64"]
    lossy_rows = [row for row in rows if row["profile"] == "lossy-64"]

    criteria = {
        "all_exact": all(bool(row["exact"]) for row in rows),
        "all_deterministic": all(bool(row["deterministic_replay"]) for row in rows),
        "clean_has_zero_retransmissions": all(int(row["retransmissions"]) == 0 for row in clean_rows),
        "lossy_exercises_retransmission": any(int(row["retransmissions"]) > 0 for row in lossy_rows),
        "lossy_exercises_duplicate_delivery": any(int(row["duplicate_deliveries"]) > 0 for row in lossy_rows),
    }
    success = all(criteria.values())
    if not success:
        raise AssertionError(f"PN-002 success criteria failed: {criteria}")

    result = {
        "experiment": "PN-002",
        "protocol": "PNF1",
        "standalone_core": True,
        "application_dependencies": [],
        "external_runtime_dependencies": [],
        "payloads": {name: {"bytes": len(data), "sha256": sha256(data)} for name, data in PAYLOADS.items()},
        "profiles": {name: asdict(profile) for name, profile in PROFILES.items()},
        "criteria": criteria,
        "success": success,
        "rows": rows,
    }

    output = Path(__file__).with_name("results.json")
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
