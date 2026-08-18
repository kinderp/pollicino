from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path

from pollicino.net import (
    DiscoveryDescriptor,
    InMemoryContentProvider,
    InMemoryResolver,
    RetrievalSource,
    ScarceLinkProfile,
    manifest_for_content,
    retrieve_exact,
    transmit_exact,
)


OBJECTS = {
    "small-1k": bytes((index * 29 + 7) % 256 for index in range(1024)),
    "large-64k": bytes((index * 73 + (index // 251) * 19 + 11) % 256 for index in range(65536)),
}

COORDINATES = {
    "small-1k": bytes.fromhex("102030405060708090a0b0c0"),
    "large-64k": bytes.fromhex("d0c0b0a09080706050403020"),
}

CLEAN_FALLBACK = ScarceLinkProfile(
    max_frame_bytes=64,
    bitrate_bps=5000,
    data_loss_ppm=0,
    ack_loss_ppm=0,
    max_retries=3,
    ack_bytes=8,
    seed=1,
)

LOSSY_FALLBACK = ScarceLinkProfile(
    max_frame_bytes=64,
    bitrate_bps=5000,
    data_loss_ppm=200_000,
    ack_loss_ppm=100_000,
    max_retries=12,
    ack_bytes=8,
    seed=11,
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    resolver = InMemoryResolver()
    provider = InMemoryContentProvider()
    descriptors: dict[str, DiscoveryDescriptor] = {}
    manifests = {}

    for index, (name, content) in enumerate(OBJECTS.items(), start=1):
        locator = f"fixture/{name}".encode("ascii")
        provider.put(locator, content)
        manifest = manifest_for_content(
            content,
            object_class=index,
            sources=(RetrievalSource(provider_id="memory-rich", locator=locator),),
        )
        coordinate = COORDINATES[name]
        resolver.register(coordinate, manifest)
        descriptors[name] = DiscoveryDescriptor(
            object_class=index,
            rendezvous_key=coordinate,
            ttl_seconds=300,
            nonce=index,
            capability_mask=1,
            authenticator=b"12345678",
        )
        manifests[name] = manifest

    # Demonstrate that a second rendezvous key may resolve the same exact object.
    rotating_alias = bytes.fromhex("0011aabbccddeeff10293847")
    resolver.register(rotating_alias, manifests["large-64k"])

    rows: list[dict[str, object]] = []
    for index, (name, content) in enumerate(OBJECTS.items(), start=1):
        descriptor = descriptors[name]
        reconstructed, report = retrieve_exact(
            descriptor,
            resolver=resolver,
            providers={"memory-rich": provider},
        )
        repeated, repeated_report = retrieve_exact(
            descriptor,
            resolver=resolver,
            providers={"memory-rich": provider},
        )

        clean_reconstructed, clean_report = transmit_exact(
            content,
            transfer_id=index * 100 + 1,
            profile=CLEAN_FALLBACK,
        )
        lossy_reconstructed, lossy_report = transmit_exact(
            content,
            transfer_id=index * 100 + 2,
            profile=LOSSY_FALLBACK,
        )

        exact = reconstructed == repeated == clean_reconstructed == lossy_reconstructed == content
        deterministic = repeated_report == report
        if not exact:
            raise AssertionError(f"{name}: exact reconstruction failed")
        if not deterministic:
            raise AssertionError(f"{name}: repeated retrieval report changed")

        rows.append(
            {
                "object": name,
                "source_bytes": len(content),
                "source_sha256": sha256(content),
                "coordinate_hex": descriptor.rendezvous_key.hex(),
                "coordinate_bytes": len(descriptor.rendezvous_key),
                "coordinate_equals_digest_prefix": descriptor.rendezvous_key
                == hashlib.sha256(content).digest()[: len(descriptor.rendezvous_key)],
                "scarce_link_discovery_bytes": report.scarce_link_bytes,
                "manifest_bytes_rich_path": report.manifest_bytes,
                "content_bytes_rich_path": report.content_bytes,
                "selected_provider": report.selected_provider_id,
                "full_hash_verified": report.expected_sha256 == report.reconstructed_sha256,
                "exact": report.exact,
                "deterministic_retrieval": deterministic,
                "clean_full_scarce_wire_bytes": clean_report.total_wire_bytes,
                "lossy_full_scarce_wire_bytes": lossy_report.total_wire_bytes,
                "discovery_vs_clean_full_fraction": report.scarce_link_bytes
                / clean_report.total_wire_bytes,
                "discovery_vs_lossy_full_fraction": report.scarce_link_bytes
                / lossy_report.total_wire_bytes,
                "clean_fallback_report": asdict(clean_report),
                "lossy_fallback_report": asdict(lossy_report),
            }
        )

    alias_descriptor = DiscoveryDescriptor(
        object_class=2,
        rendezvous_key=rotating_alias,
        ttl_seconds=60,
        nonce=99,
        capability_mask=1,
        authenticator=b"87654321",
    )
    alias_content, alias_report = retrieve_exact(
        alias_descriptor,
        resolver=resolver,
        providers={"memory-rich": provider},
    )
    rotating_alias_exact = alias_content == OBJECTS["large-64k"] and alias_report.exact

    criteria = {
        "all_exact": all(bool(row["exact"]) for row in rows),
        "all_full_hash_verified": all(bool(row["full_hash_verified"]) for row in rows),
        "all_deterministic": all(bool(row["deterministic_retrieval"]) for row in rows),
        "all_discovery_at_most_64_bytes": all(
            int(row["scarce_link_discovery_bytes"]) <= 64 for row in rows
        ),
        "coordinates_are_not_digest_prefixes": all(
            not bool(row["coordinate_equals_digest_prefix"]) for row in rows
        ),
        "discovery_smaller_than_clean_full_scarce_transfer": all(
            int(row["scarce_link_discovery_bytes"]) < int(row["clean_full_scarce_wire_bytes"])
            for row in rows
        ),
        "rotating_alias_resolves_same_exact_content": rotating_alias_exact,
    }
    success = all(criteria.values())
    if not success:
        raise AssertionError(f"PN-003 success criteria failed: {criteria}")

    result = {
        "experiment": "PN-003",
        "discovery_protocol": "PND1",
        "manifest_protocol": "PNM1",
        "standalone_core": True,
        "application_dependencies": [],
        "external_runtime_dependencies": [],
        "criteria": criteria,
        "success": success,
        "rotating_alias": {
            "coordinate_hex": rotating_alias.hex(),
            "scarce_link_discovery_bytes": alias_report.scarce_link_bytes,
            "expected_sha256": alias_report.expected_sha256,
            "exact": rotating_alias_exact,
        },
        "rows": rows,
    }

    output = Path(__file__).with_name("results.json")
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
