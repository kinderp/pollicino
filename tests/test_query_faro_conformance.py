from __future__ import annotations

import base64
import copy
from dataclasses import replace
import hashlib
from pathlib import Path
import subprocess

import pytest

faro_profiles = pytest.importorskip(
    "faro_profiles", reason="exact FARO PX4 conformance source is optional"
)

from faro_profiles.contracts import canonical_json
from faro_profiles.import_transaction import logical_store_digest
from faro_profiles.local_registry_mock import LocalRegistryMock
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
from faro_profiles.registry_protocol import build_registry_query, parse_canonical_json_bytes
from faro_profiles.store import ROOT as FARO_ROOT, load_json
from faro_profiles.trust import (
    LocalTrustStore,
    import_transfer_artifact,
    sign_package,
    trust_decision,
    verify_envelope,
    write_signed_envelope,
)
from pollicino.net.catalog import BoundedReference
from pollicino.net.persistent_catalog import (
    PersistentBoundedReferenceCatalog,
    persist_reconcile_and_pull,
)
from pollicino.net.persistent_query import PersistentQueryResultStore
from pollicino.net.query import (
    QueryRecord,
    ResultRecord,
    ResultIdentity,
    evaluate_query,
    reconcile_queries,
    reconcile_results,
)


AUTO_PATH = FARO_ROOT / "artifacts" / "r2_auto_reference.faro.json"


def attach_catalog(root: Path):
    persistent = PersistentBoundedReferenceCatalog(root)
    source = FAROPollicinoDiscoverySource()
    source._catalog = persistent
    return source, persistent


def query_bytes(value: dict) -> bytes:
    return canonical_json(value).encode("utf-8")


def evaluate_faro(registry: LocalRegistryMock):
    def handler(opaque: bytes):
        response = registry.search(parse_canonical_json_bytes(opaque))
        return tuple(package_id_to_logical_key(item["package_id"]) for item in response["results"])
    return handler


def signed_fixture(tmp_path: Path):
    operator = tmp_path / "operator"; publisher = tmp_path / "publisher"
    initialize_publisher(operator, "PX6 operator")
    initialize_publisher(publisher, "PX6 publisher")
    operator_key, _ = signing_key(operator); publisher_key, _ = signing_key(publisher)
    package = load_json(AUTO_PATH)
    envelope = sign_package(package, publisher_key, publisher_label="PX6 fixture")
    artifact = tmp_path / "signed.faro.json"
    write_signed_envelope(envelope, artifact)
    registry = LocalRegistryMock(tmp_path / "registry", operator_key)
    registry.initialize(); published = registry.publish(artifact)
    assert published["result"] == "PUBLISHED"
    return package, envelope, artifact, registry, publisher


def synthetic_reference(index: int) -> FAROPollicinoReference:
    digest = lambda label: hashlib.sha256(label.encode("ascii")).hexdigest()
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


