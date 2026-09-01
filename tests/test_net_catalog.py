from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys

import pytest

import pollicino.net.catalog as catalog_module
from pollicino.net.catalog import (
    BoundedReference,
    BoundedReferenceCatalog,
    CatalogBoundsError,
    CatalogLimits,
    LOCAL_STATE_MAGIC,
    MAX_CATALOG_BYTES,
    MAX_CATALOG_ITEMS,
    MAX_EXCHANGE_ITEMS,
    MAX_LOGICAL_KEY_BYTES,
    MAX_REFERENCE_BYTES,
    MutationResult,
    ReferenceConflictError,
    reconcile_and_pull,
)
from pollicino.net.store import PollicinoStore


STATE_HEADER = struct.Struct(">4sBIQ32s")
ENTRY_HEADER = struct.Struct(">HI")


def entry(index: int, *, reference_size: int = 16) -> BoundedReference:
    key = index.to_bytes(4, "big")
    seed = hashlib.sha256(f"reference-{index}".encode("ascii")).digest()
    value = (seed * ((reference_size + len(seed) - 1) // len(seed)))[:reference_size]
    return BoundedReference(key, value)


def catalog_of(*entries: BoundedReference, limits: CatalogLimits | None = None) -> BoundedReferenceCatalog:
    catalog = BoundedReferenceCatalog(limits=limits)
    catalog.add_many(entries)
    return catalog


def raw_state(*, version: int = 1, count: int, payload: int, body: bytes) -> bytes:
    return STATE_HEADER.pack(
        LOCAL_STATE_MAGIC,
        version,
        count,
        payload,
        hashlib.sha256(body).digest(),
    ) + body


def test_default_bounds_match_preregistered_contract() -> None:
    limits = CatalogLimits()
    assert limits.max_key_bytes == 256
    assert limits.max_reference_bytes == 4096
    assert limits.max_catalog_items == 10_000
    assert limits.max_catalog_bytes == 16 * 1024 * 1024
    assert limits.max_exchange_items == 100


@pytest.mark.parametrize(
    ("key", "value", "error"),
    [
        (b"", b"v", "logical_key"),
        (b"k", b"", "opaque_reference"),
        (bytearray(b"k"), b"v", "bytes"),
        (b"k", bytearray(b"v"), "bytes"),
    ],
)
def test_reference_rejects_empty_or_non_bytes_values(key: bytes, value: bytes, error: str) -> None:
    with pytest.raises((TypeError, CatalogBoundsError), match=error):
        BoundedReference(key, value)  # type: ignore[arg-type]


def test_key_at_maximum_is_valid_and_one_over_fails() -> None:
    assert len(BoundedReference(b"k" * MAX_LOGICAL_KEY_BYTES, b"v").logical_key) == MAX_LOGICAL_KEY_BYTES
    with pytest.raises(CatalogBoundsError, match="logical_key"):
        BoundedReference(b"k" * (MAX_LOGICAL_KEY_BYTES + 1), b"v")


def test_reference_at_maximum_is_valid_and_one_over_fails() -> None:
    value = b"v" * MAX_REFERENCE_BYTES
    assert len(BoundedReference(b"k", value).opaque_reference) == MAX_REFERENCE_BYTES
    with pytest.raises(CatalogBoundsError, match="opaque_reference"):
        BoundedReference(b"k", value + b"v")


def test_limits_may_be_lower_but_never_raise_generic_ceilings() -> None:
    CatalogLimits(
        max_key_bytes=1,
        max_reference_bytes=1,
        max_catalog_items=1,
        max_catalog_bytes=1,
        max_exchange_items=1,
    )
    with pytest.raises(CatalogBoundsError, match="max_catalog_items"):
        CatalogLimits(max_catalog_items=MAX_CATALOG_ITEMS + 1)
    with pytest.raises(CatalogBoundsError, match="max_catalog_bytes"):
        CatalogLimits(max_catalog_bytes=MAX_CATALOG_BYTES + 1)


def test_add_duplicate_is_noop_without_growth() -> None:
    item = entry(1)
    catalog = BoundedReferenceCatalog()
    assert catalog.add(item) is MutationResult.ADDED
    before = catalog.canonical_state()
    before_bytes = catalog.payload_bytes

    assert catalog.add(item) is MutationResult.NOOP_DUPLICATE
    assert len(catalog) == 1
    assert catalog.payload_bytes == before_bytes
    assert catalog.canonical_state() == before


def test_same_key_different_reference_is_explicit_conflict_and_atomic() -> None:
    catalog = catalog_of(BoundedReference(b"key", b"AAA"))
    before = catalog.canonical_state()
    before_digest = catalog.state_digest
    with pytest.raises(ReferenceConflictError, match="different reference"):
        catalog.add(BoundedReference(b"key", b"BBB"))
    assert catalog.canonical_state() == before
    assert catalog.state_digest == before_digest
    assert catalog.get(b"key").opaque_reference == b"AAA"


def test_batch_conflict_rolls_back_all_prior_staged_entries() -> None:
    catalog = catalog_of(BoundedReference(b"key", b"AAA"))
    before = catalog.canonical_state()
    with pytest.raises(ReferenceConflictError):
        catalog.add_many(
            (
                BoundedReference(b"new", b"first"),
                BoundedReference(b"key", b"BBB"),
            )
        )
    assert catalog.canonical_state() == before
    assert b"new" not in catalog


def test_catalog_exactly_at_item_limit_and_one_over_is_atomic() -> None:
    limits = CatalogLimits(max_catalog_items=3)
    catalog = BoundedReferenceCatalog(limits=limits)
    catalog.add_many((entry(1), entry(2), entry(3)))
    assert len(catalog) == 3
    before = catalog.canonical_state()
    with pytest.raises(CatalogBoundsError, match="item quota"):
        catalog.add(entry(4))
    assert catalog.canonical_state() == before


def test_default_catalog_exactly_at_maximum_items_and_one_over() -> None:
    catalog = BoundedReferenceCatalog()
    catalog.add_many(
        BoundedReference(index.to_bytes(4, "big"), b"v")
        for index in range(MAX_CATALOG_ITEMS)
    )
    assert len(catalog) == MAX_CATALOG_ITEMS
    before_digest = catalog.state_digest
    with pytest.raises(CatalogBoundsError, match="item quota"):
        catalog.add(BoundedReference(b"overflow", b"v"))
    assert catalog.state_digest == before_digest


def test_catalog_exactly_at_byte_limit_and_one_addition_over_is_atomic() -> None:
    limits = CatalogLimits(
        max_key_bytes=4,
        max_reference_bytes=6,
        max_catalog_items=3,
        max_catalog_bytes=10,
    )
    catalog = BoundedReferenceCatalog(limits=limits)
    catalog.add(BoundedReference(b"key1", b"123456"))
    assert catalog.payload_bytes == 10
    before = catalog.canonical_state()
    with pytest.raises(CatalogBoundsError, match="byte quota"):
        catalog.add(BoundedReference(b"k", b"v"))
    assert catalog.canonical_state() == before


def test_default_catalog_exactly_at_maximum_bytes_and_one_over() -> None:
    catalog = BoundedReferenceCatalog()
    per_entry_payload = 4096
    reference = b"r" * (per_entry_payload - 4)
    catalog.add_many(
        BoundedReference(index.to_bytes(4, "big"), reference)
        for index in range(MAX_CATALOG_BYTES // per_entry_payload)
    )
    assert catalog.payload_bytes == MAX_CATALOG_BYTES
    before_digest = catalog.state_digest
    with pytest.raises(CatalogBoundsError, match="byte quota"):
        catalog.add(BoundedReference(b"overflow", b"v"))
    assert catalog.state_digest == before_digest


def test_active_catalog_limits_reject_entry_before_mutation() -> None:
    limits = CatalogLimits(max_key_bytes=2, max_reference_bytes=2)
    catalog = BoundedReferenceCatalog(limits=limits)
    before = catalog.canonical_state()
    with pytest.raises(CatalogBoundsError, match="logical_key"):
        catalog.add(BoundedReference(b"key", b"v"))
    with pytest.raises(CatalogBoundsError, match="opaque_reference"):
        catalog.add(BoundedReference(b"k", b"value"))
    assert catalog.canonical_state() == before


def test_batch_byte_overflow_is_atomic() -> None:
    limits = CatalogLimits(max_catalog_bytes=12)
    catalog = catalog_of(BoundedReference(b"a", b"1234"), limits=limits)
    before = catalog.canonical_state()
    with pytest.raises(CatalogBoundsError, match="byte quota"):
        catalog.add_many(
            (
                BoundedReference(b"b", b"1234"),
                BoundedReference(b"c", b"1234"),
            )
        )
    assert catalog.canonical_state() == before


def test_remove_changes_only_catalog_mapping() -> None:
    catalog = catalog_of(BoundedReference(b"key", b"reference"))
    removed = catalog.remove(b"key")
    assert removed == BoundedReference(b"key", b"reference")
    assert len(catalog) == 0
    assert catalog.payload_bytes == 0
    assert catalog.remove(b"key") is None


def test_removal_does_not_delete_pollicino_store_bytes() -> None:
    store = PollicinoStore()
    stored = b"independent exact object"
    digest = store.put(stored)
    catalog = catalog_of(BoundedReference(b"key", b"opaque"))
    catalog.remove(b"key")
    assert store.get(digest) == stored


def test_canonical_state_is_insertion_order_independent() -> None:
    items = tuple(entry(index) for index in range(10))
    forward = catalog_of(*items)
    reverse = catalog_of(*reversed(items))
    assert forward.canonical_state() == reverse.canonical_state()
    assert forward.state_digest == reverse.state_digest


def test_canonical_state_is_process_independent() -> None:
    expected = catalog_of(entry(1), entry(2)).canonical_state().hex()
    code = """
from pollicino.net.catalog import BoundedReference, BoundedReferenceCatalog
import hashlib
def item(index):
    key = index.to_bytes(4, 'big')
    seed = hashlib.sha256(f'reference-{index}'.encode('ascii')).digest()
    return BoundedReference(key, seed[:16])
c = BoundedReferenceCatalog()
c.add_many((item(2), item(1)))
print(c.canonical_state().hex())
"""
    completed = subprocess.run(
        [sys.executable, "-c", code],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == expected


def test_canonical_state_round_trip_and_empty_state() -> None:
    for original in (BoundedReferenceCatalog(), catalog_of(entry(3), entry(1))):
        decoded = BoundedReferenceCatalog.from_canonical_state(original.canonical_state())
        assert decoded.canonical_state() == original.canonical_state()
        assert decoded.state_digest == original.state_digest


def test_canonical_state_rejects_bad_magic_and_version() -> None:
    encoded = catalog_of(entry(1)).canonical_state()
    with pytest.raises(ValueError, match="magic"):
        BoundedReferenceCatalog.from_canonical_state(b"BAD!" + encoded[4:])
    bad_version = raw_state(version=2, count=0, payload=0, body=b"")
    with pytest.raises(ValueError, match="unsupported"):
        BoundedReferenceCatalog.from_canonical_state(bad_version)


def test_canonical_state_rejects_digest_mismatch() -> None:
    encoded = bytearray(catalog_of(entry(1)).canonical_state())
    encoded[-1] ^= 1
    with pytest.raises(ValueError, match="digest mismatch"):
        BoundedReferenceCatalog.from_canonical_state(bytes(encoded))


def test_canonical_state_rejects_duplicate_keys() -> None:
    item_body = ENTRY_HEADER.pack(1, 1) + b"k" + b"v"
    encoded = raw_state(count=2, payload=4, body=item_body + item_body)
    with pytest.raises(ValueError, match="duplicate keys"):
        BoundedReferenceCatalog.from_canonical_state(encoded)


@pytest.mark.parametrize(
    ("encoded", "error"),
    [
        (raw_state(count=1, payload=0, body=b""), "header is truncated"),
        (raw_state(count=1, payload=2, body=ENTRY_HEADER.pack(1, 1) + b"k"), "entry is truncated"),
        (raw_state(count=0, payload=0, body=b"x"), "trailing"),
        (raw_state(count=0, payload=1, body=b""), "payload byte count"),
    ],
)
def test_canonical_state_rejects_malformed_lengths_and_trailing_data(encoded: bytes, error: str) -> None:
    with pytest.raises(ValueError, match=error):
        BoundedReferenceCatalog.from_canonical_state(encoded)


def test_canonical_state_rejects_oversized_declared_state_before_parse() -> None:
    limits = CatalogLimits(max_catalog_items=1, max_catalog_bytes=2)
    too_many = raw_state(count=2, payload=0, body=b"")
    too_large = raw_state(count=0, payload=3, body=b"")
    with pytest.raises(CatalogBoundsError, match="item quota"):
        BoundedReferenceCatalog.from_canonical_state(too_many, limits=limits)
    with pytest.raises(CatalogBoundsError, match="byte quota"):
        BoundedReferenceCatalog.from_canonical_state(too_large, limits=limits)


def test_sorted_ids_and_full_reference_pages_are_deterministic() -> None:
    items = (entry(4), entry(1), entry(3), entry(2))
    catalog = catalog_of(*items)
    expected = tuple(item.logical_key for item in sorted(items, key=lambda item: item.logical_key))
    assert catalog.sorted_logical_ids(limit=4) == expected
    assert tuple(item.logical_key for item in catalog.full_reference_list(limit=4)) == expected
    assert catalog.sorted_logical_ids(offset=1, limit=2) == expected[1:3]


def test_exchange_exactly_at_limit_and_one_over_fails() -> None:
    items = tuple(entry(index) for index in range(MAX_EXCHANGE_ITEMS + 1))
    catalog = catalog_of(*items)
    page = catalog.sorted_logical_ids(limit=MAX_EXCHANGE_ITEMS)
    assert len(page) == MAX_EXCHANGE_ITEMS
    with pytest.raises(CatalogBoundsError, match="exchange page"):
        catalog.sorted_logical_ids(limit=MAX_EXCHANGE_ITEMS + 1)
    with pytest.raises(CatalogBoundsError, match="advertised_keys"):
        catalog.receiver_unknown_ids(tuple(item.logical_key for item in items))
    with pytest.raises(CatalogBoundsError, match="selected_keys"):
        catalog.pull_selected(tuple(item.logical_key for item in items))


def test_receiver_known_comparison_and_exact_set_difference() -> None:
    advertised = tuple(entry(index).logical_key for index in range(5))
    receiver = catalog_of(entry(1), entry(3), entry(8))
    assert receiver.receiver_known_ids(advertised) == (entry(1).logical_key, entry(3).logical_key)
    assert receiver.receiver_unknown_ids(advertised) == (
        entry(0).logical_key,
        entry(2).logical_key,
        entry(4).logical_key,
    )


def test_pull_selected_returns_only_requested_entries_in_key_order() -> None:
    sender = catalog_of(*(entry(index) for index in range(6)))
    pulled = sender.pull_selected((entry(4).logical_key, entry(1).logical_key))
    assert tuple(item.logical_key for item in pulled) == (entry(1).logical_key, entry(4).logical_key)
    with pytest.raises(LookupError, match="not present"):
        sender.pull_selected((b"missing",))


def test_reconcile_and_pull_transfers_only_selected_new_references() -> None:
    sender = catalog_of(*(entry(index) for index in range(6)))
    receiver = catalog_of(entry(0), entry(2), entry(5))
    advertised = sender.sorted_logical_ids(limit=6)
    selected = (entry(1).logical_key, entry(4).logical_key)
    result = reconcile_and_pull(
        sender,
        receiver,
        advertised_keys=advertised,
        selected_keys=selected,
    )
    assert result.receiver_known_keys == (entry(0).logical_key, entry(2).logical_key, entry(5).logical_key)
    assert result.candidate_keys == (entry(1).logical_key, entry(3).logical_key, entry(4).logical_key)
    assert result.selected_keys == selected
    assert tuple(item.logical_key for item in result.pulled_references) == selected
    assert entry(3).logical_key not in receiver
    assert all(result is MutationResult.ADDED for result in result.mutation_results)


def test_reconcile_selection_must_be_new_and_advertised() -> None:
    sender = catalog_of(entry(1), entry(2))
    receiver = catalog_of(entry(1))
    advertised = sender.sorted_logical_ids(limit=2)
    before = receiver.canonical_state()
    with pytest.raises(ValueError, match="subset"):
        reconcile_and_pull(
            sender,
            receiver,
            advertised_keys=advertised,
            selected_keys=(entry(1).logical_key,),
        )
    assert receiver.canonical_state() == before


def test_repeated_identical_offers_from_two_nodes_remain_one_entry() -> None:
    shared = entry(7)
    node_a = catalog_of(shared)
    node_c = catalog_of(shared)
    node_b = BoundedReferenceCatalog()
    assert node_b.add(node_a.get(shared.logical_key)) is MutationResult.ADDED
    assert node_b.add(node_a.get(shared.logical_key)) is MutationResult.NOOP_DUPLICATE
    assert node_b.add(node_c.get(shared.logical_key)) is MutationResult.NOOP_DUPLICATE
    assert len(node_b) == 1


def test_conflict_from_another_node_does_not_change_receiver() -> None:
    node_b = catalog_of(BoundedReference(b"X", b"AAA"))
    node_c = catalog_of(BoundedReference(b"X", b"BBB"))
    before = node_b.canonical_state()
    with pytest.raises(ReferenceConflictError):
        node_b.add_many(node_c.full_reference_list(limit=1))
    assert node_b.canonical_state() == before


def test_three_independent_nodes_diverge_then_converge_canonically() -> None:
    node_a = catalog_of(entry(0), entry(1), entry(2))
    node_b = catalog_of(entry(2), entry(3), entry(4))
    node_c = catalog_of(entry(4), entry(5), entry(0))
    assert len({node_a.state_digest, node_b.state_digest, node_c.state_digest}) == 3

    for sender, receiver in ((node_a, node_b), (node_b, node_c), (node_a, node_c)):
        advertised = sender.sorted_logical_ids(limit=len(sender))
        reconcile_and_pull(sender, receiver, advertised_keys=advertised)

    all_entries = tuple(entry(index) for index in range(6))
    for node in (node_a, node_b, node_c):
        node.add_many(reversed(all_entries))
    assert node_a.canonical_state() == node_b.canonical_state() == node_c.canonical_state()


def test_full_list_and_reconcile_delivery_produce_same_logical_state() -> None:
    sender = catalog_of(*(entry(index) for index in range(8)))
    full_receiver = BoundedReferenceCatalog()
    full_receiver.add_many(sender.full_reference_list(limit=8))
    reconciled_receiver = BoundedReferenceCatalog()
    reconcile_and_pull(
        sender,
        reconciled_receiver,
        advertised_keys=sender.sorted_logical_ids(limit=8),
    )
    assert full_receiver.canonical_state() == reconciled_receiver.canonical_state()


def test_two_materially_different_fixtures_use_the_same_catalog_class() -> None:
    package_key = hashlib.sha256(b"synthetic-package-canonical-bytes").digest()
    package_reference = json.dumps(
        {
            "schema": "scientific-package-pointer-v0",
            "package_id": package_key.hex(),
            "retrieval": ["coordinate-a", "coordinate-b"],
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    lawful_key = hashlib.sha256(b"synthetic-lawful-object-17").digest()
    lawful_reference = b"opaque-ref-v0\x00synthetic-coordinate\x00token-001122"

    fixtures = (
        BoundedReference(package_key, package_reference),
        BoundedReference(lawful_key, lawful_reference),
    )
    catalog = BoundedReferenceCatalog()
    assert catalog.add_many(fixtures) == (MutationResult.ADDED, MutationResult.ADDED)
    assert catalog.get(package_key).opaque_reference == package_reference
    assert catalog.get(lawful_key).opaque_reference == lawful_reference


def test_caller_may_ignore_candidate_without_catalog_side_effect() -> None:
    sender = catalog_of(entry(1), entry(2))
    receiver = BoundedReferenceCatalog()
    advertised = sender.sorted_logical_ids(limit=2)
    candidates = receiver.receiver_unknown_ids(advertised)
    caller_selection = candidates[:1]
    reconcile_and_pull(
        sender,
        receiver,
        advertised_keys=advertised,
        selected_keys=caller_selection,
    )
    assert len(receiver) == 1
    assert candidates[1] not in receiver


def test_generic_core_has_zero_forbidden_semantic_tokens_or_extra_dependencies() -> None:
    source = Path(catalog_module.__file__).read_text(encoding="utf-8").lower()
    forbidden = (
        "faro",
        "evidence",
        "recommendation",
        "machineprofile",
        "ds4",
        "metal",
        "magnet",
        "torrent",
        "uri",
        "dna",
        "travel",
    )
    assert {token for token in forbidden if token in source} == set()
    assert "pollicino.integrations" not in source
    assert "pollicino.net.store" not in source
