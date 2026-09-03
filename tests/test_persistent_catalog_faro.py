from __future__ import annotations

import base64
import copy
from dataclasses import replace
import hashlib
import json
from pathlib import Path

import pytest

faro_profiles = pytest.importorskip("faro_profiles", reason="exact FARO PX4 conformance source is optional")

from faro_profiles.contracts import canonical_json
from faro_profiles.import_transaction import logical_store_digest
from faro_profiles.local_store import LocalKnowledgeStore
from faro_profiles.native_catalog import (
    FARONativeCatalogError,
    FAROPollicinoDiscoverySource,
    package_id_to_logical_key,
)
from faro_profiles.pollicino_adapter import (
    FAROPollicinoAdapter,
    FAROPollicinoError,
    FAROPollicinoReference,
)
from faro_profiles.publisher import initialize_publisher, signing_key
from faro_profiles.store import ROOT as FARO_ROOT, load_json
from faro_profiles.trust import (
    LocalTrustStore,
    import_transfer_artifact,
    sign_package,
    trust_decision,
    verify_envelope,
)
from pollicino.net.catalog import BoundedReference
import pollicino.net as net
from pollicino.net.persistent_catalog import PersistentBoundedReferenceCatalog


AUTO_PATH = FARO_ROOT / "artifacts" / "r2_auto_reference.faro.json"


def digest(label: str) -> str:
    return hashlib.sha256(label.encode("ascii")).hexdigest()


def reference(index: int) -> FAROPollicinoReference:
    return FAROPollicinoReference(
        package_id=f"faro-package-{index:020x}",
        package_schema="faro.knowledge-package.v0",
        faro_integrity_sha256=digest(f"integrity-{index}"),
        transport_sha256=digest(f"transport-{index}"),
        transport_manifest_sha256=digest(f"manifest-{index}"),
        rendezvous_key=bytes.fromhex(digest(f"coordinate-{index}")),
        size_bytes=1000 + index,
        retrieval_hints=(f"provider-{index}",),
    )


def attach(root: Path) -> tuple[FAROPollicinoDiscoverySource, PersistentBoundedReferenceCatalog]:
    persistent = PersistentBoundedReferenceCatalog(root)
    source = FAROPollicinoDiscoverySource()
    source._catalog = persistent
    return source, persistent


def test_01_faro_reference_survives_restart_and_reattachment(tmp_path: Path) -> None:
    source, persistent = attach(tmp_path / "node")
    expected = reference(1)
    assert source.advertise_reference(expected) == "ADDED"
    persistent.close()
    restarted, persistent = attach(tmp_path / "node")
    try:
        assert restarted.get_reference(expected.package_id) == expected
    finally:
        persistent.close()


def test_02_faro_a_to_b_pull_is_persisted_and_decodes_after_b_restart(tmp_path: Path) -> None:
    node_a, a = attach(tmp_path / "a")
    expected = reference(1)
    node_a.advertise_reference(expected)
    a.close()
    node_a, a = attach(tmp_path / "a")
    node_b, b = attach(tmp_path / "b")
    result = node_b.reconcile_from(node_a, selected_package_ids=(expected.package_id,))
    assert result.references == (expected,)
    b.close()
    node_b, b = attach(tmp_path / "b")
    try:
        assert node_b.get_reference(expected.package_id) == expected
    finally:
        a.close(); b.close()


def test_03_discovery_restart_does_not_mutate_knowledge_trust_or_recommendation(tmp_path: Path) -> None:
    knowledge = LocalKnowledgeStore(tmp_path / "knowledge"); knowledge.initialize()
    trust = LocalTrustStore(tmp_path / "trust")
    recommendation = {"schema_version": "faro.recommendation.v0", "result": "ADVISORY"}
    before = (logical_store_digest(knowledge), trust.digest(), canonical_json(recommendation))
    source, persistent = attach(tmp_path / "catalog")
    source.advertise_reference(reference(1)); persistent.close()
    source, persistent = attach(tmp_path / "catalog")
    persistent.close()
    assert before == (logical_store_digest(knowledge), trust.digest(), canonical_json(recommendation))


