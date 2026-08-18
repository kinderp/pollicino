from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import zlib

from pollicino.integrations.dna import (
    DNA_FLAG_INLINE,
    DNATraceV01,
    dna_trace_from_canonical_json,
    dna_trace_from_inline_descriptor,
    dna_trace_manifest,
    dna_trace_to_descriptor,
    is_dna_reference_descriptor,
)
from pollicino.net import (
    DiscoveryDescriptor,
    InMemoryContentProvider,
    InMemoryResolver,
    ScarceLinkProfile,
    retrieve_exact,
    transmit_exact,
)


PROFILE = ScarceLinkProfile(
    max_frame_bytes=64,
    bitrate_bps=5000,
    data_loss_ppm=0,
    ack_loss_ppm=0,
    max_retries=3,
    ack_bytes=8,
    seed=1,
)

FIXTURES = {
    "compact-travel": DNATraceV01(
        trace_id="trace-a1b2",
        ephemeral_sender_id="ephem001",
        domains=("travel",),
        intent_codes=(17, 24),
        rendezvous_capabilities=("internet", "lora"),
        issued_at="2026-08-18T20:00:00Z",
        expires_at="2026-08-18T20:15:00Z",
        nonce=41,
        authenticator=b"dna-auth",
        coarse_geo_cell="cell38S",
    ),
    "large-multidomain": DNATraceV01(
        trace_id="trace-" + "a" * 40,
        ephemeral_sender_id="sender-" + "b" * 64,
        domains=("travel", "shopping", "social", "mobility", "local_services"),
        intent_codes=tuple(range(100, 116)),
        rendezvous_capabilities=(
            "internet",
            "ble",
            "nfc",
            "wifi_aware",
            "wifi_direct",
            "lora",
            "qr",
        ),
        issued_at="2026-08-18T20:00:00Z",
        expires_at="2026-08-18T21:00:00Z",
        nonce=42,
        authenticator=b"large-auth",
        coarse_geo_cell="geo-" + "c" * 28,
    ),
    "offset-time": DNATraceV01(
        trace_id="trace-time",
        ephemeral_sender_id="ephem002",
        domains=("travel",),
        intent_codes=(1,),
        rendezvous_capabilities=("lora",),
        issued_at="2026-08-18T22:00:00+02:00",
        expires_at="2026-08-18T22:10:00+02:00",
        nonce=43,
        authenticator=b"time-auth",
    ),
}

COORDINATES = {
    "compact-travel": bytes.fromhex("102030405060708090a0b0c0"),
    "large-multidomain": bytes.fromhex("d0c0b0a09080706050403020"),
    "offset-time": bytes.fromhex("00112233445566778899aabb"),
}

