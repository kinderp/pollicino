from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path

from pollicino.net.catalog import (
    BoundedReference,
    BoundedReferenceCatalog,
    CatalogBoundsError,
    ReferenceConflictError,
    reconcile_and_pull,
)


ACCOUNTING_LABEL = "MODEL_PROTOCOL_ACCOUNTING_ONLY"
PAGE_ITEMS = 100
CONTROL_BYTES_PER_PAGE = 8
REFERENCE_SIZE = 512
SIZES = (10, 100, 1000)
OVERLAPS = (0.0, 0.5, 0.9, 0.99)
SELECTIONS = (1.0, 0.1, 0.01)
STRATEGIES = (
    "FULL_REFERENCE_LIST",
    "SORTED_IDS",
    "RECEIVER_KNOWN_IDS",
    "PULL_SELECTED",
    "RECONCILE_AND_PULL",
)


@dataclass(frozen=True, slots=True)
class AccountingRow:
    accounting: str
    catalog_size: int
    overlap: float
    selected_fraction: float
    strategy: str
    summary_control_bytes: int
    logical_id_bytes: int
    reference_bytes: int
    duplicate_bytes: int
    irrelevant_bytes: int
    total_modeled_bytes: int
    new_references: int
    selected_references: int
    duplicate_references: int


def key_for(index: int) -> bytes:
    return hashlib.sha256(f"px3-key-{index:06d}".encode("ascii")).digest()


def reference_for(index: int) -> bytes:
    seed = hashlib.sha256(f"px3-opaque-{index:06d}".encode("ascii")).digest()
    prefix = b"opaque-local-fixture-v0\x00"
    remaining = REFERENCE_SIZE - len(prefix)
    return prefix + (seed * math.ceil(remaining / len(seed)))[:remaining]


def fixture_entry(index: int) -> BoundedReference:
    return BoundedReference(key_for(index), reference_for(index))


def pages(items: int) -> int:
    return math.ceil(items / PAGE_ITEMS) if items else 0


def modeled_row(size: int, overlap: float, selection: float, strategy: str) -> AccountingRow:
    overlap_count = round(size * overlap)
    unknown_count = size - overlap_count
    selected_count = 0 if unknown_count == 0 else max(1, round(unknown_count * selection))
    selected_count = min(selected_count, unknown_count)
    id_unit = 2 + len(key_for(0))
    reference_unit = 4 + len(reference_for(0))
    full_unit = id_unit + reference_unit

    if strategy == "FULL_REFERENCE_LIST":
        control = pages(size) * CONTROL_BYTES_PER_PAGE
        ids = size * id_unit
        references = size * reference_unit
        duplicates = overlap_count * full_unit
        irrelevant = (unknown_count - selected_count) * full_unit
        new_references = unknown_count
        duplicate_references = overlap_count
    elif strategy == "SORTED_IDS":
        control = pages(size) * CONTROL_BYTES_PER_PAGE
        ids = size * id_unit
        references = 0
        duplicates = overlap_count * id_unit
        irrelevant = (unknown_count - selected_count) * id_unit
        new_references = 0
        duplicate_references = 0
    elif strategy == "RECEIVER_KNOWN_IDS":
        control = (pages(overlap_count) + pages(unknown_count)) * CONTROL_BYTES_PER_PAGE
        ids = (overlap_count + unknown_count) * id_unit
        references = unknown_count * reference_unit
        duplicates = overlap_count * id_unit
        irrelevant = (unknown_count - selected_count) * full_unit
        new_references = unknown_count
        duplicate_references = 0
    elif strategy == "PULL_SELECTED":
        control = pages(selected_count) * 2 * CONTROL_BYTES_PER_PAGE
        ids = selected_count * id_unit
        references = selected_count * reference_unit
        duplicates = 0
        irrelevant = 0
        new_references = selected_count
        duplicate_references = 0
    elif strategy == "RECONCILE_AND_PULL":
        control = (pages(size) + pages(selected_count) * 2) * CONTROL_BYTES_PER_PAGE
        ids = (size + selected_count) * id_unit
        references = selected_count * reference_unit
        duplicates = overlap_count * id_unit
        irrelevant = (unknown_count - selected_count) * id_unit
        new_references = selected_count
        duplicate_references = 0
    else:
        raise AssertionError(f"unknown strategy: {strategy}")

    return AccountingRow(
        accounting=ACCOUNTING_LABEL,
        catalog_size=size,
        overlap=overlap,
        selected_fraction=selection,
        strategy=strategy,
        summary_control_bytes=control,
        logical_id_bytes=ids,
        reference_bytes=references,
        duplicate_bytes=duplicates,
        irrelevant_bytes=irrelevant,
        total_modeled_bytes=control + ids + references,
        new_references=new_references,
        selected_references=selected_count,
        duplicate_references=duplicate_references,
    )


