from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path

from pollicino.net import (
    AuthorizationError,
    DiscoveryDescriptor,
    InMemoryContentProvider,
    InMemoryResolver,
    RetrievalSource,
    ScarceLinkProfile,
    deliver_exact_adaptive,
    manifest_for_content,
)


CONTENT = bytes((index * 61 + (index // 127) * 17 + 3) % 256 for index in range(4096))
COORDINATE = bytes.fromhex("102132435465768798a9bacb")
LOCATOR = b"fixture/object-4k"

CLEAN = ScarceLinkProfile(
    max_frame_bytes=64,
    bitrate_bps=5000,
    data_loss_ppm=0,
    ack_loss_ppm=0,
    max_retries=3,
    ack_bytes=8,
    seed=1,
)

LOSSY = ScarceLinkProfile(
    max_frame_bytes=64,
    bitrate_bps=5000,
    data_loss_ppm=200_000,
    ack_loss_ppm=100_000,
    max_retries=12,
    ack_bytes=8,
    seed=11,
)


class StaticGate:
    def __init__(self, allowed: bool) -> None:
        self.allowed = allowed
        self.calls = 0

    def authorize(self, descriptor: DiscoveryDescriptor, context: bytes) -> bool:
        self.calls += 1
        return self.allowed


class CountingResolver(InMemoryResolver):
    def __init__(self) -> None:
        super().__init__()
        self.resolve_calls = 0

    def resolve(self, coordinate: bytes) -> bytes:
        self.resolve_calls += 1
        return super().resolve(coordinate)


class CountingProvider(InMemoryContentProvider):
    def __init__(self) -> None:
        super().__init__()
        self.fetch_calls = 0

    def fetch(self, locator: bytes) -> bytes:
        self.fetch_calls += 1
        return super().fetch(locator)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_fixture():
    resolver = CountingResolver()
    provider = CountingProvider()
    provider.put(LOCATOR, CONTENT)
    manifest = manifest_for_content(
        CONTENT,
        object_class=4,
        sources=(RetrievalSource(provider_id="memory-rich", locator=LOCATOR),),
    )
    resolver.register(COORDINATE, manifest)
    descriptor = DiscoveryDescriptor(
        object_class=4,
        rendezvous_key=COORDINATE,
        ttl_seconds=300,
        nonce=4,
        capability_mask=1,
        authenticator=b"12345678",
    )
    return descriptor, resolver, provider, manifest


def report_row(name: str, report) -> dict[str, object]:
    return {
        "case": name,
        **asdict(report),
    }


def main() -> None:
    descriptor, resolver, provider, manifest = build_fixture()
    source_sha = sha256(CONTENT)

    rich_data, rich_report = deliver_exact_adaptive(
        descriptor,
        authorizer=StaticGate(True),
        resolver=resolver,
        rich_providers={"memory-rich": provider},
        source_content=CONTENT,
        scarce_profile=CLEAN,
        transfer_id=100,
    )

    clean_data, clean_report = deliver_exact_adaptive(
        descriptor,
        authorizer=StaticGate(True),
        resolver=resolver,
        rich_providers={},
        source_content=CONTENT,
        scarce_profile=CLEAN,
        transfer_id=200,
    )

    lossy_data, lossy_report = deliver_exact_adaptive(
        descriptor,
        authorizer=StaticGate(True),
        resolver=resolver,
        rich_providers={},
        source_content=CONTENT,
        scarce_profile=LOSSY,
        transfer_id=300,
    )

    corrupt = CountingProvider()
    corrupt_payload = b"hash-invalid-rich-copy"
    corrupt.put(LOCATOR, corrupt_payload)
    corrupt_data, corrupt_report = deliver_exact_adaptive(
        descriptor,
        authorizer=StaticGate(True),
        resolver=resolver,
        rich_providers={"memory-rich": corrupt},
        source_content=CONTENT,
        scarce_profile=CLEAN,
        transfer_id=400,
    )

    denied_descriptor, denied_resolver, denied_provider, _ = build_fixture()
    denied_gate = StaticGate(False)
    denied = False
    try:
        deliver_exact_adaptive(
            denied_descriptor,
            authorizer=denied_gate,
            authorization_context=b"opaque-policy-context",
            resolver=denied_resolver,
            rich_providers={"memory-rich": denied_provider},
            source_content=CONTENT,
            scarce_profile=CLEAN,
            transfer_id=500,
        )
    except AuthorizationError:
        denied = True

    rows = [
        report_row("rich-valid", rich_report),
        report_row("fallback-clean", clean_report),
        report_row("fallback-lossy", lossy_report),
        report_row("corrupt-rich-then-fallback", corrupt_report),
    ]

    exact_cases = all(
        data == CONTENT
        for data in (rich_data, clean_data, lossy_data, corrupt_data)
    ) and all(row["sha256"] == source_sha for row in rows)

    criteria = {
        "all_allowed_cases_exact": exact_cases,
        "rich_uses_only_discovery_on_scarce_link": rich_report.total_scarce_wire_bytes
        == len(descriptor.encode()),
        "clean_fallback_sends_manifest_and_content": clean_report.scarce_manifest_wire_bytes > 0
        and clean_report.scarce_content_wire_bytes > 0,
        "lossy_fallback_sends_manifest_and_content": lossy_report.scarce_manifest_wire_bytes > 0
        and lossy_report.scarce_content_wire_bytes > 0,
        "lossy_fallback_exercises_retransmission": (
            lossy_report.fallback_manifest_retransmissions
            + lossy_report.fallback_content_retransmissions
            > 0
        ),
        "corrupt_rich_bytes_are_accounted": corrupt_report.rich_manifest_bytes
        == len(manifest.encode())
        and corrupt_report.rich_content_bytes == len(corrupt_payload),
        "corrupt_rich_falls_back_exactly": corrupt_report.path == "scarce-exact"
        and corrupt_report.exact,
        "denial_precedes_resolution_and_fetch": denied
        and denied_gate.calls == 1
        and denied_resolver.resolve_calls == 0
        and denied_provider.fetch_calls == 0,
    }
    success = all(criteria.values())
    if not success:
        raise AssertionError(f"PN-004 success criteria failed: {criteria}")

    result = {
        "experiment": "PN-004",
        "standalone_core": True,
        "application_dependencies": [],
        "external_runtime_dependencies": [],
        "source": {
            "bytes": len(CONTENT),
            "sha256": source_sha,
            "descriptor_bytes": len(descriptor.encode()),
            "manifest_bytes": len(manifest.encode()),
        },
        "profiles": {
            "clean": asdict(CLEAN),
            "lossy": asdict(LOSSY),
        },
        "criteria": criteria,
        "success": success,
        "rows": rows,
    }

    output = Path(__file__).with_name("results.json")
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
