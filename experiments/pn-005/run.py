from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path

from pollicino.net import (
    PollicinoStore,
    ScarceLinkProfile,
    build_chunk_manifest,
    sync_missing_chunks,
    transmit_exact,
)


CHUNK_SIZE = 512
CHUNK_COUNT = 16
CACHE_COUNTS = (0, 4, 8, 12, 16)


def make_chunk(index: int) -> bytes:
    seed = hashlib.sha256(f"pn005-unique-chunk-{index}".encode("ascii")).digest()
    return seed * (CHUNK_SIZE // len(seed))


CHUNKS = tuple(make_chunk(index) for index in range(CHUNK_COUNT))
DATA = b"".join(CHUNKS)

PROFILE = ScarceLinkProfile(
    max_frame_bytes=64,
    bitrate_bps=5000,
    data_loss_ppm=0,
    ack_loss_ppm=0,
    max_retries=3,
    ack_bytes=8,
    seed=1,
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    manifest, rebuilt_chunks = build_chunk_manifest(DATA, chunk_size=CHUNK_SIZE)
    if rebuilt_chunks != CHUNKS:
        raise AssertionError("frozen PN-005 chunking changed")
    if len({ref.sha256_digest for ref in manifest.chunks}) != CHUNK_COUNT:
        raise AssertionError("frozen PN-005 chunks are not unique")

    direct_data, direct_report = transmit_exact(
        DATA,
        transfer_id=900,
        profile=PROFILE,
    )
    if direct_data != DATA:
        raise AssertionError("direct PNF1 baseline failed exact reconstruction")

    rows: list[dict[str, object]] = []
    for mode_index, manifest_on_scarce in enumerate((True, False), start=1):
        mode = "manifest-on-scarce" if manifest_on_scarce else "manifest-pre-resolved"
        for level_index, cached_count in enumerate(CACHE_COUNTS, start=1):
            sender = PollicinoStore()
            receiver = PollicinoStore()
            for chunk in CHUNKS[:cached_count]:
                receiver.put(chunk)

            reconstructed, report = sync_missing_chunks(
                DATA,
                chunk_size=CHUNK_SIZE,
                sender_store=sender,
                receiver_store=receiver,
                profile=PROFILE,
                transfer_id_base=mode_index * 10_000 + level_index * 100,
                manifest_on_scarce=manifest_on_scarce,
            )
            if reconstructed != DATA or not report.exact:
                raise AssertionError(f"{mode}/{cached_count}: exact reconstruction failed")

            rows.append(
                {
                    "mode": mode,
                    "cached_chunk_count_requested": cached_count,
                    "cached_fraction": cached_count / CHUNK_COUNT,
                    **asdict(report),
                    "scarce_vs_direct_fraction": report.total_scarce_wire_bytes
                    / direct_report.total_wire_bytes,
                    "pre_resolved_scarce_vs_direct_fraction": report.total_scarce_if_manifest_pre_resolved
                    / direct_report.total_wire_bytes,
                }
            )

    def mode_rows(mode: str) -> list[dict[str, object]]:
        return [row for row in rows if row["mode"] == mode]

    on_scarce = mode_rows("manifest-on-scarce")
    pre_resolved = mode_rows("manifest-pre-resolved")

    missing_counts = [int(row["missing_chunk_count"]) for row in on_scarce]
    missing_bytes = [int(row["missing_source_bytes"]) for row in on_scarce]
    chunk_wire = [int(row["chunk_wire_bytes"]) for row in on_scarce]

    criteria = {
        "all_exact": all(bool(row["exact"]) for row in rows),
        "missing_chunk_count_monotone": missing_counts == sorted(missing_counts, reverse=True),
        "missing_source_bytes_monotone": missing_bytes == sorted(missing_bytes, reverse=True),
        "chunk_wire_strictly_decreases": all(
            left > right for left, right in zip(chunk_wire, chunk_wire[1:])
        ),
        "fully_cached_has_zero_chunk_wire": chunk_wire[-1] == 0,
        "pre_resolved_has_zero_manifest_wire": all(
            int(row["manifest_wire_bytes"]) == 0 for row in pre_resolved
        ),
        "pre_resolved_never_costs_more_scarce_bytes": all(
            int(pre["total_scarce_wire_bytes"]) <= int(full["total_scarce_wire_bytes"])
            for pre, full in zip(pre_resolved, on_scarce)
        ),
        "twentyfive_percent_cache_beats_direct_with_manifest": int(on_scarce[1]["total_scarce_wire_bytes"])
        < direct_report.total_wire_bytes,
        "cached_counts_match_frozen_levels": [
            int(row["cached_chunk_count"]) for row in on_scarce
        ]
        == list(CACHE_COUNTS),
    }
    success = all(criteria.values())
    if not success:
        raise AssertionError(f"PN-005 success criteria failed: {criteria}")

    result = {
        "experiment": "PN-005",
        "standalone_core": True,
        "application_dependencies": [],
        "external_runtime_dependencies": [],
        "source": {
            "bytes": len(DATA),
            "sha256": sha256(DATA),
            "chunk_size": CHUNK_SIZE,
            "chunk_count": CHUNK_COUNT,
            "manifest_bytes": len(manifest.encode()),
            "manifest_fingerprint": manifest.fingerprint.hex(),
        },
        "profile": asdict(PROFILE),
        "direct_full_object": asdict(direct_report),
        "criteria": criteria,
        "success": success,
        "rows": rows,
    }

    output = Path(__file__).with_name("results.json")
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