def test_04_px1_exact_fetch_after_catalog_restart(tmp_path: Path) -> None:
    package_bytes = canonical_json(load_json(AUTO_PATH)).encode()
    adapter = FAROPollicinoAdapter()
    expected = adapter.publish_package(package_bytes)
    source, persistent = attach(tmp_path / "catalog")
    source.advertise_reference(expected); persistent.close()
    source, persistent = attach(tmp_path / "catalog")
    try:
        result = adapter.retrieve_package(source.get_reference(expected.package_id))
        assert result.transport_exact
        assert result.package_bytes == package_bytes
    finally:
        persistent.close()


def test_05_fetch_does_not_import_and_explicit_import_still_works(tmp_path: Path) -> None:
    package_bytes = canonical_json(load_json(AUTO_PATH)).encode()
    knowledge = LocalKnowledgeStore(tmp_path / "knowledge"); knowledge.initialize()
    before = logical_store_digest(knowledge)
    adapter = FAROPollicinoAdapter(); expected = adapter.publish_package(package_bytes)
    source, persistent = attach(tmp_path / "catalog")
    source.advertise_reference(expected); persistent.close()
    source, persistent = attach(tmp_path / "catalog")
    fetched = adapter.retrieve_package(source.get_reference(expected.package_id)); persistent.close()
    assert logical_store_digest(knowledge) == before
    artifact = tmp_path / "selected.faro.json"; artifact.write_bytes(fetched.package_bytes)
    receipt = import_transfer_artifact(artifact, knowledge)
    assert receipt["persistent_mutation"]
    assert logical_store_digest(knowledge) != before


def test_06_trust_divergence_survives_identical_persistent_state(tmp_path: Path) -> None:
    publisher = tmp_path / "publisher"; initialize_publisher(publisher, "PX5 Publisher")
    private, _ = signing_key(publisher)
    envelope = sign_package(load_json(AUTO_PATH), private)
    adapter = FAROPollicinoAdapter(); expected = adapter.publish_package(canonical_json(envelope).encode())
    states = []
    for name in ("b", "c"):
        source, persistent = attach(tmp_path / name); source.advertise_reference(expected)
        states.append(source.canonical_state); persistent.close()
    verification = verify_envelope(json.loads(adapter.retrieve_package(expected).package_bytes))
    unknown = trust_decision(verification, LocalTrustStore(tmp_path / "unknown"))
    trusted_store = LocalTrustStore(tmp_path / "trusted")
    trusted_store.add(publisher / "publisher-public.pem", "PX5 Publisher", trust_state="TRUSTED")
    trusted = trust_decision(verification, trusted_store)
    assert states[0] == states[1]
    assert unknown["trust_status"] == "UNKNOWN"
    assert trusted["trust_status"] == "TRUSTED"


def test_07_faro_compatible_variant_conflict_survives_restart(tmp_path: Path) -> None:
    first = reference(1); second = replace(first, retrieval_hints=("other-provider",))
    source, persistent = attach(tmp_path / "node"); source.advertise_reference(first); persistent.close()
    source, persistent = attach(tmp_path / "node")
    before = source.canonical_state
    with pytest.raises(FARONativeCatalogError) as raised: source.advertise_reference(second)
    assert raised.value.code == "REFERENCE_VARIANT_CONFLICT"
    assert source.canonical_state == before
    persistent.close()
    source, persistent = attach(tmp_path / "node")
    try: assert source.get_reference(first.package_id) == first
    finally: persistent.close()