def build_matrix() -> tuple[list[dict[str, object]], dict[str, object]]:
    rows: list[dict[str, object]] = []
    for size in SIZES:
        for overlap in OVERLAPS:
            if round(size * overlap) >= size:
                continue
            for selection in SELECTIONS:
                for strategy in STRATEGIES:
                    rows.append(asdict(modeled_row(size, overlap, selection, strategy)))

    def find(strategy: str) -> dict[str, object]:
        return next(
            row
            for row in rows
            if row["catalog_size"] == 1000
            and row["overlap"] == 0.0
            and row["selected_fraction"] == 0.01
            and row["strategy"] == strategy
        )

    full = find("FULL_REFERENCE_LIST")
    reconcile = find("RECONCILE_AND_PULL")
    reduction = 1.0 - int(reconcile["total_modeled_bytes"]) / int(full["total_modeled_bytes"])
    target = {
        "catalog_size": 1000,
        "overlap": 0.0,
        "selected_fraction": 0.01,
        "baseline_strategy": "FULL_REFERENCE_LIST",
        "candidate_strategy": "RECONCILE_AND_PULL",
        "baseline_total_modeled_bytes": full["total_modeled_bytes"],
        "candidate_total_modeled_bytes": reconcile["total_modeled_bytes"],
        "reduction_fraction": reduction,
        "reduction_percent": reduction * 100,
        "success_threshold_percent": 50.0,
        "threshold_crossed": reduction >= 0.5,
    }
    return rows, target


def exchange_all(sender: BoundedReferenceCatalog, receiver: BoundedReferenceCatalog) -> None:
    offset = 0
    while True:
        advertised = sender.sorted_logical_ids(offset=offset)
        if not advertised:
            return
        reconcile_and_pull(sender, receiver, advertised_keys=advertised)
        offset += len(advertised)


def multi_node_record() -> dict[str, object]:
    node_a = BoundedReferenceCatalog()
    node_b = BoundedReferenceCatalog()
    node_c = BoundedReferenceCatalog()
    node_a.add_many(fixture_entry(index) for index in (0, 1, 2))
    node_b.add_many(fixture_entry(index) for index in (2, 3, 4))
    node_c.add_many(fixture_entry(index) for index in (4, 5, 0))
    initial = {name: node.state_digest.hex() for name, node in (("A", node_a), ("B", node_b), ("C", node_c))}

    contacts: list[dict[str, object]] = []
    for left_name, left, right_name, right in (
        ("A", node_a, "B", node_b),
        ("B", node_b, "C", node_c),
        ("A", node_a, "C", node_c),
    ):
        exchange_all(left, right)
        exchange_all(right, left)
        contacts.append(
            {
                "contact": f"{left_name}<->{right_name}",
                "left_items": len(left),
                "right_items": len(right),
                "left_digest": left.state_digest.hex(),
                "right_digest": right.state_digest.hex(),
            }
        )

    final = {name: node.state_digest.hex() for name, node in (("A", node_a), ("B", node_b), ("C", node_c))}
    return {
        "transport": "LOCAL_METHOD_CALLS_ONLY",
        "independent_initial_catalogs": len(set(initial.values())) == 3,
        "initial_digests": initial,
        "contacts": contacts,
        "final_digests": final,
        "deterministic_convergence": len(set(final.values())) == 1,
        "final_item_count": len(node_a),
    }


def conflict_record() -> dict[str, object]:
    receiver = BoundedReferenceCatalog()
    receiver.add(BoundedReference(b"X", b"AAA"))
    before_conflict = receiver.state_digest.hex()
    conflict = None
    try:
        receiver.add(BoundedReference(b"X", b"BBB"))
    except ReferenceConflictError:
        conflict = "REFERENCE_CONFLICT"
    after_conflict = receiver.state_digest.hex()

    limited = BoundedReferenceCatalog()
    limited.add(BoundedReference(b"Y", b"value"))
    before_bound = limited.state_digest.hex()
    bound = None
    try:
        limited.pull_selected(tuple(b"k" + bytes((index,)) for index in range(101)))
    except CatalogBoundsError:
        bound = "EXCHANGE_BOUND_REJECTED"
    after_bound = limited.state_digest.hex()
    return {
        "same_key_different_value": conflict,
        "conflict_state_unchanged": before_conflict == after_conflict,
        "one_over_exchange": bound,
        "bound_failure_state_unchanged": before_bound == after_bound,
        "conflict_arbitration": "NONE",
    }