EXPECTED_MODES = {
    "compact-travel": "inline",
    "large-multidomain": "reference",
    "offset-time": "reference",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    rows: list[dict[str, object]] = []

    for index, (name, trace) in enumerate(FIXTURES.items(), start=1):
        coordinate = COORDINATES[name]
        canonical = trace.canonical_json()
        descriptor = dna_trace_to_descriptor(trace, coordinate=coordinate)
        descriptor_bytes = descriptor.encode()

        received_descriptor_bytes, descriptor_report = transmit_exact(
            descriptor_bytes,
            transfer_id=index * 100 + 1,
            profile=PROFILE,
        )
        received_descriptor = DiscoveryDescriptor.decode(received_descriptor_bytes)

        direct_json, direct_json_report = transmit_exact(
            canonical,
            transfer_id=index * 100 + 2,
            profile=PROFILE,
        )
        if direct_json != canonical:
            raise AssertionError(f"{name}: direct canonical JSON transfer changed bytes")

        rich_manifest_bytes = 0
        rich_content_bytes = 0
        full_hash_verified = False

        if received_descriptor.flags == DNA_FLAG_INLINE:
            mode = "inline"
            decoded_trace = dna_trace_from_inline_descriptor(received_descriptor)
            reconstructed_canonical = decoded_trace.canonical_json()
            exact = decoded_trace == trace and reconstructed_canonical == canonical
        elif is_dna_reference_descriptor(received_descriptor):
            mode = "reference"
            resolver = InMemoryResolver()
            provider = InMemoryContentProvider()
            locator = f"dna/{name}".encode("ascii")
            provider.put(locator, canonical)
            manifest = dna_trace_manifest(
                trace,
                provider_id="memory-dna",
                locator=locator,
            )
            resolver.register(coordinate, manifest)
            retrieved, retrieval_report = retrieve_exact(
                received_descriptor,
                resolver=resolver,
                providers={"memory-dna": provider},
            )
            decoded_trace = dna_trace_from_canonical_json(retrieved)
            reconstructed_canonical = retrieved
            exact = decoded_trace == trace and retrieved == canonical and retrieval_report.exact
            rich_manifest_bytes = retrieval_report.manifest_bytes
            rich_content_bytes = retrieval_report.content_bytes
            full_hash_verified = retrieval_report.expected_sha256 == retrieval_report.reconstructed_sha256
        else:
            raise AssertionError(f"{name}: descriptor selected neither DNA mode")

        if not exact:
            raise AssertionError(f"{name}: DNA trace round-trip failed")

        rows.append(
            {
                "fixture": name,
                "expected_mode": EXPECTED_MODES[name],
                "mode": mode,
                "canonical_json_bytes": len(canonical),
                "zlib9_json_bytes": len(zlib.compress(canonical, level=9)),
                "descriptor_bytes": len(descriptor_bytes),
                "descriptor_scarce_wire_bytes": descriptor_report.total_wire_bytes,
                "direct_json_scarce_wire_bytes": direct_json_report.total_wire_bytes,
                "rich_manifest_bytes": rich_manifest_bytes,
                "rich_content_bytes": rich_content_bytes,
                "canonical_sha256": sha256(canonical),
                "coordinate_hex": coordinate.hex(),
                "coordinate_equals_digest_prefix": coordinate
                == hashlib.sha256(canonical).digest()[: len(coordinate)],
                "full_hash_verified_on_reference": full_hash_verified,
                "exact": exact,
                "descriptor_scarce_vs_direct_json_fraction": descriptor_report.total_wire_bytes
                / direct_json_report.total_wire_bytes,
            }
        )

    criteria = {
        "all_exact": all(bool(row["exact"]) for row in rows),
        "all_modes_match_frozen_expectation": all(
            row["mode"] == row["expected_mode"] for row in rows
        ),
        "compact_is_inline": rows[0]["mode"] == "inline",
        "reference_cases_full_hash_verified": all(
            bool(row["full_hash_verified_on_reference"])
            for row in rows
            if row["mode"] == "reference"
        ),
        "all_descriptors_smaller_than_canonical_json": all(
            int(row["descriptor_bytes"]) < int(row["canonical_json_bytes"])
            for row in rows
        ),
        "all_descriptor_wire_cheaper_than_direct_json_wire": all(
            int(row["descriptor_scarce_wire_bytes"])
            < int(row["direct_json_scarce_wire_bytes"])
            for row in rows
        ),
        "coordinates_are_not_content_digest_prefixes": all(
            not bool(row["coordinate_equals_digest_prefix"]) for row in rows
        ),
        "inline_has_no_rich_content": all(
            int(row["rich_manifest_bytes"]) == 0 and int(row["rich_content_bytes"]) == 0
            for row in rows
            if row["mode"] == "inline"
        ),
    }
    success = all(criteria.values())
    if not success:
        raise AssertionError(f"PN-006 success criteria failed: {criteria}")

    result = {
        "experiment": "PN-006",
        "integration": "DNA DNATrace v0.1",
        "dna_contract": {
            "repository": "kinderp/dna",
            "commit": "01ba2b4d381168566cc3e47c9bda8045897adc0f",
            "schema_path": "schemas/v0.1/dna-trace.schema.json",
            "schema_blob_sha": "bbb2dcdce06935d2de51504bd9a7ad38ca76efba",
        },
        "core_runtime_dependency_on_dna": False,
        "profile": asdict(PROFILE),
        "criteria": criteria,
        "success": success,
        "rows": rows,
    }

    output = Path(__file__).with_name("results.json")
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
