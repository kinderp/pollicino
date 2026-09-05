from __future__ import annotations

from pathlib import Path

import pytest

from pollicino.net import (
    CustodyLedger,
    DirectoryPollicinoStore,
    DiscoveryDescriptor,
    ForwardBundle,
    ForwardPeer,
    seed_bundle_custody,
    seed_forwarding_object,
)
from pollicino.net.relay_storage import (
    RelayStorageCatalog,
    RelayStoragePolicy,
    collect_relay_storage,
    load_relay_storage_catalog,
    save_relay_storage_catalog,
)


def descriptor(key: bytes, *, nonce: int, ttl_seconds: int = 1000) -> DiscoveryDescriptor:
    return DiscoveryDescriptor(
        object_class=1,
        rendezvous_key=key,
        ttl_seconds=ttl_seconds,
        hop_limit=8,
        nonce=nonce,
    )


def make_bundle(manifest, key: bytes, *, nonce: int, created_at_s: int = 0, ttl_seconds: int = 1000):
    return ForwardBundle.from_descriptor(
        manifest,
        descriptor(key, nonce=nonce, ttl_seconds=ttl_seconds),
        created_at_s=created_at_s,
    )


def test_expiry_removes_only_unreferenced_objects_and_prunes_local_custody(tmp_path: Path) -> None:
    store = DirectoryPollicinoStore(tmp_path / "relay")
    relay = ForwardPeer("relay", store)
    shared = b"S" * 32
    data1 = shared + b"A" * 32
    data2 = shared + b"B" * 32
    manifest1 = seed_forwarding_object(data1, chunk_size=32, store=store)
    manifest2 = seed_forwarding_object(data2, chunk_size=32, store=store)
    bundle1 = make_bundle(manifest1, b"bundle-1", nonce=1)
    bundle2 = make_bundle(manifest2, b"bundle-2", nonce=2)

    policy = RelayStoragePolicy(max_store_bytes=1_000_000, retention_seconds=10)
    catalog = RelayStorageCatalog("relay")
    catalog.register(bundle1, manifest1, now_s=100, policy=policy)
    catalog.register(bundle2, manifest2, now_s=105, policy=policy)

    ledger = CustodyLedger()
    seed_bundle_custody(bundle1, manifest1, origin=relay, ledger=ledger, now_s=100)
    seed_bundle_custody(bundle2, manifest2, origin=relay, ledger=ledger, now_s=105)

    shared_digest = manifest1.chunks[0].sha256_digest
    unique1 = manifest1.chunks[1].sha256_digest
    unique2 = manifest2.chunks[1].sha256_digest
    assert shared_digest == manifest2.chunks[0].sha256_digest

    report, pruned = collect_relay_storage(
        store, catalog, policy, now_s=111, ledger=ledger
    )

    assert report.expired_bundle_ids == (bundle1.bundle_id.hex(),)
    assert report.quota_evicted_bundle_ids == ()
    assert report.freed_bytes > 0
    assert not store.has(manifest1.fingerprint)
    assert not store.has(unique1)
    assert store.has(shared_digest)
    assert store.has(unique2)
    assert store.has(manifest2.fingerprint)
    assert catalog.get(bundle1.bundle_id) is None
    assert catalog.get(bundle2.bundle_id) is not None
    assert pruned is not None
    assert pruned.get(bundle1.bundle_id, "relay") is None
    assert pruned.get(bundle2.bundle_id, "relay") is not None


def test_quota_evicts_oldest_unpinned_bundle_but_preserves_pinned(tmp_path: Path) -> None:
    store = DirectoryPollicinoStore(tmp_path / "relay")
    manifest1 = seed_forwarding_object(b"A" * 64, chunk_size=64, store=store)
    manifest2 = seed_forwarding_object(b"B" * 64, chunk_size=64, store=store)
    bundle1 = make_bundle(manifest1, b"pinned", nonce=11, ttl_seconds=10_000)
    bundle2 = make_bundle(manifest2, b"evictable", nonce=12, ttl_seconds=10_000)

    keep_bytes = len(manifest1.encode()) + 64
    policy = RelayStoragePolicy(max_store_bytes=keep_bytes, retention_seconds=1000)
    catalog = RelayStorageCatalog("relay")
    catalog.register(bundle1, manifest1, now_s=0, policy=policy, pinned=True)
    catalog.register(bundle2, manifest2, now_s=10, policy=policy)

    report, _ = collect_relay_storage(store, catalog, policy, now_s=20)

    assert report.expired_bundle_ids == ()
    assert report.quota_evicted_bundle_ids == (bundle2.bundle_id.hex(),)
    assert report.store_bytes_after == keep_bytes
    assert report.over_quota_bytes == 0
    assert store.has(manifest1.fingerprint)
    assert store.has(manifest1.chunks[0].sha256_digest)
    assert not store.has(manifest2.fingerprint)
    assert not store.has(manifest2.chunks[0].sha256_digest)
    assert catalog.get(bundle1.bundle_id) is not None
    assert catalog.get(bundle2.bundle_id) is None