def test_08_incompatible_identity_conflict_survives_restart(tmp_path: Path) -> None:
    first = reference(1); second = replace(first, faro_integrity_sha256=digest("different"))
    source, persistent = attach(tmp_path / "node"); source.advertise_reference(first); persistent.close()
    source, persistent = attach(tmp_path / "node")
    with pytest.raises(FARONativeCatalogError) as raised: source.advertise_reference(second)
    assert raised.value.code == "REFERENCE_CONFLICT"
    persistent.close()


def test_09_malformed_faro_bytes_persist_generically_then_decode_fails(tmp_path: Path) -> None:
    expected = reference(1)
    with PersistentBoundedReferenceCatalog(tmp_path / "node") as catalog:
        catalog.add(BoundedReference(package_id_to_logical_key(expected.package_id), b"not-json"))
    source, persistent = attach(tmp_path / "node")
    try:
        with pytest.raises(FARONativeCatalogError) as raised: source.get_reference(expected.package_id)
        assert raised.value.code == "REFERENCE_DECODE_FAILURE"
    finally: persistent.close()


def test_10_invalid_signature_remains_distinct_after_restart(tmp_path: Path) -> None:
    publisher = tmp_path / "publisher"; initialize_publisher(publisher, "PX5 Publisher")
    private, _ = signing_key(publisher)
    envelope = sign_package(load_json(AUTO_PATH), private)
    changed = copy.deepcopy(envelope)
    signature = bytearray(base64.b64decode(changed["signatures"][0]["signature_base64"]))
    signature[0] ^= 1
    changed["signatures"][0]["signature_base64"] = base64.b64encode(signature).decode()
    bad_bytes = canonical_json(changed).encode()
    adapter = FAROPollicinoAdapter()
    good = adapter.publish_package(canonical_json(envelope).encode())
    locator = hashlib.sha256(bad_bytes).digest()
    provider = net.InMemoryContentProvider(); provider.put(locator, bad_bytes)
    manifest = net.manifest_for_content(
        bad_bytes,
        object_class=0xF5,
        sources=(net.RetrievalSource(provider_id="invalid-signature", locator=locator),),
    )
    coordinate = b"px5-invalid-signature"
    resolver = net.InMemoryResolver(); resolver.register(coordinate, manifest)
    expected = replace(
        good,
        transport_sha256=hashlib.sha256(bad_bytes).hexdigest(),
        transport_manifest_sha256=hashlib.sha256(manifest.encode()).hexdigest(),
        rendezvous_key=coordinate,
        size_bytes=len(bad_bytes),
        retrieval_hints=("invalid-signature",),
    )
    source, persistent = attach(tmp_path / "node"); source.advertise_reference(expected); persistent.close()
    source, persistent = attach(tmp_path / "node")
    persisted = source.get_reference(expected.package_id); persistent.close()
    reconstructed, report = net.retrieve_exact(
        net.DiscoveryDescriptor(object_class=0xF5, rendezvous_key=coordinate, ttl_seconds=0, nonce=0),
        resolver=resolver,
        providers={"invalid-signature": provider},
    )
    assert report.exact
    with pytest.raises(FAROPollicinoError) as raised:
        adapter.verify_reconstructed_package(persisted, reconstructed)
    assert raised.value.code == "FARO_SIGNATURE_FAILURE"


def test_11_three_persistent_holders_do_not_create_science(tmp_path: Path) -> None:
    recommendation = {"evidence_grade": "E3", "result": "DO_NOT_PROMOTE"}
    before = canonical_json(recommendation)
    for name in "abc":
        source, persistent = attach(tmp_path / name); source.advertise_reference(reference(1)); persistent.close()
    assert canonical_json(recommendation) == before


def test_12_exact_px4_source_is_unmodified() -> None:
    source = Path(faro_profiles.__file__).resolve().parents[1]
    completed = __import__("subprocess").run(
        ["git", "-C", str(source), "rev-parse", "HEAD"], check=True, text=True, capture_output=True
    )
    assert completed.stdout.strip() == "44af3e4f0fbdd4f3373a9d464f54892481f0d891"