def test_exact_faro_px4_is_read_only() -> None:
    repository = Path(faro_profiles.__file__).resolve().parents[1]
    result = subprocess.run(
        ["git", "-C", str(repository), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    )
    assert result.stdout.strip() == "44af3e4f0fbdd4f3373a9d464f54892481f0d891"


def test_real_registry_query_positive_zero_and_external_evaluation(tmp_path: Path) -> None:
    package, _, _, registry, _ = signed_fixture(tmp_path)
    store = PersistentQueryResultStore(tmp_path / "query")
    catalog = PersistentBoundedReferenceCatalog(tmp_path / "catalog")
    adapter = FAROPollicinoAdapter(); reference = adapter.publish_package(
        canonical_json(sign_package(package, signing_key(tmp_path / "publisher")[0])).encode()
    )
    catalog.add(BoundedReference(
        package_id_to_logical_key(reference.package_id), reference.encode()
    ))
    positive = build_registry_query(package_type=package["package_type"])
    zero = build_registry_query(package_type="SYNTHETIC-NO-MATCH")
    store.add_query(QueryRecord(b"faro-positive", query_bytes(positive)))
    store.add_query(QueryRecord(b"faro-zero", query_bytes(zero)))
    evaluate_query(store, query_id=b"faro-positive", result_id=b"b-positive", catalog=catalog, handler=evaluate_faro(registry))
    evaluate_query(store, query_id=b"faro-zero", result_id=b"b-zero", catalog=catalog, handler=evaluate_faro(registry))
    assert store.results_for_query(b"faro-positive")[0].candidate_keys == (
        package_id_to_logical_key(package["package_id"]),
    )
    assert store.results_for_query(b"faro-zero")[0].candidate_keys == ()
    store.close(); catalog.close()


def test_async_faro_query_to_result_to_d2_px1_and_explicit_import(tmp_path: Path) -> None:
    package, envelope, artifact, registry, _ = signed_fixture(tmp_path)
    adapter = FAROPollicinoAdapter(); reference = adapter.publish_package(canonical_json(envelope).encode())
    source_b, catalog_b = attach_catalog(tmp_path / "catalog-b")
    source_b.advertise_reference(reference)
    with PersistentQueryResultStore(tmp_path / "query-a") as query_a:
        query_a.add_query(QueryRecord(b"q", query_bytes(build_registry_query(package_type=package["package_type"]))))
    with PersistentQueryResultStore(tmp_path / "query-a") as query_a, PersistentQueryResultStore(tmp_path / "query-b") as query_b:
        reconcile_queries(query_a, query_b, advertised_ids=query_a.sorted_query_ids())
        evaluate_query(query_b, query_id=b"q", result_id=b"b", catalog=catalog_b, handler=evaluate_faro(registry))
    knowledge = LocalKnowledgeStore(tmp_path / "knowledge"); knowledge.initialize()
    trust = LocalTrustStore(tmp_path / "trust")
    recommendation = {"result": "ADVISORY", "validated_here": False}
    before = (logical_store_digest(knowledge), trust.digest(), canonical_json(recommendation))
    with PersistentQueryResultStore(tmp_path / "query-a") as query_a, PersistentQueryResultStore(tmp_path / "query-b") as query_b:
        reconcile_results(query_b, query_a, advertised_ids=query_b.sorted_result_ids())
        candidate = query_a.get_result(ResultIdentity(b"q", b"b")).candidate_keys[0]
    source_a, catalog_a = attach_catalog(tmp_path / "catalog-a")
    assert len(catalog_a) == 0  # result receipt did not auto-pull
    persist_reconcile_and_pull(catalog_b, catalog_a, advertised_keys=(candidate,), selected_keys=(candidate,))
    discovered = source_a.get_reference(package["package_id"])
    fetched = adapter.retrieve_package(discovered)
    assert fetched.transport_exact and fetched.package_bytes == canonical_json(envelope).encode()
    assert before == (logical_store_digest(knowledge), trust.digest(), canonical_json(recommendation))
    receipt = import_transfer_artifact(artifact, knowledge)
    assert receipt["persistent_mutation"]
    assert logical_store_digest(knowledge) != before[0]
    catalog_a.close(); catalog_b.close()


def test_same_generic_result_preserves_local_trust_divergence(tmp_path: Path) -> None:
    _, envelope, _, _, publisher = signed_fixture(tmp_path)
    verification = verify_envelope(envelope)
    unknown_store = LocalTrustStore(tmp_path / "unknown")
    trusted_store = LocalTrustStore(tmp_path / "trusted")
    trusted_store.add(publisher / "publisher-public.pem", "PX6 publisher", trust_state="TRUSTED")
    generic = ResultIdentity(b"q", b"r")
    assert generic == ResultIdentity(b"q", b"r")
    assert trust_decision(verification, unknown_store)["trust_status"] == "UNKNOWN"
    assert trust_decision(verification, trusted_store)["trust_status"] == "TRUSTED"


def test_query_result_cannot_bypass_faro_variant_conflict(tmp_path: Path) -> None:
    first = synthetic_reference(1); second = replace(first, retrieval_hints=("other-provider",))
    source_a, a = attach_catalog(tmp_path / "a"); source_b, b = attach_catalog(tmp_path / "b")
    source_a.advertise_reference(first); source_b.advertise_reference(second)
    qs = PersistentQueryResultStore(tmp_path / "query")
    qs.add_query(QueryRecord(b"q", b"opaque"))
    qs.add_result(ResultRecord(
        b"q", b"r", (package_id_to_logical_key(first.package_id),)
    ))
    with pytest.raises(FARONativeCatalogError) as raised:
        source_a.advertise_reference(source_b.get_reference(first.package_id))
    assert raised.value.code == "REFERENCE_VARIANT_CONFLICT"
    qs.close(); a.close(); b.close()


def test_invalid_signature_remains_a_later_faro_layer(tmp_path: Path) -> None:
    _, envelope, _, _, _ = signed_fixture(tmp_path)
    changed = copy.deepcopy(envelope)
    signature = bytearray(base64.b64decode(changed["signatures"][0]["signature_base64"])); signature[0] ^= 1
    changed["signatures"][0]["signature_base64"] = base64.b64encode(signature).decode()
    bad_bytes = canonical_json(changed).encode()
    adapter = FAROPollicinoAdapter(); good = adapter.publish_package(canonical_json(envelope).encode())
    import pollicino.net as net
    locator = hashlib.sha256(bad_bytes).digest(); provider = net.InMemoryContentProvider(); provider.put(locator, bad_bytes)
    manifest = net.manifest_for_content(bad_bytes, object_class=0xF6, sources=(net.RetrievalSource(provider_id="bad", locator=locator),))
    coordinate = b"px6-invalid-signature"; resolver = net.InMemoryResolver(); resolver.register(coordinate, manifest)
    bad = replace(good, transport_sha256=hashlib.sha256(bad_bytes).hexdigest(), transport_manifest_sha256=hashlib.sha256(manifest.encode()).hexdigest(), rendezvous_key=coordinate, size_bytes=len(bad_bytes), retrieval_hints=("bad",))
    catalog = PersistentBoundedReferenceCatalog(tmp_path / "catalog")
    catalog.add(BoundedReference(package_id_to_logical_key(bad.package_id), bad.encode()))
    store = PersistentQueryResultStore(tmp_path / "query"); store.add_query(QueryRecord(b"q", b"opaque")); store.add_result(ResultRecord(b"q", b"r", (package_id_to_logical_key(bad.package_id),)))
    reconstructed, report = net.retrieve_exact(net.DiscoveryDescriptor(object_class=0xF6, rendezvous_key=coordinate, ttl_seconds=0, nonce=0), resolver=resolver, providers={"bad": provider})
    assert report.exact
    with pytest.raises(FAROPollicinoError) as raised:
        adapter.verify_reconstructed_package(bad, reconstructed)
    assert raised.value.code == "FARO_SIGNATURE_FAILURE"
    store.close(); catalog.close()