def test_pinned_data_reports_over_quota_instead_of_silent_deletion(tmp_path: Path) -> None:
    store = DirectoryPollicinoStore(tmp_path / "relay")
    manifest = seed_forwarding_object(b"P" * 64, chunk_size=64, store=store)
    bundle = make_bundle(manifest, b"pinned-only", nonce=21, ttl_seconds=10_000)
    policy = RelayStoragePolicy(max_store_bytes=0, retention_seconds=1000)
    catalog = RelayStorageCatalog("relay")
    catalog.register(bundle, manifest, now_s=0, policy=policy, pinned=True)

    report, _ = collect_relay_storage(store, catalog, policy, now_s=1)

    assert report.quota_evicted_bundle_ids == ()
    assert report.over_quota_bytes == report.store_bytes_after
    assert report.store_bytes_after > 0
    assert catalog.get(bundle.bundle_id) is not None
    assert store.has(manifest.fingerprint)


def test_bundle_ttl_is_a_hard_upper_bound_on_local_retention(tmp_path: Path) -> None:
    store = DirectoryPollicinoStore(tmp_path / "relay")
    manifest = seed_forwarding_object(b"T" * 64, chunk_size=64, store=store)
    bundle = make_bundle(
        manifest, b"short-ttl", nonce=31, created_at_s=100, ttl_seconds=5
    )
    policy = RelayStoragePolicy(max_store_bytes=1_000_000, retention_seconds=10_000)
    catalog = RelayStorageCatalog("relay")
    record = catalog.register(bundle, manifest, now_s=100, policy=policy, pinned=True)

    assert record.retain_until_s == 105
    report, _ = collect_relay_storage(store, catalog, policy, now_s=105)
    assert report.expired_bundle_ids == (bundle.bundle_id.hex(),)
    assert catalog.get(bundle.bundle_id) is None
    assert not store.has(manifest.fingerprint)


def test_catalog_round_trip_and_checksum_failure(tmp_path: Path) -> None:
    store = DirectoryPollicinoStore(tmp_path / "relay")
    manifest = seed_forwarding_object(b"C" * 64, chunk_size=64, store=store)
    bundle = make_bundle(manifest, b"catalog", nonce=41)
    policy = RelayStoragePolicy(max_store_bytes=100_000, retention_seconds=90)
    catalog = RelayStorageCatalog("relay")
    catalog.register(bundle, manifest, now_s=7, policy=policy)

    checkpoint = tmp_path / "relay-catalog.json"
    save_relay_storage_catalog(checkpoint, catalog)
    restored = load_relay_storage_catalog(checkpoint)
    assert restored.to_dict() == catalog.to_dict()

    raw = checkpoint.read_bytes()
    assert b'"pinned":false' in raw
    checkpoint.write_bytes(raw.replace(b'"pinned":false', b'"pinned":true', 1))
    with pytest.raises(ValueError, match="checksum mismatch"):
        load_relay_storage_catalog(checkpoint)


def test_corrupt_address_file_is_removed_even_when_bundle_references_it(tmp_path: Path) -> None:
    store = DirectoryPollicinoStore(tmp_path / "relay")
    manifest = seed_forwarding_object(b"Z" * 64, chunk_size=64, store=store)
    bundle = make_bundle(manifest, b"corrupt", nonce=51)
    policy = RelayStoragePolicy(max_store_bytes=1_000_000, retention_seconds=1000)
    catalog = RelayStorageCatalog("relay")
    catalog.register(bundle, manifest, now_s=0, policy=policy)

    digest = manifest.chunks[0].sha256_digest
    store.path_for_digest(digest).write_bytes(b"corrupt")
    assert not store.has(digest)

    report, _ = collect_relay_storage(store, catalog, policy, now_s=1)

    assert digest.hex() in report.removed_invalid_object_digests
    assert not store.path_for_digest(digest).exists()
    assert catalog.get(bundle.bundle_id) is not None