def write_json(name: str, value: object) -> None:
    Path(__file__).with_name(name).write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    rows, target = build_matrix()
    multi_node = multi_node_record()
    conflicts = conflict_record()
    core_path = Path(__file__).parents[2] / "src/pollicino/net/catalog.py"
    source = core_path.read_text(encoding="utf-8").lower()
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
    matches = [token for token in forbidden if token in source]

    complexity = {
        "FULL_REFERENCE_LIST": {
            "new_parser": False,
            "new_schema": False,
            "new_persistent_state": False,
            "new_dependency": False,
            "algorithmic_complexity": "O(n log n) deterministic key ordering; O(n) exchange planning",
            "new_network_format": False,
        },
        "SORTED_IDS": {
            "new_parser": False,
            "new_schema": False,
            "new_persistent_state": False,
            "new_dependency": False,
            "algorithmic_complexity": "O(n log n) deterministic key ordering",
            "new_network_format": False,
        },
        "RECEIVER_KNOWN_IDS": {
            "new_parser": False,
            "new_schema": False,
            "new_persistent_state": False,
            "new_dependency": False,
            "algorithmic_complexity": "O(n + m) exact set membership after deterministic ordering",
            "new_network_format": False,
        },
        "PULL_SELECTED": {
            "new_parser": False,
            "new_schema": False,
            "new_persistent_state": False,
            "new_dependency": False,
            "algorithmic_complexity": "O(k log k) selected-key ordering and O(k) lookup",
            "new_network_format": False,
        },
        "RECONCILE_AND_PULL": {
            "new_parser": False,
            "new_schema": False,
            "new_persistent_state": False,
            "new_dependency": False,
            "algorithmic_complexity": "O(n log n + k log k) exact ordered reconciliation and pull",
            "new_network_format": False,
        },
    }

    write_json(
        "catalog-matrix.json",
        {
            "accounting": ACCOUNTING_LABEL,
            "encoding_model": {
                "control_bytes_per_page": CONTROL_BYTES_PER_PAGE,
                "logical_id_length_prefix_bytes": 2,
                "reference_length_prefix_bytes": 4,
                "max_page_items": PAGE_ITEMS,
                "reference_fixture_bytes": REFERENCE_SIZE,
                "diagnostic_note": "duplicate_bytes and irrelevant_bytes are subsets of logical_id_bytes/reference_bytes, not additional total fields",
            },
            "pre_registered_threshold": {
                "success": ">= 50% reduction in one size >= 100 sparse-interest workload",
                "kill_defer": "no >= 25% reduction in any size >= 100 workload",
            },
            "target_result": target,
            "complexity": complexity,
            "rows": rows,
        },
    )
    write_json("multi-node-fixtures.json", multi_node)
    write_json("conflict-matrix.json", conflicts)
    write_json(
        "genericity-matrix.json",
        {
            "same_core": "pollicino.net.catalog.BoundedReferenceCatalog",
            "fixtures": [
                {
                    "name": "FARO_LIKE_SANITIZED",
                    "source_evidence": "FARO PX2",
                    "final_closure": "6edf1f7d6f3ff91e07822a28910e7335958e1da3",
                    "runtime_dependency": False,
                    "semantic_parsing_in_core": False,
                },
                {
                    "name": "CONTENT_LIKE_SYNTHETIC_LAWFUL",
                    "external_contact": False,
                    "semantic_parsing_in_core": False,
                },
            ],
            "application_specific_core_branches": 0,
            "forbidden_semantic_token_matches": matches,
            "variant_model": "A_SINGLE_OPAQUE_REFERENCE",
            "new_dependency": False,
        },
    )

    ready = (
        bool(target["threshold_crossed"])
        and bool(multi_node["deterministic_convergence"])
        and bool(conflicts["conflict_state_unchanged"])
        and not matches
    )
    write_json(
        "gate-record.json",
        {
            "gate": "PX3-PN-D2",
            "classification": (
                "POLLICINO_BOUNDED_REFERENCE_CATALOG_LOCAL_READY" if ready else "INCONCLUSIVE"
            ),
            "confidence": "HIGH" if ready else "LOW",
            "base_commit": "750405a4aba86e7335141383396edf84347fc1d8",
            "branch": "pollicino/px3-pn-d2-bounded-reference-catalog",
            "docs_checkpoint": "7f6457427b68ec8145f992fb0bf81cade94e1e38",
            "implementation_commit": "5fd578ac54a223892ddaa692119606d9e99d151b",
            "observed_pr52_head_read_only": "be8bf8a8f3f9410efd3c82deaacd2f9917709f80",
            "pr52_dependency": "NONE",
            "network_used": "NOT_USED_BY_DESIGN",
            "benchmark": "NOT_RUN_BY_DESIGN",
            "accounting": ACCOUNTING_LABEL,
            "state_format": "LOCAL_CANONICAL_STATE_FORMAT",
            "network_wire_format_created": False,
            "variant_model": "A_SINGLE_OPAQUE_REFERENCE",
            "application_specific_core_branches": len(matches),
            "target_result": target,
            "advanced_reconciliation": "DEFERRED_NOT_JUSTIFIED",
            "next_gate": "PN-D2R",
        },
    )
    if not ready:
        raise AssertionError("PX3-PN-D2 experiment criteria did not pass")
    print(json.dumps({"ready": ready, "target_result": target}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
